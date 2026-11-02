# ruff: noqa: D102, INP001, PT009, PT027
"""Importer integrity checks must precede R execution and output creation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import import_euptf2


class ImportIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.data = self.source / 'model.rdata'
        self.data.write_bytes(b'abc')
        self.manifest = self.root / 'manifest.json'
        expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        self.manifest.write_text(
            json.dumps(
                {
                    'files': {
                        'model.rdata': expected,
                    }
                }
            )
        )
        self.addCleanup(patch.stopall)
        patch.object(import_euptf2, 'MANIFEST', self.manifest).start()
        self.r = patch.object(import_euptf2.subprocess, 'run').start()

    def test_changed_content_is_rejected_before_r_and_output(self) -> None:
        self.data.write_bytes(b'abd')
        output = self.root / 'output.ptfq'
        with self.assertRaises(ValueError):
            import_euptf2.convert(self.source, output, 'Rscript')
        self.r.assert_not_called()
        self.assertFalse(output.exists())

    def test_existing_output_is_preserved_without_running_r(self) -> None:
        output = self.root / 'output.ptfq'
        output.write_bytes(b'reviewed')
        with self.assertRaises(FileExistsError):
            import_euptf2.convert(self.source, output, 'Rscript')
        self.r.assert_not_called()
        self.assertEqual(output.read_bytes(), b'reviewed')

    def test_collection_checks_unselected_sources_before_r(self) -> None:
        data = self.source / 'data'
        data.mkdir()
        (data / 'scalar.rdata').write_bytes(b'abc')
        (data / 'multi.rdata').write_bytes(b'abd')
        expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        collection = self.root / 'collection.json'
        collection.write_text(
            json.dumps(
                {
                    'models': [
                        {'file': 'scalar.rdata', 'source_sha256': expected, 'components': [{}]},
                        {'file': 'multi.rdata', 'source_sha256': expected, 'components': [{}, {}]},
                    ]
                }
            )
        )
        patch.object(import_euptf2, 'COLLECTION', collection).start()
        output = self.root / 'models'
        with self.assertRaises(ValueError):
            import_euptf2.convert_collection(self.source, output, 'Rscript', 'scalar')
        self.r.assert_not_called()
        self.assertFalse(output.exists())

    def test_collection_output_creation_waits_for_every_digest(self) -> None:
        data = self.source / 'data'
        data.mkdir()
        (data / 'scalar.rdata').write_bytes(b'abc')
        expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        collection = self.root / 'collection.json'
        collection.write_text(
            json.dumps(
                {
                    'models': [
                        {
                            'id': 1,
                            'name': 'scalar',
                            'original': 'scalar',
                            'file': 'scalar.rdata',
                            'source_sha256': expected,
                            'components': [{'transform': 0}],
                            'features': ['USSAND', 'USSILT', 'USCLAY', 'DEPTH_M'],
                            'status': 'implemented',
                            'artifact': {'sha256': expected, 'bytes': 3},
                        }
                    ]
                }
            )
        )
        patch.object(import_euptf2, 'COLLECTION', collection).start()

        def fake_r(command: list[str], *, check: bool) -> None:
            if not check:
                raise AssertionError
            (Path(command[-1]) / 'scalar.ptfq').write_bytes(b'abd')

        self.r.side_effect = fake_r
        output = self.root / 'models'
        with self.assertRaises(ValueError):
            import_euptf2.convert_collection(self.source, output, 'Rscript', 'scalar')
        self.r.assert_called_once()
        self.assertFalse(output.exists())

    def test_archive_model_requires_explicit_authenticated_source(self) -> None:
        collection = self.root / 'collection.json'
        collection.write_text(
            json.dumps(
                {'models': [{'source_kind': 'scientific-archive', 'components': [{}, {}, {}, {}]}]}
            )
        )
        patch.object(import_euptf2, 'COLLECTION', collection).start()
        output = self.root / 'models'
        with self.assertRaisesRegex(ValueError, 'requires --archive'):
            import_euptf2.convert_collection(self.source, output, 'Rscript', 'all')
        self.r.assert_not_called()
        self.assertFalse(output.exists())

    def test_changed_archive_source_is_rejected_before_r(self) -> None:
        archive = self.root / 'archive'
        archive.mkdir()
        (archive / 'forest.rdata').write_bytes(b'abd')
        expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        collection = self.root / 'collection.json'
        collection.write_text(
            json.dumps(
                {
                    'models': [
                        {
                            'source_kind': 'scientific-archive',
                            'components': [{}, {}, {}, {}],
                            'sources': [{'file': 'forest.rdata', 'sha256': expected}],
                        }
                    ]
                }
            )
        )
        patch.object(import_euptf2, 'COLLECTION', collection).start()
        output = self.root / 'models'
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch: forest.rdata'):
            import_euptf2.convert_collection(self.source, output, 'Rscript', 'all', archive)
        self.r.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
