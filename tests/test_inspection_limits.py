"""User-facing budget query must be read-only and headless."""
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch

from reaper_timecapsule.__main__ import main
from reaper_timecapsule.inspection_limits import inspection_limits, inspection_limits_text
from reaper_timecapsule.gui import App


class InspectionLimitsTests(unittest.TestCase):
    def test_cli_works_without_resource_files_or_gui(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["timecapsule", "inspection-limits"]), \
             patch("pathlib.Path.open", side_effect=AssertionError("unexpected file access")), \
             patch("reaper_timecapsule.__main__.preview", side_effect=AssertionError("unexpected scan")), \
             contextlib.redirect_stdout(output):
            main()
        report = json.loads(output.getvalue())
        self.assertEqual(report["report_format"], "timecapsule-inspection-limits")
        self.assertFalse(report["user_configurable"])
        self.assertEqual(report["archive"]["zip_members"], report["archive"]["source_records"] + 1)
        self.assertTrue(all(value > 0 for group in ("archive", "midi", "reapack", "configuration") for value in report[group].values()))

    def test_summary_uses_current_enforcement_constants(self):
        with patch("reaper_timecapsule.core.MAX_FILES", 12), \
             patch("reaper_timecapsule.reapack_profile.MAX_INI_BYTES", 3 * 1024 ** 2):
            report = inspection_limits()
            self.assertEqual(report["archive"]["source_records"], 12)
            self.assertEqual(report["archive"]["zip_members"], 13)
            self.assertEqual(report["reapack"]["ini_bytes"], 3 * 1024 ** 2)
            self.assertIn("ini bytes: 3 MiB", inspection_limits_text())

    def test_gui_help_does_not_replace_current_report_or_start_operation(self):
        app = object()
        with patch("reaper_timecapsule.gui.messagebox.showinfo") as dialog:
            App._show_limits(app)
        self.assertEqual(dialog.call_args.kwargs["parent"], app)
        self.assertIn("Free-space estimates are not reservations", dialog.call_args.args[1])
