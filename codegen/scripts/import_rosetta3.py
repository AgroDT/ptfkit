# ruff: noqa: EM101, EM102, INP001, PLC0415, S603, S607, T201, TRY003
"""Verify and convert the pinned Rosetta networks for local use only.

NPZ metadata uses pickle. No NPZ is opened until every pinned source and
artifact hash has been checked. The output is deliberately outside packages.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'specs/models/rosetta3/manifest.json'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_checkout(checkout: Path) -> dict:
    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    revision = subprocess.check_output(
        ['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True
    ).strip()
    if revision != lock['revision']:
        raise ValueError(f'upstream revision mismatch: {revision}')
    for name, expected in lock['files'].items():
        if digest(checkout / name) != expected:
            raise ValueError(f'upstream SHA-256 mismatch: {name}')
    return lock


def convert(checkout: Path, output: Path) -> None:
    lock = verify_checkout(checkout)
    # This import and the pickle loader occur only after integrity verification.
    import numpy as np

    data = bytearray()
    networks = []
    for name in lock['required_models']:
        with np.load(checkout / f'src/rosetta/data/{name}.npz', allow_pickle=True) as z:
            widths = [int(z['ninput'])] + [int(x['nnodes']) for x in z['layers']]
            nboot = int(z['nboot'])
            layers = [str(x['activate']) for x in z['layers']]
            if len(widths) != int(z['nlayer']) + 1:
                raise ValueError(f'invalid layer count: {name}')
            offset = len(data) // 8
            stored_weights = z['weights']
            stored_biases = z['biases']
            for boot in range(nboot):
                for layer, (nin, nout) in enumerate(itertools.pairwise(widths)):
                    weights = np.asarray(stored_weights[boot][layer], dtype=np.float64)
                    biases = np.asarray(stored_biases[boot][layer], dtype=np.float64)
                    if weights.shape != (nout, nin) or biases.size != nout:
                        raise ValueError(f'invalid network dimensions: {name}')
                    for value in [*weights.flat, *biases.flat]:
                        if not math.isfinite(value):
                            raise ValueError(f'non-finite trained parameter: {name}')
                        data.extend(struct.pack('<d', value))

            def scalers(key: str) -> list[dict]:
                return [
                    {'kind': str(x['scale']), 'params': [float(v) for v in x['params']]}
                    for x in z[key]
                ]

            networks.append(
                {
                    'name': name,
                    'nboot': nboot,
                    'widths': widths,
                    'activations': layers,
                    'offset': offset,
                    'inputs': scalers('inputs'),
                    'outputs': scalers('outputs'),
                }
            )
    converted = hashlib.sha256(data).hexdigest()
    if converted != lock['converted_sha256']:
        raise ValueError('converted artifact differs from the reviewed manifest')
    metadata = {
        'format_version': 1,
        'upstream_revision': lock['revision'],
        'artifact': 'models.bin',
        'sha256': converted,
        'networks': networks,
    }
    # Exclusive creation prevents silently replacing reviewed local artifacts.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'models.bin').write_bytes(data)
    (output / 'models.json').write_text(
        json.dumps(metadata, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n'
    )
    print(f'Imported {len(networks)} ensembles, {len(data)} bytes; SHA-256 {converted}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / '.rosetta-local/imported')
    args = parser.parse_args()
    convert(args.upstream.resolve(), args.output.resolve())
