import tempfile
import unittest
from pathlib import Path
from reaper_timecapsule.core import preview

class SymlinkTests(unittest.TestCase):
    def test_scan_skips_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "REAPER"
            src.mkdir()
            target = base / "outside.txt"
            target.write_text("unrelated")
            try:
                (src / "linked.txt").symlink_to(target)
            except OSError:
                self.skipTest("Symlinks not permitted on this platform")
            result = preview(src)
            self.assertEqual(result["files"], 0)
