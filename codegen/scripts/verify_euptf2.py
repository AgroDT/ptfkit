# ruff: noqa: C901, EM101, EM102, INP001, PLC0415, PLR0912, PLR2004, S603, T201, TRY003
"""Compare all four public targets with frozen predictions from upstream R."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(model_path: Path, build: Path, rust: Path) -> None:
    from ptfkit.models import Euptf2Ths, ModelInputError, ModelIntegrityError

    refs = json.loads((ROOT / 'specs/models/euptf2/reference.json').read_text())
    if len(refs['cases']) != 60:
        raise AssertionError('incomplete upstream reference fixture')
    suffix = rust.suffix
    executables = {
        'c11': build / f'euptf2_public_c{suffix}',
        'cpp23': build / f'euptf2_public_cpp{suffix}',
        'rust': rust,
    }
    model = Euptf2Ths.load(model_path)
    for name in ('python', *executables):
        maximum = 0.0
        for i, case in enumerate(refs['cases']):
            if name == 'python':
                actual = model.predict(*case['inputs'])
            else:
                output = subprocess.check_output(
                    [str(executables[name]), str(model_path), *map(str, case['inputs'])],
                    text=True,
                )
                actual = [float(v) for v in output.split()]
            if len(actual) != 4:
                raise AssertionError(f'{name}: output shape')
            for a, e in zip(actual, case['expected'], strict=True):
                # 200 scalar additions and type-7 interpolation, all binary64.
                if not math.isfinite(a) or abs(a - e) > 2e-14:
                    raise AssertionError(f'{name} case {i}: {a} != {e}')
                maximum = max(maximum, abs(a - e))
        for feature in range(4):
            values = [40.0, 40.0, 20.0, 30.0]
            values[feature] = float('nan')
            if name == 'python':
                try:
                    model.predict(*values)
                except ModelInputError:
                    pass
                else:
                    raise AssertionError('missing predictor accepted')
            else:
                result = subprocess.run(
                    [str(executables[name]), str(model_path), *map(str, values)],
                    check=False,
                    capture_output=True,
                )
                if result.returncode != 15:
                    raise AssertionError(f'{name}: wrong missing-input error {result.returncode}')
        print(f'{name}: 60 upstream cases, 4 missing-input cases; max absolute error {maximum:.3g}')

    with tempfile.TemporaryDirectory() as temporary:
        damaged = Path(temporary) / 'changed.ptfq'
        data = bytearray(model_path.read_bytes())
        data[-1] ^= 1
        damaged.write_bytes(data)
        try:
            Euptf2Ths.load(damaged)
        except ModelIntegrityError:
            pass
        else:
            raise AssertionError('changed artifact accepted')
        for name, executable in executables.items():
            result = subprocess.run(
                [str(executable), str(damaged), '40', '40', '20', '30'],
                capture_output=True,
                check=False,
            )
            if result.returncode != 12:
                raise AssertionError(f'{name}: wrong integrity error {result.returncode}')
    print('all four targets rejected a changed artifact')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--rust', type=Path, required=True)
    args = parser.parse_args()
    run(args.model.resolve(), args.build.resolve(), args.rust.resolve())
