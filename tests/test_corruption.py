import tempfile
import unittest
import zipfile
from pathlib import Path
from reaper_timecapsule.core import make_backup, verify_backup

class CorruptionTests(unittest.TestCase):
    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "Src"
            src.mkdir()
            (src / "reaper-kb.ini").write_text("original")
            archive = base / "backup.zip"
            make_backup(src, archive)
            with zipfile.ZipFile(archive) as z:
                entries = {x.filename: z.read(x) for x in z.infolist()}
            entries["resources/reaper-kb.ini"] = b"changed!"
            with zipfile.ZipFile(archive, "w") as z:
                for name, data in entries.items():
                    z.writestr(name, data)
            with self.assertRaises(ValueError):
                verify_backup(archive)
