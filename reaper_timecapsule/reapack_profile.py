"""Read-only ReaPack 1.x profile/registry inventory.

Verified against cfillion/reapack src/config.cpp, src/remote.cpp,
src/registry.cpp and src/path.cpp (last 1.x branch, 2025).
Never writes a configuration, downloads packages, or activates extensions.
The input may contain secrets, so reports avoid exposing original URLs
with embedded credentials or query tokens.
"""
from __future__ import annotations

import configparser
from pathlib import Path
import re
import sqlite3

from urllib.parse import urlsplit

MAX_INI_BYTES = 2 * 1024 * 1024
MAX_REGISTRY_BYTES = 128 * 1024 * 1024
MAX_REMOTES = 2000
MAX_PACKAGES = 10000
REMOTE_KEY = re.compile(r"remote([0-9]+)$", re.IGNORECASE)


def _safe_url(value: str) -> str | None:
    """Discard username, password, query, fragment and non-http(s) URL."""
    try:
        url = urlsplit(value.strip())
        if url.scheme.lower() not in ("http", "https") or not url.hostname:
            return None
        if not url.path or not url.path.lower().endswith(".xml"):
            return None
        host = url.hostname.lower()
        if ":" in host:
            host = f"[{host}]"
        return f"{url.scheme.lower()}://{host}{':' + str(url.port) if url.port else ''}{url.path}"
    except ValueError:
        return None


def _boolean(value: str | None, fallback: bool | None = None) -> bool | None:
    """C++ ReaPack INI stores bool as numeric 0/1. Do not guess invalid values."""
    if value is None:
        return fallback
    if value.strip() == "1":
        return True
    if value.strip() == "0":
        return False
    return None


def _tri(value: str | None) -> bool | None:
    # boost::logic::tribool serializes indeterminate as 2.
    return _boolean(value, None)


def _empty_profile(status: str, note: str = "") -> dict:
    return {
        "status": status,
        "configuration_version": None,
        "repositories": [],
        "repository_count": 0,
        "enabled_count": 0,
        "disabled_count": 0,
        "options": {},
        "notes": [note] if note else [],
        "automatic_sync": False,
    }


def parse_profile(config_file: Path) -> dict:
    """Parse the actual [remotes] remote0=name|url|enabled|autoInstall layout.

    Never infer that ReaPack 1.x's built-in default repositories were enabled
    when not present in the input; the user's current source is authoritative.
    """
    config_file = Path(config_file)
    try:
        if config_file.is_symlink() or not config_file.is_file():
            return _empty_profile("missing", "No trusted reapack.ini available")
        if config_file.stat().st_size > MAX_INI_BYTES:
            return _empty_profile("too-large", "reapack.ini exceeds parser size limit")
        contents = config_file.read_bytes()
    except OSError:
        return _empty_profile("unreadable", "Could not open reapack.ini")

    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Win32 legacy INI files may use Windows ANSI encoding. Preserve bytes
        # elsewhere in the backup; this fallback is for display only.
        text = contents.decode("cp1252", errors="replace")

    config = configparser.RawConfigParser(
        interpolation=None, strict=True, delimiters=("=",),
        comment_prefixes=(";", "#"), inline_comment_prefixes=None,
    )
    try:
        config.read_string(text)
    except (configparser.Error, ValueError):
        return _empty_profile("invalid", "INI syntax not recognized; saved original remains available")

    raw_version = config.get("general", "version", fallback=None)
    try:
        version = int(raw_version) if raw_version is not None else None
    except ValueError:
        version = None
    if version is not None and (version < 0 or version > 4):
        return {
            **_empty_profile("unsupported", "Unsupported ReaPack configuration version"),
            "configuration_version": version,
        }

    defaults = {
        "install_new_on_sync": ("install", "autoinstall", False),
        "enable_prereleases": ("install", "prereleases", False),
        "prompt_to_uninstall_obsolete": ("install", "promptobsolete", True),
        "expand_search_synonyms": ("browser", "synonyms", True),
    }
    options = {}
    notes = []
    for label, (section, key, default) in defaults.items():
        raw_value = config.get(section, key, fallback=None)
        value = _boolean(raw_value, default)
        options[label] = {
            "value": value,
            "origin": "explicit" if raw_value is not None else "upstream-default",
        }
        if value is None:
            notes.append("Invalid boolean option: " + section + "." + key)

    if not config.has_section("remotes"):
        notes.append("No [remotes] section; cannot reconstruct repository state")
        return {
            **_empty_profile("partial"),
            "configuration_version": version,
            "options": options,
            "notes": notes,
        }
    try:
        size = int(config.get("remotes", "size", fallback="-1"))
    except ValueError:
        size = -1
    if not 0 <= size <= MAX_REMOTES:
        notes.append("Missing or invalid [remotes] size")
        return {
            **_empty_profile("partial"),
            "configuration_version": version,
            "options": options,
            "notes": notes,
        }

    repositories = []
    seen_names = set()
    missing_or_invalid = 0
    for index in range(size):
        raw = config.get("remotes", f"remote{index}", fallback=None)
        if raw is None:
            missing_or_invalid += 1
            continue
        components = raw.split("|")
        if len(components) < 3 or not components[0].strip():
            missing_or_invalid += 1
            continue
        name, original_url, enabled_raw = components[:3]
        clean_url = _safe_url(original_url)
        enabled = _boolean(enabled_raw)
        per_repo_auto = _tri(components[3]) if len(components) > 3 else None
        if clean_url is None or enabled is None or name in seen_names:
            missing_or_invalid += 1
            continue
        seen_names.add(name)
        repositories.append({
            "name": name,
            "index_url": clean_url,
            "enabled": enabled,
            "auto_install_override": per_repo_auto,
            "order": index,
        })

    if missing_or_invalid:
        notes.append(f"{missing_or_invalid} malformed or missing repository record(s)")
    # A recognized profile can contain zero remotes; do not invent defaults.
    status = "parsed" if missing_or_invalid == 0 and all(
        row["value"] is not None for row in options.values()
    ) else "partial"
    return {
        "status": status,
        "configuration_version": version,
        "repositories": repositories,
        "repository_count": len(repositories),
        "enabled_count": sum(x["enabled"] for x in repositories),
        "disabled_count": sum(not x["enabled"] for x in repositories),
        "options": options,
        "notes": notes,
        "automatic_sync": False,
    }


