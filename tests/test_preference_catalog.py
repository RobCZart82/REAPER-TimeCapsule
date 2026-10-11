import json
import subprocess
import sys
import unittest
from pathlib import Path

from reaper_timecapsule.config_migration import APPROVED_PREFERENCES
from reaper_timecapsule.preference_catalog import preference_catalog


class PreferenceCatalogTests(unittest.TestCase):
    def test_only_exact_evidence_backed_keys_are_approved(self):
        catalog = preference_catalog()
        identities = {(entry['section'], entry['key']) for entry in catalog['preferences']}
        self.assertEqual(identities, set(APPROVED_PREFERENCES))
        self.assertEqual(identities, {('reaper', 'tinttcp'), ('reaper', 'peaksedges')})
        self.assertTrue(all(entry['documentation_url'].startswith('https://www.reaper.fm/')
                            and entry['minimum_documented_version'] == '5.0'
                            and entry['status'] == 'approved-subset-manual-review-required'
                            for entry in catalog['preferences']))

    def test_theme_directives_are_not_mistaken_for_reaper_ini_keys(self):
        catalog = preference_catalog()
        candidates = {entry['key']: entry for entry in catalog['not_approved']}
        self.assertEqual(set(candidates), {'tcp_folderindent', 'tcp_heights', 'transport_showborders'})
        self.assertTrue(all(entry['status'] == 'review' for entry in candidates.values()))

    def test_unknown_settings_remain_review_and_active_writes_are_disabled(self):
        catalog = preference_catalog()
        self.assertFalse(catalog['active_writes_supported'])
        self.assertIn('Unknown or unsupported values stay review; no active writes.',
                      catalog['expansion_requirements'])

    def test_catalog_is_read_only_and_cli_exports_same_evidence(self):
        with self.assertRaises(TypeError):
            APPROVED_PREFERENCES[('reaper', 'new-key')] = frozenset({'1'})

        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, '-m', 'reaper_timecapsule', 'config-catalog'],
                                cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        cli_catalog = json.loads(result.stdout)
        cli_identities = {(entry['section'], entry['key'])
                          for entry in cli_catalog['preferences']}
        self.assertEqual(cli_identities, set(APPROVED_PREFERENCES))
