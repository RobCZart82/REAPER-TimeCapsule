"""Snapshot, verification, and non-destructive staged restore for REAPER."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import tempfile
import zipfile
import unicodedata
import zlib
from contextlib import ExitStack
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .rules import decide
from .publication import publish_directory
from .operation import checkpoint
from .inventory import build_inventory, inventory_input_limit
from .safe_paths import trusted_resource_file

VERSION = "0.9.0-beta.2"
FORMAT = "reaper-timecapsule"
SCHEMA = 2
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_FILES = 200_000
MAX_TOTAL_BYTES = 32 * 1024 ** 3
MAX_SINGLE_FILE = 8 * 1024 ** 3
BLOCK_SIZE = 1024 * 1024


def default_resource() -> Path:
    import sys
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "REAPER"
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "REAPER"
    return Path.home() / ".config" / "REAPER"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(BLOCK_SIZE), b""):
            h.update(block)
    return h.hexdigest()


def _valid_path(path: str) -> bool:
    if not isinstance(path, str) or not path or "\\" in path or ":" in path or "\x00" in path:
        return False
    if path.startswith("/") or path.endswith("/"):
        return False
    return all(p not in ("", ".", "..") for p in path.split("/"))


WINDOWS_RESERVED_NAMES = {'con', 'prn', 'aux', 'nul'} | {
    prefix + digit for prefix in ('com', 'lpt') for digit in '123456789¹²³'
}


def _validate_portable_paths(paths) -> None:
    """Conservative cross-platform namespace preflight, without renaming data."""
    prefixes = {}
    for path in paths:
        if not _valid_path(path):
            raise ValueError("Unsafe archive path: " + repr(path))
        original = path.split('/')
        normalized = []
        for index, part in enumerate(original):
            if (part.endswith((' ', '.')) or any(char in '<>:"\\|?*' for char in part)
                    or any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in part)
                    or part.split('.')[0].rstrip(' ').casefold() in WINDOWS_RESERVED_NAMES):
                raise ValueError("Archive contains a nonportable filename: " + repr(path))
            normalized.append(unicodedata.normalize('NFC', part).casefold())
            identity = tuple(normalized)
            spelling = tuple(original[:index + 1])
            is_file = index == len(original) - 1
            existing = prefixes.get(identity)
            if existing is not None and existing != (spelling, is_file):
                raise ValueError("Archive paths collide across platforms: " + repr(path)
                                 + " conflicts with " + repr('/'.join(existing[0])))
            prefixes[identity] = spelling, is_file


def scan(source: Path, *, control=None) -> list[dict]:
    """Non-invasive inventory; NEVER follows directory/file symlinks."""
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Source must be a directory")
    result = []

    def walk_error(error):
        raise OSError(error.errno, "Cannot scan source directory: " + str(error), error.filename) from error

    def excluded_link(path, metadata):
        # Windows junctions/reparse points are not reliably covered by is_symlink.
        linked = stat.S_ISLNK(metadata.st_mode) or bool(
            getattr(metadata, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))
        if linked:
            result.append({"path": path.relative_to(source).as_posix(), "size": 0,
                           "policy": "exclude", "reason": "Link/reparse point omitted; target not read",
                           "kind": "link"})
        return linked

    for base, folders, files in os.walk(source, followlinks=False, onerror=walk_error):
        checkpoint(control, "Scanning")
        traversed = []
        for name in sorted(folders):
            checkpoint(control, "Scanning")
            path = Path(base) / name
            metadata = path.lstat()  # Propagate permission/disappearance errors.
            if not excluded_link(path, metadata) and name not in (".git", "__pycache__", ".svn"):
                traversed.append(name)
        folders[:] = traversed
        for filename in sorted(files):
            checkpoint(control, "Scanning")
            path = Path(base) / filename
            metadata = path.lstat()
            if excluded_link(path, metadata):
                continue
            rel = path.relative_to(source).as_posix()
            if not stat.S_ISREG(metadata.st_mode):
                result.append({"path": rel, "size": 0, "policy": "exclude",
                               "reason": "Special filesystem entry omitted; content not read",
                               "kind": "special"})
                continue
            # Native names are inventory input; portability is a separate preflight.
            rule = decide(rel)
            result.append({"path": rel, "size": metadata.st_size, "policy": rule.policy, "reason": rule.reason})
    return result


def preview(source: Path) -> dict:
    items = scan(source)
    counts = Counter(x["policy"] for x in items)
    sizes = Counter()
    for x in items:
        sizes[x["policy"]] += x["size"]
    issues = []
    portable = []
    for item in items:
        if item["policy"] not in ("keep", "review"):
            continue
        try:
            _validate_portable_paths([item["path"]])
            portable.append(item["path"])
        except ValueError as exc:
            issues.append({"path": item["path"], "reason": str(exc)})
    try:
        _validate_portable_paths(portable)
    except ValueError as exc:
        issues.append({"reason": str(exc)})
    return {"files": len(items), "counts": dict(counts), "bytes": dict(sizes), "items": items,
            "inventory": build_inventory(Path(source).expanduser().resolve(strict=True), items),
            "portable_names_ready": not issues, "portability_issues": issues,
            "skipped_entries": [x for x in items if x.get("kind") in ("link", "special")]}


def make_backup(source: Path, destination: Path, *, control=None) -> dict:
    checkpoint(control, "Preparing backup")
    source = Path(source).expanduser().resolve(strict=True)
    destination = Path(destination).expanduser().absolute()
    if source == destination or source in destination.parents:
        raise ValueError("Backup ZIP cannot be inside the source directory")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Refusing to overwrite an existing backup")
    # Resolve the parent, not the filename: existing/dangling targets must
    # retain the exclusive-publication protection above.
    destination = destination.parent.resolve() / destination.name
    if source == destination.parent or source in destination.parent.parents:
        raise ValueError("Backup ZIP cannot be inside the source directory")
    items = scan(source, control=control)
    selected = [x for x in items if x["policy"] in ("keep", "review")]
    try:
        _validate_portable_paths(item["path"] for item in selected)
    except ValueError as exc:
        raise ValueError("Cannot create a portable backup. " + str(exc)
                         + ". Use Scan / Preview to inspect filename conflicts. "
                         "No files were renamed or omitted; keep the original resources.") from None
    if len(selected) > MAX_FILES or sum(x["size"] for x in selected) > MAX_TOTAL_BYTES:
        raise ValueError("Backup exceeds safe snapshot limits")
    for x in selected:
        if x["size"] > MAX_SINGLE_FILE:
            raise ValueError("Single file too large: " + x["path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    parent_identity = destination.parent.stat()

    def validate_destination_parent():
        current_parent = destination.parent.resolve(strict=True)
        current = destination.parent.stat()
        if (current_parent != destination.parent or
                (current.st_dev, current.st_ino) != (parent_identity.st_dev, parent_identity.st_ino)):
            raise ValueError("Backup destination directory changed during backup")
        if current_parent == source or source in current_parent.parents:
            raise ValueError("Backup ZIP cannot be inside the source directory")

    validate_destination_parent()
    fd, staging = tempfile.mkstemp(prefix=".timecapsule-", suffix=".zip", dir=destination.parent)
    os.close(fd)
    manifest_files = []
    completed = 0
    total = sum(item["size"] for item in selected)
    try:
        with tempfile.TemporaryDirectory(prefix="timecapsule-inventory-") as snapshot_name, \
                zipfile.ZipFile(staging, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as out:
            snapshot = Path(snapshot_name)
            for item in selected:
                checkpoint(control, "Copying backup", completed, total)
                p = trusted_resource_file(source, item["path"])
                if p.is_symlink() or not p.is_file():
                    raise ValueError("Source changed during backup: " + item["path"])
                # Copy once while hashing, so the digest refers to ZIP contents, not a later file state.
                hash_value = hashlib.sha256()
                bytes_written = 0
                entry = "resources/" + item["path"]
                limit = inventory_input_limit(item["path"])
                copied = snapshot / item["path"] if limit and item["size"] <= limit else None
                if copied:
                    copied.parent.mkdir(parents=True, exist_ok=True)
                with ExitStack() as streams:
                    src = streams.enter_context(p.open("rb"))
                    dst = streams.enter_context(out.open(entry, "w"))
                    inventory_copy = streams.enter_context(copied.open("xb")) if copied else None
                    before = os.fstat(src.fileno())
                    for block in iter(lambda: src.read(BLOCK_SIZE), b""):
                        checkpoint(control, "Copying backup", completed, total)
                        bytes_written += len(block)
                        completed += len(block)
                        if bytes_written > MAX_SINGLE_FILE or bytes_written > item["size"]:
                            raise ValueError("Changed source exceeds size limit")
                        hash_value.update(block)
                        dst.write(block)
                        if inventory_copy:
                            inventory_copy.write(block)
                    after = os.fstat(src.fileno())
                    current = p.stat()
                    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
                    if identity(before) != identity(after) or identity(after) != identity(current):
                        raise ValueError("Source changed during backup: " + item["path"])
                if bytes_written != item["size"]:
                    raise ValueError("Source changed during backup: " + item["path"])
                manifest_files.append({**item, "sha256": hash_value.hexdigest()})
            manifest = {
                "format": FORMAT, "schema": SCHEMA, "app_version": VERSION,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_platform": platform.system(), "source_architecture": platform.machine(),
                "strategy": "clean-migration", "files": manifest_files,
                "inventory": build_inventory(snapshot, items),
                "inventory_basis": "archived-resource-bytes",
                "omitted": [x for x in items if x["policy"] in ("exclude", "regenerate")],
                "notes": "review items are backed up but never restored into active REAPER resources automatically",
            }
            out.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        verify_backup(Path(staging), control=control)
        checkpoint(control, "Publishing backup")
        validate_destination_parent()
        # Atomic exclusive publication: linking fails if ANY destination entry
        # exists, including a concurrently created file or dangling symlink.
        # Staging is in the same directory/filesystem. Never fall back to rename
        # or copying: unsupported filesystems must fail without risking overwrite.
        try:
            os.link(staging, destination)
        except FileExistsError:
            raise
        except OSError as exc:
            raise OSError("Cannot safely publish backup: choose a writable destination "
                          "filesystem supporting hard links") from exc
        return {"archive": str(destination), "saved": len(selected), "omitted": len(items) - len(selected),
                "skipped_entries": [x for x in items if x.get("kind") in ("link", "special")]}
    finally:
        if os.path.exists(staging):
            os.unlink(staging)


def _validate_entry_info(info: zipfile.ZipInfo) -> None:
    # Block Unix symlinks and special device files in untrusted archives.
    mode = info.external_attr >> 16
    mode_type = stat.S_IFMT(mode)
    if info.is_dir() or mode_type not in (0, stat.S_IFREG):
        raise ValueError("Archive contains a directory, symlink or special file")
    if info.file_size > MAX_SINGLE_FILE:
        raise ValueError("Archive file exceeds size limit")


LEGACY_POLICY_VERSIONS = {"0.2.0-dev", "0.3.0-dev", "0.4.0-dev"}


def _effective_policy(path: str, stored: str, version: str) -> str:
    """Apply current safety rules to legacy archives without trusting old policy.

    ReaPack/registry.db was KEEP through 0.4, but must now be REVIEW.
    Likewise its downloaded cache used to be KEEP and is now REGENERATE.
    Narrow compatibility exceptions prevent inadvertent policy promotion.
    """
    actual = decide(path).policy
    if stored == actual:
        return actual
    if (
        version in LEGACY_POLICY_VERSIONS
        and path.lower().startswith("reapack/")
        and stored == "keep"
        and actual in ("review", "regenerate")
    ):
        return actual
    raise ValueError("Snapshot restore policy mismatch: " + path)


def _unique_manifest_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate manifest field")
        result[key] = value
    return result


def verify_backup(archive: Path, *, control=None) -> dict:
    """Normalize malformed archive/encoding errors for API, GUI and CLI callers."""
    try:
        return _verify_backup(archive, control=control)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, UnicodeError,
            json.JSONDecodeError, EOFError, zlib.error, RuntimeError, NotImplementedError):
        raise ValueError("Invalid or unsupported backup archive") from None


def _verify_backup(archive: Path, *, control=None) -> dict:
    checkpoint(control, "Preparing verification")
    archive = Path(archive)
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        completed = 0
        progress_total = sum(info.file_size for info in infos if info.filename.startswith("resources/"))
        if len(infos) > MAX_FILES + 1:
            raise ValueError("Too many archive members")
        names = [x.filename for x in infos]
        if len(set(names)) != len(names) or "manifest.json" not in names:
            raise ValueError("Invalid or duplicate archive members")
        manifest_info = z.getinfo("manifest.json")
        _validate_entry_info(manifest_info)
        if manifest_info.file_size > MAX_MANIFEST_BYTES:
            raise ValueError("Manifest exceeds size limit")
        manifest = json.loads(z.read(manifest_info), object_pairs_hook=_unique_manifest_object)
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be an object")
        if manifest.get("format") != FORMAT or manifest.get("schema") != SCHEMA:
            raise ValueError("Unsupported archive format or schema")
        files = manifest.get("files")
        if not isinstance(files, list) or len(files) > MAX_FILES:
            raise ValueError("Invalid file index")
        # Validate the complete namespace before hashing or creating restore paths.
        if any(not isinstance(item, dict) for item in files):
            raise ValueError("Invalid file record")
        _validate_portable_paths(item.get("path") for item in files)
        expected = {"manifest.json"}
        total_bytes = 0
        for item in files:
            checkpoint(control, "Verifying", completed, progress_total)
            if not isinstance(item, dict):
                raise ValueError("Invalid file record")
            rel = item.get("path")
            if not _valid_path(rel):
                raise ValueError("Unsafe archive path")
            if item.get("policy") not in ("keep", "review"):
                raise ValueError("Invalid restore policy")
            # An archive cannot promote native binaries or machine-specific settings
            # from 'review' to 'keep' by changing the untrusted manifest.
            _effective_policy(rel, item["policy"], manifest.get("app_version", ""))
            if not isinstance(item.get("size"), int) or item["size"] < 0:
                raise ValueError("Invalid size")
            if not isinstance(item.get("sha256"), str) or len(item["sha256"]) != 64:
                raise ValueError("Invalid hash")
            name = "resources/" + rel
            if name in expected or name not in names:
                raise ValueError("Duplicate or missing resource: " + rel)
            expected.add(name)
            info = z.getinfo(name)
            _validate_entry_info(info)
            if info.file_size != item["size"]:
                raise ValueError("Incorrect file size: " + rel)
            total_bytes += info.file_size
            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError("Archive exceeds total size limit")
            h = hashlib.sha256()
            with z.open(info) as fp:
                for block in iter(lambda: fp.read(BLOCK_SIZE), b""):
                    checkpoint(control, "Verifying", completed, progress_total)
                    completed += len(block)
                    h.update(block)
            if h.hexdigest() != item["sha256"]:
                raise ValueError("Checksum mismatch: " + rel)
        if expected != set(names):
            raise ValueError("Unexpected archive members")
        checkpoint(control, "Verification complete", completed, progress_total)
        return manifest


def restore_backup(archive: Path, destination: Path, *, control=None) -> dict:
    """Restore into a NEW folder, in staging. Review files remain quarantined.

    Never merges into a running REAPER config, overwrites, or installs native plugins.
    """
    archive = Path(archive).expanduser().resolve(strict=True)
    destination = Path(destination).expanduser().absolute()
    manifest = verify_backup(archive, control=control)
    checkpoint(control, "Preparing restore")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Choose a NEW destination folder; existing folders are never overwritten")
    parent = destination.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("Restore parent must be a directory")
    staging = Path(tempfile.mkdtemp(prefix=".timecapsule-restore-", dir=parent))
    counts = Counter()
    completed = 0
    progress_total = sum(item["size"] for item in manifest["files"])
    try:
        with zipfile.ZipFile(archive) as z:
            for item in manifest["files"]:
                checkpoint(control, "Restoring", completed, progress_total)
                # Old policy metadata is advisory: the CURRENT policy rules
                # decide which destination is safe, even for legacy snapshots.
                effective = _effective_policy(
                    item["path"], item["policy"], manifest.get("app_version", "")
                )
                if effective in ("exclude", "regenerate"):
                    counts["regenerate"] += 1
                    continue
                # Explicitly separate undecided settings to avoid accidentally activating them.
                prefix = "REAPER" if effective == "keep" else "NeedsReview"
                target = staging / prefix / PurePosixPath(item["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open("resources/" + item["path"]) as src, target.open("xb") as dst:
                    h = hashlib.sha256()
                    for block in iter(lambda: src.read(BLOCK_SIZE), b""):
                        checkpoint(control, "Restoring", completed, progress_total)
                        completed += len(block)
                        h.update(block)
                        dst.write(block)
                if h.hexdigest() != item["sha256"]:
                    raise ValueError("Corrupt data detected during restore")
                counts[effective] += 1
        info = {
            "restored_portable": counts["keep"],
            "isolated_for_review": counts["review"],
            "legacy_cache_skipped": counts["regenerate"],
            "instructions": "Copy REAPER/ into a CLEAN, CLOSED REAPER resource directory only after reviewing conflicts. NeedsReview/ is NOT automatically installed.",
            "inventory": manifest.get("inventory", {}),
        }
        (staging / "RESTORE_REPORT.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        checkpoint(control, "Publishing restore")
        publish_directory(staging, parent / destination.name)
        return {"destination": str(destination), **info}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def preview_backup(archive: Path, *, control=None) -> dict:
    manifest = verify_backup(archive, control=control)
    decisions = [{"path": x["path"], "stored": x["policy"],
                  "effective": _effective_policy(x["path"], x["policy"], manifest.get("app_version", ""))}
                 for x in manifest["files"]]
    counts = Counter(x["effective"] for x in decisions)
    omitted = Counter(x["policy"] for x in manifest["omitted"])
    changes = [{**x, "reason": decide(x["path"]).reason} for x in decisions if x["stored"] != x["effective"]]
    return {"saved": dict(counts), "stored_saved": dict(Counter(x["stored"] for x in decisions)),
            "policy_changes": changes, "omitted": dict(omitted), "created_utc": manifest["created_utc"],
            "inventory": manifest.get("inventory", {}),
            "inventory_basis": manifest.get("inventory_basis", "legacy-unverified-source-inventory")}
