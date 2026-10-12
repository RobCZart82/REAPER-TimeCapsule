"""Synthetic ReaPack encoding diagnostics and read-only controls."""
import tempfile
import unittest
from pathlib import Path

from reaper_timecapsule.reapack_profile import parse_profile


class ReaPackEncodingTests(unittest.TestCase):
    def parse(self, data):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'reapack.ini'
            path.write_bytes(data)
            report = parse_profile(path)
            self.assertEqual(path.read_bytes(), data)
            return report

    def test_valid_utf8_and_bom_have_no_fallback_warning(self):
        data = '[general]\nversion=4\n[remotes]\nsize=1\nremote0=Café �|https://example.org/index.xml|1|2\n'.encode('utf-8')
        for bom in (b'', b'\xef\xbb\xbf'):
            with self.subTest(bom=bom):
                report = self.parse(bom + data)
                self.assertEqual(report['status'], 'parsed')
                self.assertEqual(report['notes'], [])

    def test_cp1252_and_undefined_bytes_remain_partial(self):
        for name in (b'Caf\xe9', b'Broken\x81'):
            with self.subTest(name=name):
                report = self.parse(b'[general]\nversion=4\n[remotes]\nsize=1\nremote0=' + name + b'|https://user:secret@example.org/index.xml?token=private|1|2\n')
                self.assertEqual(report['status'], 'partial')
                self.assertEqual(report['repository_count'], 1)
                self.assertIn('cp1252', report['notes'][0])
                self.assertNotIn('secret', str(report))
                self.assertNotIn('private', str(report))

    def test_invalid_unsupported_and_incomplete_profiles_keep_warning(self):
        for data, status in ((b'broken\xe9', 'invalid'),
                             (b'[general]\nversion=99\n;\xe9', 'unsupported'),
                             (b'[general]\nversion=4\n;\xe9', 'partial')):
            with self.subTest(status=status):
                report = self.parse(data)
                self.assertEqual(report['status'], status)
                self.assertIn('cp1252', report['notes'][0])
