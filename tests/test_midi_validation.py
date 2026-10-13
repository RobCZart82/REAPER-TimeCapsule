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
        self.assertEqual(result["status"], "needs-review")
        self.assertEqual(result["toolbar_icon_dependencies"]["status"], "not-checked")
        self.assertEqual(len(result["unverified_numeric_commands"]), 4)

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

    def test_script_case_mismatch_requires_review(self):
        self.put("Scripts/Case.lua", "-- synthetic\n")
        self.put("reaper-kb.ini", f'SCR 4 32060 "{GUID}" "Test" "Scripts/case.lua"\n')
        result = self.report()
        self.assertEqual(result["status"], "missing-dependencies")
        self.assertEqual(result["script_registration_issues"][0]["reason"], "case-mismatch-requires-review")

    def test_exact_script_names_and_relative_script_base_remain_saved(self):
        self.put("Scripts/Case.lua", "-- synthetic\n")
        for script_path in ("Scripts/Case.lua", "Case.lua", "Scripts\\Case.lua"):
            with self.subTest(script_path=script_path):
                self.put("reaper-kb.ini", f'SCR 4 32060 "{GUID}" "Test" "{script_path}"\n')
                self.assertEqual(self.report()["script_registration_issues"], [])

    def test_absolute_script_reference_requires_remapping(self):
        self.put("reaper-kb.ini",
                 'SCR 4 32060 "' + GUID + '" "Custom: test.lua" "/Users/old/Library/Application Support/REAPER/Scripts/test.lua"\n')
        self.assertEqual(self.report()["script_registration_issues"][0]["reason"],
                         "absolute-path-requires-remapping")

    def test_reascript_registration_ids_resolve_from_menu_and_saved_script_paths(self):
        rs_id = "RS" + "a" * 40
        contextual_id = "RS1234_" + "b" * 40
        self.put("Scripts/one.lua", "-- synthetic script fixture\n")
        self.put("Scripts/two.lua", "-- synthetic script fixture\n")
        self.put("KeyMaps/scripts.ReaperKeyMap",
                 f'SCR 4 32060 {rs_id} "Custom: One" "Scripts/one.lua"\n'
                 f'SCR 4 32060 {contextual_id} "Custom: Two" "Scripts/two.lua"\n')
        self.put("MenuSets/scripts.ReaperMenu",
                 "[MIDI piano roll context]\n"
                 f"item_1=_{rs_id} One\n"
                 f"item_2=_{contextual_id} Two\n")
        result = self.report()
        self.assertEqual(result["script_registrations_checked"], 2)
        self.assertEqual(result["resolved_menu_references"], 2)
        self.assertEqual(result["missing_custom_actions"], [])
        self.assertEqual(result["script_registration_issues"], [])
        self.assertEqual(result["issue_counts"]["parse_problems"], 0)

    def test_custom_action_resolves_supported_reascript_dependencies(self):
        for rs_id in ("RS" + "a" * 40, "RS1234_" + "b" * 40):
            with self.subTest(rs_id=rs_id):
                self.put("Scripts/test.lua", "error('must never execute')\n")
                self.put("reaper-menu.ini", f"[MIDI piano roll context]\nitem_0=_{GUID} Test\n")
                self.put("reaper-kb.ini", f'ACT 1 32060 "{GUID}" "Test" _{rs_id}\n'
                         f'SCR 4 32060 {rs_id} "Test" "Scripts/test.lua"\n')
                result = self.report()
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["unverified_extension_commands"], [])
                self.assertEqual(result["missing_custom_actions"], [])
                self.assertEqual(result["script_registration_issues"], [])
                self.assertEqual(result["runtime_validation"]["status"], "not-performed")

    def test_custom_action_reports_missing_or_wrong_section_reascript(self):
        rs_id = "RS" + "a" * 40
        for registration in ("", f'SCR 4 0 {rs_id} "Test" "Scripts/test.lua"\n'):
            with self.subTest(registration=registration):
                self.put("Scripts/test.lua", "-- synthetic\n")
                self.put("reaper-kb.ini", f'ACT 1 32060 "{GUID}" "Test" _{rs_id}\n' + registration)
                result = self.report()
                self.assertEqual(result["status"], "missing-dependencies")
                self.assertEqual(result["issue_counts"]["missing"], 1)
                self.assertEqual(result["missing_custom_actions"][0]["command"], "_" + rs_id.lower())
                self.assertEqual(result["unverified_extension_commands"], [])

    def test_malformed_rs_and_extension_dependencies_remain_unverified(self):
        self.put("reaper-kb.ini", f'ACT 1 32060 "{GUID}" "Test" _RSshort _SWS_TEST\n')
        result = self.report()
        self.assertEqual(result["status"], "needs-review")
        self.assertEqual(result["unverified_extension_commands"], ["_rsshort", "_sws_test"])
        self.assertEqual(result["missing_custom_actions"], [])

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
        result = self.report()
        self.assertEqual(result["status"], "needs-review")
        self.assertEqual(result["toolbar_icon_dependencies"]["status"], "not-checked")
        self.assertEqual(result["runtime_validation"]["status"], "not-performed")

    def test_parse_problem_total_and_truncation_are_reported(self):
        self.put("reaper-kb.ini", "\n".join(f"ACT malformed {i}" for i in range(125)))
        result = self.report()
        self.assertEqual(result["issue_counts"]["parse_problems"], 125)
        self.assertEqual(len(result["parse_problems"]), 100)
        self.assertEqual(result["issue_detail_limit"], 100)
        self.assertTrue(result["truncated_issue_details"]["parse_problems"])


