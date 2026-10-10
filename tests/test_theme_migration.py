import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.theme_migration import preview_themes


class ThemeMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source, self.factory, self.target = (root / name for name in ('source', 'factory', 'target'))
        for folder in (self.source, self.factory, self.target):
            folder.mkdir()

    def preview(self, **kwargs):
        return preview_themes(self.source, self.factory, self.target,
                              source_version='7.82', factory_version=kwargs.get('version', '7.82'))

    def put(self, folder, name, content=b'synthetic theme'):
        (folder / name).write_bytes(content)

    def test_factory_modified_and_user_themes_without_writes(self):
        self.put(self.source, 'Default.ReaperThemeZip')
        self.put(self.factory, 'Default.ReaperThemeZip')
        self.put(self.source, 'Variant.ReaperThemeZip', b'PRIVATE_THEME_CONTENT')
        self.put(self.factory, 'Variant.ReaperThemeZip', b'factory')
        self.put(self.source, 'MyTheme.ReaperThemeZip')
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                  for d in (self.source, self.factory, self.target) for p in d.iterdir()}
        with patch('zipfile.ZipFile', side_effect=AssertionError('unpack')), \
             patch.object(Path, 'write_bytes', side_effect=AssertionError('write')):
            report = self.preview()
        self.assertEqual(report['summary'], dict(factory_match=1, modified_factory=1, user_theme=1, review=0))
        self.assertFalse(report['writes_performed'])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertNotIn('PRIVATE_THEME_CONTENT', json.dumps(report))

    def test_destination_conflict_never_recommends_reuse(self):
        for directory in (self.source, self.factory):
            self.put(directory, 'Default.ReaperThemeZip')
        self.put(self.target, 'Default.ReaperThemeZip', b'other theme')
        row = self.preview()['entries'][0]
        self.assertEqual((row['status'], row['target_state']), ('review', 'conflict'))
        self.assertTrue(row['factory_identical'])
        self.put(self.target, 'Default.ReaperThemeZip')
        self.assertEqual(self.preview()['entries'][0]['target_state'], 'identical')

    def test_different_or_unknown_factory_versions_require_review(self):
        for directory in (self.source, self.factory):
            self.put(directory, 'Default.ReaperThemeZip')
        for version in (None, '7.81', '8.0', 'invalid'):
            with self.subTest(version=version):
                self.assertEqual(self.preview(version=version)['summary']['review'], 1)
        self.assertEqual(preview_themes(self.source, self.factory, self.target)['summary']['review'], 1)

    def test_unpacked_and_unknown_entries_always_review(self):
        self.put(self.source, 'Default.ReaperTheme')
        self.put(self.factory, 'Default.ReaperTheme')
        (self.source / 'assets').mkdir()
        self.put(self.source / 'assets', 'private.png', b'private')
        self.put(self.source, 'unknown.ini', b'PRIVATE_PASSWORD')
        report = self.preview()
        self.assertEqual(report['summary']['review'], 3)
        self.assertNotIn('PRIVATE_PASSWORD', json.dumps(report))
        self.assertNotIn('private.png', json.dumps(report))

    def test_case_insensitive_names_and_collisions(self):
        self.put(self.source, 'DEFAULT.ReaperThemeZip')
        self.put(self.factory, 'default.reaperthemezip')
        self.assertEqual(self.preview()['summary']['factory_match'], 1)
        # Simulate case-sensitive/Unicode filename ambiguity on any host.
        with patch.object(Path, 'iterdir', return_value=iter([
                self.source / 'DEFAULT.ReaperThemeZip', self.source / 'default.reaperthemezip'])):
            with self.assertRaises(ValueError):
                self.preview()

    def test_symlinks_are_not_read_or_traversed(self):
        link = self.source / 'link.ReaperThemeZip'
        try:
            link.symlink_to(self.factory / 'missing')
        except (OSError, NotImplementedError):
            self.skipTest('Symlink privilege unavailable')
        self.assertEqual(self.preview()['summary']['review'], 1)
        rootlink = self.source.parent / 'linked-dir'
        rootlink.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            preview_themes(rootlink, self.factory, self.target)

    def test_limits_and_missing_inputs(self):
        self.put(self.source, 'Default.ReaperThemeZip', b'12345')
        with patch('reaper_timecapsule.theme_migration.MAX_FILE_BYTES', 4):
            with self.assertRaises(ValueError):
                self.preview()
        with patch('reaper_timecapsule.theme_migration.MAX_FILES', 0):
            with self.assertRaises(ValueError):
                self.preview()
        with self.assertRaises(ValueError):
            preview_themes(self.source / 'missing', self.factory, self.target)

    def test_cli_json(self):
        self.put(self.source, 'User.ReaperThemeZip')
        command = [sys.executable, '-m', 'reaper_timecapsule', 'theme-preview',
                   str(self.source), str(self.factory), str(self.target),
                   '--source-version', '7.82', '--factory-version', '7.82']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['read_only'])
