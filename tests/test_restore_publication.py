import errno
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, restore_backup
from reaper_timecapsule.publication import publish_directory


class RestorePublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = self.root / 'source'
        source.mkdir()
        (source / 'reaper-kb.ini').write_text('synthetic')
        self.archive = self.root / 'backup.zip'
        make_backup(source, self.archive)
        self.destination = self.root / 'Recovered'

    def test_competing_empty_directory_is_not_replaced(self):
        def compete(source, target):
            Path(target).mkdir()
            return publish_directory(source, target)
        with patch('reaper_timecapsule.core.publish_directory', side_effect=compete):
            with self.assertRaises(FileExistsError):
                restore_backup(self.archive, self.destination)
        self.assertTrue(self.destination.is_dir())
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertEqual(list(self.root.glob('.timecapsule-restore-*')), [])

    def test_competing_file_is_preserved(self):
        def compete(source, target):
            Path(target).write_bytes(b'competitor')
            return publish_directory(source, target)
        with patch('reaper_timecapsule.core.publish_directory', side_effect=compete):
            with self.assertRaises(OSError):
                restore_backup(self.archive, self.destination)
        self.assertEqual(self.destination.read_bytes(), b'competitor')
        self.assertEqual(list(self.root.glob('.timecapsule-restore-*')), [])

    def test_native_success_publishes_complete_directory(self):
        restore_backup(self.archive, self.destination)
        self.assertEqual((self.destination / 'REAPER/reaper-kb.ini').read_text(), 'synthetic')
        self.assertTrue((self.destination / 'RESTORE_REPORT.json').is_file())
        self.assertEqual(list(self.root.glob('.timecapsule-restore-*')), [])

    def test_unsupported_publication_cleans_staging(self):
        with patch('reaper_timecapsule.core.publish_directory', side_effect=OSError(errno.ENOTSUP, 'unsupported')):
            with self.assertRaises(OSError):
                restore_backup(self.archive, self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob('.timecapsule-restore-*')), [])

    def test_unknown_platform_never_falls_back_to_rename(self):
        with patch('reaper_timecapsule.publication.sys.platform', 'unsupported'), \
             patch('reaper_timecapsule.publication.os.rename', side_effect=AssertionError('fallback')):
            with self.assertRaises(OSError):
                publish_directory(self.root / 'missing', self.destination)
