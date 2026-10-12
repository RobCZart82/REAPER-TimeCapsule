"""Synthetic encoding fixtures; original profile bytes must stay untouched."""
import tempfile
import unittest
from pathlib import Path

from reaper_timecapsule.core import scan
from reaper_timecapsule.midi_validation import validate_midi_workflow


class MIDIEncodingTests(unittest.TestCase):
    def report(self, data, filename='reaper-kb.ini'):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            result = validate_midi_workflow(root, scan(root))
            self.assertEqual(path.read_bytes(), data)
            return result

    def test_utf8_bom_and_literal_replacement_character_are_valid(self):
        for text in ('; árvíztűrő\n', '; valid �\n'):
            for bom in (b'', b'\xef\xbb\xbf'):
                with self.subTest(text=text, bom=bom):
                    report = self.report(bom + text.encode('utf-8'))
                    self.assertEqual(report['parse_problems'], [])
                    self.assertEqual(report['issue_counts']['parse_problems'], 0)

    def test_legacy_and_corrupt_bytes_require_review(self):
        for data in (b'; caf\xe9\n', b'; broken \xff\x80\n'):
            with self.subTest(data=data):
                report = self.report(data)
                self.assertEqual(report['status'], 'needs-review')
                self.assertEqual(report['issue_counts']['parse_problems'], 1)
                self.assertEqual(report['parse_problems'][0]['decoding'], 'replacement')
                self.assertEqual(report['parse_problems'][0]['encoding'], 'utf-8-sig')

    def test_menu_decode_warning_retains_static_references(self):
        report = self.report(b'[MIDI piano roll context]\n; \xff\nitem_0=40001 Command\n',
                             'MenuSets/test.ReaperMenu')
        self.assertEqual(report['issue_counts']['parse_problems'], 1)
        self.assertEqual(report['unverified_numeric_commands'],
                         [{'section': 32060, 'command': '40001'}])
