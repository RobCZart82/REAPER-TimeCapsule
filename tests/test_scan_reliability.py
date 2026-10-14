"""Synthetic traversal and destination-boundary regressions; no live profiles."""
import errno
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

from reaper_timecapsule.core import _windows_desktop_directory, default_restore_destination, make_backup, preview, scan, verify_backup
from reaper_timecapsule.gui import App
from reaper_timecapsule.safe_paths import filesystem_path


class ScanReliabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.source = self.base / 'source'
        self.source.mkdir()
        (self.source / 'reaper-kb.ini').write_text('synthetic')

    def link(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink privilege unavailable')

    def test_traversal_error_aborts_scan_and_backup_before_staging(self):
        blocked = self.source / 'Scripts' / 'Restricted'
        def failing_walk(root, *, followlinks, onerror=None):
            yield str(root), [], ['reaper-kb.ini']
            error = PermissionError(errno.EACCES, 'Permission denied', str(blocked))
            if onerror:
                onerror(error)
        with patch('reaper_timecapsule.core.os.walk', side_effect=failing_walk):
            with self.assertRaisesRegex(OSError, 'Restricted'):
                scan(self.source)
            with self.assertRaisesRegex(OSError, 'Restricted'):
                make_backup(self.source, self.base / 'new' / 'backup.zip')
        self.assertFalse((self.base / 'new').exists())
        self.assertEqual(list(self.base.rglob('.timecapsule-*.zip')), [])

    def test_file_metadata_error_is_not_silently_skipped(self):
        real_lstat = Path.lstat
        def fail(path):
            if path.name == 'reaper-kb.ini':
                raise PermissionError(errno.EACCES, 'Permission denied', str(path))
            return real_lstat(path)
        with patch.object(Path, 'lstat', fail):
            with self.assertRaises(PermissionError):
                make_backup(self.source, self.base / 'backup.zip')
        self.assertFalse((self.base / 'backup.zip').exists())

    def test_external_dangling_and_cyclic_links_reported_and_not_archived(self):
        external = self.base / 'external'
        external.mkdir()
        (external / 'private.lua').write_text('never archive this')
        self.link(self.source / 'external-tools', external, True)
        self.link(self.source / 'dangling.lua', self.base / 'missing')
        self.link(self.source / 'cycle', self.source, True)
        report = preview(self.source)
        names = {x['path'] for x in report['skipped_entries']}
        self.assertEqual(names, {'external-tools', 'dangling.lua', 'cycle'})
        self.assertEqual(App._brief(report)['skipped_entries'], report['skipped_entries'])
        archive = self.base / 'backup.zip'
        make_backup(self.source, archive)
        manifest = verify_backup(archive)
        self.assertEqual({x['path'] for x in manifest['omitted']}, names)
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(set(z.namelist()), {'resources/reaper-kb.ini', 'manifest.json'})
            self.assertNotIn('never archive this', z.read('manifest.json').decode())

    def test_destination_alias_into_source_rejected_without_writes(self):
        alias = self.base / 'alias'
        self.link(alias, self.source, True)
        with self.assertRaisesRegex(ValueError, 'inside the source'):
            make_backup(self.source, alias / 'nested' / 'backup.zip')
        self.assertFalse((self.source / 'nested').exists())
        self.assertEqual(list(self.source.iterdir()), [self.source / 'reaper-kb.ini'])

    def test_external_alias_is_pinned_even_if_retargeted_during_verification(self):
        outside = self.base / 'outside'
        outside.mkdir()
        alias = self.base / 'alias'
        self.link(alias, outside, True)
        original_verify = verify_backup
        def retarget(*args, **kwargs):
            result = original_verify(*args, **kwargs)
            alias.unlink()
            alias.symlink_to(self.source, target_is_directory=True)
            return result
        with patch('reaper_timecapsule.core.verify_backup', side_effect=retarget):
            make_backup(self.source, alias / 'backup.zip')
        self.assertTrue((outside / 'backup.zip').is_file())
        self.assertFalse((self.source / 'backup.zip').exists())
        original_verify(outside / 'backup.zip')

    @unittest.skipUnless(os.name == 'nt', 'Windows known-folder API')
    def test_restore_default_uses_redirected_windows_desktop(self):
        desktop = _windows_desktop_directory()
        self.assertTrue(desktop.is_absolute())
        self.assertEqual(default_restore_destination(), desktop / 'TimeCapsule-Restored')

    @unittest.skipUnless(os.name == 'nt', 'Windows extended-length paths')
    def test_long_windows_script_path_is_scanned_and_backed_up(self):
        scripts = self.source / 'Scripts'
        scripts.mkdir()
        name = 'x' * 240 + '.lua'  # One legal component; full path exceeds MAX_PATH.
        source_file = scripts / name
        self.assertGreater(len(str(source_file)), 260)
        io_file = Path(filesystem_path(source_file))
        io_file.write_bytes(b'-- synthetic long-path script\\n')
        self.addCleanup(lambda: io_file.unlink(missing_ok=True))

        relative = 'Scripts/' + name
        items = scan(self.source)
        self.assertIn(relative, {item['path'] for item in items})
        archive = self.base / 'long-path.zip'
        make_backup(self.source, archive)
        manifest = verify_backup(archive)
        self.assertIn(relative, {item['path'] for item in manifest['files']})

    def test_windows_reparse_entry_excluded_without_traversal(self):
        from types import SimpleNamespace
        marker = getattr(__import__('stat'), 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
        real_lstat = Path.lstat
        entry = self.source / 'junction'
        entry.mkdir()
        def attributes(path):
            if Path(filesystem_path(path, force=True)) == Path(filesystem_path(entry, force=True)):
                value = real_lstat(path)
                return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=marker)
            return real_lstat(path)
        with patch('reaper_timecapsule.core.stat.FILE_ATTRIBUTE_REPARSE_POINT', marker, create=True), \
             patch.object(Path, 'lstat', attributes):
            result = scan(self.source)
        self.assertEqual([x['path'] for x in result if x.get('kind') == 'link'], ['junction'])
