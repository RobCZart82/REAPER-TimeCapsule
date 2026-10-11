"""Bounded ZIP preflight and conservative space estimates, without deletions."""
import os
import shutil
import stat
import struct
from pathlib import Path

MAX_CENTRAL_DIRECTORY = 64 * 1024 * 1024
SPACE_MARGIN = 16 * 1024 * 1024


def require_space(directory, required):
    if shutil.disk_usage(directory).free < required + SPACE_MARGIN:
        raise OSError('Insufficient free space for safe staging (conservative estimate)')


def preflight_zip(path, max_members):
    """Read only ZIP footers before ZipFile allocates its central-directory index.

    Single-volume, non-prefixed ZIP/ZIP64 only; trailing data is refused. Both
    advertised member count and directory bytes are independently bounded.
    """
    path = Path(path)
    with path.open('rb') as stream:
        size = os.fstat(stream.fileno()).st_size
        stream.seek(max(0, size - 65557))
        tail = stream.read(65557)
        offset = tail.rfind(b'PK\x05\x06')
        if offset < 0 or offset + 22 > len(tail):
            raise ValueError('Invalid ZIP footer')
        _, disk, directory_disk, disk_count, count, directory_size, start, comment = struct.unpack(
            '<4s4H2LH', tail[offset:offset + 22])
        if offset + 22 + comment != len(tail) or disk or directory_disk or disk_count != count:
            raise ValueError('Unsupported ZIP volume or trailing data')
        footer = size - len(tail) + offset
        if count == 65535 or directory_size == 0xffffffff or start == 0xffffffff:
            if footer < 20:
                raise ValueError('Missing ZIP64 locator')
            stream.seek(footer - 20)
            signature, zip_disk, zip_offset, disks = struct.unpack('<4sLQL', stream.read(20))
            if signature != b'PK\x06\x07' or zip_disk or disks != 1:
                raise ValueError('Unsupported ZIP64 volume')
            if zip_offset + 56 > footer - 20:
                raise ValueError('Invalid ZIP64 footer position')
            stream.seek(zip_offset)
            record = stream.read(56)
            signature, length, made, needed, disk, directory_disk, disk_count, count, directory_size, start = struct.unpack('<4sQ2H2L4Q', record)
            if (signature != b'PK\x06\x06' or length < 44 or length > 4096
                    or zip_offset + 12 + length != footer - 20 or disk or directory_disk
                    or disk_count != count):
                raise ValueError('Invalid ZIP64 footer')
            footer = zip_offset
        if count > max_members or directory_size > MAX_CENTRAL_DIRECTORY:
            raise ValueError('ZIP central-directory inspection budget exceeded')
        if start + directory_size != footer:
            raise ValueError('Unsupported ZIP directory position')
        return {'members': count, 'directory_bytes': directory_size}


def inspect_residues(parent):
    """Read-only candidates, not proof of ownership or abandonment."""
    parent = Path(parent).expanduser().resolve(strict=True)
    candidates = []
    for path in sorted(parent.iterdir()):
        if not (path.name.startswith('.timecapsule-') or path.name.startswith('timecapsule-inventory-')):
            continue
        metadata = path.lstat()
        linked = stat.S_ISLNK(metadata.st_mode) or bool(getattr(metadata, 'st_file_attributes', 0)
                 & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))
        candidates.append({'name': path.name, 'modified_ns': metadata.st_mtime_ns,
                           'kind': 'link-not-followed' if linked else 'directory' if stat.S_ISDIR(metadata.st_mode) else 'file',
                           'size': metadata.st_size, 'action': 'manual-review-only'})
    return {'parent': str(parent), 'candidates': candidates,
            'note': 'No content read or deleted; names do not prove ownership or inactivity.'}
