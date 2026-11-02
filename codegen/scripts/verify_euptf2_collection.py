# ruff: noqa: C901, EM101, EM102, INP001, PLC0415, PLR0912, PLR0915, PLR2004, S603, T201, TRY003
"""Check every implemented original model against independent upstream R fixtures."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def compare(actual: list[float], expected: list[float], context: str) -> tuple[float, float]:
    if len(actual) != len(expected):
        raise AssertionError(f'{context}: output shape {len(actual)} != {len(expected)}')
    absolute = relative = 0.0
    for a, e in zip(actual, expected, strict=True):
        # Binary64 forest aggregation, interpolation, and original exponential transforms.
        if not math.isfinite(a) or abs(a - e) > max(2e-14, 2e-13 * abs(e)):
            raise AssertionError(f'{context}: {a} != {e}')
        absolute = max(absolute, abs(a - e))
        if e:
            relative = max(relative, abs(a - e) / abs(e))
    return absolute, relative


def run(args: argparse.Namespace) -> dict:
    collection = json.loads((ROOT / 'specs/models/euptf2/collection.json').read_text())
    selected = [m for m in collection['models'] if m['status'] == 'implemented']
    if not selected:
        raise AssertionError('no implemented model cases')
    suffix = '.exe' if args.rust.suffix == '.exe' else ''
    executables = {
        'rust': args.rust,
        'c11': args.build / f'euptf2_public_c{suffix}',
        'cpp23': args.build / f'euptf2_public_cpp{suffix}',
    }
    if 'python' in args.targets:
        from ptfkit import szabo_weynants_weber2021 as scientific
        from ptfkit.models import Euptf2Model, ModelInputError, ModelIntegrityError, euptf2_models

        if set(euptf2_models()) != {m['name'] for m in selected}:
            raise AssertionError('Python model registry differs from the inventory')
    report = {
        'models': [],
        'available': len(collection['models']),
        'implemented': len(selected),
        'blocked': sum(m['status'] == 'blocked' for m in collection['models']),
    }
    for model in selected:
        name = model['name']
        reference = json.loads(
            (ROOT / 'specs/models/euptf2/references' / f'{name}.json').read_text()
        )
        if reference['features'] != model['features']:
            raise AssertionError(
                f'{name}: predictor ordering differs from the independent R reference'
            )
        for group in ['cases', 'custom_cases']:
            for case in reference[group]:
                case['inputs'] = [float(x) for x in case['inputs']]
        count = {'VG': 25, 'MVG': 31}.get(model['family'], 16)
        if len(reference['cases']) != count or len(reference['custom_cases']) != 2:
            raise AssertionError(f'{name}: incomplete upstream cases')
        path = args.models / f'{name}.ptfq'
        cases = reference['cases']
        invalid = []
        for feature in range(len(model['features'])):
            values = list(cases[0]['inputs'])
            values[feature] = float('nan')
            invalid.append(values)
        invalid.extend([cases[0]['inputs'][:-1], [*cases[0]['inputs'], 0]])
        record = {'name': name, 'targets': {}}
        for target in args.targets:
            maximum_abs = maximum_rel = 0.0
            if target == 'python':
                loaded = Euptf2Model.load(name, path)
                if (
                    loaded.inputs != tuple(model['features'])
                    or loaded.mean_outputs != tuple(model['mean_outputs'])
                    or loaded.quantile_outputs != tuple(model['quantile_outputs'])
                ):
                    raise AssertionError(f'{name}: Python metadata differs')
            for group, probabilities in [
                ('cases', reference['probabilities']),
                ('custom_cases', reference['custom_probabilities']),
            ]:
                current = reference[group]
                if target == 'python':
                    rows = []
                    for case in current:
                        prediction = loaded.predict(case['inputs'], probabilities)
                        flat = list(prediction.mean) + [
                            v for row in prediction.quantiles for v in row
                        ]
                        if group == 'cases':
                            function = getattr(scientific, f'calc_ptf_szabo2021_{name.lower()}')
                            named = function(
                                loaded,
                                **dict(
                                    zip(
                                        (f.lower() for f in model['features']),
                                        case['inputs'],
                                        strict=True,
                                    )
                                ),
                            )
                            if list(named) != flat:
                                raise AssertionError(
                                    f'{name}: named and generic predictions differ'
                                )
                            flat = list(named)
                        rows.append(flat)
                else:
                    command = [str(executables[target]), '--collection', name, str(path)]
                    if group == 'custom_cases':
                        command.extend(map(str, probabilities))
                    inputs = '\n'.join(' '.join(map(str, c['inputs'])) for c in current) + '\n'
                    output = subprocess.check_output(command, input=inputs, text=True)
                    rows = [[float(v) for v in line.split()] for line in output.splitlines()]
                if len(rows) != len(current):
                    raise AssertionError(f'{target}/{name}: missing output rows')
                for index, (actual, case) in enumerate(zip(rows, current, strict=True)):
                    means = case.get('mean', cases[index]['mean'])
                    if isinstance(means, (float, int)):
                        means = [means]
                    absolute, relative = compare(
                        actual, list(means) + case['quantiles'], f'{target}/{name}/{group}/{index}'
                    )
                    maximum_abs = max(maximum_abs, absolute)
                    maximum_rel = max(maximum_rel, relative)
            if target == 'python':
                for values in invalid:
                    try:
                        loaded.predict(values)
                    except ModelInputError:
                        pass
                    else:
                        raise AssertionError(f'{name}: invalid predictors accepted')
                for probabilities in ([0, 0.5], [0.5, 1], [float('nan')], [-0.1], [0.5] * 65):
                    try:
                        loaded.predict(cases[0]['inputs'], probabilities)
                    except (ModelInputError, ValueError):
                        pass
                    else:
                        raise AssertionError(f'{name}: invalid quantiles accepted')
            else:
                command = [str(executables[target]), '--collection', name, str(path)]
                output = subprocess.check_output(
                    command,
                    input='\n'.join(' '.join(map(str, x)) for x in invalid) + '\n',
                    text=True,
                )
                if output.splitlines() != ['error15'] * len(invalid):
                    raise AssertionError(f'{target}/{name}: wrong invalid-input behavior')
                output = subprocess.check_output(
                    [*command, '0', '.5'],
                    input=' '.join(map(str, cases[0]['inputs'])) + '\n',
                    text=True,
                )
                if output.strip() != 'error15':
                    raise AssertionError(f'{target}/{name}: invalid probability accepted')
            with tempfile.TemporaryDirectory() as temporary:
                changed = Path(temporary) / 'changed.ptfq'
                data = bytearray(path.read_bytes())
                data[-1] ^= 1
                changed.write_bytes(data)
                if target == 'python':
                    try:
                        Euptf2Model.load(name, changed)
                    except ModelIntegrityError:
                        pass
                    else:
                        raise AssertionError(f'{name}: corruption accepted')
                else:
                    result = subprocess.run(
                        [str(executables[target]), '--collection', name, str(changed)],
                        capture_output=True,
                        check=False,
                    )
                    if result.returncode != 12:
                        raise AssertionError(
                            f'{target}/{name}: wrong integrity error {result.returncode}'
                        )
            record['targets'][target] = {
                'default_cases': count,
                'custom_cases': 2,
                'missing_and_shape_rejections': len(invalid),
                'integrity_rejections': 1,
                'max_absolute_error': maximum_abs,
                'max_relative_error': maximum_rel,
            }
        report['models'].append(record)
        print(f'{name}: {count} default + 2 custom cases per target passed', flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--build', type=Path, default=ROOT / 'targets/ptfkit-native/build/tests')
    parser.add_argument(
        '--rust',
        type=Path,
        default=ROOT / 'targets/ptfkit-rs/target/debug/examples/euptf2_runner.exe',
    )
    parser.add_argument(
        '--targets',
        nargs='+',
        choices=['python', 'rust', 'c11', 'cpp23'],
        default=['python', 'rust', 'c11', 'cpp23'],
    )
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = run(args)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
