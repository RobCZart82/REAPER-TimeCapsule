import errno
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, restore_backup, verify_backup


class ArchiveFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / 'Source'
        self.source.mkdir()
        self.input = self.source / 'reaper-kb.ini'
        self.input.write_bytes(b'action')
        self.archive = self.root / 'one.zip'

    def test_same_size_source_change_aborts_publication(self):
        original_write = zipfile._ZipWriteFile.write
        changed = False
        def mutate(stream, data):
            nonlocal changed
            result = original_write(stream, data)
            if not changed and stream._zinfo.filename.startswith('resources/'):
                changed = True
                timestamp = self.input.stat().st_mtime_ns
                self.input.write_bytes(b'change')
                os.utime(self.input, ns=(timestamp + 1000000000, timestamp + 1000000000))
            return result
        with patch.object(zipfile._ZipWriteFile, 'write', mutate):
            with self.assertRaises(ValueError):
                make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.root.glob('.timecapsule-*.zip')), [])

    def test_disk_full_during_backup_cleans_temporary_archive(self):
        with patch.object(zipfile.ZipFile, 'writestr', side_effect=OSError(errno.ENOSPC, 'full disk')):
            with self.assertRaises(OSError):
                make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.root.glob('.timecapsule-*.zip')), [])
        self.assertEqual(self.input.read_bytes(), b'action')

    def test_permission_failure_during_backup_cleans_temporary_archive(self):
        original_open = Path.open
        def guarded(path, *args, **kwargs):
            if path == self.input:
                raise PermissionError('denied')
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded):
            with self.assertRaises(PermissionError):
                make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.root.glob('.timecapsule-*.zip')), [])

    def test_restore_write_failure_keeps_archive_and_cleans_staging(self):
        make_backup(self.source, self.archive)
        before = self.archive.read_bytes()
        original_open = Path.open
        def fail_write(path, mode='r', *args, **kwargs):
            if mode == 'xb':
                raise OSError(errno.ENOSPC, 'full disk')
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', fail_write):
            with self.assertRaises(OSError):
                restore_backup(self.archive, self.root / 'Recovered')
        self.assertFalse((self.root / 'Recovered').exists())
        self.assertEqual(list(self.root.glob('.timecapsule-restore-*')), [])
        self.assertEqual(self.archive.read_bytes(), before)

    def test_malformed_zip_cli_reports_error_without_traceback(self):
        self.archive.write_bytes(b'not a zip')
        with self.assertRaises(ValueError):
            verify_backup(self.archive)
        result = subprocess.run([sys.executable, '-m', 'reaper_timecapsule', 'verify', str(self.archive)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('TimeCapsule error', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_manifest_type_encoding_and_duplicates_rejected(self):
        for data in (b'[]', b'PRIVATE_INVALID_JSON', b'\xff', b'{"schema":2,"schema":2}'):
            with self.subTest(data=data):
                with zipfile.ZipFile(self.archive, 'w') as archive:
                    archive.writestr('manifest.json', data)
                with self.assertRaises(ValueError) as error:
                    verify_backup(self.archive)
                self.assertNotIn('PRIVATE_INVALID_JSON', str(error.exception))
