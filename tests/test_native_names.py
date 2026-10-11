"""Native-name archive boundaries with synthetic resources only."""
import json
import os
import platform
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, verify_backup, restore_backup


class NativeNameTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.archive = self.root / 'capsule.zip'

    def put(self, name):
        file = self.source / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b'synthetic preset\n')
        return file

    def rewrite(self, mutate):
        with zipfile.ZipFile(self.archive) as z:
            data = {name: z.read(name) for name in z.namelist()}
        manifest = json.loads(data['manifest.json'])
        mutate(manifest)
        data['manifest.json'] = json.dumps(manifest).encode()
        with zipfile.ZipFile(self.archive, 'w') as z:
            for name, value in data.items():
                z.writestr(name, value)

    def test_schema_three_roundtrip_and_legacy_default(self):
        self.put('presets/test.ini')
        make_backup(self.source, self.archive, native_names=True)
        report = verify_backup(self.archive)
        self.assertEqual(report['schema'], 3)
        self.assertEqual(report['files'][0]['archive_member'], 'objects/000000.bin')
        destination = self.root / 'restored'
        restore_backup(self.archive, destination)
        self.assertEqual((destination / 'REAPER/presets/test.ini').read_bytes(), b'synthetic preset\n')
        legacy = self.root / 'legacy.zip'
        make_backup(self.source, legacy)
        self.assertEqual(verify_backup(legacy)['schema'], 2)

    @unittest.skipIf(os.name == 'nt', 'Colon is not a Windows filename')
    def test_colon_filename_preserved_without_renaming_original(self):
        original = self.put('presets/au-discodsp: OB-Xd-builtin.ini')
        with self.assertRaises(ValueError):
            make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        make_backup(self.source, self.archive, native_names=True)
        self.assertTrue(original.exists())
        destination = self.root / 'restored'
        restore_backup(self.archive, destination)
        self.assertEqual((destination / 'REAPER' / original.relative_to(self.source)).read_bytes(), original.read_bytes())
        with zipfile.ZipFile(self.archive) as z:
            self.assertEqual(set(z.namelist()), {'manifest.json', 'objects/000000.bin'})

    def test_portable_recovery_is_isolated_and_reversible(self):
        original = self.put('presets/test.ini')
        make_backup(self.source, self.archive, native_names=True)
        destination = self.root / 'portable'
        report = restore_backup(self.archive, destination, portable_names=True)
        mapping = report['filename_mapping'][0]
        self.assertEqual(mapping['original'], 'presets/test.ini')
        self.assertEqual((destination / mapping['restored']).read_bytes(), original.read_bytes())
        self.assertEqual(report['restored_portable'], 0)
        self.assertEqual(report['isolated_for_review'], 1)
        self.assertFalse((destination / 'REAPER').exists())

    def test_cross_platform_original_names_require_explicit_mapping(self):
        self.put('presets/test.ini')
        make_backup(self.source, self.archive, native_names=True)
        with patch('reaper_timecapsule.core.platform.system', return_value='DifferentOS'):
            with self.assertRaises(ValueError):
                restore_backup(self.archive, self.root / 'bad')
            restore_backup(self.archive, self.root / 'mapped', portable_names=True)
        self.assertFalse((self.root / 'bad').exists())

    def test_malicious_original_and_member_paths_rejected_before_restore(self):
        for field, value in [('path', '../escape.ini'), ('path', '/tmp/escape'),
                             ('path', 'C:\\escape.ini'), ('archive_member', 'objects/../../escape'),
                             ('archive_member', 'objects/000001.bin')]:
            with self.subTest(field=field, value=value):
                self.put('presets/test.ini')
                make_backup(self.source, self.archive, native_names=True)
                self.rewrite(lambda m: m['files'][0].update({field: value}))
                with self.assertRaises(ValueError):
                    restore_backup(self.archive, self.root / 'bad', portable_names=True)
                self.assertFalse((self.root / 'bad').exists())
                self.archive.unlink()

    def test_duplicate_objects_are_rejected(self):
        self.put('presets/a.ini')
        self.put('presets/b.ini')
        make_backup(self.source, self.archive, native_names=True)
        self.rewrite(lambda m: m['files'][1].update(archive_member=m['files'][0]['archive_member']))
        with self.assertRaises(ValueError):
            verify_backup(self.archive)

    def test_case_collision_is_only_restored_with_isolated_mapping(self):
        self.put('presets/a.ini')
        self.put('presets/b.ini')
        make_backup(self.source, self.archive, native_names=True)
        self.rewrite(lambda m: m['files'][1].update(path='presets/A.ini'))
        # Original spelling ambiguity cannot safely activate on a case-insensitive FS.
        with self.assertRaises(ValueError):
            restore_backup(self.archive, self.root / 'bad')
        report = restore_backup(self.archive, self.root / 'mapped', portable_names=True)
        self.assertEqual(len(report['filename_mapping']), 2)

    def test_native_mode_keeps_license_and_cache_exclusions(self):
        self.put('reaper-license.rk')
        self.put('reaper-vstplugins64.ini')
        self.put('presets/test.ini')
        make_backup(self.source, self.archive, native_names=True)
        report = verify_backup(self.archive)
        self.assertEqual([x['path'] for x in report['files']], ['presets/test.ini'])
        self.assertEqual(len(report['omitted']), 2)

    def test_nonportable_manifest_names_can_be_extracted_on_windows_without_using_them(self):
        self.put('presets/test.ini')
        make_backup(self.source, self.archive, native_names=True)
        self.rewrite(lambda m: m['files'][0].update(path='presets/colon: preset.ini'))
        destination = self.root / 'mapped'
        report = restore_backup(self.archive, destination, portable_names=True)
        mapping = report['filename_mapping'][0]
        self.assertEqual(mapping['original'], 'presets/colon: preset.ini')
        self.assertEqual((destination / mapping['restored']).read_bytes(), b'synthetic preset\n')
