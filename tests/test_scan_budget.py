"""Bound inventory records, including directory reparse points; synthetic only."""
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, scan


class ScanBudgetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        self.marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        self.real_lstat = Path.lstat

    def linked_metadata(self, path):
        if path.name in ("a", "b", "c", "link"):
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=self.marker)
        return self.real_lstat(path)

    def test_directory_links_cannot_bypass_record_budget(self):
        with patch("reaper_timecapsule.core.MAX_FILES", 2), \
             patch("reaper_timecapsule.core.stat.FILE_ATTRIBUTE_REPARSE_POINT", self.marker, create=True), \
             patch("reaper_timecapsule.core.os.walk", return_value=iter([
                 (str(self.source), ["a", "b", "c"], [])
             ])), patch.object(Path, "lstat", lambda path: self.linked_metadata(path)):
            with self.assertRaisesRegex(ValueError, "inspection budget"):
                scan(self.source)

    def test_exact_directory_link_budget_is_allowed_without_following_targets(self):
        with patch("reaper_timecapsule.core.MAX_FILES", 2), \
             patch("reaper_timecapsule.core.stat.FILE_ATTRIBUTE_REPARSE_POINT", self.marker, create=True), \
             patch("reaper_timecapsule.core.os.walk", return_value=iter([
                 (str(self.source), ["a", "b"], [])
             ])), patch.object(Path, "lstat", lambda path: self.linked_metadata(path)):
            result = scan(self.source)
        self.assertEqual([row["path"] for row in result], ["a", "b"])
        self.assertTrue(all(row["kind"] == "link" and row["policy"] == "exclude" for row in result))

    def test_file_and_later_directory_link_share_one_budget(self):
        (self.source / "reaper-kb.ini").write_text("synthetic", encoding="utf-8")
        real_lstat = Path.lstat
        def metadata(path):
            if path.name == "link":
                return self.linked_metadata(path)
            return real_lstat(path)
        with patch("reaper_timecapsule.core.MAX_FILES", 1), \
             patch("reaper_timecapsule.core.stat.FILE_ATTRIBUTE_REPARSE_POINT", self.marker, create=True), \
             patch("reaper_timecapsule.core.os.walk", return_value=iter([
                 (str(self.source), [], ["reaper-kb.ini"]),
                 (str(self.source), ["link"], [])
             ])), patch.object(Path, "lstat", metadata):
            with self.assertRaisesRegex(ValueError, "inspection budget"):
                scan(self.source)

    def test_empty_regular_directories_do_not_consume_record_budget(self):
        (self.source / "empty").mkdir()
        (self.source / "reaper-kb.ini").write_text("synthetic", encoding="utf-8")
        with patch("reaper_timecapsule.core.MAX_FILES", 1):
            result = scan(self.source)
        self.assertEqual([row["path"] for row in result], ["reaper-kb.ini"])

    def test_over_budget_backup_stops_before_inventory_and_staging(self):
        destination = self.root / "new" / "capsule.zip"
        with patch("reaper_timecapsule.core.MAX_FILES", 1), \
             patch("reaper_timecapsule.core.stat.FILE_ATTRIBUTE_REPARSE_POINT", self.marker, create=True), \
             patch("reaper_timecapsule.core.os.walk", return_value=iter([
                 (str(self.source), ["a", "b"], [])
             ])), patch.object(Path, "lstat", lambda path: self.linked_metadata(path)), \
             patch("reaper_timecapsule.core.build_inventory", return_value={}) as inventory:
            with self.assertRaisesRegex(ValueError, "inspection budget"):
                make_backup(self.source, destination)
            inventory.assert_not_called()
        self.assertFalse(destination.parent.exists())
        self.assertEqual(list(self.root.glob(".timecapsule-*")), [])
