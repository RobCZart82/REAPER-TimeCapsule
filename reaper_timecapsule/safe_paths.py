"""Validate existing resource-relative files without following link components."""
import stat
from pathlib import Path


def trusted_resource_file(source, relative):
    root = Path(source).expanduser().resolve(strict=True)
    parts = relative.split('/')
    if not parts or any(p in ('', '.', '..') or '\\' in p for p in parts):
        raise ValueError('Invalid resource-relative file')
    path = root
    for part in parts:
        path = path / part
        value = path.lstat()
        if stat.S_ISLNK(value.st_mode) or (getattr(value, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)):
            raise ValueError('Linked resource path refused: ' + relative)
    if not stat.S_ISREG(value.st_mode) or not path.resolve(strict=True).is_relative_to(root):
        raise ValueError('Resource is not a trusted regular file: ' + relative)
    return path
