# ruff: noqa: C901, EM101, EM102, INP001, PLR0912, PLR0915, PLR2004, S603, T201, TRY003
"""Compare built local native targets with frozen, actually executed upstream results."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODES = {'arith': 0, 'log': 1, 'geo': 2}


def compare(actual: list[float], expected: list[float], name: str) -> tuple[float, float]:
    if len(actual) != 14 or len(expected) != 14:
        raise AssertionError(f'incomplete outputs: {name}')
    max_abs = max_rel = 0.0
    for i, (value, reference) in enumerate(zip(actual, expected, strict=True)):
        difference = abs(value - reference)
        # This is a numerical reproduction check, deliberately much tighter
        # than physical predictive accuracy. See the committed audit report.
        if not math.isfinite(value) or difference > max(1e-11, 1e-12 * abs(reference)):
            raise AssertionError(f'{name} output {i}: {value} != {reference}')
        max_abs = max(max_abs, difference)
        max_rel = max(max_rel, difference / max(abs(reference), 1e-300))
    return max_abs, max_rel


def run(build: Path, rust: Path, reference: Path, output: Path) -> None:
    refs = json.loads(reference.read_text(encoding='utf-8'))
    manifest_path = ROOT / 'specs/models/rosetta3/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (
        refs['provenance']['revision'] != manifest['revision']
        or refs['provenance']['manifest_sha256']
        != hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    ):
        raise AssertionError('reference provenance differs from the reviewed manifest')
    cases = refs['cases']
    if len(cases) != 120 or {c['level'] for c in cases} != {2, 3, 4, 5}:
        raise AssertionError('incomplete upstream case coverage')
    # This extension uses only the CPython C API and the native C engine.
    sys.path.insert(0, str(build))
    native = importlib.import_module('_rosetta3_local')
    suffix = '.exe' if sys.platform == 'win32' else ''
    binaries = {
        'c11': build / f'rosetta_c{suffix}',
        'cpp23': build / f'rosetta_cpp{suffix}',
        'rust': rust,
    }
    report = {}
    baseline = {}
    validation_cases = list(refs['validation_cases'])
    for level, mode, inputs in [
        (0, 0, [40, 40, 20]),
        (6, 0, [40, 40, 20]),
        (2, 3, [40, 40, 20]),
        (5, 0, [40, 40, 20]),
    ]:
        validation_cases.append(
            {'id': f'level_{level}_mode_{mode}', 'level': level, 'mode': mode, 'inputs': inputs}
        )
    for i in range(6):
        for value in ('nan', 'inf', '-inf'):
            inputs = [30, 30, 40, 1.5, 0.3, 0.1]
            inputs[i] = value
            validation_cases.append({'id': f'nonfinite_{i}_{value}', 'inputs': inputs})
    for target in ('c11', 'cpp23', 'rust', 'python_native'):
        max_abs = max_rel = max_cross = 0.0
        start = time.perf_counter()
        for case in cases:
            level, mode, inputs = case['level'], MODES[case['mode']], case['inputs']
            if target == 'python_native':
                actual = list(native.calc_ptf_zhang2017(level, mode, inputs))
            else:
                raw = subprocess.check_output(
                    [str(binaries[target]), str(level), str(mode), *map(str, inputs)], text=True
                )
                actual = [float(v) for v in raw.split()]
            absolute, relative = compare(actual, case['mean'] + case['std'], case['id'])
            max_abs, max_rel = max(max_abs, absolute), max(max_rel, relative)
            if target == 'c11':
                baseline[case['id']] = actual
            else:
                cross, _ = compare(actual, baseline[case['id']], case['id'])
                max_cross = max(max_cross, cross)
        report[target] = {
            'cases': len(cases),
            'max_absolute_difference': max_abs,
            'max_relative_difference': max_rel,
            'max_cross_target_difference': max_cross,
            'seconds_including_process_startup': time.perf_counter() - start,
        }
        for case in validation_cases:
            inputs = [float(v) for v in case['inputs']]
            level, mode = case.get('level', len(inputs) - 1), case.get('mode', 0)
            # Deliberate API difference: explicitly selected levels reject an
            # invalid predictor instead of upstream's best-available downgrade.
            if target == 'python_native':
                try:
                    native.calc_ptf_zhang2017(level, mode, inputs)
                except ValueError:
                    pass
                else:
                    raise AssertionError(f'accepted invalid inputs: {case["id"]}')
            else:
                result = subprocess.run(
                    [str(binaries[target]), str(level), str(mode), *map(str, inputs)],
                    capture_output=True,
                    check=False,
                )
                if result.returncode != 3:
                    raise AssertionError(
                        f'incorrect invalid-input behavior: {target} '
                        f'{case["id"]}: {result.returncode}'
                    )
        report[target]['rejection_cases'] = len(validation_cases)
        print(
            f'{target}: {len(cases)} upstream cases, max abs {max_abs:.4e}, max rel {max_rel:.4e}'
        )
    # Isolate repeated inference cost from command-line process startup.
    inputs = [30, 30, 40, 1.5, 0.3, 0.1]
    start = time.perf_counter()
    for _ in range(1000):
        native.calc_ptf_zhang2017(5, 0, inputs)
    report['python_native']['microseconds_per_prediction'] = (time.perf_counter() - start) * 1000
    report['files_bytes'] = {
        p.name: p.stat().st_size
        for p in [
            *binaries.values(),
            *build.glob('*rosetta3_local*.pyd'),
            *build.glob('*rosetta3_local*.so'),
        ]
    }
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, type=Path)
    parser.add_argument('--rust', required=True, type=Path)
    parser.add_argument(
        '--reference', type=Path, default=ROOT / 'specs/models/rosetta3/reference.json'
    )
    parser.add_argument('--report', type=Path, default=ROOT / '.rosetta-local/comparison.json')
    args = parser.parse_args()
    run(args.build.resolve(), args.rust.resolve(), args.reference.resolve(), args.report.resolve())
