import tempfile
import unittest
from pathlib import Path
from reaper_timecapsule.core import make_backup, restore_backup, verify_backup

class RoundtripTests(unittest.TestCase):
    def test_backup_restore_with_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "Source"
            (src / "Scripts").mkdir(parents=True)
            (src / "Scripts" / "my.lua").write_text("-- demo")
            (src / "reaper.ini").write_text("device=old")
            (src / "reaper-vstplugins_arm64.ini").write_text("stale")
            archive = base / "snapshot.zip"
            make_backup(src, archive)
            self.assertEqual(verify_backup(archive)["schema"], 2)
            out = base / "Out"
            restore_backup(archive, out)
            self.assertTrue((out / "REAPER/Scripts/my.lua").exists())
            self.assertTrue((out / "NeedsReview/reaper.ini").exists())
            self.assertFalse((out / "REAPER/reaper-vstplugins_arm64.ini").exists())
