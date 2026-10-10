"""Read-only factory theme comparison. Never changes backup/restore policy."""
import hashlib
import re
import stat
import unicodedata
from pathlib import Path

MAX_FILES = 10000
MAX_FILE_BYTES = 128 * 1024 * 1024


def _inventory(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('Theme input must be an explicit non-symlink directory')
    result = {}
    for path in directory.iterdir():
        if len(result) >= MAX_FILES:
            raise ValueError('Theme directory exceeds entry limit')
        name = path.name
        if any(ord(c) < 32 or c in '\\' for c in name):
            raise ValueError('Unsupported theme filename')
        identity = unicodedata.normalize('NFC', name).casefold()
        if identity in result:
            raise ValueError('Ambiguous cross-platform theme filenames')
        mode = path.lstat().st_mode
        digest = None
        kind = 'unsupported'
        if stat.S_ISREG(mode) and path.suffix.casefold() in {'.reaperthemezip', '.reapertheme'}:
            kind = 'packed' if path.suffix.casefold() == '.reaperthemezip' else 'unpacked_descriptor'
            with path.open('rb') as stream:
                before = path.stat()
                if before.st_size > MAX_FILE_BYTES:
                    raise ValueError('Theme file exceeds size limit')
                digest_object = hashlib.sha256()
                total = 0
                while chunk := stream.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_FILE_BYTES:
                        raise ValueError('Theme file exceeds size limit')
                    digest_object.update(chunk)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns, before.st_ino) != (
                        after.st_size, after.st_mtime_ns, after.st_ino) or total != before.st_size:
                    raise ValueError('Theme input changed while reading')
                digest = digest_object.hexdigest()
        # Directories and symlinks are listed for review, never traversed/read.
        result[identity] = dict(name=name, kind=kind, sha256=digest)
    return result


def preview_themes(source, factory, target, *, source_version=None, factory_version=None):
    """Compare direct children of three explicit ColorThemes directories.

    Factory provenance is caller-supplied. Packed themes are compared as opaque
    bytes; archives are never unpacked. No resources are omitted by this API.
    """
    old, clean, destination = map(_inventory, (source, factory, target))
    compatible = bool(source_version and source_version == factory_version and
                      re.fullmatch(r'(?:[5-9]|[1-9][0-9]+)\.[0-9]+', source_version))
    rows = []
    for identity, item in sorted(old.items()):
        reference = clean.get(identity)
        existing = destination.get(identity)
        comparable = item['sha256'] is not None
        match = bool(comparable and reference and reference['sha256'] == item['sha256'])
        target_state = ('absent' if existing is None else 'identical' if comparable and
                        existing['sha256'] == item['sha256'] else 'conflict')
        if item['kind'] != 'packed':
            status, recommendation = 'review', 'review unpacked dependencies or unsupported entry'
        elif target_state == 'conflict':
            status, recommendation = 'review', 'resolve destination conflict; preserve source'
        elif not compatible:
            status, recommendation = 'review', 'confirm matching factory build; preserve source'
        elif match:
            status, recommendation = 'factory_match', 'reuse factory copy after manual review'
        elif reference is not None:
            status, recommendation = 'modified_factory', 'preserve personalized variant'
        else:
            status, recommendation = 'user_theme', 'preserve user theme'
        rows.append(dict(name=item['name'], kind=item['kind'], sha256=item['sha256'],
                         factory_identical=match, target_state=target_state,
                         status=status, recommendation=recommendation))
    return dict(schema=1, read_only=True, writes_performed=False,
                factory_version_compatible=compatible, provenance='caller-supplied factory directory and versions',
                entries=rows, summary={status: sum(row['status'] == status for row in rows)
                for status in ('factory_match', 'modified_factory', 'user_theme', 'review')})
