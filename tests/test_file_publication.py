import errno
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, verify_backup, restore_backup
from reaper_timecapsule.publication import publish_file, require_path_capacity


class FilePublicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'reaper-kb.ini').write_bytes(b'synthetic')
        self.archive = self.root / 'capsule.zip'

    def unsupported_link(self):
        return patch('reaper_timecapsule.core.os.link', side_effect=OSError(errno.ENOTSUP, 'Synthetic non-link filesystem'))

    def test_non_link_filesystem_uses_native_exclusive_publication(self):
        with self.unsupported_link():
            make_backup(self.source, self.archive)
        self.assertEqual(verify_backup(self.archive)['files'][0]['path'], 'reaper-kb.ini')
        self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_competing_file_survives_exclusive_rename_fallback(self):
        def compete(source, destination):
            Path(destination).write_bytes(b'concurrent owner')
            return publish_file(source, destination)
        with self.unsupported_link(), patch('reaper_timecapsule.core.publish_file', side_effect=compete):
            with self.assertRaises(FileExistsError):
                make_backup(self.source, self.archive)
        self.assertEqual(self.archive.read_bytes(), b'concurrent owner')
        self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_competing_directory_survives_exclusive_rename_fallback(self):
        def compete(source, destination):
            Path(destination).mkdir()
            (Path(destination) / 'owner').write_bytes(b'keep')
            return publish_file(source, destination)
        with self.unsupported_link(), patch('reaper_timecapsule.core.publish_file', side_effect=compete):
            with self.assertRaises(OSError):
                make_backup(self.source, self.archive)
        self.assertEqual((self.archive / 'owner').read_bytes(), b'keep')
        self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_permission_error_does_not_trigger_publication_retry(self):
        with patch('reaper_timecapsule.core.os.link', side_effect=PermissionError(errno.EACCES, 'denied')), patch('reaper_timecapsule.core.publish_file') as publish:
            with self.assertRaises(PermissionError):
                make_backup(self.source, self.archive)
        publish.assert_not_called()

    def test_path_capacity_refusal_precedes_restore_staging(self):
        make_backup(self.source, self.archive)
        with patch('reaper_timecapsule.core.require_path_capacity', side_effect=ValueError('capacity')):
            with self.assertRaises(ValueError):
                restore_backup(self.archive, self.root / 'restored')
        self.assertFalse((self.root / 'restored').exists())
        self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_windows_capacity_counts_utf16_units(self):
        with patch('reaper_timecapsule.publication.sys.platform', 'win32'):
            with self.assertRaises(ValueError):
                require_path_capacity(self.root, ['x' * 260])
            with self.assertRaises(ValueError):
                require_path_capacity(self.root, ['\U0001f3b9' * 128])
            require_path_capacity(self.root, ['NeedsReview/RecoveredResources/000000.bin'])
