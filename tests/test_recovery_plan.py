import json
import sqlite3
import tempfile
import unittest
import zipfile
from contextlib import closing
from pathlib import Path

from reaper_timecapsule.core import make_backup
from reaper_timecapsule.recovery_plan import plan_recovery
from reaper_timecapsule.operation import OperationControl, OperationCancelled


class RecoveryPlanTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'reapack.ini').write_text('[general]\nversion=4\n[remotes]\nsize=2\nremote0=Enabled|https://example.org/on.xml|1|2\nremote1=Disabled|https://example.org/off.xml|0|2\n')
        (self.source / 'ReaPack').mkdir()
        with closing(sqlite3.connect(self.source / 'ReaPack/registry.db')) as db:
            db.execute('CREATE TABLE entries(id INTEGER, remote TEXT, category TEXT, package TEXT, version TEXT, flags INTEGER)')
            db.execute('CREATE TABLE files(entry INTEGER, path TEXT)')
            db.execute('INSERT INTO entries VALUES (1, "Enabled", "MIDI", "Synthetic", "1.2", 1)')
            db.commit()
        self.archive = self.root / 'capsule.zip'
        make_backup(self.source, self.archive)

    def rewrite(self, mutate):
        with zipfile.ZipFile(self.archive) as z:
            contents = {name: z.read(name) for name in z.namelist()}
        manifest = json.loads(contents['manifest.json'])
        mutate(manifest)
        contents['manifest.json'] = json.dumps(manifest).encode()
        with zipfile.ZipFile(self.archive, 'w') as z:
            for name, value in contents.items():
                z.writestr(name, value)

    def test_plan_preserves_repo_order_state_and_package_pin_without_writes(self):
        archive_bytes = self.archive.read_bytes()
        report = plan_recovery(self.archive)
        remotes = report['reapack']['repositories_in_saved_order']
        self.assertEqual([x['name'] for x in remotes], ['Enabled', 'Disabled'])
        self.assertEqual([x['enabled'] for x in remotes], [True, False])
        package = report['reapack']['packages_for_review'][0]
        self.assertTrue(package['pinned'])
        self.assertEqual(package['version'], '1.2')
        self.assertFalse(package['version_availability_verified'])
        self.assertFalse(report['automatic_install_supported'])
        self.assertFalse(report['resource_writes_performed'])
        self.assertFalse(report['integration_gate']['runtime_test_performed'])
        self.assertEqual(self.archive.read_bytes(), archive_bytes)
        self.assertEqual(sorted(x.name for x in self.root.iterdir()), ['capsule.zip', 'source'])

    def test_legacy_inventory_and_missing_runtime_validation_block_automation(self):
        self.rewrite(lambda m: m.pop('inventory_basis'))
        report = plan_recovery(self.archive)
        self.assertTrue(any('Legacy inventory' in x for x in report['blockers']))
        self.assertFalse(report['midi']['runtime_validation_performed'])
        self.assertFalse(report['publisher_authenticated'])

    def test_malformed_inventory_is_normalized_and_no_plan_claimed(self):
        self.rewrite(lambda m: m.update(inventory={'reapack': []}))
        with self.assertRaises(ValueError):
            plan_recovery(self.archive)

    def test_corrupt_capsule_cannot_produce_a_plan(self):
        self.rewrite(lambda m: m['files'][0].update(sha256='0' * 64))
        with self.assertRaises(ValueError):
            plan_recovery(self.archive)

    def test_cancelled_verification_produces_no_plan(self):
        control = OperationControl()
        control.cancel()
        with self.assertRaises(OperationCancelled):
            plan_recovery(self.archive, control=control)
