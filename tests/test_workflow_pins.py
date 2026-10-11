import re
import unittest
from collections import Counter
from pathlib import Path


class WorkflowPinTests(unittest.TestCase):
    REVIEWED_ACTIONS = Counter({
        'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1': 2,
        'actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97': 2,
        'actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9': 1,
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
