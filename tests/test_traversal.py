import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from reaper_timecapsule.core import make_backup, verify_backup

class PathValidationTests(unittest.TestCase):
    def test_archive_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "Src"
            src.mkdir()
            (src / "reaper-kb.ini").write_text("actions")
            archive = base / "backup.zip"
            make_backup(src, archive)
            with zipfile.ZipFile(archive) as z:
                entries = {x.filename: z.read(x) for x in z.infolist()}
            manifest = json.loads(entries["manifest.json"])
            manifest["files"][0]["path"] = "../invalid"
            entries["manifest.json"] = json.dumps(manifest).encode()
            with zipfile.ZipFile(archive, "w") as z:
                for name, data in entries.items():
                    z.writestr(name, data)
            with self.assertRaises(ValueError):
                verify_backup(archive)
