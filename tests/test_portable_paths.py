"""Portable archive namespace tests never create OS-invalid files on disk."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import FORMAT, SCHEMA, VERSION, verify_backup, restore_backup
from reaper_timecapsule.rules import decide


class PortableArchivePathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / 'synthetic.zip'

    def build(self, paths):
        data = b'synthetic portable resource'
        manifest = dict(format=FORMAT, schema=SCHEMA, app_version=VERSION, files=[
            dict(path=path, policy=decide(path).policy, size=len(data),
                 sha256=hashlib.sha256(data).hexdigest()) for path in paths])
        with zipfile.ZipFile(self.archive, 'w') as archive:
            archive.writestr('manifest.json', json.dumps(manifest))
            for path in paths:
                archive.writestr('resources/' + path, data)

    def assert_rejected_before_restore(self, paths):
        self.build(paths)
        with self.assertRaises(ValueError):
            verify_backup(self.archive)
        with patch('reaper_timecapsule.core.tempfile.mkdtemp', side_effect=AssertionError('restore writes')):
            with self.assertRaises(ValueError):
                restore_backup(self.archive, self.root / 'Recovered')
        self.assertFalse((self.root / 'Recovered').exists())

    def test_windows_reserved_devices_with_extensions_and_directories(self):
        for name in ('CON', 'nul.txt', 'AUX.lua', 'PRN', 'COM1.lua', 'LPT9.lua',
                     'COM¹.lua', 'LPT².txt', 'con .lua'):
            for path in ('Scripts/' + name, 'Scripts/' + name + '/file.lua'):
                with self.subTest(path=path):
                    self.assert_rejected_before_restore([path])

    def test_forbidden_characters_controls_and_trailing_characters(self):
        for name in ('bad?.lua', 'bad*.lua', 'bad|name', 'bad"name', 'bad<name',
                     'bad>name', 'trailing.', 'trailing ', 'line\nname', 'tab\tname'):
            with self.subTest(name=name):
                self.assert_rejected_before_restore(['Scripts/' + name])

    def test_case_collisions_at_file_or_directory_level(self):
        for paths in (['Scripts/Action.lua', 'Scripts/action.lua'],
                      ['Scripts/one.lua', 'scripts/two.lua']):
            with self.subTest(paths=paths):
                self.assert_rejected_before_restore(paths)

    def test_unicode_normalization_collisions(self):
        self.assert_rejected_before_restore(['Scripts/café.lua', 'Scripts/cafe\u0301.lua'])
        self.assert_rejected_before_restore(['Scripts/café/one.lua', 'Scripts/cafe\u0301/two.lua'])

    def test_file_directory_prefix_conflicts_in_either_order(self):
        for paths in (['Scripts/item', 'Scripts/item/file.lua'],
                      ['Scripts/item/file.lua', 'Scripts/item']):
            with self.subTest(paths=paths):
                self.assert_rejected_before_restore(paths)

    def test_noncolliding_unicode_and_shared_directories_restore(self):
        paths = ['Scripts/café.lua', 'Scripts/音楽.lua', 'Scripts/folder/a.lua',
                 'Scripts/folder/b.lua', 'Scripts/COM10.lua', 'Scripts/.hidden.lua']
        self.build(paths)
        self.assertEqual(len(verify_backup(self.archive)['files']), len(paths))
        destination = self.root / 'Recovered'
        restore_backup(self.archive, destination)
        for path in paths:
            self.assertEqual((destination / 'REAPER' / path).read_bytes(), b'synthetic portable resource')
