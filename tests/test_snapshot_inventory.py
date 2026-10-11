"""Inventory describes archived bytes and refuses linked resource parents."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.core import make_backup, preview, verify_backup
from reaper_timecapsule.inventory import audit_reapack, build_inventory
from reaper_timecapsule.midi_validation import validate_midi_workflow


class SnapshotInventoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.source = self.base / 'source'
        self.source.mkdir()
        self.archive = self.base / 'backup.zip'

    def link(self, path, target, directory=False):
        try:
            path.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink privilege unavailable')

    def test_source_changes_after_copy_do_not_change_inventory(self):
        ini = self.source / 'reapack.ini'
        original = 'repo=https://example.org/archived.xml\n'
        ini.write_text(original)
        kb = self.source / 'reaper-kb.ini'
        action = 'ACT 1 32060 "' + 'a' * 32 + '" "Synthetic" 40001\n'
        kb.write_text(action)
        saved_ini, saved_kb = ini.read_bytes(), kb.read_bytes()
        seen = []
        def changed_source(snapshot, items):
            ini.write_text('repo=https://example.org/later.xml\n')
            kb.write_text('')
            seen.append(Path(snapshot))
            self.assertNotEqual(Path(snapshot), self.source)
            return build_inventory(snapshot, items)
        with patch('reaper_timecapsule.core.build_inventory', side_effect=changed_source):
            make_backup(self.source, self.archive)
        manifest = verify_backup(self.archive)
        self.assertEqual(manifest['inventory_basis'], 'archived-resource-bytes')
        self.assertEqual(manifest['inventory']['reapack']['repository_index_urls'],
                         ['https://example.org/archived.xml'])
        self.assertEqual(manifest['inventory']['midi_workflow']['validation']['action_definitions'], 1)
        with zipfile.ZipFile(self.archive) as z:
            self.assertEqual(z.read('resources/reapack.ini'), saved_ini)
            self.assertEqual(z.read('resources/reaper-kb.ini'), saved_kb)
        self.assertFalse(seen[0].exists())

    def test_inventory_failure_cleans_snapshot_and_unpublished_zip(self):
        (self.source / 'reapack.ini').write_text('synthetic')
        seen = []
        def fail(snapshot, items):
            seen.append(Path(snapshot))
            raise OSError('Synthetic inventory failure')
        with patch('reaper_timecapsule.core.build_inventory', side_effect=fail):
            with self.assertRaises(OSError):
                make_backup(self.source, self.archive)
        self.assertFalse(self.archive.exists())
        self.assertFalse(seen[0].exists())
        self.assertEqual(list(self.base.glob('.timecapsule-*.zip')), [])

    def test_linked_reapack_parent_is_not_opened_by_inventory_or_audit(self):
        external = self.base / 'external'
        external.mkdir()
        (external / 'registry.db').write_bytes(b'external private data')
        self.link(self.source / 'ReaPack', external, True)
        # Scan does not select this file; the registry reader must not be invoked.
        with patch('reaper_timecapsule.inventory.inspect_registry', side_effect=AssertionError('external read')):
            self.assertEqual(preview(self.source)['inventory']['reapack']['registry']['status'], 'missing')
            self.assertEqual(audit_reapack(self.source)['registry']['status'], 'missing')
            forged = [{'path': 'ReaPack/registry.db', 'policy': 'review', 'size': 21}]
            self.assertEqual(build_inventory(self.source, forged)['reapack']['registry']['status'], 'missing')

    def test_unselected_ini_not_read(self):
        (self.source / 'reapack.ini').write_text('repo=https://example.org/private.xml')
        with patch('reaper_timecapsule.inventory.parse_profile', side_effect=AssertionError('unselected read')):
            self.assertEqual(build_inventory(self.source, [])['reapack']['profile']['status'], 'missing')

    def test_midi_reader_refuses_linked_parent_even_with_stale_selected_list(self):
        external = self.base / 'external'
        external.mkdir()
        (external / 'test.ReaperKeyMap').write_text('PRIVATE')
        self.link(self.source / 'KeyMaps', external, True)
        items = [{'path': 'KeyMaps/test.ReaperKeyMap', 'policy': 'keep', 'size': 7}]
        report = validate_midi_workflow(self.source, items)
        self.assertEqual(report['status'], 'needs-review')
        self.assertIn('Linked resource path refused', report['parse_problems'][0]['problem'])
        self.assertNotIn('PRIVATE', str(report))

    def test_unselected_linked_sqlite_sidecar_prevents_registry_open(self):
        (self.source / 'ReaPack').mkdir()
        (self.source / 'ReaPack/registry.db').write_bytes(b'synthetic')
        outside = self.base / 'private-wal'
        outside.write_bytes(b'PRIVATE')
        self.link(self.source / 'ReaPack/registry.db-wal', outside)
        items = [{'path': 'ReaPack/registry.db', 'policy': 'review', 'size': 9}]
        with patch('reaper_timecapsule.inventory.inspect_registry', side_effect=AssertionError('unsafe WAL read')):
            self.assertEqual(build_inventory(self.source, items)['reapack']['registry']['status'], 'missing')
            make_backup(self.source, self.archive)
        self.assertEqual(verify_backup(self.archive)['inventory']['reapack']['registry']['status'], 'missing')

    def test_parser_limit_does_not_drop_archived_resource(self):
        (self.source / 'reapack.ini').write_bytes(b'X' * (2 * 1024 * 1024 + 1))
        make_backup(self.source, self.archive)
        manifest = verify_backup(self.archive)
        self.assertEqual(manifest['files'][0]['path'], 'reapack.ini')
        self.assertEqual(manifest['inventory']['inspection_omissions'],
                         [{'path': 'reapack.ini', 'reason': 'Parser size limit exceeded'}])

    def test_registry_mutation_after_copy_keeps_archived_package_count(self):
        import sqlite3
        from contextlib import closing
        (self.source / 'ReaPack').mkdir()
        database = self.source / 'ReaPack/registry.db'
        with closing(sqlite3.connect(database)) as db:
            db.execute('CREATE TABLE entries (id INTEGER, remote TEXT, category TEXT, package TEXT, version TEXT, flags INTEGER)')
            db.execute('CREATE TABLE files (entry INTEGER, path TEXT)')
            db.execute("INSERT INTO entries VALUES (1, 'Synthetic', 'MIDI', 'Original', '1.0', 0)")
            db.commit()
        def mutate(snapshot, items):
            with closing(sqlite3.connect(database)) as db:
                db.execute('DELETE FROM entries')
                db.commit()
            return build_inventory(snapshot, items)
        with patch('reaper_timecapsule.core.build_inventory', side_effect=mutate):
            make_backup(self.source, self.archive)
        registry = verify_backup(self.archive)['inventory']['reapack']['registry']
        self.assertEqual(registry['installed_count'], 1)
        self.assertEqual(registry['installed_packages'][0]['name'], 'Original')
