import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from reaper_timecapsule.config_staging import export_preferences, verify_staging


class ConfigurationStagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        inputs = self.root / 'inputs'
        inputs.mkdir()
        self.source, self.target = inputs / 'old.ini', inputs / 'target.ini'
        self.source.write_text('[REAPER]\ntinttcp=0\npeaksedges=1\npassword=PRIVATE_SECRET\nunknown=PRIVATE_VALUE\n')
        self.target.write_text('[REAPER]\ntinttcp=1\npeaksedges=0\npassword=TARGET_SECRET\n')
        staging = self.root / 'TimeCapsule-Staging'
        staging.mkdir()
        self.archive = staging / 'review.timecapsule-stage.zip'

    def export(self, **kwargs):
        options = dict(selections=['REAPER/tinttcp'], source_version='7.82', target_version='7.82', opt_in=True)
        options.update(kwargs)
        return export_preferences(self.source, self.target, self.archive, **options)

    def rewrite(self, mutate):
        with zipfile.ZipFile(self.archive) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        mutate(files)
        with zipfile.ZipFile(self.archive, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data)

    def test_selected_patch_rollback_and_baseline_without_input_writes(self):
        before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in (self.source, self.target)]
        self.assertEqual(self.export()['staged_preferences'], 1)
        self.assertTrue(verify_staging(self.archive, target=self.target)['target_baseline_matches'])
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual(set(archive.namelist()), {'manifest.json', 'preferences.json', 'rollback-preferences.json'})
            text = '\n'.join(archive.read(name).decode() for name in archive.namelist())
            self.assertNotIn('SECRET', text)
            self.assertNotIn('PRIVATE_VALUE', text)
            self.assertNotIn('peaksedges', text)
            self.assertEqual(json.loads(archive.read('rollback-preferences.json'))['preferences'][0]['value'], '1')
        self.assertEqual(before, [(p.read_bytes(), p.stat().st_mtime_ns) for p in (self.source, self.target)])

    def test_opt_in_is_required_and_no_file_created(self):
        with self.assertRaises(ValueError):
            self.export(opt_in=False)
        self.assertFalse(self.archive.exists())

    def test_invalid_unknown_duplicate_unchanged_and_version_selections(self):
        for selected in ([], ['REAPER/password'], ['REAPER/unknown'], ['REAPER/missing'],
                         ['REAPER/tinttcp', 'reaper/tinttcp'], ['tinttcp']):
            with self.subTest(selected=selected):
                with self.assertRaises(ValueError):
                    self.export(selections=selected)
                self.assertFalse(self.archive.exists())
        self.target.write_text('[REAPER]\ntinttcp=0\n')
        with self.assertRaises(ValueError):
            self.export()
        self.target.write_text('[REAPER]\ntinttcp=1\n')
        with self.assertRaises(ValueError):
            self.export(target_version='7.81')

    def test_no_overwrite_existing_file(self):
        self.archive.write_bytes(b'keep me')
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(self.archive.read_bytes(), b'keep me')

    def test_input_resource_and_install_directories_rejected(self):
        for folder in (self.source.parent, self.root / 'REAPER', self.root / 'portable'):
            folder.mkdir(exist_ok=True)
            if folder.name == 'portable':
                (folder / 'reaper.ini').write_text('[REAPER]\n')
            nested = folder / 'TimeCapsule-Staging'
            nested.mkdir(exist_ok=True)
            with self.subTest(folder=folder):
                with self.assertRaises(ValueError):
                    export_preferences(self.source, self.target, nested / self.archive.name,
                                       selections=['reaper/tinttcp'], opt_in=True,
                                       source_version='7.82', target_version='7.82')
        with patch('reaper_timecapsule.config_staging.default_resource', return_value=self.root):
            with self.assertRaises(ValueError):
                self.export()

    def test_symlink_parent_or_existing_output_rejected(self):
        link = self.root / 'link'
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink privilege unavailable')
        with self.assertRaises(ValueError):
            export_preferences(self.source, self.target, link / self.archive.name,
                               selections=['reaper/tinttcp'], opt_in=True)
        self.archive.symlink_to(self.root / 'missing')
        with self.assertRaises(ValueError):
            self.export()
        self.assertTrue(self.archive.is_symlink())

    def test_target_changes_detected(self):
        self.export()
        self.target.write_text('[REAPER]\ntinttcp=0\n')
        with self.assertRaises(ValueError):
            verify_staging(self.archive, target=self.target)

    def test_corruption_and_unexpected_member_rejected(self):
        self.export()
        self.rewrite(lambda files: files.update({'preferences.json': b'corrupt'}))
        with self.assertRaises(ValueError):
            verify_staging(self.archive)
        self.archive.unlink()
        self.export()
        self.rewrite(lambda files: files.update({'../reaper.ini': b'PRIVATE'}))
        with self.assertRaises(ValueError):
            verify_staging(self.archive)
        self.assertFalse((self.root / 'reaper.ini').exists())

    def test_forged_unknown_key_rejected_even_with_recomputed_checksums(self):
        self.export()
        def forge(files):
            import hashlib
            manifest = json.loads(files['manifest.json'])
            manifest['selections'][0]['key'] = 'password'
            files['preferences.json'] = b'{}'
            manifest['files']['preferences.json'] = hashlib.sha256(b'{}').hexdigest()
            files['manifest.json'] = json.dumps(manifest).encode()
        self.rewrite(forge)
        with self.assertRaises(ValueError):
            verify_staging(self.archive)

    def test_duplicate_members_and_size_limits_rejected(self):
        self.export()
        with zipfile.ZipFile(self.archive, 'a') as archive:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                archive.writestr('manifest.json', b'{}')
        with self.assertRaises(ValueError):
            verify_staging(self.archive)
        with patch('reaper_timecapsule.config_staging.MAX_ARCHIVE_BYTES', 1):
            with self.assertRaises(ValueError):
                verify_staging(self.archive)

    def test_partial_write_failure_cleans_up_owned_archive(self):
        original_open = Path.open
        archive_path = self.archive
        class BrokenWriter:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def fileno(self):
                return self.stream.fileno()
            def write(self, content):
                self.stream.write(content[:8])
                raise OSError('simulated full disk')
        def open_file(path, mode='r', *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            return BrokenWriter(stream) if path == archive_path and mode == 'xb' else stream
        with patch.object(Path, 'open', open_file):
            with self.assertRaises(OSError):
                self.export()
        self.assertFalse(self.archive.exists())

    def test_duplicate_manifest_fields_rejected(self):
        self.export()
        def duplicate(files):
            files['manifest.json'] = files['manifest.json'].replace(b'{', b'{"schema":1,', 1)
        self.rewrite(duplicate)
        with self.assertRaises(ValueError):
            verify_staging(self.archive)

    def test_dedicated_staging_parent_required(self):
        with self.assertRaises(ValueError):
            export_preferences(self.source, self.target, self.root / self.archive.name,
                               selections=['reaper/tinttcp'], opt_in=True,
                               source_version='7.82', target_version='7.82')

    def test_two_explicit_preferences_and_cli(self):
        command = [sys.executable, '-m', 'reaper_timecapsule', 'config-stage', str(self.source),
                   str(self.target), str(self.archive), '--source-version', '7.82', '--target-version',
                   '7.82', '--select', 'REAPER/tinttcp', '--select', 'REAPER/peaksedges']
        denied = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(denied.returncode, 0)
        self.assertFalse(self.archive.exists())
        result = subprocess.run(command + ['--opt-in'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        verified = subprocess.run([sys.executable, '-m', 'reaper_timecapsule', 'verify-stage',
                                   str(self.archive), '--target', str(self.target)], capture_output=True, text=True)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)['staged_preferences'], 2)
