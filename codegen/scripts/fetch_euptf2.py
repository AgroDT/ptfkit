# ruff: noqa: EM101, EM102, INP001, S310, T201, TRY003
"""Download pinned EU-PTF v2 sources and import external models locally.

Uses only the Python standard library and the existing offline base-R converter.
Neither sources nor trained artifacts become part of a ptfkit release package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from import_euptf2 import COLLECTION, MANIFEST, convert_collection


def download(url: str, destination: Path, algorithm: str, expected: str) -> Path:
    """Reuse verified cached bytes; publish new downloads only after authentication."""
    if destination.exists():
        with destination.open('rb') as source:
            actual = hashlib.file_digest(source, algorithm).hexdigest()
        if actual != expected:
            raise ValueError(f'cached archive checksum mismatch: {destination}')
        print(f'Using verified cache: {destination}')
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f'Downloading {url}', flush=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        partial = Path(temporary) / 'archive.zip'
        digest = hashlib.new(algorithm)
        with urllib.request.urlopen(url, timeout=60) as source, partial.open('wb') as target:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
                target.write(chunk)
        if digest.hexdigest() != expected:
            raise ValueError(f'downloaded archive checksum mismatch: {url}')
        partial.replace(destination)
    return destination


def extract(archive: Path, destination: Path, files: dict[str, str]) -> None:
    """Copy only allowlisted, SHA-256-verified files, ignoring ZIP extraction paths."""
    with zipfile.ZipFile(archive) as source:
        for relative, expected in files.items():
            matches = [m for m in source.infolist() if m.filename.partition('/')[2] == relative]
            if len(matches) != 1 or matches[0].is_dir():
                raise ValueError(f'archive must contain exactly one source: {relative}')
            data = source.read(matches[0])
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f'upstream SHA-256 mismatch: {relative}')
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)


def fetch(output: Path, cache: Path, rscript: str, group: str) -> None:
    """Fetch original sources, authenticate them and invoke the offline importer."""
    if output.exists():
        raise FileExistsError(output)
    executable = shutil.which(rscript)
    if executable is None:
        raise FileNotFoundError(
            'Rscript is required for conversion; pass --rscript /path/to/Rscript'
        )
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    collection = json.loads(COLLECTION.read_text(encoding='utf-8'))
    package = manifest['package']
    package_zip = download(
        f'https://codeload.github.com/tkdweber/euptf2/zip/{package["revision"]}',
        cache / 'euptf2-v1.0.0.zip',
        'sha256',
        package['archive_sha256'],
    )
    scientific_zip = None
    if group == 'all':
        scientific_zip = download(
            'https://zenodo.org/records/3759443/files/'
            'TothSzaboBrigitta/euptfv2-v.2.0.0.zip?download=1',
            cache / 'euptfv2-v.2.0.0.zip',
            'md5',
            manifest['scientific_release']['archive_md5_published'],
        )
    package_files = dict(manifest['files'])
    archive_files = {}
    for model in collection['models']:
        if model.get('source_kind') == 'scientific-archive':
            archive_files.update({s['file']: s['sha256'] for s in model['sources']})
        else:
            package_files[f'data/{model["file"]}'] = model['source_sha256']
    with tempfile.TemporaryDirectory(dir=cache) as temporary:
        staging = Path(temporary)
        upstream = staging / 'package'
        extract(package_zip, upstream, package_files)
        archive = None
        if scientific_zip is not None:
            archive = staging / 'scientific'
            extract(scientific_zip, archive, archive_files)
        convert_collection(upstream, output, executable, group, archive)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('.euptf2-local/models'))
    parser.add_argument('--cache', type=Path, default=Path('.euptf2-local/downloads'))
    parser.add_argument('--rscript', default='Rscript')
    parser.add_argument('--group', choices=['scalar', 'package', 'all'], default='all')
    args = parser.parse_args()
    fetch(args.output.resolve(), args.cache.resolve(), args.rscript, args.group)
