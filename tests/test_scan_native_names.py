"""Read-only inventory accepts native names; portable backup fails before writing."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, preview
from reaper_timecapsule.gui import App


class NativeScanTests(unittest.TestCase):
    def test_native_colon_preset_scans_without_modifying_source(self):
        if os.name == 'nt':
            self.skipTest('Windows cannot create native colon filenames')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'REAPER'
            (source / 'presets').mkdir(parents=True)
            preset = source / 'presets' / 'au-example: Synth-builtin.ini'
            preset.write_bytes(b'synthetic preset')
            before = preset.stat()
            result = preview(source)
            self.assertEqual(result['files'], 1)
            self.assertEqual(result['items'][0]['policy'], 'keep')
            self.assertFalse(result['portable_names_ready'])
            self.assertEqual(result['portability_issues'][0]['path'], preset.relative_to(source).as_posix())
            self.assertEqual(App._brief(result)['portability_issues'], result['portability_issues'])
            with patch('reaper_timecapsule.core.tempfile.mkstemp', side_effect=AssertionError('backup wrote staging')):
                with self.assertRaisesRegex(ValueError, 'Cannot create a portable backup.*au-example'):
                    make_backup(source, root / 'snapshot.zip')
            self.assertFalse((root / 'snapshot.zip').exists())
            self.assertEqual(preset.read_bytes(), b'synthetic preset')
            self.assertEqual(preset.stat().st_mtime_ns, before.st_mtime_ns)

    def test_portability_report_and_preflight_on_every_platform(self):
        for paths in (['presets/au-example: Synth.ini'], ['Scripts/CON.lua'],
                      ['Scripts/one.lua', 'scripts/two.lua']):
            with self.subTest(paths=paths), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / 'REAPER'
                source.mkdir()
                items = [dict(path=p, size=1, policy='keep', reason='synthetic') for p in paths]
                with patch('reaper_timecapsule.core.scan', return_value=items), \
                     patch('reaper_timecapsule.core.tempfile.mkstemp', side_effect=AssertionError('staging created')):
                    result = preview(source)
                    self.assertFalse(result['portable_names_ready'])
                    self.assertTrue(result['portability_issues'])
                    with self.assertRaisesRegex(ValueError, 'Cannot create a portable backup'):
                        make_backup(source, Path(tmp) / 'backup.zip')

    def test_excluded_names_do_not_block_portable_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            items = [dict(path='private:token.key', size=1, policy='exclude', reason='credential')]
            with patch('reaper_timecapsule.core.scan', return_value=items):
                result = preview(source)
            self.assertTrue(result['portable_names_ready'])
            self.assertEqual(result['portability_issues'], [])

    def test_portable_source_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / 'reaper-kb.ini').write_text('synthetic', encoding='utf-8')
            result = preview(source)
            self.assertTrue(result['portable_names_ready'])
            self.assertEqual(result['portability_issues'], [])
