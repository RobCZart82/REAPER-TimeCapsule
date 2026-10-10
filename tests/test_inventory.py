"""Synthetic inventory tests. Never inspect the developer's live REAPER directory."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper_timecapsule.core import make_backup, preview, preview_backup, restore_backup


class RecoveryInventoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.source = self.base / "REAPER"
        self.source.mkdir()

    def put(self, name: str, value: str = "sample"):
        target = self.source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

    def test_repositories_export_safe_display_urls(self):
        self.put("reapack.ini", (
            "[test]\n"
            "repo1=https://raw.githubusercontent.com/iliaspoulakis/Reaper-Tools/master/index.xml\n"
            "repo2=https://raw.githubusercontent.com/TouristKiller/TK-Scripts/master/index.xml\n"
            "restricted=https://user:password@example.org/private/index.xml?secret=abc#frag\n"
        ))
        report = preview(self.source)["inventory"]["reapack"]
        self.assertEqual(len(report["repository_index_urls"]), 3)
        self.assertIn("https://example.org/private/index.xml", report["repository_index_urls"])
        self.assertNotIn("password", str(report))
        self.assertNotIn("secret=", str(report))
        self.assertEqual(report["repository_states"], "not-parsed-preserved-in-original-settings")

    def test_midi_and_native_extensions_are_identified(self):
        self.put("MenuSets/Chords.ReaperMenu")
        self.put("KeyMaps/Chords.ReaperKeyMap")
        self.put("reaper-menu.ini")
        self.put("reaper-kb.ini")
        self.put("UserPlugins/reaper_reapack-arm64.dylib")
        self.put("UserPlugins/reaper_sws-arm64.dylib")
        info = preview(self.source)["inventory"]
        self.assertEqual(len(info["midi_workflow"]["right_click_menu_files"]), 1)
        self.assertEqual(len(info["midi_workflow"]["keymap_files"]), 1)
        self.assertTrue(info["midi_workflow"]["custom_actions_saved"])
        self.assertEqual({x["family"] for x in info["native_extensions"]}, {"ReaPack", "SWS"})
        self.assertFalse(info["reapack"]["automatic_sync"])

    def test_inventory_survives_backup_restore(self):
        self.put("reapack.ini", "repo=https://raw.githubusercontent.com/TouristKiller/TK-Scripts/master/index.xml\n")
        self.put("UserPlugins/reaper_sws-arm64.dylib")
        self.put("Scripts/midi.lua")
        archive = self.base / "snapshot.zip"
        make_backup(self.source, archive)
        stored = preview_backup(archive)["inventory"]
        self.assertEqual(stored["format"], "inventory-v1")
        recovered = self.base / "recovery"
        restore_backup(archive, recovered)
        self.assertTrue((recovered / "REAPER/reapack.ini").exists())
        self.assertTrue((recovered / "REAPER/Scripts/midi.lua").exists())
        self.assertTrue((recovered / "NeedsReview/UserPlugins/reaper_sws-arm64.dylib").exists())
        self.assertFalse((recovered / "REAPER/UserPlugins/reaper_sws-arm64.dylib").exists())


if __name__ == "__main__":
    unittest.main()
