# ruff: noqa: C901, EM101, EM102, INP001, PLC0415, T201, TRY003
"""Execute the verified upstream implementation to create immutable references.

Run in a separate environment containing the pinned upstream installation.
This script never imports ptfkit or the new native inference engine.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

from import_rosetta3 import verify_checkout


def generate(checkout: Path, output: Path) -> None:
    lock = verify_checkout(checkout)
    import numpy as np
    import rosetta
    from rosetta.rosetta import Rosetta, UnsaturatedK

    # Verify the installed implementation as well as the source checkout.
    installed = Path(rosetta.__file__).parent
    for name in ('rosetta.py', 'nn_model.py'):
        expected = lock['files'][f'src/rosetta/{name}']
        if hashlib.sha256((installed / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'installed upstream source mismatch: {name}')
    for name in lock['required_models']:
        path = f'src/rosetta/data/{name}.npz'
        if (
            hashlib.sha256((installed / 'data' / f'{name}.npz').read_bytes()).hexdigest()
            != lock['files'][path]
        ):
            raise ValueError(f'installed upstream artifact mismatch: {name}')
    soils = [
        ('clay_loam', [30, 30, 40, 1.5, 0.3, 0.1]),
        ('silt_loam', [20, 60, 20, 1.3, 0.35, 0.15]),
        ('sandy_loam', [55, 25, 20, 1.1, 0.22, 0.09]),
        ('sand', [94, 5, 1, 1.8, 0.20, 0.005]),
        ('clay', [10, 20, 70, 1.2, 0.45, 0.25]),
        ('no_sand', [0, 68, 32, 0.625, 0.215, 0.036]),
        ('density_lower', [40, 40, 20, 0.5, 0.3, 0.1]),
        ('density_upper', [40, 40, 20, 2.0, 0.3, 0.1]),
        ('sum_lower', [39, 40, 20, 1.4, 0.3, 0.1]),
        ('sum_upper', [41, 40, 20, 1.4, 0.3, 0.1]),
    ]
    cases = []
    for level in (2, 3, 4, 5):
        inputs = [row[: level + 1] for _, row in soils]
        raw, ks = Rosetta(3, level, validate_network=True).predict(inputs)
        for mode in ('arith', 'log', 'geo'):
            mean, std, codes = rosetta.rosetta(3, inputs, estimate_type=mode)
            if not np.all(codes == level):
                raise ValueError('reference inputs selected an unexpected model')
            for i, (name, _) in enumerate(soils):
                cases.append(
                    {
                        'id': f'mod{level}_{mode}_{name}',
                        'level': level,
                        'mode': mode,
                        'inputs': inputs[i],
                        'mean': mean[i].tolist(),
                        'std': std[i].tolist(),
                        'raw_members': [
                            {'index': j, 'values': [*raw[j, i].tolist(), float(ks[j, i, 0])]}
                            for j in (0, 499, 999)
                        ],
                    }
                )
    invalid = [
        ('bad_sum', [20, 20, 20], -1),
        ('negative_texture', [-1, 51, 50], -1),
        ('missing_sand', [float('nan'), 50, 50], -1),
        ('infinite_sand', [float('inf'), 0, 0], -1),
        ('bad_density', [40, 40, 20, 2.01], 2),
        ('zero_theta33', [40, 40, 20, 1.4, 0], 3),
        ('theta33_one', [40, 40, 20, 1.4, 1], 3),
        ('retention_order', [40, 40, 20, 1.4, 0.3, 0.3], 4),
    ]
    boundary = []
    for name, row, expected_code in invalid:
        mean, std, codes = rosetta.rosetta(3, [row])
        if int(codes[0]) != expected_code:
            raise ValueError(f'upstream validation behavior changed: {name}')
        boundary.append(
            {
                'id': name,
                'inputs': [v if np.isfinite(v) else str(v) for v in row],
                'code': int(codes[0]),
                'mean': [float(v) if np.isfinite(v) else None for v in mean[0]],
                'std': [float(v) if np.isfinite(v) else None for v in std[0]],
            }
        )
    # A separate conductivity ensemble, evaluated from physical VG parameters.
    vg = [[0.1, 0.45, 0.01, 1.4], [0.05, 0.38, 0.03, 2.5]]
    unsat = UnsaturatedK(validate_network=True).predict(vg)
    document = {
        'provenance': {
            'kind': 'published',
            'repository': lock['repository'],
            'revision': lock['revision'],
            'manifest_sha256': hashlib.sha256(
                Path(__file__)
                .resolve()
                .parents[2]
                .joinpath('specs/models/rosetta3/manifest.json')
                .read_bytes()
            ).hexdigest(),
            'python': platform.python_version(),
            'numpy': np.__version__,
            'upstream_distribution': importlib.metadata.version('rosetta-soil'),
            'execution': 'rosetta.rosetta(3, inputs, estimate_type=mode)',
        },
        'cases': cases,
        'validation_cases': boundary,
        'conductivity': {
            'inputs': vg,
            'mean': np.mean(unsat, axis=0).tolist(),
            'std': np.std(unsat, axis=0, ddof=1).tolist(),
        },
    }
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(document, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(f'Wrote {len(cases)} upstream prediction cases and {len(boundary)} validation cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    generate(args.upstream.resolve(), args.output.resolve())
