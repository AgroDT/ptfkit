# ruff: noqa: EM101, EM102, INP001, PLC0415, S603, S607, S608, T201, TRY003
"""Compare pinned author SQLite tensors with pinned USDA NPZs without executing author code.

This is a parameter/provenance audit, not a replacement prediction oracle or a
license determination. Only hashes and comparison results are written; trained
parameters stay in the ignored local checkouts. NPZ pickle loading occurs only
after the existing importer has authenticated every pinned USDA artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import struct
import subprocess
from collections import Counter
from pathlib import Path

from import_rosetta3 import verify_checkout


ROOT = Path(__file__).resolve().parents[2]
AUTHOR_MANIFEST = ROOT / 'specs/models/rosetta3/author-manifest.json'
LEGACY_MODEL_OFFSET = 100
CONDUCTIVITY_OUTPUTS = 2


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_member(blob: bytes, model_id: int, sequence: int) -> tuple[list[int], bytes]:
    """Decode the documented binary layout directly; preserve all binary64 bits."""
    stored_model, stored_sequence, nin, nlayer, hidden, unused, nout = struct.unpack_from(
        '<7i', blob, 32
    )
    if (stored_model, stored_sequence, nlayer, unused) != (model_id, sequence, 2, 0):
        raise ValueError('unexpected author member header')
    offset = 60
    parameters = bytearray()
    for shape in [(hidden, nin), (hidden, 1), (nout, hidden), (nout, 1)]:
        rows, cols = struct.unpack_from('<2i', blob, offset)
        if (rows, cols) != shape:
            raise ValueError('unexpected author matrix orientation')
        offset += 8
        size = rows * cols * 8
        parameters.extend(blob[offset : offset + size])
        offset += size
    if offset != len(blob):
        raise ValueError('truncated author member or trailing bytes')
    return [nin, hidden, nout], bytes(parameters)


def compare_network(
    connection: sqlite3.Connection, upstream: Path, model_id: int, name: str
) -> dict:
    import numpy as np

    rows = connection.execute(
        'SELECT seq, ann_bin FROM Ann WHERE model_id=? ORDER BY seq', (model_id,)
    ).fetchall()
    shapes, author = zip(*(decode_member(blob, model_id, seq) for seq, blob in rows), strict=True)
    if any(shape != shapes[0] for shape in shapes):
        raise ValueError('inconsistent author network shapes')
    # Use the same successful-member selection as the author, without its Python runtime.
    filtered = connection.execute(
        'SELECT count(*) FROM Ann A JOIN Ann_res R ON A.replica_hash=R.replica_hash '
        'WHERE A.model_id=? AND R.model_id=A.model_id AND R.nfail=0',
        (model_id,),
    ).fetchone()[0]
    if filtered != len(author):
        raise ValueError('author successful-member selection differs from stored ensemble')
    with np.load(upstream / f'src/rosetta/data/{name}.npz', allow_pickle=True) as npz:
        count = int(npz['nboot'])
        widths = [int(npz['ninput']), *(int(layer['nnodes']) for layer in npz['layers'])]
        usda = [
            b''.join(
                np.asarray(array, dtype='<f8').tobytes(order='C')
                for pair in zip(npz['weights'][i], npz['biases'][i], strict=True)
                for array in pair
            )
            for i in range(count)
        ]
        normalization = (
            compare_rosetta_scalers(connection, model_id, npz)
            if model_id < LEGACY_MODEL_OFFSET
            else None
        )
        activations = connection.execute(
            'SELECT DISTINCT nhid1_transfer,nout_transfer FROM Ann WHERE model_id=?', (model_id,)
        ).fetchall()
        translated = {'tansig': 'tansig', 'logsig': 'sigmoid'}
        activation_match = len(activations) == 1 and [
            translated[value.decode('ascii')] for value in activations[0]
        ] == [layer['activate'] for layer in npz['layers']]
    same_order = list(author) == usda
    same_members = Counter(author) == Counter(usda)
    if widths != shapes[0] or not (same_order and same_members and activation_match):
        raise ValueError(f'author/USDA parameter or topology mismatch: {name}')
    if normalization is not None and not normalization['equal']:
        raise ValueError(f'author/USDA scaler mismatch: {name}')
    return {
        'author_model_id': model_id,
        'usda_artifact': f'{name}.npz',
        'members': count,
        'widths': widths,
        'parameter_values': sum(map(len, usda)) // 8,
        'parameter_sha256': digest(b''.join(usda)),
        'parameters_bitwise_equal_in_sequence_order': same_order,
        'parameter_multisets_equal': same_members,
        'activations_equal': activation_match,
        'rosetta3_scalers': normalization,
    }


def compare_rosetta_scalers(connection: sqlite3.Connection, model_id: int, npz: dict) -> dict:
    inputs, outputs = [], []
    for table, result in [('Models_in_var', inputs), ('Models_out_var', outputs)]:
        rows = connection.execute(
            f'SELECT M.var_name,M.xmin,M.gain,M.ymin,M.scs,M.sco,M.sct '
            f'FROM minmax M JOIN {table} V ON M.var_id=V.var_id '
            'WHERE V.model_id=? ORDER BY V.var_pos',
            (model_id,),
        ).fetchall()
        for name, xmin, gain, ymin, slope, offset, log_flag in rows:
            result.append(
                {
                    'variable': name.decode('ascii'),
                    'scale': 'minmax' if table == 'Models_in_var' else 'linear',
                    'params': [xmin, gain, ymin] if table == 'Models_in_var' else [slope, offset],
                    'physical_output_is_log10': bool(log_flag),
                }
            )
    equal = all(
        len(author) == len(npz[key])
        and all(
            row['scale'] == scaler['scale']
            and row['params'] == [float(v) for v in scaler['params']]
            for row, scaler in zip(author, npz[key], strict=True)
        )
        for key, author in [('inputs', inputs), ('outputs', outputs)]
    )
    if [row['physical_output_is_log10'] for row in outputs] != [False, False, True, True, True]:
        raise ValueError('unexpected author physical/log output convention')
    return {'equal': equal, 'inputs': inputs, 'outputs': outputs}


def compare(author: Path, upstream: Path) -> dict:
    manifest_bytes = AUTHOR_MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    revision = subprocess.check_output(
        ['git', '-C', str(author), 'rev-parse', 'HEAD'], text=True
    ).strip()
    if revision != manifest['revision']:
        raise ValueError('author revision differs from pinned manifest')
    for name, expected in manifest['files'].items():
        if digest((author / name).read_bytes()) != expected:
            raise ValueError(f'author file differs from pinned manifest: {name}')
    usda_manifest = verify_checkout(upstream)
    uri = (author / 'sqlite/Rosetta.sqlite').resolve().as_uri() + '?mode=ro&immutable=1'
    with sqlite3.connect(uri, uri=True) as connection:
        # The original database stores binary networks as TEXT; never decode them as UTF-8.
        connection.text_factory = bytes
        networks = [
            compare_network(connection, upstream, level, f'rose3_mod{level}_0')
            for level in range(2, 6)
        ]
        legacy = [
            compare_network(
                connection,
                upstream,
                level + LEGACY_MODEL_OFFSET * (suffix + 1),
                f'rose1_mod{level}_{suffix}',
            )
            for suffix in range(2)
            for level in range(2, 6)
        ]
        inventory = [
            {'model_id': model_id, 'input_width': nin, 'output_width': nout, 'members': count}
            for model_id, nin, nout, count in connection.execute(
                'SELECT model_id,nin,nout,count(*) FROM Ann GROUP BY model_id ORDER BY model_id'
            )
        ]
    return {
        'format_version': 1,
        'author_revision': revision,
        'author_manifest_sha256': digest(manifest_bytes),
        'usda_revision': usda_manifest['revision'],
        'usda_manifest_sha256': digest((ROOT / 'specs/models/rosetta3/manifest.json').read_bytes()),
        'comparison': (
            'Exact little-endian binary64 bytes; row-major weights then biases, '
            'member order by Ann.seq.'
        ),
        'rosetta3': networks,
        'legacy_retention_and_ksat': legacy,
        'author_database_inventory': inventory,
        'unsaturated_conductivity': {
            'usda_artifact': 'rose1_unsat_k.npz',
            'required_topology': [4, 6, 2],
            'status': (
                'No two-output network exists in this author database; '
                'K0/L provenance is not established by this comparison.'
            ),
        },
        'scope': (
            'Parameter/topology/scaler comparison only. '
            'The author uses population covariance (ddof=0); '
            'ptfkit retains USDA sample SD (ddof=1). '
            'This does not establish identical high-level APIs '
            'or determine ownership or license validity.'
        ),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--author', required=True, type=Path)
    parser.add_argument('--upstream', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = compare(args.author.resolve(), args.upstream.resolve())
    if any(
        row['output_width'] == CONDUCTIVITY_OUTPUTS for row in report['author_database_inventory']
    ):
        raise ValueError('author conductivity inventory changed; review the audit scope')
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')
    print(
        'Rosetta3: all 4000 members match bitwise, '
        'including sequence, topology, activations and scalers.'
    )
    print('Eight additional Rosetta1 retention/Ksat ensembles match; the K0/L ensemble is absent.')
