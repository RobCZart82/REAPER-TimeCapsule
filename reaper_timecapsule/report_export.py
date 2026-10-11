"""Explicit, no-overwrite export of complete local reports."""
import json
import os
import tempfile
from pathlib import Path

from .publication import publish_file
from .operation import checkpoint


def export_report(report, destination, *, forbidden_root=None, control=None):
    """Write a complete JSON report to a user-selected path, never replacing data.

    The temporary file is created next to the destination so final publication can
    use the same no-replace primitive as backup archives. If supplied, forbidden_root
    prevents placing a report anywhere inside the scanned REAPER resource directory.
    """
    requested = Path(destination).expanduser()
    if not requested.name:
        raise ValueError("Choose a file name for the report")
    parent = requested.parent.resolve(strict=True)
    target = parent / requested.name
    if target.exists() or target.is_symlink():
        raise FileExistsError("Refusing to overwrite an existing report")

    if forbidden_root is not None:
        roots = (forbidden_root,) if isinstance(forbidden_root, (str, os.PathLike)) else tuple(forbidden_root)
        for forbidden in roots:
            root = Path(forbidden).expanduser().resolve(strict=False)
            if target == root or root in target.parents:
                raise ValueError("Choose a report location outside the scanned REAPER resource folder")

    checkpoint(control, "Preparing private report export")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix="." + target.name + ".", suffix=".tmp", dir=parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            for piece in json.JSONEncoder(ensure_ascii=False, indent=2).iterencode(report):
                checkpoint(control, "Writing private report export")
                stream.write(piece)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        publish_file(temporary, target)
        return target.resolve()
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
