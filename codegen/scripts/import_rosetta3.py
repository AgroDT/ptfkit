# ruff: noqa: EM101, EM102, INP001, PLC0415, T201, TRY003
"""Import bundled Rosetta parameters from a trusted upstream checkout.

NPZ metadata uses pickle: only pass a trusted checkout. The YAML specification
owns topology and ordering; this script does not supply scientific calculations.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from itertools import pairwise
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NAMES = ('rose3_mod2_0', 'rose3_mod3_0', 'rose3_mod4_0', 'rose3_mod5_0', 'rose1_unsat_k')


def convert(checkout: Path, output: Path) -> None:  # noqa: C901, PLR0912
    import numpy as np
    import yaml

    spec = yaml.safe_load((ROOT / 'specs/functions/zhang_schaap2017.yaml').read_text())
    declarations = {}
    for function in spec['functions']:
        for network in function['implementation']['networks'].values():
            index = network['parameters']['network']
            if index in declarations and declarations[index] != network:
                raise ValueError(f'inconsistent network declaration: {index}')
            declarations[index] = network
    if sorted(declarations) != list(range(len(NAMES))):
        raise ValueError('expected the five declared Rosetta networks')
    header = bytearray(b'PTFKNN01' + struct.pack('<I', len(NAMES)))
    values = bytearray()
    activations = ('linear', 'sigmoid', 'tansig', 'relu')
    scales = ('asis', 'division', 'logtr', 'affine', 'minmax', 'linear')
    for index, name in enumerate(NAMES):
        declared = declarations[index]
        with np.load(checkout / f'src/rosetta/data/{name}.npz', allow_pickle=True) as archive:
            widths = [int(archive['ninput'])] + [
                int(layer['nnodes']) for layer in archive['layers']
            ]
            acts = [str(layer['activate']) for layer in archive['layers']]
            members = int(archive['nboot'])
            if (
                widths != declared['widths']
                or acts != declared['activations']
                or members != declared['members']
                or int(archive['nlayer']) != len(acts)
                or declared['parameters']['offset'] != len(values) // 8
            ):
                raise ValueError(f'topology or ordering differs from YAML: {name}')
            header.extend(struct.pack('<2I', members, len(acts)))
            header.extend(struct.pack(f'<{len(widths)}I', *widths))
            header.extend(struct.pack(f'<{len(acts)}I', *(activations.index(a) for a in acts)))
            for key in ('inputs', 'outputs'):
                channels = archive[key]
                if len(channels) != len(declared[key]):
                    raise ValueError(f'channel count differs from YAML: {name}/{key}')
                for actual, expected in zip(channels, declared[key], strict=True):
                    params = [float(v) for v in actual['params']]
                    if str(actual['scale']) != expected['scale'] or params != expected['params']:
                        raise ValueError(f'scale differs from YAML: {name}/{key}')
                    padded = params + [0.0] * (3 - len(params))
                    header.extend(struct.pack('<I3d', scales.index(expected['scale']), *padded))
            header.extend(struct.pack('<Q', len(values) // 8))
            stored_weights = archive['weights']
            stored_biases = archive['biases']
            # Container order: member, layer, output row, input column, then biases.
            for member in range(members):
                for layer, (nin, nout) in enumerate(pairwise(widths)):
                    weights = np.asarray(stored_weights[member][layer], dtype='<f8')
                    biases = np.asarray(stored_biases[member][layer], dtype='<f8')
                    if weights.shape != (nout, nin) or biases.size != nout:
                        raise ValueError(f'invalid parameter dimensions: {name}/{member}/{layer}')
                    if not np.isfinite(weights).all() or not np.isfinite(biases).all():
                        raise ValueError(f'non-finite parameters: {name}/{member}/{layer}')
                    values.extend(weights.tobytes(order='C'))
                    values.extend(biases.tobytes(order='C'))
    header.extend(struct.pack('<Q', len(values) // 8))
    data = header + values
    artifact = declarations[0]['parameters']['artifact']
    if len(data) != artifact['bytes'] or hashlib.sha256(data).hexdigest() != artifact['sha256']:
        raise ValueError('imported binary differs from the YAML artifact declaration')
    output.write_bytes(data)
    print(f'Imported {len(NAMES)} networks into {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'specs/models/rosetta3/rosetta3.ptfm')
    args = parser.parse_args()
    convert(args.upstream.resolve(), args.output.resolve())