def _empty_registry(status: str, note: str = "") -> dict:
    return {
        "status": status,
        "installed_count": None,
        "owned_file_count": None,
        "installed_packages": [],
        "truncated": False,
        "notes": [note] if note else [],
    }


def inspect_registry(database_path: Path) -> dict:
    """Audit the ReaPack/registry.db SQLite file via a read-only connection.

    Uses immutable=1 to avoid creating SHM/WAL files and refuses nonempty WAL
    sidecars: do not claim a consistent snapshot of a running ReaPack registry.
    """
    database_path = Path(database_path)
    try:
        if database_path.is_symlink() or not database_path.is_file():
            return _empty_registry("missing", "ReaPack/registry.db not found")
        if database_path.stat().st_size > MAX_REGISTRY_BYTES:
            return _empty_registry("too-large", "Registry exceeds inspection limit")
        if any(
            Path(str(database_path) + suffix).is_file() and
            Path(str(database_path) + suffix).stat().st_size
            for suffix in ("-wal", "-journal")
        ):
            return _empty_registry("busy-or-incomplete", "Close REAPER before inspecting pending SQLite journals")
        with database_path.open("rb") as fp:
            if fp.read(16) != b"SQLite format 3\x00":
                return _empty_registry("unsupported", "Not a SQLite 3 registry")
    except OSError:
        return _empty_registry("unreadable", "Could not inspect SQLite registry")

    # URI uses percent-encoding from Path.as_uri; never interpolate a
    # database-controlled string into SQL.
    uri = database_path.resolve().as_uri() + "?mode=ro&immutable=1"
    try:
        with sqlite3.connect(uri, uri=True, timeout=1.0) as db:
            db.execute("PRAGMA query_only=ON")
            names = {x[0] for x in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            if not {"entries", "files"}.issubset(names):
                return _empty_registry("unsupported", "Missing ReaPack 1.x registry tables")
            columns = {x[1] for x in db.execute("PRAGMA table_info(entries)")}
            if not {"id", "remote", "category", "package", "version", "flags"}.issubset(columns):
                return _empty_registry("unsupported", "Unrecognized entries table columns")
            file_columns = {x[1] for x in db.execute("PRAGMA table_info(files)")}
            if not {"entry", "path"}.issubset(file_columns):
                return _empty_registry("unsupported", "Unrecognized files table columns")

            installed = db.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            file_count = db.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            rows = db.execute(
                "SELECT e.remote, e.category, e.package, e.version, e.flags, "
                "COUNT(f.entry) FROM entries e "
                "LEFT JOIN files f ON f.entry=e.id "
                "GROUP BY e.id ORDER BY e.remote, e.category, e.package "
                "LIMIT ?", (MAX_PACKAGES,)
            ).fetchall()
            packages = []
            for remote, category, name, version, flags, count in rows:
                flagbits = flags if isinstance(flags, int) else 0
                packages.append({
                    "repository": str(remote),
                    "category": str(category),
                    "name": str(name),
                    "version": str(version),
                    "pinned": bool(flagbits & 1),
                    "prerelease_override": bool(flagbits & 2),
                    "owned_files": count,
                })
            return {
                "status": "parsed",
                "installed_count": installed,
                "owned_file_count": file_count,
                "installed_packages": packages,
                "truncated": installed > MAX_PACKAGES,
                "notes": [] if installed <= MAX_PACKAGES else [
                    "Only the first 10000 packages appear in the diagnostic manifest"
                ],
            }
    except (sqlite3.Error, OSError, ValueError):
        return _empty_registry("invalid", "Could not read a consistent ReaPack 1.x registry")
