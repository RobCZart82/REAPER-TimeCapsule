import re
import unittest
from collections import Counter
from pathlib import Path


class WorkflowPinTests(unittest.TestCase):
    REVIEWED_ACTIONS = Counter({
        'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683': 2,
        'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065': 2,
        'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02': 1,
    })

    def test_external_actions_are_pinned_to_full_commit_ids(self):
        workflows = Path('.github/workflows')
        uses = []
        for path in workflows.glob('*.yml'):
            uses.extend((path.name, value) for value in re.findall(r'^\s*- uses:\s*([^\s]+)',
                                                                   path.read_text(), re.MULTILINE))
        self.assertTrue(uses)
        for filename, value in uses:
            with self.subTest(workflow=filename, action=value):
                self.assertRegex(value, r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$')

    def test_workflows_use_only_the_reviewed_action_commits(self):
        actual = Counter()
        for path in Path('.github/workflows').glob('*.yml'):
            actual.update(re.findall(r'^\s*- uses:\s*([^\s]+)',
                                     path.read_text(), re.MULTILINE))
        self.assertEqual(actual, self.REVIEWED_ACTIONS)

    def test_least_privilege_workflow_tokens(self):
        for path in Path('.github/workflows').glob('*.yml'):
            content = path.read_text()
            self.assertIn('permissions:\n  contents: read', content)
            self.assertNotIn('write-all', content)
