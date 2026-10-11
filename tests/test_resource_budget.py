import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, restore_backup, verify_backup
from reaper_timecapsule.resource_budget import inspect_residues, preflight_zip


class ResourceBudgetTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'reaper-kb.ini').write_bytes(b'synthetic')
        self.archive = self.root / 'capsule.zip'

    def test_low_space_aborts_backup_before_creating_staging(self):
        with patch('reaper_timecapsule.resource_budget.shutil.disk_usage', return_value=SimpleNamespace(free=0)):
            with self.assertRaises(OSError):
                make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_low_space_aborts_restore_before_creating_staging(self):
        make_backup(self.source, self.archive)
        with patch('reaper_timecapsule.resource_budget.shutil.disk_usage', return_value=SimpleNamespace(free=0)):
            with self.assertRaises(OSError):
                restore_backup(self.archive, self.root / 'restored')
        self.assertFalse((self.root / 'restored').exists())
        self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_footer_member_budget_checked_before_zipfile_allocation(self):
        make_backup(self.source, self.archive)
        with patch('reaper_timecapsule.core.MAX_FILES', 0), patch('reaper_timecapsule.core.zipfile.ZipFile', side_effect=AssertionError('central directory loaded')):
            with self.assertRaises(ValueError):
                verify_backup(self.archive)

    def test_zip64_footer_budget_and_invalid_position(self):
        # Empty single-volume ZIP64 fixture, no huge payload allocation.
        record = struct.pack('<4sQ2H2L4Q', b'PK\x06\x06', 44, 45, 45, 0, 0, 0, 0, 0, 0)
        locator = struct.pack('<4sLQL', b'PK\x06\x07', 0, 0, 1)
        footer = struct.pack('<4s4H2LH', b'PK\x05\x06', 0, 0, 65535, 65535, 0xffffffff, 0xffffffff, 0)
        self.archive.write_bytes(record + locator + footer)
        self.assertEqual(preflight_zip(self.archive, 2)['members'], 0)
        with patch('reaper_timecapsule.resource_budget.MAX_CENTRAL_DIRECTORY', -1):
            with self.assertRaises(ValueError):
                preflight_zip(self.archive, 2)

    def test_trailing_data_and_bad_footer_refused(self):
        make_backup(self.source, self.archive)
        data = self.archive.read_bytes()
        for altered in (data + b'trailing', b'PK\x05\x06'):
            self.archive.write_bytes(altered)
            with self.assertRaises(ValueError):
                preflight_zip(self.archive, 100)

    def test_valid_comment_and_compressible_payload_are_allowed(self):
        with zipfile.ZipFile(self.archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('synthetic', b'0' * 1024 * 1024)
            z.comment = b'ordinary comment'
        self.assertEqual(preflight_zip(self.archive, 1)['members'], 1)

    def test_generated_manifest_budget_failure_cleans_unpublished_output(self):
        with patch('reaper_timecapsule.core.MAX_MANIFEST_BYTES', 1):
            with self.assertRaises(ValueError):
                make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_residue_report_does_not_read_or_remove_candidates(self):
        leftover = self.root / '.timecapsule-synthetic.zip'
        leftover.write_bytes(b'private contents')
        folder = self.root / '.timecapsule-restore-synthetic'
        folder.mkdir()
        before = leftover.read_bytes()
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('content inspection')):
            report = inspect_residues(self.root)
        self.assertEqual(len(report['candidates']), 2)
        self.assertTrue(folder.exists())
        self.assertEqual(leftover.read_bytes(), before)
        self.assertNotIn('private contents', json.dumps(report))
