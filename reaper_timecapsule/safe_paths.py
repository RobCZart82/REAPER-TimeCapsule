"""Validate existing resource-relative files without following link components."""
import os
import stat
from pathlib import Path


def filesystem_path(path, *, force=False):
    """Return an absolute Windows path, extended when needed or explicitly requested."""
    value = os.path.abspath(os.fspath(path))
    if os.name != 'nt' or value.startswith('\\\\?\\'):
        return value
    if not force and len(value) < 260:
        return value
    if value.startswith('\\\\'):
        return '\\\\?\\UNC\\' + value[2:]
    return '\\\\?\\' + value


def trusted_resource_file(source, relative):
    root = Path(source).expanduser().resolve(strict=True)
    parts = relative.split('/')
    if not parts or any(p in ('', '.', '..') or '\\' in p for p in parts):
        raise ValueError('Invalid resource-relative file')
    path = root
    for part in parts:
        path = path / part
        io_path = Path(filesystem_path(path))
        value = io_path.lstat()
        if stat.S_ISLNK(value.st_mode) or (getattr(value, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)):
            raise ValueError('Linked resource path refused: ' + relative)
    io_root = Path(filesystem_path(root, force=True))
    resolved = Path(filesystem_path(io_path.resolve(strict=True), force=True))
    if not stat.S_ISREG(value.st_mode) or not resolved.is_relative_to(io_root):
        raise ValueError('Resource is not a trusted regular file: ' + relative)
    return io_path
