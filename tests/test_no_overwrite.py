import tempfile
import unittest
from pathlib import Path
from reaper_timecapsule.core import make_backup, restore_backup

class NoOverwriteTests(unittest.TestCase):
    def test_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "Source"
            src.mkdir()
            (src / "reaper-kb.ini").write_text("action")
            archive = base / "one.zip"
            make_backup(src, archive)
            with self.assertRaises(FileExistsError):
                make_backup(src, archive)
            out = base / "Restore"
            restore_backup(archive, out)
            with self.assertRaises(FileExistsError):
                restore_backup(archive, out)
