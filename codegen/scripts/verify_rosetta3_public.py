# ruff: noqa: C901, EM101, EM102, INP001, PLC0415, PLR0912, PLR0915, PLR2004, S603, T201, TRY003
"""Verify installed public APIs against the existing, unchanged upstream fixtures."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from verify_rosetta3_targets import compare


ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, context: str) -> None:  # noqa: FBT001
    if not condition:
        raise AssertionError(context)


def run(model_path: Path | None, build: Path, rust: Path, *, builtin: bool = False) -> None:
    from ptfkit import zhang_schaap2017 as api
    from ptfkit.models import Model, ModelIntegrityError

    refs = json.loads((ROOT / 'specs/models/rosetta3/reference.json').read_text(encoding='utf-8'))
    require(len(refs['cases']) == 120, 'incomplete frozen reference cases')
    if builtin:
        model = api.Rosetta3()
        generic = model.model
    else:
        if model_path is None:
            raise ValueError('an external model path is required without --builtin')
        model = api.Rosetta3.load(model_path)
        generic = Model.load(model_path, api.MODEL_SHA256)
    selector = '--builtin' if builtin else str(model_path)
    require(generic.sha256 == api.MODEL_SHA256, 'wrong loaded digest')
    suffix = '.exe' if rust.suffix == '.exe' else ''
    executables = {
        'c11': build / f'rosetta_public_c{suffix}',
        'cpp23': build / f'rosetta_public_cpp{suffix}',
        'rust': rust,
    }
    modes = {
        'arith': api.Estimate.ARITHMETIC,
        'log': api.Estimate.LOG10,
        'geo': api.Estimate.GEOMETRIC,
    }
    predictors = ('sand', 'silt', 'clay', 'bulk_density', 'theta_33', 'theta_1500')
    invalid = list(refs['validation_cases'])
    for level, mode, inputs in [
        (0, 0, [40, 40, 20]),
        (6, 0, [40, 40, 20]),
        (2, 3, [40, 40, 20]),
        (5, 0, [40, 40, 20]),
    ]:
        invalid.append(
            {'id': f'level_{level}_mode_{mode}', 'level': level, 'mode': mode, 'inputs': inputs}
        )
    for i in range(6):
        for value in ('nan', 'inf', '-inf'):
            inputs = [30, 30, 40, 1.5, 0.3, 0.1]
            inputs[i] = value
            invalid.append({'id': f'nonfinite_{i}_{value}', 'inputs': inputs})
    for target in ('python', *executables):
        max_abs = max_rel = 0.0
        for case in refs['cases']:
            level, inputs, mode = case['level'], case['inputs'], modes[case['mode']]
            if target == 'python':
                result = model.predict(level, inputs, mode)
                actual = list(result.mean + result.stddev)
                if mode == api.Estimate.ARITHMETIC:
                    named = getattr(api, f'calc_ptf_zhang2017_mod{level}')(
                        model, **dict(zip(predictors[: len(inputs)], inputs, strict=True))
                    )
                    require(named == result, f'public function differs: {case["id"]}')
            else:
                output = subprocess.check_output(
                    [
                        str(executables[target]),
                        selector,
                        str(level),
                        str(int(mode)),
                        *map(str, inputs),
                    ],
                    text=True,
                )
                actual = [float(v) for v in output.split()]
            absolute, relative = compare(actual, case['mean'] + case['std'], case['id'])
            max_abs, max_rel = max(max_abs, absolute), max(max_rel, relative)
        for case in invalid:
            inputs = [float(v) for v in case['inputs']]
            level, mode = case.get('level', len(inputs) - 1), case.get('mode', 0)
            if target == 'python':
                try:
                    model.predict(level, inputs, mode)
                except ValueError:
                    pass
                else:
                    raise AssertionError(f'invalid predictors accepted: {case["id"]}')
            else:
                result = subprocess.run(
                    [
                        str(executables[target]),
                        selector,
                        str(level),
                        str(mode),
                        *map(str, inputs),
                    ],
                    capture_output=True,
                    check=False,
                )
                require(result.returncode == 15, f'{target} {case["id"]}: {result.returncode}')
        print(f'{target}: 120 upstream cases, max abs {max_abs:.4e}, max rel {max_rel:.4e}')
        print(f'{target}: {len(invalid)} rejected predictor/level/mode cases')
    # Retain the original raw-member oracle, in addition to summary statistics.
    for case in refs['cases']:
        raw = generic.predict_network(case['level'] - 2, case['inputs'])
        for member in case['raw_members']:
            for actual, expected in zip(raw[member['index']], member['values'], strict=True):
                require(
                    abs(actual - expected) <= max(1e-11, 1e-12 * abs(expected)),
                    'raw member differs',
                )
    if builtin:
        print(
            'Bundled model: no model path supplied; '
            'original members and invalid predictors verified'
        )
        return
    if model_path is None:
        raise ValueError('missing external model path')
    with tempfile.TemporaryDirectory(prefix='ptfkit-model-integrity-') as temp:
        damaged = Path(temp) / 'damaged.ptfm'
        data = bytearray(model_path.read_bytes())
        data[-1] ^= 1
        damaged.write_bytes(data)
        try:
            api.Rosetta3.load(damaged)
        except ModelIntegrityError:
            pass
        else:
            raise AssertionError('Python accepted changed parameters')
        for target, executable in executables.items():
            result = subprocess.run(
                [str(executable), str(damaged), '2', '0', '40', '40', '20'],
                capture_output=True,
                check=False,
            )
            require(result.returncode == 12, f'{target} changed file: {result.returncode}')
            missing = subprocess.run(
                [str(executable), str(Path(temp) / 'missing.ptfm'), '2', '0', '40', '40', '20'],
                capture_output=True,
                check=False,
            )
            require(missing.returncode == 11, f'{target} missing file: {missing.returncode}')
    print('Public model handles: original members, invalid predictors and tampered files verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path)
    parser.add_argument('--builtin', action='store_true')
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--rust', type=Path, required=True)
    args = parser.parse_args()
    run(
        args.model.resolve() if args.model else None,
        args.build.resolve(),
        args.rust.resolve(),
        builtin=args.builtin,
    )
