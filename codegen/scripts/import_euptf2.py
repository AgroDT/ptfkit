# ruff: noqa: EM101, EM102, INP001, S603, T201, TRY003
"""Authenticate local EU-PTF v2 sources and convert THS_PTF01 offline.

Only the caller's local output directory receives trained parameters. R is a
conversion tool, never a ptfkit runtime dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'specs/models/euptf2/manifest.json'


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rscript', default='Rscript')
    args = parser.parse_args()
    convert(args.upstream.resolve(), args.output.resolve(), args.rscript)
