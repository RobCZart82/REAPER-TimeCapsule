"""Explicit opt-in preference data export; no active configuration writer."""
import io
import os
import json
import hashlib
import re
import zipfile
import zlib
from pathlib import Path

from .config_migration import APPROVED_PREFERENCES, _read, _compare_entries
from .core import default_resource

MAX_ARCHIVE_BYTES = 128 * 1024
MEMBERS = {'manifest.json', 'preferences.json', 'rollback-preferences.json'}


def _json(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _payload(selections, reverse=False):
    return _json({'schema': 1, 'apply_supported': False, 'preferences': [
        {'section': row['section'], 'key': row['key'],
         'value': row['target_value'] if reverse else row['source_value']}
        for row in selections]})


def _destination(path, source, target):
    path = Path(path).absolute()
    if not path.name.endswith('.timecapsule-stage.zip'):
        raise ValueError('Use a .timecapsule-stage.zip filename')
    if path.exists() or path.is_symlink():
        raise ValueError('Staging archive already exists; never overwrite')
    if not path.parent.is_dir():
        raise ValueError('Staging parent must already exist')
    # Reject symlink ancestors rather than resolving writes through them.
    if any(parent.is_symlink() for parent in path.parents):
        raise ValueError('Staging parent cannot contain symlinks')
    parent = path.parent.resolve()
    if parent.name != 'TimeCapsule-Staging':
        raise ValueError('Use a dedicated TimeCapsule-Staging parent directory')
    forbidden = [Path(source).resolve().parent, Path(target).resolve().parent,
                 default_resource().resolve()]
    if any(parent == root or root in parent.parents for root in forbidden):
        raise ValueError('Staging must be outside configuration/resource directories')
    for ancestor in (parent, *parent.parents):
        if ancestor.name.casefold() == 'reaper':
            raise ValueError('Staging cannot be inside a REAPER directory')
        if ancestor.is_dir():
            names = {item.name.casefold() for item in ancestor.iterdir()}
            if names & {'reaper.ini', 'reaper.exe', 'reaper.app', 'reaper-kb.ini'}:
                raise ValueError('Recognized REAPER resource/install directory is forbidden')
    return path


def export_preferences(source, target, archive, *, selections, source_version=None,
                       target_version=None, opt_in=False):
    """Export selected changed candidates only, never a complete configuration."""
    if opt_in is not True:
        raise ValueError('Explicit opt-in is required for staging export')
    destination = _destination(archive, source, target)
    old, source_digest = _read(source, with_digest=True)
    new, target_digest = _read(target, with_digest=True)
    preview = _compare_entries(old, new, source_version, target_version)
    available = {(row['section'], row['key']): row for row in preview['entries']}
    chosen = []
    seen = set()
    for choice in selections:
        parts = choice.casefold().split('/')
        if len(parts) != 2:
            raise ValueError('Select an exact section/key identity')
        identity = tuple(parts)
        row = available.get(identity)
        if identity in seen or not row or row['status'] != 'candidate' or row['change'] != 'conflict':
            raise ValueError('Selection must be a unique changed approved candidate')
        seen.add(identity)
        chosen.append({key: row[key] for key in ('section', 'key', 'source_value', 'target_value')})
    if not chosen:
        raise ValueError('Select at least one changed approved preference')
    chosen.sort(key=lambda row: (row['section'], row['key']))
    files = {'preferences.json': _payload(chosen), 'rollback-preferences.json': _payload(chosen, True)}
    manifest = dict(schema=1, kind='timecapsule-preference-staging', apply_supported=False,
                    source_sha256=source_digest, target_sha256=target_digest,
                    source_version=source_version, target_version=target_version,
                    selections=chosen, files={name: _digest(data) for name, data in files.items()})
    files['manifest.json'] = _json(manifest)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive_file:
        for name, content in files.items():
            archive_file.writestr(name, content)
    # All validation/serialization occurs before the exclusive output creation.
    # No directory creation, resource-file writes, network, extraction or apply.
    _destination(destination, source, target)
    owned = None
    try:
        with destination.open('xb') as stream:
            metadata = os.fstat(stream.fileno())
            owned = metadata.st_dev, metadata.st_ino
            stream.write(buffer.getvalue())
    except BaseException:
        if owned is not None:
            try:
                metadata = destination.lstat()
                if (metadata.st_dev, metadata.st_ino) == owned:
                    destination.unlink()
            except OSError:
                pass
        raise
    return dict(schema=1, staged_preferences=len(chosen), apply_supported=False,
                input_writes_performed=False)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate staging JSON field')
        result[key] = value
    return result


def verify_staging(archive, *, target=None):
    """Read-only integrity and allowlist checks; never extracts or applies data."""
    path = Path(archive)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Staging input must be a regular non-symlink file')
    with path.open('rb') as stream:
        raw = stream.read(MAX_ARCHIVE_BYTES + 1)
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError('Staging archive exceeds size limit')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as staged:
            info = staged.infolist()
            if len(info) != len(MEMBERS) or {item.filename for item in info} != MEMBERS:
                raise ValueError('Unexpected or duplicate staging members')
            if any(item.file_size > MAX_ARCHIVE_BYTES or item.flag_bits & 1 for item in info):
                raise ValueError('Oversized or encrypted staging member')
            files = {item.filename: staged.read(item) for item in info}
        manifest = json.loads(files['manifest.json'], object_pairs_hook=_unique_object)
        required = {'schema', 'kind', 'apply_supported', 'source_sha256', 'target_sha256',
                    'source_version', 'target_version', 'selections', 'files'}
        if not isinstance(manifest, dict) or set(manifest) != required:
            raise ValueError('Invalid staging manifest')
        if (manifest['schema'] != 1 or manifest['kind'] != 'timecapsule-preference-staging'
                or manifest['apply_supported'] is not False):
            raise ValueError('Unsupported staging manifest')
        for name in ('source_sha256', 'target_sha256'):
            if not isinstance(manifest[name], str) or not re.fullmatch('[0-9a-f]{64}', manifest[name]):
                raise ValueError('Invalid input fingerprint')
        version = manifest['source_version']
        if (not isinstance(version, str) or version != manifest['target_version'] or
                not re.fullmatch(r'(?:[5-9]|[1-9][0-9]+)\.[0-9]+', version)):
            raise ValueError('Incompatible staging versions')
        selections = manifest['selections']
        if not isinstance(selections, list) or not 1 <= len(selections) <= len(APPROVED_PREFERENCES):
            raise ValueError('Invalid staging selection count')
        seen = set()
        for row in selections:
            if not isinstance(row, dict) or set(row) != {'section', 'key', 'source_value', 'target_value'}:
                raise ValueError('Invalid staging preference')
            if not all(isinstance(value, str) for value in row.values()):
                raise ValueError('Invalid staging preference type')
            identity = row['section'], row['key']
            allowed = APPROVED_PREFERENCES.get(identity)
            if (identity in seen or allowed is None or row['source_value'] not in allowed or
                    row['target_value'] not in allowed or row['source_value'] == row['target_value']):
                raise ValueError('Staging preference violates approval policy')
            seen.add(identity)
        expected = {'preferences.json': _payload(selections),
                    'rollback-preferences.json': _payload(selections, True)}
        if manifest['files'] != {name: _digest(data) for name, data in expected.items()}:
            raise ValueError('Staging checksum mismatch')
        if any(files[name] != data for name, data in expected.items()):
            raise ValueError('Staging content does not match approved selections')
    except (zipfile.BadZipFile, UnicodeError, json.JSONDecodeError, TypeError, KeyError, RuntimeError, NotImplementedError, EOFError, zlib.error):
        raise ValueError('Invalid staging archive') from None
    matches = None
    if target is not None:
        _, digest = _read(target, with_digest=True)
        matches = digest == manifest['target_sha256']
        if not matches:
            raise ValueError('Target configuration differs from staged baseline')
    return dict(schema=1, valid=True, apply_supported=False, staged_preferences=len(selections),
                target_baseline_matches=matches)
