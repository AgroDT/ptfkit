# ruff: noqa: C901, EM101, EM102, INP001, S603, T201, TRY003
"""Authenticate local EU-PTF v2 sources and convert the original collection offline.

Only the caller's local output directory receives trained parameters. R is a
conversion tool, never a ptfkit runtime dependency.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'specs/models/euptf2/manifest.json'
COLLECTION = ROOT / 'specs/models/euptf2/collection.json'


def verify(upstream: Path) -> dict:
    """Check every pinned file before R deserializes any upstream object."""
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if hashlib.sha256((upstream / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'upstream SHA-256 mismatch: {name}')
    return manifest


def convert(upstream: Path, output: Path, rscript: str) -> None:
    manifest = verify(upstream)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        binary = Path(temporary) / 'ths.ptfq'
        subprocess.run(
            [
                rscript,
                '--vanilla',
                str(Path(__file__).with_suffix('.R')),
                str(upstream / 'data/THS_PTF01.rdata'),
                str(binary),
            ],
            check=True,
        )
        data = binary.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != manifest['artifact']['sha256'] or len(data) != manifest['artifact']['bytes']:
            raise ValueError('converted QRF differs from the reviewed artifact identity')
        with output.open('xb') as target:
            target.write(data)
    print(f'Imported THS_PTF01: {len(data)} bytes; SHA-256 {actual}')


def convert_collection(
    upstream: Path, output: Path, rscript: str, group: str, archive: Path | None = None
) -> None:
    """Authenticate the complete source collection before any R deserialization."""
    verify(upstream)
    collection = json.loads(COLLECTION.read_text(encoding='utf-8'))
    for model in collection['models']:
        if model.get('source_kind') == 'scientific-archive':
            if archive is not None:
                for source in model['sources']:
                    if (
                        hashlib.sha256((archive / source['file']).read_bytes()).hexdigest()
                        != source['sha256']
                    ):
                        raise ValueError(f'upstream SHA-256 mismatch: {source["file"]}')
            continue
        path = upstream / 'data' / model['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != model['source_sha256']:
            raise ValueError(f'upstream SHA-256 mismatch: {model["file"]}')
    if output.exists():
        raise FileExistsError(output)
    selected = [
        m
        for m in collection['models']
        if group == 'all'
        or (group == 'package' and m.get('source_kind') != 'scientific-archive')
        or (group == 'scalar' and len(m['components']) == 1)
    ]
    if archive is None and any(m.get('source_kind') == 'scientific-archive' for m in selected):
        raise ValueError('VG_PTF26 requires --archive pointing to the pinned scientific source')
    if not selected or any(m['status'] != 'implemented' for m in selected):
        raise ValueError('requested collection includes an unimplemented model')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staging = Path(temporary)
        plan = staging / 'plan.csv'
        write_plan(selected, plan, upstream, archive)
        artifacts = staging / 'models'
        artifacts.mkdir()
        subprocess.run(
            [
                rscript,
                '--vanilla',
                str(Path(__file__).with_suffix('.R')),
                'collection',
                str(upstream),
                str(plan),
                str(artifacts),
            ],
            check=True,
        )
        for model in selected:
            data = (artifacts / f'{model["name"]}.ptfq').read_bytes()
            if (
                hashlib.sha256(data).hexdigest() != model['artifact']['sha256']
                or len(data) != model['artifact']['bytes']
            ):
                raise ValueError(f'converted artifact mismatch: {model["name"]}')
        artifacts.rename(output)
    print(f'Imported {len(selected)} original models into {output}')


def write_plan(models: list[dict], path: Path, upstream: Path, archive: Path | None = None) -> None:
    """Write a base-R-readable plan with original predictor/component ordering."""
    with path.open('w', encoding='utf-8', newline='') as target:
        writer = csv.DictWriter(
            target, fieldnames=['id', 'name', 'original', 'file', 'features', 'transforms']
        )
        writer.writeheader()
        for model in models:
            if model.get('source_kind') == 'scientific-archive':
                if archive is None:
                    raise ValueError('archive sources are required')
                files = ';'.join(str(archive / s['file']) for s in model['sources'])
                originals = ';'.join(s['original'] for s in model['sources'])
            else:
                files = str(upstream / 'data' / model['file'])
                originals = model['original']
            writer.writerow(
                {key: model[key] for key in ('id', 'name', 'original', 'file')}
                | {
                    'file': files,
                    'original': originals,
                    'features': ';'.join(model['features']),
                    'transforms': ';'.join(str(c['transform']) for c in model['components']),
                }
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rscript', default='Rscript')
    parser.add_argument('--collection', action='store_true')
    parser.add_argument('--group', choices=['scalar', 'package', 'all'], default='all')
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    if args.collection:
        convert_collection(
            args.upstream.resolve(),
            args.output.resolve(),
            args.rscript,
            args.group,
            args.archive.resolve() if args.archive else None,
        )
    else:
        convert(args.upstream.resolve(), args.output.resolve(), args.rscript)
