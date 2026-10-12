"""Read-only, fail-closed reaper.ini comparison. No writer or merge API."""
import re
import hashlib
from pathlib import Path
from .preference_catalog import APPROVED_PREFERENCES, preference_catalog

MAX_BYTES = 4 * 1024 * 1024
BLOCKED = re.compile(
    r'audio|asio|wasapi|coreaudio|midi|device|driver|vst|aucache|clap|plugin|'
    r'cache|path|directory|dir$|recent|license|register|password|token|secret|'
    r'credential|serial|keyfile|window|wnd|screen|monitor|dpi|cpu|thread|'
    r'linux|win32|win64|macos|osx|hardware', re.I)


def _read(path, *, with_digest=False, with_provenance=False):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Configuration must be a regular non-symlink file')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Configuration exceeds size limit')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeError:
        raise ValueError('Configuration must be UTF-8; convert a private copy first') from None
    if any(ord(char) < 32 and char not in '\r\n\t' for char in text):
        raise ValueError('Configuration contains unsupported control characters')
    section = None
    sections = set()
    entries = {}
    for number, line in enumerate(text.splitlines(), 1):
        original = line
        line = line.strip()
        if not line or line.startswith((';', '#')):
            continue
        if original[:1].isspace():
            raise ValueError(f'Indented or continued entry at line {number}')
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1].strip().casefold()
            if (not section or section == 'default' or section in sections
                    or any(char in section for char in '[]=\t')):
                raise ValueError(f'Ambiguous section at line {number}')
            sections.add(section)
        elif line.startswith('['):
            raise ValueError(f'Malformed section at line {number}')
        elif section is not None and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip().casefold()
            identity = (section, key)
            if not key or identity in entries or any(char in key for char in '[]\t'):
                raise ValueError(f'Ambiguous key at line {number}')
            entries[identity] = value.strip()
        else:
            # Never include raw content in an exception (could contain credentials).
            raise ValueError(f'Malformed configuration at line {number}')
    if not sections:
        raise ValueError('Configuration has no sections')
    if with_provenance:
        return entries, {
            'encoding': 'utf-8', 'utf8_bom': raw.startswith(b'\xef\xbb\xbf'),
            'decoding': 'strict', 'fallback_used': False, 'bytes_read': len(raw),
            'basis': 'validated input bytes; not original encoding detection',
        }
    return (entries, hashlib.sha256(raw).hexdigest()) if with_digest else entries


def preview_migration(source, target, *, source_version=None, target_version=None):
    """Compare explicit files without writes; unknown values are never disclosed.

    Versions are caller-supplied provenance, not inferred from arbitrary INI keys.
    Only identical REAPER 5+ versions permit approved candidates. A candidate is
    still a proposal requiring review, never permission to overwrite a target.
    """
    old, source_provenance = _read(source, with_provenance=True)
    new, target_provenance = _read(target, with_provenance=True)
    report = _compare_entries(old, new, source_version, target_version)
    report['input_provenance'] = {'source': source_provenance, 'target': target_provenance}
    return report


def _compare_entries(old, new, source_version, target_version):
    known_version = bool(source_version and target_version and
                         re.fullmatch(r'(?:[5-9]|[1-9][0-9]+)\.[0-9]+', source_version) and
                         source_version == target_version)
    rows = []
    for section, key in sorted(old.keys() | new.keys()):
        identity = section, key
        before, after = old.get(identity), new.get(identity)
        change = ('same' if before == after else 'source_only' if after is None
                  else 'target_only' if before is None else 'conflict')
        allowed = APPROVED_PREFERENCES.get(identity)
        if section in {'au', 'reaper-au', 'reaper-vstplugins', 'reaper-clap'} or BLOCKED.search(section + '/' + key):
            status, reason = 'exclude', 'machine/platform/cache/path/private state'
        elif allowed is None:
            status, reason = 'review', 'not explicitly approved'
        elif before not in allowed or after not in allowed:
            status, reason = 'review', 'missing or unsupported preference value'
        elif not known_version:
            status, reason = 'review', 'unknown or different REAPER version'
        else:
            status, reason = 'candidate', 'approved appearance preference; manual review required'
        row = dict(section=section, key=key, change=change, status=status, reason=reason)
        # Reveal only validated preference literals; no arbitrary values or paths.
        if allowed is not None and before in allowed and after in allowed:
            row.update(source_value=before, target_value=after)
        rows.append(row)
    return dict(schema=1, read_only=True, writes_performed=False,
                preference_catalog=preference_catalog(),
                version_compatible=known_version, entries=rows,
                changes={change: sum(r['change'] == change for r in rows)
                         for change in ('same', 'conflict', 'source_only', 'target_only')},
                summary={status: sum(r['status'] == status for r in rows)
                         for status in ('candidate', 'review', 'exclude')})
