import tempfile
import unittest
from pathlib import Path
from reaper_timecapsule.core import make_backup, restore_backup

class NoOverwriteTests(unittest.TestCase):
    def test_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "Source"
            src.mkdir()
            (src / "reaper-kb.ini").write_text("action")
            archive = base / "one.zip"
            make_backup(src, archive)
            with self.assertRaises(FileExistsError):
                make_backup(src, archive)
            out = base / "Restore"
            restore_backup(archive, out)
            with self.assertRaises(FileExistsError):
                restore_backup(archive, out)


class AtomicBackupPublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'Source'
        self.source.mkdir()
        (self.source / 'reaper-kb.ini').write_text('synthetic action')
        self.archive = self.base / 'one.zip'

    def assert_no_staging(self):
        self.assertEqual(list(self.base.glob('.timecapsule-*.zip')), [])

    def test_concurrent_file_created_at_publication_is_preserved(self):
        import os
        from unittest.mock import patch
        real_link = os.link
        def competing_link(source, target):
            Path(target).write_bytes(b'concurrent owner')
            return real_link(source, target)
        with patch('reaper_timecapsule.core.os.link', side_effect=competing_link):
            with self.assertRaises(FileExistsError):
                make_backup(self.source, self.archive)
        self.assertEqual(self.archive.read_bytes(), b'concurrent owner')
        self.assert_no_staging()

    def test_concurrent_directory_created_at_publication_is_preserved(self):
        import os
        from unittest.mock import patch
        real_link = os.link
        def competing_link(source, target):
            Path(target).mkdir()
            (Path(target) / 'owned.txt').write_text('keep')
            return real_link(source, target)
        with patch('reaper_timecapsule.core.os.link', side_effect=competing_link):
            with self.assertRaises(FileExistsError):
                make_backup(self.source, self.archive)
        self.assertEqual((self.archive / 'owned.txt').read_text(), 'keep')
        self.assert_no_staging()

    def test_unsupported_filesystem_fails_without_rename_fallback(self):
        import errno
        from unittest.mock import patch
        with patch('reaper_timecapsule.core.os.link', side_effect=OSError(errno.ENOTSUP, 'No hard links')), \
             patch('reaper_timecapsule.core.os.rename', side_effect=AssertionError('unsafe fallback')):
            with self.assertRaises(OSError):
                make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        self.assert_no_staging()

    def test_success_leaves_verified_archive_only(self):
        from reaper_timecapsule.core import verify_backup
        make_backup(self.source, self.archive)
        self.assertEqual(verify_backup(self.archive)['files'][0]['path'], 'reaper-kb.ini')
        self.assert_no_staging()

    def test_dangling_symlink_target_is_preserved(self):
        try:
            self.archive.symlink_to(self.base / 'missing')
        except (OSError, NotImplementedError):
            self.skipTest('Symlink privilege unavailable')
        with self.assertRaises(FileExistsError):
            make_backup(self.source, self.archive)
        self.assertTrue(self.archive.is_symlink())
        self.assertFalse((self.base / 'missing').exists())
        self.assert_no_staging()
