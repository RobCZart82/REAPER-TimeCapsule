import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import preview
from reaper_timecapsule.operation import OperationControl, OperationCancelled
from reaper_timecapsule.reports import scan_report, report_page, export_report, PAGE_SIZE


class ReportTests(unittest.TestCase):
    def fixture(self):
        entries = [{'path': f'Scripts/synthetic-{i:04d}.lua', 'policy': 'keep' if i % 2 else 'review',
                    'size': i, 'reason': 'synthetic evidence'} for i in range(501)]
        return {'entries': entries, 'report_schema': 1}

    def test_filter_pagination_preserves_exact_evidence_and_bound(self):
        report = self.fixture()
        first = report_page(report)
        second = report_page(report, page=1)
        self.assertEqual(len(first['rows']), PAGE_SIZE)
        self.assertEqual(second['rows'][0], report['entries'][PAGE_SIZE])
        filtered = report_page(report, policy='review', query='SYNTHETIC-000')
        self.assertEqual(filtered['matches'], 5)
        self.assertTrue(all(x['policy'] == 'review' for x in filtered['rows']))
        self.assertEqual(report_page(report, page=10)['rows'], [])

    def test_cancelled_filter_never_returns_partial_report(self):
        control = OperationControl()
        control.cancel()
        with self.assertRaises(OperationCancelled):
            report_page(self.fixture(), control=control)

    def test_live_scan_report_marks_provenance_and_not_transactional(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            (source / 'reaper-kb.ini').write_bytes(b'synthetic')
            report = scan_report(preview(source))
        self.assertEqual(report['report_schema'], 1)
        self.assertTrue(report['scan_completed'])
        self.assertFalse(report['transactional_snapshot'])
        self.assertEqual(report['entries'][0]['path'], 'reaper-kb.ini')
        self.assertEqual(report['summary']['counts']['keep'], 1)

    def test_export_never_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'private.json'
            export_report(self.fixture(), path)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                export_report({}, path)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(json.loads(before)['entries']), 501)

    def test_cancelled_export_cleans_only_owned_partial_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'private.json'
            control = OperationControl()
            original = control.checkpoint
            calls = []
            def cancel_during_write(*args):
                calls.append(args)
                if len(calls) == 3:
                    control.cancel()
                original(*args)
            with patch.object(control, 'checkpoint', side_effect=cancel_during_write):
                with self.assertRaises(OperationCancelled):
                    export_report(self.fixture(), path, control=control)
            self.assertFalse(path.exists())
