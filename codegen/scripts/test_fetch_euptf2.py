# ruff: noqa: D102, INP001, PT009, PT027
"""Protect authenticated downloads, bounded extraction and import preconditions."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

import fetch_euptf2


SHA256_ABC = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'


class FetchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_verified_download_is_cached_without_another_request(self) -> None:
        destination = self.root / 'cache' / 'archive.zip'
        with patch.object(
            fetch_euptf2.urllib.request, 'urlopen', return_value=io.BytesIO(b'abc')
        ) as request:
            fetch_euptf2.download('https://example.org/model', destination, 'sha256', SHA256_ABC)
            self.assertEqual(destination.read_bytes(), b'abc')
            fetch_euptf2.download('https://example.org/model', destination, 'sha256', SHA256_ABC)
            request.assert_called_once()

    def test_bad_download_never_becomes_a_cache_entry(self) -> None:
        destination = self.root / 'archive.zip'
        with (
            patch.object(fetch_euptf2.urllib.request, 'urlopen', return_value=io.BytesIO(b'abd')),
            self.assertRaisesRegex(ValueError, 'downloaded archive checksum mismatch'),
        ):
            fetch_euptf2.download('https://example.org/model', destination, 'sha256', SHA256_ABC)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_interrupted_download_removes_partial_bytes(self) -> None:
        reader = Mock()
        reader.read.side_effect = [b'ab', OSError('connection lost')]
        with (
            patch.object(fetch_euptf2.urllib.request, 'urlopen', return_value=nullcontext(reader)),
            self.assertRaisesRegex(OSError, 'connection lost'),
        ):
            fetch_euptf2.download(
                'https://example.org/model', self.root / 'archive.zip', 'sha256', SHA256_ABC
            )
        self.assertEqual(list(self.root.iterdir()), [])

    def test_corrupted_cache_is_rejected_without_network_or_replacement(self) -> None:
        destination = self.root / 'archive.zip'
        destination.write_bytes(b'abd')
        with (
            patch.object(fetch_euptf2.urllib.request, 'urlopen') as request,
            self.assertRaisesRegex(ValueError, 'cached archive checksum mismatch'),
        ):
            fetch_euptf2.download('https://example.org/model', destination, 'sha256', SHA256_ABC)
        request.assert_not_called()
        self.assertEqual(destination.read_bytes(), b'abd')

    def test_extraction_copies_only_authenticated_allowlisted_paths(self) -> None:
        archive = self.root / 'archive.zip'
        with zipfile.ZipFile(archive, 'w') as target:
            target.writestr('release/data/model.rdata', b'abc')
            target.writestr('release/../../outside', b'not allowed')
            target.writestr('release/unwanted.R', b'not allowed')
        output = self.root / 'extracted'
        fetch_euptf2.extract(archive, output, {'data/model.rdata': SHA256_ABC})
        self.assertEqual((output / 'data/model.rdata').read_bytes(), b'abc')
        self.assertEqual(
            sorted(
                p.relative_to(self.root).as_posix() for p in self.root.rglob('*') if p.is_file()
            ),
            ['archive.zip', 'extracted/data/model.rdata'],
        )

    def test_wrong_file_content_is_rejected_before_writing(self) -> None:
        archive = self.root / 'archive.zip'
        with zipfile.ZipFile(archive, 'w') as target:
            target.writestr('release/data/model.rdata', b'abd')
        output = self.root / 'extracted'
        with self.assertRaisesRegex(ValueError, 'upstream SHA-256 mismatch'):
            fetch_euptf2.extract(archive, output, {'data/model.rdata': SHA256_ABC})
        self.assertFalse(output.exists())

    def test_ambiguous_archive_source_is_rejected(self) -> None:
        archive = self.root / 'archive.zip'
        with zipfile.ZipFile(archive, 'w') as target:
            target.writestr('release/data/model.rdata', b'abc')
            target.writestr('other/data/model.rdata', b'abc')
        output = self.root / 'extracted'
        with self.assertRaisesRegex(ValueError, 'exactly one source'):
            fetch_euptf2.extract(archive, output, {'data/model.rdata': SHA256_ABC})
        self.assertFalse(output.exists())

    def test_existing_output_and_missing_r_stop_before_download(self) -> None:
        output = self.root / 'models'
        output.mkdir()
        marker = output / 'reviewed.ptfq'
        marker.write_bytes(b'reviewed')
        with patch.object(fetch_euptf2, 'download') as download:
            with self.assertRaises(FileExistsError):
                fetch_euptf2.fetch(output, self.root / 'cache', 'Rscript', 'all')
            self.assertEqual(marker.read_bytes(), b'reviewed')
            with (
                patch.object(fetch_euptf2.shutil, 'which', return_value=None),
                self.assertRaisesRegex(FileNotFoundError, 'Rscript is required'),
            ):
                fetch_euptf2.fetch(self.root / 'new-models', self.root / 'cache', 'Rscript', 'all')
            download.assert_not_called()
        self.assertFalse((self.root / 'cache').exists())

    def test_full_fetch_authenticates_sources_before_handing_them_to_r(self) -> None:
        package = self.root / 'package.zip'
        scientific = self.root / 'scientific.zip'
        with zipfile.ZipFile(package, 'w') as target:
            target.writestr('package/LICENSE', b'abc')
            target.writestr('package/data/model.rdata', b'abc')
        manifest = self.root / 'manifest.json'
        manifest.write_text(
            json.dumps(
                {
                    'files': {'LICENSE': SHA256_ABC},
                    'package': {'revision': 'pinned', 'archive_sha256': SHA256_ABC},
                    'scientific_release': {'archive_md5_published': 'published'},
                }
            )
        )
        collection = self.root / 'collection.json'
        collection.write_text(
            json.dumps(
                {
                    'models': [
                        {'file': 'model.rdata', 'source_sha256': SHA256_ABC},
                        {
                            'source_kind': 'scientific-archive',
                            'sources': [{'file': 'forest.rdata', 'sha256': SHA256_ABC}],
                        },
                    ]
                }
            )
        )
        cache = self.root / 'cache'
        cache.mkdir()

        def converter(
            upstream: Path, output: Path, rscript: str, group: str, archive: Path
        ) -> None:
            self.assertEqual((upstream / 'data/model.rdata').read_bytes(), b'abc')
            self.assertEqual((archive / 'forest.rdata').read_bytes(), b'abc')
            self.assertEqual((rscript, group), ('Rscript', 'all'))
            output.mkdir()

        for data in [b'abd', b'abc']:
            with self.subTest(scientific_source=data):
                with zipfile.ZipFile(scientific, 'w') as target:
                    target.writestr('scientific/forest.rdata', data)
                with (
                    patch.object(fetch_euptf2, 'MANIFEST', manifest),
                    patch.object(fetch_euptf2, 'COLLECTION', collection),
                    patch.object(fetch_euptf2.shutil, 'which', return_value='Rscript'),
                    patch.object(fetch_euptf2, 'download', side_effect=[package, scientific]),
                    patch.object(
                        fetch_euptf2, 'convert_collection', side_effect=converter
                    ) as convert,
                ):
                    output = self.root / 'models'
                    if data == b'abd':
                        with self.assertRaisesRegex(ValueError, 'upstream SHA-256 mismatch'):
                            fetch_euptf2.fetch(output, cache, 'Rscript', 'all')
                        convert.assert_not_called()
                        self.assertFalse(output.exists())
                    else:
                        fetch_euptf2.fetch(output, cache, 'Rscript', 'all')
                        convert.assert_called_once()
                        self.assertTrue(output.is_dir())
                    self.assertEqual(list(cache.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
