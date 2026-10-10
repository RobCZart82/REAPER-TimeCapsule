"""Synthetic tests: no copyrighted or private user REAPER assets committed."""
import tempfile
import unittest
from pathlib import Path

from reaper_timecapsule.core import scan
from reaper_timecapsule.midi_validation import validate_midi_workflow

GUID = "36e86106806c014f86ed11788747f024"
SECOND = "17ae964ffd642144a74b5ed80299396a"


class MIDIWorkflowValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name)

    def put(self, name, value):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def report(self):
        return validate_midi_workflow(self.source, scan(self.source))

    def test_menu_resolves_custom_actions_from_keymap(self):
        self.put("MenuSets/midi.ReaperMenu",
                 "[MIDI piano roll context]\nitem_0=40001 Native command\nitem_1=_" + GUID + " Scale\n")
        self.put("KeyMaps/scale.ReaperKeyMap",
                 'ACT 1 32060 "' + GUID + '" "Custom: Scale" 40214 40164 40048\n')
        result = self.report()
        self.assertEqual(result["menu_custom_references"], 1)
        self.assertEqual(result["resolved_menu_references"], 1)
        self.assertEqual(result["missing_custom_actions"], [])
        self.assertEqual(result["status"], "ok")

    def test_menu_missing_action(self):
        self.put("MenuSets/midi.ReaperMenu", "[MIDI piano roll context]\nitem_1=_" + GUID + " Scale\n")
        result = self.report()
        self.assertEqual(result["status"], "missing-dependencies")
        self.assertEqual(result["missing_custom_actions"][0]["command"], "_" + GUID)

    def test_wrong_section_not_treated_as_midi_action(self):
        self.put("reaper-menu.ini", "[Main toolbar]\nitem_1=_" + GUID + " Action\n")
        self.assertEqual(self.report()["menu_custom_references"], 0)

    def test_action_in_wrong_section_not_falsely_resolved(self):
        self.put("MenuSets/midi.ReaperMenu", "[MIDI piano roll context]\nitem_1=_" + GUID + " Action\n")
        self.put("reaper-kb.ini", 'ACT 1 0 "' + GUID + '" "Custom: main only" 40001\n')
        self.assertEqual(self.report()["resolved_menu_references"], 0)
        self.assertEqual(self.report()["status"], "missing-dependencies")

    def test_script_registration_portability(self):
        self.put("reaper-kb.ini", 'SCR 4 32060 "' + GUID + '" "Custom: my.lua" "my.lua"\n')
        self.assertEqual(self.report()["script_registration_issues"][0]["reason"], "missing-from-backup")
        self.put("Scripts/my.lua", "-- a test script, not an executable fixture\n")
        self.assertEqual(self.report()["script_registration_issues"], [])

    def test_absolute_script_reference_requires_remapping(self):
        self.put("reaper-kb.ini",
                 'SCR 4 32060 "' + GUID + '" "Custom: test.lua" "/Users/old/Library/Application Support/REAPER/Scripts/test.lua"\n')
        self.assertEqual(self.report()["script_registration_issues"][0]["reason"],
                         "absolute-path-requires-remapping")

    def test_external_extension_is_unverified_not_dropped(self):
        self.put("MenuSets/midi.ReaperMenu", "[MIDI piano roll context]\nitem_1=_SWS_MY_ACTION Menu\n")
        result = self.report()
        self.assertEqual(result["status"], "needs-review")
        self.assertIn("_sws_my_action", result["unverified_extension_commands"])

    def test_custom_action_can_depend_on_another_missing_action(self):
        self.put("reaper-kb.ini",
                 'ACT 1 32060 "' + GUID + '" "Custom: A" _' + SECOND + '\n')
        result = self.report()
        self.assertEqual(result["status"], "missing-dependencies")
        self.assertEqual(result["missing_custom_actions"][0]["command"], "_" + SECOND)

    def test_large_chord_menu_all_120_references_resolve(self):
        # Models the size of the user's chord/scale/arpeggio bundle without
        # redistributing any of its third-party content.
        menu = ["[MIDI piano roll context]"]
        keymap = []
        for i in range(1, 121):
            guid = format(i, "032x")
            menu.append(f"item_{i}=_{guid} Action {i}")
            keymap.append(f'ACT 1 32060 "{guid}" "Custom: Synthetic {i}" 40001')
        self.put("MenuSets/large.ReaperMenu", "\n".join(menu))
        self.put("KeyMaps/large.ReaperKeyMap", "\n".join(keymap))
        report = self.report()
        self.assertEqual(report["menu_custom_references"], 120)
        self.assertEqual(report["resolved_menu_references"], 120)
        self.assertEqual(report["missing_custom_actions"], [])

    def test_empty_midi_inventory_not_claimed_to_be_complete(self):
        self.assertEqual(self.report()["status"], "needs-review")


if __name__ == "__main__":
    unittest.main()
