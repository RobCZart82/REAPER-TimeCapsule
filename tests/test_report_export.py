import json
import tempfile
import unittest
from pathlib import Path

from reaper_timecapsule.report_export import export_report


class ReportExportTests(unittest.TestCase):
    def test_exports_complete_json_without_changing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "REAPER"
            source.mkdir()
            sentinel = source / "reaper.ini"
            sentinel.write_text("private config", encoding="utf-8")
            destination = root / "reports" / "audit.json"
            destination.parent.mkdir()
            report = {"items": [f"item-{index}" for index in range(500)]}

            saved = export_report(report, destination, forbidden_root=source)

            self.assertEqual(saved, destination.resolve())
            self.assertEqual(json.loads(saved.read_text(encoding="utf-8")), report)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "private config")
            self.assertEqual(list(root.glob(".audit.json.*.tmp")), [])

    def test_refuses_export_inside_scanned_resource_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "REAPER"
            root.mkdir()
            with self.assertRaisesRegex(ValueError, "outside the scanned REAPER"):
                export_report({"safe": True}, root / "audit.json", forbidden_root=root)
            self.assertEqual(list(root.iterdir()), [])

    def test_existing_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "audit.json"
            destination.write_text("existing", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                export_report({"replacement": True}, destination)
            self.assertEqual(destination.read_text(encoding="utf-8"), "existing")

    def test_serialization_failure_cleans_only_its_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(TypeError):
                export_report({"unsupported": object()}, root / "audit.json")
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
