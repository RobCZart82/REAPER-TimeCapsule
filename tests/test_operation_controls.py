import tempfile
import unittest
from pathlib import Path

from reaper_timecapsule.core import make_backup, restore_backup, verify_backup
from reaper_timecapsule.operation import OperationControl, OperationCancelled


class CancelAt(OperationControl):
    def __init__(self, phase, occurrence=1):
        super().__init__()
        self.phase, self.occurrence, self.count = phase, occurrence, 0

    def checkpoint(self, phase, completed=0, total=0):
        if phase == self.phase:
            self.count += 1
            if self.count == self.occurrence:
                self.cancel()
        super().checkpoint(phase, completed, total)


class OperationControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / 'Source'
        self.source.mkdir()
        (self.source / 'reaper-kb.ini').write_bytes(b'action' * 100)
        self.archive = self.root / 'one.zip'

    def test_backup_cancel_during_scan_copy_verification_and_publication(self):
        for phase, count in [('Scanning', 1), ('Copying backup', 2), ('Verifying', 1), ('Publishing backup', 1)]:
            with self.subTest(phase=phase):
                with self.assertRaises(OperationCancelled):
                    make_backup(self.source, self.archive, control=CancelAt(phase, count))
                self.assertFalse(self.archive.exists())
                self.assertEqual(list(self.root.glob('.timecapsule-*')), [])

    def test_restore_cancel_during_copy_and_before_publication(self):
        make_backup(self.source, self.archive)
        before = self.archive.read_bytes()
        for phase, count in [('Verifying', 1), ('Restoring', 2), ('Publishing restore', 1)]:
            with self.subTest(phase=phase):
                with self.assertRaises(OperationCancelled):
                    restore_backup(self.archive, self.root / 'Recovered', control=CancelAt(phase, count))
                self.assertFalse((self.root / 'Recovered').exists())
                self.assertEqual(list(self.root.glob('.timecapsule-restore-*')), [])
                self.assertEqual(self.archive.read_bytes(), before)

    def test_completed_progress_and_pre_cancelled_verification(self):
        control = OperationControl()
        make_backup(self.source, self.archive, control=control)
        verifying = OperationControl()
        verify_backup(self.archive, control=verifying)
        phase, completed, total = verifying.latest()
        self.assertEqual(phase, 'Verification complete')
        self.assertEqual(completed, total)
        verifying.cancel()
        with self.assertRaises(OperationCancelled):
            verify_backup(self.archive, control=verifying)