if __name__ == "__main__":
    unittest.main()


class MIDIGraphTests(unittest.TestCase):
    setUp = MIDIWorkflowValidationTests.setUp
    put = MIDIWorkflowValidationTests.put
    report = MIDIWorkflowValidationTests.report
    def test_duplicate_inside_one_file_is_reported_not_overwritten(self):
        self.put('reaper-kb.ini', f'ACT 1 32060 "{GUID}" "A" 40001\nACT 1 32060 "{GUID}" "B" _{SECOND}\n')
        report = self.report()
        self.assertEqual(report['status'], 'invalid-action-graph')
        self.assertTrue(report['duplicate_definitions'][0]['conflicting'])
        self.assertEqual(report['missing_custom_actions'][0]['command'], '_' + SECOND)

    def test_identical_export_and_live_definition_requires_review(self):
        record = f'ACT 1 32060 "{GUID}" "A" 40001\n'
        self.put('reaper-kb.ini', record)
        self.put('KeyMaps/test.ReaperKeyMap', record)
        report = self.report()
        self.assertFalse(report['duplicate_definitions'][0]['conflicting'])
        self.assertEqual(report['status'], 'needs-review')

    def test_numeric_dependency_is_unverified_even_if_implausible(self):
        self.put('reaper-kb.ini', f'ACT 1 32060 "{GUID}" "A" 999999999\n')
        self.assertEqual(self.report()['unverified_numeric_commands'], [{'section': 32060, 'command': '999999999'}])

    def test_nested_action_cycle_is_reported(self):
        self.put('reaper-kb.ini', f'ACT 1 32060 "{GUID}" "A" _{SECOND}\nACT 1 32060 "{SECOND}" "B" _{GUID}\n')
        report = self.report()
        self.assertEqual(report['status'], 'invalid-action-graph')
        self.assertEqual(report['dependency_cycles'][0]['length'], 3)

    def test_same_identifier_in_other_section_is_not_duplicate(self):
        self.put('reaper-kb.ini', f'ACT 1 32060 "{GUID}" "A" 40001\nACT 1 0 "{GUID}" "B" 40001\n')
        self.assertEqual(self.report()['duplicate_definitions'], [])

    def test_deep_chain_uses_no_recursion_and_reports_missing_leaf(self):
        records = [f'ACT 1 32060 "{i:032x}" "A" _{i+1:032x}' for i in range(1, 1600)]
        self.put('reaper-kb.ini', '\n'.join(records))
        report = self.report()
        self.assertEqual(report['status'], 'missing-dependencies')
        self.assertEqual(report['dependency_cycles'], [])

    def test_truncation_keeps_total_numeric_issue_count(self):
        self.put('reaper-kb.ini', f'ACT 1 32060 "{GUID}" "A" ' + ' '.join(str(i) for i in range(1, 151)))
        report = self.report()
        self.assertEqual(report['issue_counts']['unverified_numeric'], 150)
        self.assertEqual(len(report['unverified_numeric_commands']), 100)
        self.assertTrue(report['truncated_issue_details']['unverified_numeric'])
