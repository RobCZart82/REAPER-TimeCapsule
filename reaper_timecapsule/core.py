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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .rules import decide

VERSION = "0.2.0-dev"
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


def scan(source: Path) -> list[dict]:
    """Non-invasive inventory; NEVER follows directory/file symlinks."""
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Source must be a directory")
    result = []
    for base, folders, files in os.walk(source, followlinks=False):
        folders[:] = sorted(
            x for x in folders if not (Path(base) / x).is_symlink() and x not in (".git", "__pycache__", ".svn")
        )
        for filename in sorted(files):
            path = Path(base) / filename
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(source).as_posix()
            if not _valid_path(rel):
                raise ValueError("Unexpected source path")
            rule = decide(rel)
            size = path.stat().st_size
            result.append({"path": rel, "size": size, "policy": rule.policy, "reason": rule.reason})
    return result


def preview(source: Path) -> dict:
    items = scan(source)
    counts = Counter(x["policy"] for x in items)
    sizes = Counter()
    for x in items:
        sizes[x["policy"]] += x["size"]
    return {"files": len(items), "counts": dict(counts), "bytes": dict(sizes), "items": items}


def make_backup(source: Path, destination: Path) -> dict:
    source = Path(source).expanduser().resolve(strict=True)
    destination = Path(destination).expanduser().absolute()
    if source == destination or source in destination.parents:
        raise ValueError("Backup ZIP cannot be inside the source directory")
    if destination.exists():
        raise FileExistsError("Refusing to overwrite an existing backup")
    destination.parent.mkdir(parents=True, exist_ok=True)
    items = scan(source)
    selected = [x for x in items if x["policy"] in ("keep", "review")]
    if len(selected) > MAX_FILES or sum(x["size"] for x in selected) > MAX_TOTAL_BYTES:
        raise ValueError("Backup exceeds safe snapshot limits")
    for x in selected:
        if x["size"] > MAX_SINGLE_FILE:
            raise ValueError("Single file too large: " + x["path"])
    fd, staging = tempfile.mkstemp(prefix=".timecapsule-", suffix=".zip", dir=destination.parent)
    os.close(fd)
    manifest_files = []
    try:
        with zipfile.ZipFile(staging, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as out:
            for item in selected:
                p = source.joinpath(*item["path"].split("/"))
                if p.is_symlink() or not p.is_file():
                    raise ValueError("Source changed during backup: " + item["path"])
                # Copy once while hashing, so the digest refers to ZIP contents, not a later file state.
                hash_value = hashlib.sha256()
                bytes_written = 0
                entry = "resources/" + item["path"]
                with p.open("rb") as src, out.open(entry, "w") as dst:
                    for block in iter(lambda: src.read(BLOCK_SIZE), b""):
                        bytes_written += len(block)
                        if bytes_written > MAX_SINGLE_FILE:
                            raise ValueError("Changed source exceeds size limit")
                        hash_value.update(block)
                        dst.write(block)
                if bytes_written != item["size"]:
                    raise ValueError("Source changed during backup: " + item["path"])
                manifest_files.append({**item, "sha256": hash_value.hexdigest()})
            manifest = {
                "format": FORMAT, "schema": SCHEMA, "app_version": VERSION,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_platform": platform.system(), "source_architecture": platform.machine(),
                "strategy": "clean-migration", "files": manifest_files,
                "omitted": [x for x in items if x["policy"] in ("exclude", "regenerate")],
                "notes": "review items are backed up but never restored into active REAPER resources automatically",
            }
            out.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        verify_backup(Path(staging))
        # Do not overwrite an already existing archive, including a concurrent creation.
        if destination.exists():
            raise FileExistsError("Backup target appeared during creation")
        os.rename(staging, destination)
        return {"archive": str(destination), "saved": len(selected), "omitted": len(items) - len(selected)}
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


def verify_backup(archive: Path) -> dict:
    archive = Path(archive)
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        if len(infos) > MAX_FILES + 1:
            raise ValueError("Too many archive members")
        names = [x.filename for x in infos]
        if len(set(names)) != len(names) or "manifest.json" not in names:
            raise ValueError("Invalid or duplicate archive members")
        manifest_info = z.getinfo("manifest.json")
        _validate_entry_info(manifest_info)
        if manifest_info.file_size > MAX_MANIFEST_BYTES:
            raise ValueError("Manifest exceeds size limit")
        manifest = json.loads(z.read(manifest_info))
        if manifest.get("format") != FORMAT or manifest.get("schema") != SCHEMA:
            raise ValueError("Unsupported archive format or schema")
        files = manifest.get("files")
        if not isinstance(files, list) or len(files) > MAX_FILES:
            raise ValueError("Invalid file index")
        expected = {"manifest.json"}
        total_bytes = 0
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("Invalid file record")
            rel = item.get("path")
            if not _valid_path(rel):
                raise ValueError("Unsafe archive path")
            if item.get("policy") not in ("keep", "review"):
                raise ValueError("Invalid restore policy")
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
                    h.update(block)
            if h.hexdigest() != item["sha256"]:
                raise ValueError("Checksum mismatch: " + rel)
        if expected != set(names):
            raise ValueError("Unexpected archive members")
        return manifest


def restore_backup(archive: Path, destination: Path) -> dict:
    """Restore into a NEW folder, in staging. Review files remain quarantined.

    Never merges into a running REAPER config, overwrites, or installs native plugins.
    """
    archive = Path(archive).expanduser().resolve(strict=True)
    destination = Path(destination).expanduser().absolute()
    manifest = verify_backup(archive)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Choose a NEW destination folder; existing folders are never overwritten")
    parent = destination.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("Restore parent must be a directory")
    staging = Path(tempfile.mkdtemp(prefix=".timecapsule-restore-", dir=parent))
    counts = Counter()
    try:
        with zipfile.ZipFile(archive) as z:
            for item in manifest["files"]:
                # Explicitly separate undecided settings to avoid accidentally activating them.
                prefix = "REAPER" if item["policy"] == "keep" else "NeedsReview"
                target = staging / prefix / PurePosixPath(item["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open("resources/" + item["path"]) as src, target.open("xb") as dst:
                    h = hashlib.sha256()
                    for block in iter(lambda: src.read(BLOCK_SIZE), b""):
                        h.update(block)
                        dst.write(block)
                if h.hexdigest() != item["sha256"]:
                    raise ValueError("Corrupt data detected during restore")
                counts[item["policy"]] += 1
        info = {
            "restored_portable": counts["keep"],
            "isolated_for_review": counts["review"],
            "instructions": "Copy REAPER/ into a CLEAN, CLOSED REAPER resource directory only after reviewing conflicts. NeedsReview/ is NOT automatically installed.",
        }
        (staging / "RESTORE_REPORT.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        if destination.exists():
            raise FileExistsError("Destination appeared during restore")
        staging.rename(destination)
        return {"destination": str(destination), **info}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def preview_backup(archive: Path) -> dict:
    manifest = verify_backup(archive)
    counts = Counter(x["policy"] for x in manifest["files"])
    omitted = Counter(x["policy"] for x in manifest["omitted"])
    return {"saved": dict(counts), "omitted": dict(omitted), "created_utc": manifest["created_utc"]}
