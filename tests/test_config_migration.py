import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.config_migration import preview_migration, MAX_BYTES


class ConfigurationMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.old = self.root / 'old.ini'
        self.new = self.root / 'new.ini'
        self.write('[REAPER]\ntinttcp=0\npeaksedges=1\n', '[REAPER]\ntinttcp=1\npeaksedges=1\n')

    def write(self, old, new='[REAPER]\ntinttcp=1\n'):
        self.old.write_bytes(old.encode('utf-8'))
        self.new.write_bytes(new.encode('utf-8'))

    def preview(self, **kwargs):
        return preview_migration(self.old, self.new, source_version='7.82',
                                 target_version=kwargs.pop('target_version', '7.82'), **kwargs)

    def test_approved_diff_and_no_writes(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (self.old, self.new)}
        with patch.object(Path, 'write_text', side_effect=AssertionError('write')), \
             patch.object(Path, 'write_bytes', side_effect=AssertionError('write')):
            report = self.preview()
        self.assertTrue(report['read_only'])
        self.assertFalse(report['writes_performed'])
        self.assertEqual(report['summary']['candidate'], 2)
        self.assertEqual({r['key']: r['change'] for r in report['entries']},
                         {'tinttcp': 'conflict', 'peaksedges': 'same'})
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})

    def test_windows_and_macos_sensitive_paths_not_reported(self):
        for path in (r'C:\Users\Private\AppData\Roaming\REAPER',
                     '/Users/Private/Library/Application Support/REAPER',
                     r'\\server\Private\REAPER'):
            with self.subTest(path=path):
                self.write('[REAPER]\nvstpath=' + path + '\npassword=PRIVATE\nunknown=PRIVATE\n'
                           '[Audio]\ndevice=PRIVATE\n[VST3]\nentry=PRIVATE\n[CLAP]\nentry=PRIVATE\n')
                report = self.preview()
                self.assertNotIn('PRIVATE', json.dumps(report))
                self.assertNotIn(path, json.dumps(report))
                self.assertEqual(report['summary'], {'candidate': 0, 'review': 2, 'exclude': 5})

    def test_exact_identity_and_unsupported_values(self):
        self.write('[Other]\ntinttcp=0\n[REAPER]\ntinttcp=999\npeaksedges=/secret\n')
        self.assertEqual(self.preview()['summary']['candidate'], 0)
        self.assertNotIn('/secret', json.dumps(self.preview()))

    def test_missing_keys_never_proposed_for_addition_or_deletion(self):
        self.write('[REAPER]\npeaksedges=0\n')
        rows = self.preview()['entries']
        self.assertEqual({r['change'] for r in rows}, {'source_only', 'target_only'})
        self.assertTrue(all(r['status'] == 'review' for r in rows))

    def test_version_changes_unknown_and_invalid(self):
        for version in (None, '8.0', '7.81', 'invalid', '4.99'):
            with self.subTest(version=version):
                self.assertEqual(self.preview(target_version=version)['summary']['candidate'], 0)
        self.assertEqual(preview_migration(self.old, self.new)['summary']['candidate'], 0)

    def test_bom_crlf_case_and_literal_interpolation(self):
        self.write('\ufeff[REAPER]\r\nTINTTCP=0\r\nunknown=%(password)s\r\n')
        self.assertEqual(self.preview()['summary']['candidate'], 1)
        self.assertNotIn('%(password)s', json.dumps(self.preview()))

    def test_malformed_ambiguous_and_multiline_fail_closed(self):
        for data in ('tinttcp=0', '[REAPER]\nSECRET', '[REAPER]\ntinttcp=0\nTINTTCP=1',
                     '[REAPER]\na=1\n[reaper]\nb=2', '[DEFAULT]\ntinttcp=0',
                     '[REAPER]\nx=1\n continuation', '[REAPER]\nx=\x00', ''):
            with self.subTest(data=data):
                self.write(data)
                with self.assertRaises(ValueError) as error:
                    self.preview()
                self.assertNotIn('SECRET', str(error.exception))

    def test_invalid_encoding_size_directory_and_missing(self):
        self.old.write_bytes(b'[REAPER]\nx=\xff')
        with self.assertRaises(ValueError):
            self.preview()
        self.old.write_bytes(b'x' * (MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            self.preview()
        for source in (self.root, self.root / 'missing'):
            with self.assertRaises(ValueError):
                preview_migration(source, self.new)

    def test_symlink_rejected_when_supported(self):
        link = self.root / 'link.ini'
        try:
            link.symlink_to(self.old)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink privilege unavailable')
        with self.assertRaises(ValueError):
            preview_migration(link, self.new)

    def test_control_characters_and_ambiguous_headers_fail_closed(self):
        for data in ('[REAPER]\nx=PRIVATE\x1b[31m', '[REAPER]\ntinttcp=0\n tinttcp=1',
                     '[REAPER]\nx=1\n[extra]=PRIVATE', '[[REAPER]]\ntinttcp=0',
                     '[REAPER]\nkey[alias]=PRIVATE', '[REAPER]\nkey\talias=PRIVATE'):
            with self.subTest(data=data):
                self.write(data)
                with self.assertRaises(ValueError) as error:
                    self.preview()
                self.assertNotIn('PRIVATE', str(error.exception))

    def test_changes_summary_includes_unchanged_and_conflicts(self):
        report = self.preview()
        self.assertEqual(report['changes'], {'same': 1, 'conflict': 1,
                                             'source_only': 0, 'target_only': 0})

    def test_cli_json_and_safe_error(self):
        command = [sys.executable, '-m', 'reaper_timecapsule', 'config-preview',
                   str(self.old), str(self.new), '--source-version', '7.82', '--target-version', '7.82']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['read_only'])
        self.write('[REAPER]\nPRIVATE_SECRET')
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('PRIVATE_SECRET', result.stderr)
