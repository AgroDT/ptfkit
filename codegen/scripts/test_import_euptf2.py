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


if __name__ == '__main__':
    unittest.main()
