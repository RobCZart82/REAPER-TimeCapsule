"""Read-only recovery planning from a fully verified capsule, no installers."""
from .core import verify_backup, VERSION
from .operation import checkpoint


def _object(value):
    if not isinstance(value, dict):
        raise ValueError('Invalid recovery inventory object')
    return value


def _records(value, limit):
    if not isinstance(value, list) or len(value) > limit or any(not isinstance(x, dict) for x in value):
        raise ValueError('Invalid recovery inventory records')
    return value


def plan_recovery(archive, *, control=None):
    manifest = verify_backup(archive, control=control)
    checkpoint(control, 'Planning isolated recovery')
    inventory = _object(manifest.get('inventory', {}))
    midi = _object(_object(inventory.get('midi_workflow', {})).get('validation', {}))
    reapack = _object(inventory.get('reapack', {}))
    profile, registry = _object(reapack.get('profile', {})), _object(reapack.get('registry', {}))
    reliable = manifest.get('inventory_basis') == 'archived-resource-bytes'
    repositories = []
    for remote in _records(profile.get('repositories', []), 2000):
        checkpoint(control, 'Planning ReaPack repositories')
        repositories.append({key: remote.get(key) for key in
                             ('name', 'index_url', 'enabled', 'auto_install_override')})
    packages = []
    for package in _records(registry.get('installed_packages', []), 10000):
        checkpoint(control, 'Planning ReaPack packages')
        packages.append({**{key: package.get(key) for key in ('repository', 'category', 'name', 'version', 'pinned', 'prerelease_override', 'owned_files')}, 'action': 'review-in-isolated-ReaPack',
                         'version_availability_verified': False, 'download_performed': False})
    blockers = []
    if not reliable:
        blockers.append('Legacy inventory was not derived from archived resource bytes; re-audit staged resources.')
    if midi.get('status') != 'ok':
        blockers.append('MIDI dependencies require review/runtime registration checks.')
    if profile.get('status') != 'parsed':
        blockers.append('Repository configuration is missing or unsupported.')
    if registry.get('status') != 'parsed' or registry.get('truncated'):
        blockers.append('Package inventory is missing, unsupported or incomplete.')
    return {'report_format': 'timecapsule-recovery-plan', 'report_schema': 1,
            'app_version': VERSION, 'capsule_created_utc': manifest.get('created_utc'),
            'source_platform': manifest.get('source_platform'),
            'inventory_basis': manifest.get('inventory_basis', 'legacy-unverified'),
            'archive_checksums_verified': True, 'publisher_authenticated': False,
            'automatic_install_supported': False, 'resource_writes_performed': False,
            'blockers': blockers,
            'midi': {'audit': midi, 'runtime_validation_performed': False,
                     'tasks': ['Recover only into a NEW external staging directory.',
                               'Review duplicate IDs, cycles, missing scripts and absolute-path registrations.',
                               'Re-register reviewed scripts in a separate disposable REAPER installation.',
                               'Verify numeric/extension commands and menu actions in the actual MIDI editor.']},
            'reapack': {'profile_status': profile.get('status', 'unknown'),
                        'registry_status': registry.get('status', 'unknown'),
                        'repositories_in_saved_order': repositories,
                        'global_options_for_review': profile.get('options', {}),
                        'packages_for_review': packages,
                        'tasks': ['Install the correct platform ReaPack extension independently.',
                                  'Review repository URLs and enabled/disabled states before network access.',
                                  'Check package/version availability; preserve pins only after review.',
                                  'Use a new registry; never activate the archived registry/cache blindly.']},
            'integration_gate': {'disposable_installation_required': True,
                                 'live_resource_folder_permitted': False,
                                 'runtime_test_performed': False},
            'privacy': 'Keep this local plan private: it contains repository and package metadata.'}
