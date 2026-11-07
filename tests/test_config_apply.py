import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.config_apply import apply_preferences, rollback_preferences
from reaper_timecapsule.config_staging import export_preferences


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        (self.root / 'inputs').mkdir()
        self.source = self.root / 'inputs/source.ini'
        self.target = self.root / 'inputs/reaper.ini'
        self.source.write_bytes(b'[REAPER]\ntinttcp=0\npeaksedges=1\n')
        self.original = b'\xef\xbb\xbf;private comment\r\n[REAPER]\r\ntinttcp = 1  \r\npeaksedges=0\r\npassword=secret\r\n[Audio]\r\ndevice=private'
        self.target.write_bytes(self.original)
        staging = self.root / 'TimeCapsule-Staging'
        staging.mkdir()
        self.archive = staging / 'review.timecapsule-stage.zip'
        self.recovery = staging / 'recovery'
        export_preferences(self.source, self.target, self.archive, selections=['REAPER/tinttcp'],
                           source_version='7.84', target_version='7.84', opt_in=True)

    def apply(self, **options):
        return apply_preferences(self.archive, self.target, self.recovery,
                                 opt_in=options.get('opt_in', True),
                                 reaper_closed=options.get('reaper_closed', True))

    def rollback(self):
        return rollback_preferences(self.recovery, self.target, opt_in=True, reaper_closed=True)

    def test_exact_full_file_recovery_and_formatting(self):
        self.assertTrue(self.apply()['applied'])
        self.assertEqual(self.target.read_bytes(), self.original.replace(b'tinttcp = 1', b'tinttcp = 0'))
        self.assertEqual((self.recovery / 'original.ini').read_bytes(), self.original)
        self.assertTrue(self.rollback()['restored'])
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertTrue(self.rollback()['already_original'])

    def test_embedded_bom_in_unknown_key_is_not_treated_as_approved_key(self):
        self.original += b'\n[Other]\nkey=value\n[Unused]\nx=1'
        # Same section, different exact key: only the document-leading BOM is special.
        self.original = self.original.replace(b'peaksedges=0', b'\xef\xbb\xbftinttcp=1\r\npeaksedges=0')
        self.target.write_bytes(self.original)
        self.archive = self.archive.with_name('embedded.timecapsule-stage.zip')
        export_preferences(self.source, self.target, self.archive, selections=['REAPER/tinttcp'],
                           source_version='7.84', target_version='7.84', opt_in=True)
        self.apply()
        self.assertEqual(self.target.read_bytes(), self.original.replace(b'tinttcp = 1', b'tinttcp = 0'))
        self.rollback()
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_consent_required(self):
        for options in ({'opt_in': False}, {'reaper_closed': False}):
            with self.assertRaises(ValueError):
                self.apply(**options)
        self.assertFalse(self.recovery.exists())
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_stale_baseline_and_existing_bundle_refused(self):
        self.target.write_bytes(self.original + b'\n;changed')
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse(self.recovery.exists())
        self.target.write_bytes(self.original)
        self.recovery.mkdir()
        with self.assertRaises(FileExistsError):
            self.apply()
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_replace_failure_keeps_original_and_verified_recovery(self):
        with patch('reaper_timecapsule.config_apply.os.replace', side_effect=OSError('failure')):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual((self.recovery / 'original.ini').read_bytes(), self.original)
        self.assertFalse(self.target.with_name('reaper.ini.timecapsule-lock').exists())
        self.assertFalse(list(self.target.parent.glob('.timecapsule-config-*')))

    def test_backup_write_failure_cannot_touch_target(self):
        with patch('reaper_timecapsule.config_apply._write_new', side_effect=OSError('full')):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_final_conflict_check(self):
        from reaper_timecapsule import config_apply
        real = config_apply._load_recovery
        changed = self.original + b'\n; concurrent edit'
        def race(path):
            result = real(path)
            self.target.write_bytes(changed)
            return result
        with patch.object(config_apply, '_load_recovery', side_effect=race):
            with self.assertRaisesRegex(ValueError, 'Target changed'):
                self.apply()
        self.assertEqual(self.target.read_bytes(), changed)

    def test_rollback_refuses_later_edits_and_corrupt_backup(self):
        self.apply()
        applied = self.target.read_bytes()
        self.target.write_bytes(applied + b'\n; new work')
        with self.assertRaisesRegex(ValueError, 'Target changed'):
            self.rollback()
        self.target.write_bytes(applied)
        (self.recovery / 'original.ini').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.rollback()
        self.assertEqual(self.target.read_bytes(), applied)

    def test_existing_lock_and_unsafe_backup_location(self):
        lock = self.target.with_name('reaper.ini.timecapsule-lock')
        lock.write_text('other operation')
        with self.assertRaises(FileExistsError):
            self.apply()
        self.assertEqual(lock.read_text(), 'other operation')
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_cli_requires_confirmation_and_round_trips(self):
        command = [sys.executable, '-m', 'reaper_timecapsule', 'config-apply',
                   str(self.archive), str(self.target), str(self.recovery)]
        failed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 1)
        self.assertFalse(self.recovery.exists())
        result = subprocess.run(command + ['--opt-in', '--reaper-closed'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, '-m', 'reaper_timecapsule', 'config-rollback',
                                 str(self.recovery), str(self.target), '--opt-in', '--reaper-closed'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_recovery_must_be_external_and_target_mode_is_preserved(self):
        self.recovery = self.target.parent / 'TimeCapsule-Staging/recovery'
        self.recovery.parent.mkdir()
        with self.assertRaises(ValueError):
            self.apply()
        self.assertEqual(self.target.read_bytes(), self.original)
        self.recovery = self.archive.parent / 'recovery'
        if os.name != 'nt':
            self.target.chmod(0o640)
        self.apply()
        if os.name != 'nt':
            self.assertEqual(self.target.stat().st_mode & 0o777, 0o640)

    @unittest.skipIf(os.name == 'nt', 'symlink privilege varies')
    def test_symlink_and_hardlink_target_refused(self):
        linked = self.target.with_name('linked.ini')
        linked.symlink_to(self.target)
        for path in (linked,):
            with self.assertRaises(ValueError):
                apply_preferences(self.archive, path, self.recovery, opt_in=True, reaper_closed=True)
        linked.unlink()
        os.link(self.target, linked)
        with self.assertRaises(ValueError):
            self.apply()


if __name__ == '__main__':
    unittest.main()
