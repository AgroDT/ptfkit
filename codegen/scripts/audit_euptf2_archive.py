# ruff: noqa: EM102, INP001, S603, T201, TRY003
"""Authenticate and reconcile every original scientific-archive trained forest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from import_euptf2 import ROOT, verify


def run(upstream: Path, archive: Path, library: Path, output: Path, rscript: str) -> None:
    """Authenticate both distributions before comparing their original R state."""
    verify(upstream)
    collection = json.loads((ROOT / 'specs/models/euptf2/collection.json').read_text())
    for model in collection['models']:
        if model.get('source_kind') == 'scientific-archive':
            continue
        data = (upstream / 'data' / model['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != model['source_sha256']:
            raise ValueError(f'package SHA-256 mismatch: {model["file"]}')
    manifest = json.loads((ROOT / 'specs/models/euptf2/scientific-archive.json').read_text())
    for source in manifest['files']:
        data = (archive / source['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != source['sha256']:
            raise ValueError(f'archive SHA-256 mismatch: {source["path"]}')
    subprocess.run(
        [
            rscript,
            '--vanilla',
            str(Path(__file__).with_suffix('.R')),
            str(archive),
            str(library),
            str(ROOT / 'specs/models/euptf2'),
            str(output),
        ],
        check=True,
    )
    print(f'Compared all {len(manifest["files"])} authenticated original forests')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rscript', default='Rscript')
    args = parser.parse_args()
    run(
        args.upstream.resolve(),
        args.archive.resolve(),
        args.library.resolve(),
        args.output.resolve(),
        args.rscript,
    )
