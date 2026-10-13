"""Read-only inventory of ReaPack/SWS and MIDI workflow dependencies.

This module reports evidence, not installation state: REAPER/ReaPack may keep some
repository and package information in formats which this tool does not yet parse.
No user scripts, extensions or binaries are executed.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from .midi_validation import validate_midi_workflow
from .reapack_profile import inspect_registry, parse_profile, _empty_profile, _empty_registry
from .operation import checkpoint
from .safe_paths import trusted_resource_file

MAX_REAPACK_INI_BYTES = 2 * 1024 * 1024
MAX_URLS = 1000
URL_PATTERN = re.compile(r"https?://[^\s<>\"'|]+", flags=re.IGNORECASE)
EXTENSION_SUFFIXES = (".dylib", ".dll", ".so")


def _public_repo_urls(ini_file: Path) -> list[str]:
    """Return display-safe repository index URLs; remove credentials/query/fragment.

    The original (possibly credential-bearing) configuration is left untouched.
    Disabled/enabled state MUST NOT be inferred from a bare URL match.
    """
    try:
        if ini_file.is_symlink() or ini_file.stat().st_size > MAX_REAPACK_INI_BYTES:
            return []
        with ini_file.open("rb") as stream:
            raw = stream.read(MAX_REAPACK_INI_BYTES + 1)
        if len(raw) > MAX_REAPACK_INI_BYTES:
            return []
    except (OSError, ValueError):
        return []
    contents = raw.decode("utf-8-sig", errors="replace")
    output = set()
    for match in URL_PATTERN.finditer(contents):
        candidate = match.group(0).rstrip("\\,;.)]}")
        # Some INI values terminate URLs with an escaped quote.
        candidate = candidate.rstrip("\\")
        try:
            url = urlsplit(candidate)
            if url.scheme.lower() not in ("http", "https") or not url.hostname:
                continue
            if not url.path.lower().endswith(".xml"):
                continue
            # Display-safe URL: drop user info, query, and fragment.
            host = url.hostname.lower()
            if ":" in host:
                host = "[" + host + "]"
            port = f":{url.port}" if url.port else ""
            output.add(f"{url.scheme.lower()}://{host}{port}{url.path}")
        except ValueError:
            continue
        if len(output) >= MAX_URLS:
            break
    return sorted(output)


def build_inventory(source: Path, items: list[dict], *, control=None, include_midi=True) -> dict:
    """Inventory strictly from paths plus the configured ReaPack INI file."""
    checkpoint(control, "Inspecting inventory")
    source = Path(source)
    portable = {x["path"] for x in items if x["policy"] == "keep"}
    review = {x["path"] for x in items if x["policy"] == "review"}
    paths = portable | review
    indexed = {x["path"]: x for x in items}
    native = []
    for name in sorted(review):
        lower = name.lower()
        if not lower.startswith("userplugins/") or not lower.endswith(EXTENSION_SUFFIXES):
            continue
        basename = Path(name).name
        if "reapack" in basename.lower():
            family = "ReaPack"
        elif "sws" in basename.lower():
            family = "SWS"
        else:
            family = "Other"
        native.append({"filename": basename, "family": family, "restore": "manual-review"})
    def selected_path(relative):
        if relative not in paths:
            return None
        try:
            return trusted_resource_file(source, relative)
        except (OSError, ValueError):
            return None

    ini = selected_path("reapack.ini")
    database = selected_path("ReaPack/registry.db")
    # Inspect sidecar boundaries too: SQLite must not observe an external WAL.
    for suffix in ("-wal", "-journal"):
        relative = "ReaPack/registry.db" + suffix
        sidecar = indexed.get(relative)
        if sidecar and (relative not in paths or sidecar["size"] > inventory_input_limit(relative)):
            database = None
        if database:
            try:
                (database.parent / (database.name + suffix)).lstat()
            except FileNotFoundError:
                continue
            if selected_path(relative) is None:
                database = None
    profile = parse_profile(ini) if ini else _empty_profile("missing", "No selected trusted reapack.ini")
    registry = inspect_registry(database, control=control) if database else _empty_registry("missing", "No selected trusted registry")
    # Legacy URL-only scan remains a compatibility fallback when an INI
    # predates the 1.x [remotes] section or uses an unknown format.
    repo_urls = ([x["index_url"] for x in profile["repositories"]]
                 if profile["status"] == "parsed" or profile.get("repository_layout_recognized") else
                 _public_repo_urls(ini) if ini else [])
    menu_files = sorted(
        x for x in portable if x.lower().startswith("menusets/") and x.lower().endswith(".reapermenu")
    )
    keymap_files = sorted(
        x for x in portable if x.lower().startswith("keymaps/") and x.lower().endswith(".reaperkeymap")
    )
    return {
        "format": "inventory-v1",
        "inspection_omissions": [{"path": x["path"], "reason": "Parser size limit exceeded"}
                                 for x in items if x["path"] in paths and
                                 inventory_input_limit(x["path"]) and
                                 x["size"] > inventory_input_limit(x["path"])],
        "reapack": {
            "settings_file_saved": "reapack.ini" in paths,
            "data_files_saved": sum(1 for x in portable if x.lower().startswith("reapack/")),
            "repository_index_urls": repo_urls,
            "profile": profile,
            "registry": registry,
            "repository_states": (
                "parsed-from-reapack-ini" if profile["status"] == "parsed"
                else "not-parsed-preserved-in-original-settings"
            ),
            "global_options": profile["options"],
            "automatic_sync": False,
        },
        "native_extensions": native,
        "midi_workflow": {
            "right_click_menu_files": menu_files,
            "keymap_files": keymap_files,
            "custom_actions_saved": "reaper-kb.ini" in portable,
            "custom_toolbar_settings_saved": "reaper-menu.ini" in portable,
            "dependency_resolution": "static-action-and-script-audit",
            "validation": validate_midi_workflow(source, items, control=control) if include_midi else None,
        },
        "sws_settings": sorted(
            x for x in portable if x.lower() in ("s&m.ini", "br.ini", "sws-autocoloricon.ini")
        ),
    }


def inventory_input_limit(relative):
    """Only parser inputs need a byte-identical private copy; scripts stay paths."""
    lower = relative.lower()
    if lower in ('reapack/registry.db', 'reapack/registry.db-wal', 'reapack/registry.db-journal'):
        return 128 * 1024 * 1024
    if lower == 'reapack.ini':
        return MAX_REAPACK_INI_BYTES
    if (lower in ('reaper-kb.ini', 'reaper-menu.ini') or
            lower.startswith('keymaps/') and lower.endswith('.reaperkeymap') or
            lower.startswith('menusets/') and lower.endswith('.reapermenu')):
        return 8 * 1024 * 1024
    return 0


def audit_reapack(source, *, control=None):
    """Resource-boundary checked GUI/CLI audit, without reading linked parents."""
    from .core import scan
    result = build_inventory(Path(source).expanduser().resolve(strict=True), scan(source, control=control), control=control, include_midi=False)["reapack"]
    return {"profile": result["profile"], "registry": result["registry"]}
