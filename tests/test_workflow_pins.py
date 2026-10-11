import re
import unittest
from pathlib import Path


class WorkflowPinTests(unittest.TestCase):
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

    def test_expected_official_release_commits_are_used(self):
        content = '\n'.join(path.read_text() for path in Path('.github/workflows').glob('*.yml'))
        for sha in ('11bd71901bbe5b1630ceea73d27597364c9af683',
                    'a26af69be951a213d495a4c3e4e4022e16d87065',
                    'ea165f8d65b6e75b540449e92b4886f43607fa02'):
            self.assertIn('@' + sha, content)

    def test_least_privilege_workflow_tokens(self):
        for path in Path('.github/workflows').glob('*.yml'):
            content = path.read_text()
            self.assertIn('permissions:\n  contents: read', content)
            self.assertNotIn('write-all', content)
