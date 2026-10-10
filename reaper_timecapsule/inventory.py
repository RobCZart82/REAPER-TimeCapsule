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
from .reapack_profile import inspect_registry, parse_profile

MAX_REAPACK_INI_BYTES = 2 * 1024 * 1024
MAX_URLS = 1000
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", flags=re.IGNORECASE)
EXTENSION_SUFFIXES = (".dylib", ".dll", ".so")


def _public_repo_urls(ini_file: Path) -> list[str]:
    """Return display-safe repository index URLs; remove credentials/query/fragment.

    The original (possibly credential-bearing) configuration is left untouched.
    Disabled/enabled state MUST NOT be inferred from a bare URL match.
    """
    try:
        if ini_file.is_symlink() or ini_file.stat().st_size > MAX_REAPACK_INI_BYTES:
            return []
        raw = ini_file.read_bytes()
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


def build_inventory(source: Path, items: list[dict]) -> dict:
    """Inventory strictly from paths plus the configured ReaPack INI file."""
    source = Path(source)
    portable = {x["path"] for x in items if x["policy"] == "keep"}
    review = {x["path"] for x in items if x["policy"] == "review"}
    paths = portable | review
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
    profile = parse_profile(source / "reapack.ini") if "reapack.ini" in paths else parse_profile(source / "reapack.ini")
    registry = inspect_registry(source / "ReaPack" / "registry.db")
    # Legacy URL-only scan remains a compatibility fallback when an INI
    # predates the 1.x [remotes] section or uses an unknown format.
    repo_urls = ([x["index_url"] for x in profile["repositories"]]
                 if profile["status"] == "parsed" else
                 _public_repo_urls(source / "reapack.ini") if "reapack.ini" in paths else [])
    menu_files = sorted(
        x for x in portable if x.lower().startswith("menusets/") and x.lower().endswith(".reapermenu")
    )
    keymap_files = sorted(
        x for x in portable if x.lower().startswith("keymaps/") and x.lower().endswith(".reaperkeymap")
    )
    return {
        "format": "inventory-v1",
        "reapack": {
            "settings_file_saved": "reapack.ini" in paths,
            "data_files_saved": sum(1 for x in portable if x.lower().startswith("reapack/")),
            "repository_index_urls": repo_urls,
            "profile": profile,
            "registry": registry,
            "repository_states": (
                "parsed-from-reapack-ini" if profile["status"] == "parsed"
                else "unverified-original-settings-saved"
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
            "validation": validate_midi_workflow(source, items),
        },
        "sws_settings": sorted(
            x for x in portable if x.lower() in ("s&m.ini", "br.ini", "sws-autocoloricon.ini")
        ),
    }
