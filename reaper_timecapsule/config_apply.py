"""Opt-in, offline preference apply with a complete target-file recovery bundle.

REAPER must be closed. Stable, local directories are required: the final hash
check is not a filesystem compare-and-swap against unrelated concurrent writers.
"""
import json
import os
import re
import stat
import tempfile
from pathlib import Path

from .config_migration import MAX_BYTES, _read
from .config_staging import _destination, _digest, _json, _load_staging, _unique_object


def _regular(path):
    path = Path(os.path.abspath(path))
    for component in (path, *path.parents):
        value = component.lstat()
        if stat.S_ISLNK(value.st_mode) or (getattr(value, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)):
            raise ValueError('Linked configuration/recovery paths are forbidden')
    value = path.stat()
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise ValueError('Expected an unlinked regular file')
    return path


def _bytes(path):
    path = _regular(path)
    with path.open('rb') as stream:
        value = stream.read(MAX_BYTES + 1)
    if len(value) > MAX_BYTES:
        raise ValueError('Configuration exceeds size limit')
    return value


def _sync_directory(path):
    if os.name != 'nt':
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _render(raw, selections):
    """Replace approved literals only; keep BOM, comments and newline bytes."""
    edits = {(row['section'], row['key']): row for row in selections}
    section, found, output = '', set(), []
    for line in raw.decode('utf-8').splitlines(keepends=True):
        content = line.lstrip('\ufeff').strip()
        if content.startswith('[') and content.endswith(']'):
            section = content[1:-1].strip().casefold()
        elif '=' in content and not content.startswith((';', '#')):
            key = content.split('=', 1)[0].strip().casefold()
            identity = section, key
            if identity in edits:
                row = edits[identity]
                if content.split('=', 1)[1].strip() != row['target_value']:
                    raise ValueError('Selected target preference conflicts with staged baseline')
                match = re.fullmatch(r'([^=]+=\s*)[^\r\n]*?([ \t]*)(\r\n|\n|\r)?', line)
                if not match:
                    raise ValueError('Cannot preserve target preference formatting')
                line = match[1] + row['source_value'] + match[2] + (match[3] or '')
                found.add(identity)
        output.append(line)
    if found != set(edits):
        raise ValueError('Selected preference is missing from target')
    return ''.join(output).encode('utf-8')


def _replace(target, expected, replacement):
    """All fallible preparation precedes replacement; backup exists beforehand."""
    target = _regular(target)
    mode = stat.S_IMODE(target.stat().st_mode)
    lock = target.with_name(target.name + '.timecapsule-lock')
    # Cooperative exclusion. A crash leaves this marker for manual review.
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    temp = None
    try:
        fd, name = tempfile.mkstemp(prefix='.timecapsule-config-', dir=target.parent)
        temp = Path(name)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(replacement)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, mode)
        if _bytes(target) != expected:
            raise ValueError('Target changed; refusing to overwrite concurrent edits')
        os.replace(temp, target)
        temp = None
    finally:
        # Cleanup failure must not turn a completed replacement into a reported
        # apply failure. A leftover lock is safe and requires manual inspection.
        for leftover in (temp, lock):
            if leftover is not None:
                try:
                    leftover.unlink(missing_ok=True)
                except OSError:
                    pass


def _consent(opt_in, reaper_closed):
    if opt_in is not True or reaper_closed is not True:
        raise ValueError('Explicit opt-in and confirmation that REAPER is closed are required')


def apply_preferences(archive, target, recovery, *, opt_in=False, reaper_closed=False):
    _consent(opt_in, reaper_closed)
    target = _regular(target)
    manifest = _load_staging(archive)
    _, baseline = _read(target, with_digest=True)
    original = _bytes(target)
    if baseline != manifest['target_sha256'] or _digest(original) != baseline:
        raise ValueError('Target configuration differs from staged baseline')
    updated = _render(original, manifest['selections'])
    recovery = Path(os.path.abspath(recovery))
    # Reuse external staging guards; a recovery bundle is a directory, not a ZIP.
    _destination(recovery.parent / (recovery.name + '.timecapsule-stage.zip'), target, target)
    recovery.mkdir(mode=0o700)  # exclusive; never replace an existing bundle
    # Interrupted preparation intentionally leaves evidence, never touches target.
    _write_new(recovery / 'original.ini', original)
    _write_new(recovery / 'applied.ini', updated)
    record = dict(schema=1, kind='timecapsule-config-recovery',
                  original_sha256=_digest(original), applied_sha256=_digest(updated))
    _write_new(recovery / 'manifest.json', _json(record))
    _sync_directory(recovery)
    _sync_directory(recovery.parent)
    before, after = _load_recovery(recovery)
    if before != original or after != updated:
        raise ValueError('Recovery readback failed')
    _replace(target, original, updated)
    return dict(applied=True, preferences=len(manifest['selections']),
                recovery_created=True, reaper_runtime_validated=False)


def _load_recovery(recovery):
    recovery = Path(recovery)
    raw = _bytes(recovery / 'manifest.json')
    if len(raw) > 4096:
        raise ValueError('Recovery manifest exceeds size limit')
    try:
        manifest = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError('Invalid recovery manifest') from None
    if (not isinstance(manifest, dict) or set(manifest) != {
            'schema', 'kind', 'original_sha256', 'applied_sha256'}
            or manifest['schema'] != 1 or manifest['kind'] != 'timecapsule-config-recovery'):
        raise ValueError('Invalid recovery manifest')
    original, applied = (_bytes(recovery / name) for name in ('original.ini', 'applied.ini'))
    if (_digest(original) != manifest['original_sha256']
            or _digest(applied) != manifest['applied_sha256']):
        raise ValueError('Recovery checksum mismatch')
    return original, applied


def rollback_preferences(recovery, target, *, opt_in=False, reaper_closed=False):
    _consent(opt_in, reaper_closed)
    original, applied = _load_recovery(recovery)
    target = _regular(target)
    current = _bytes(target)
    if current == original:
        return dict(restored=True, already_original=True)
    if current != applied:
        raise ValueError('Target changed since apply; preserve edits and recover manually')
    _replace(target, applied, original)
    return dict(restored=True, already_original=False)
