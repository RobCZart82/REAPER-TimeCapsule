"""Headless interaction tests: no real resource directories or Tk windows."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from reaper_timecapsule.gui import App


class ConfigurationPreviewGUITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source, self.target = root / 'old.ini', root / 'clean.ini'
        self.source.write_text('[REAPER]\ntinttcp=0\nvstpath=PRIVATE\n')
        self.target.write_text('[REAPER]\ntinttcp=1\n')
        self.outputs = []
        self.app = SimpleNamespace(_do=lambda fn, **kwargs: self.outputs.append(fn()),
                                   _configuration_report=App._configuration_report)

    def run_dialog(self, files, versions):
        with patch('reaper_timecapsule.gui.filedialog.askopenfilename', side_effect=files) as select, \
             patch('reaper_timecapsule.gui.simpledialog.askstring', side_effect=versions) as version:
            App._config_preview(self.app)
            return select.call_count, version.call_count

    def test_explicit_selection_reports_conflicts_without_writes(self):
        before = [p.read_bytes() for p in (self.source, self.target)]
        self.assertEqual(self.run_dialog([str(self.source), str(self.target)], [' 7.82 ', '7.82']), (2, 2))
        report = self.outputs[0]
        self.assertEqual(report['Summary'], {'candidate': 1, 'review': 0, 'exclude': 1})
        self.assertEqual(report['Changes']['conflict'], 1)
        self.assertNotIn('PRIVATE', json.dumps(report))
        self.assertIn('Read-only', report['Configuration preview'])
        self.assertEqual(len(report['Preference evidence catalog']['preferences']), 2)
        self.assertFalse(report['Preference evidence catalog']['active_writes_supported'])
        self.assertEqual(before, [p.read_bytes() for p in (self.source, self.target)])

    def test_unknown_versions_remain_review(self):
        self.run_dialog([str(self.source), str(self.target)], ['', ''])
        self.assertFalse(self.outputs[0]['Version compatible'])
        self.assertEqual(self.outputs[0]['Summary']['candidate'], 0)

    def test_cancel_at_each_step_does_not_compare(self):
        for files, versions, expected in (([''], [], (1, 0)),
                ([str(self.source), ''], [], (2, 0)),
                ([str(self.source), str(self.target)], [None], (2, 1)),
                ([str(self.source), str(self.target)], ['7.82', None], (2, 2))):
            with self.subTest(expected=expected):
                with patch('reaper_timecapsule.gui.preview_migration') as compare:
                    self.assertEqual(self.run_dialog(files, versions), expected)
                    compare.assert_not_called()
        self.assertEqual(self.outputs, [])

    def test_parse_error_uses_existing_error_dialog(self):
        self.source.write_text('[REAPER]\nPRIVATE_SECRET')
        self.app.log = Mock()
        self.app._do = lambda fn, **kwargs: App._do(self.app, fn, **kwargs)
        with patch('reaper_timecapsule.gui.messagebox.showerror') as error:
            self.run_dialog([str(self.source), str(self.target)], ['7.82', '7.82'])
            error.assert_called_once()
            self.assertNotIn('PRIVATE_SECRET', str(error.call_args))
            self.app.log.insert.assert_not_called()
