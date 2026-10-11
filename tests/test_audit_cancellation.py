"""Synthetic registry and GUI audit budgets; no user configuration."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import preview
from reaper_timecapsule.midi_validation import validate_midi_workflow
from reaper_timecapsule.operation import OperationControl, OperationCancelled
from reaper_timecapsule.reapack_profile import inspect_registry


class AuditCancellationTests(unittest.TestCase):
    def registry(self, root):
        path = root / 'registry.db'
        with closing(sqlite3.connect(path)) as db:
            db.execute('CREATE TABLE entries(id INTEGER, remote TEXT, category TEXT, package TEXT, version TEXT, flags INTEGER)')
            db.execute('CREATE TABLE files(entry INTEGER, path TEXT)')
            db.executemany('INSERT INTO entries VALUES (?, "Synthetic", "MIDI", "Test", "1", 0)', [(i,) for i in range(2000)])
            db.executemany('INSERT INTO files VALUES (?, "Scripts/test.lua")', [(i,) for i in range(2000)])
            db.commit()
        return path

    def test_expired_query_returns_explicit_timeout_and_preserves_database(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.registry(Path(temp))
            before = database.read_bytes()
            with patch('reaper_timecapsule.reapack_profile.time.monotonic', side_effect=[0, 0, 10]):
                report = inspect_registry(database, query_timeout=1)
            self.assertEqual(report['status'], 'timed-out')
            self.assertEqual(before, database.read_bytes())
            self.assertEqual(list(Path(temp).iterdir()), [database])

    def test_sqlite_progress_handler_honours_cancellation_during_query(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.registry(Path(temp))
            before = database.read_bytes()
            control = OperationControl()
            calls = []
            def clock():
                calls.append(1)
                # Deadline plus seven small statements, then a real VM callback.
                if len(calls) > 10:
                    control.cancel()
                return 0
            with patch('reaper_timecapsule.reapack_profile.time.monotonic', side_effect=clock):
                with self.assertRaises(OperationCancelled):
                    inspect_registry(database, control=control)
            self.assertGreater(len(calls), 10)
            self.assertEqual(before, database.read_bytes())
            self.assertEqual(list(Path(temp).iterdir()), [database])

    def test_cancelled_scan_and_midi_stop_before_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            control = OperationControl()
            control.cancel()
            with self.assertRaises(OperationCancelled):
                preview(Path(temp), control=control)
            with self.assertRaises(OperationCancelled):
                validate_midi_workflow(Path(temp), [{'path': 'reaper-kb.ini', 'policy': 'keep'}], control=control)
