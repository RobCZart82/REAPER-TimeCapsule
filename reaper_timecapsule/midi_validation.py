"""Read-only MIDI Editor menu, custom-action and script dependency validator.

Checks saved REAPER configurations without running scripts or loading extensions.
An exported .ReaperMenu/.ReaperKeyMap pair is only examined when its files are
already inside the selected REAPER resource directory.
"""
from __future__ import annotations

from .safe_paths import trusted_resource_file

import re
from pathlib import Path, PurePosixPath, PureWindowsPath

MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_ISSUES = 100
RE_GUID = re.compile(r"^_[0-9a-fA-F]{32}$")
RE_ACTION = re.compile(
    r'^(ACT|SCR)\s+\d+\s+(\d+)\s+"([a-fA-F0-9]{32})"\s+"(?:[^"\\]|\\.)*"(?:\s+(.*))?$',
    re.IGNORECASE,
)
RE_MENU_ITEM = re.compile(r"^item_\d+\s*=\s*(\S+)", re.IGNORECASE)


def _text(source: Path, relative: str, problems: list[dict]) -> str | None:
    """Bound the read and refuse symlinks. Legacy-encoded configs are tolerated."""
    file = source.joinpath(*relative.split("/"))
    try:
        file = trusted_resource_file(source, relative)
        if file.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError("file exceeds 8 MiB parser limit")
        return file.read_bytes().decode("utf-8-sig", errors="replace")
    except (OSError, ValueError) as exc:
        if len(problems) < MAX_ISSUES:
            problems.append({"file": relative, "problem": str(exc)})
        return None


def _action_records(text: str) -> dict[tuple[int, str], dict]:
    actions: dict[tuple[int, str], dict] = {}
    for line in text.splitlines():
        m = RE_ACTION.match(line.strip())
        if not m:
            continue
        kind, section, action_id, tail = m.groups()
        key = (int(section), "_" + action_id.lower())
        actions[key] = {"kind": kind.upper(), "tail": tail or ""}
    return actions


def _menu_records(text: str, filename: str) -> list[dict]:
    entries = []
    section_name = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1]
            continue
        m = RE_MENU_ITEM.match(line)
        if not m:
            continue
        command = m.group(1)
        # Action-section 32060 is the MIDI Editor piano roll. Other sections
        # cannot be mapped to 32060 safely without additional context.
        if not section_name.lower().startswith("midi piano roll"):
            continue
        if command.startswith("_"):
            entries.append({"file": filename, "section": 32060, "command": command.lower()})
    return entries


def _script_resolution(script_path: str, known_files: set[str]) -> str:
    path = script_path.strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    if not path:
        return "missing-path"
    if PureWindowsPath(path).is_absolute() or PurePosixPath(path).is_absolute() or path.startswith("~"):
        return "absolute-path-requires-remapping"
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if not parts or ".." in parts:
        return "invalid-relative-path"
    folded = {p.casefold() for p in known_files}
    if normalized.casefold() in folded or ("Scripts/" + normalized).casefold() in folded:
        return "saved"
    return "missing-from-backup"


def validate_midi_workflow(source: Path, items: list[dict]) -> dict:
    """Statically check custom MIDI menus and action registrations.

    Only the existence of named files and references is verified. A successful
    result does NOT attest that ReaPack/SWS binaries, command IDs or Lua
    scripts have been activated correctly by REAPER.
    """
    source = Path(source)
    saved = {x["path"] for x in items if x["policy"] == "keep"}
    problems: list[dict] = []
    menu_files = sorted(p for p in saved if (
        p.casefold() == "reaper-menu.ini" or
        (p.casefold().startswith("menusets/") and p.casefold().endswith(".reapermenu"))
    ))
    keymap_files = sorted(p for p in saved if (
        p.casefold().startswith("keymaps/") and p.casefold().endswith(".reaperkeymap")
    ))
    action_files = keymap_files + (["reaper-kb.ini"] if "reaper-kb.ini" in saved else [])

    definitions: dict[tuple[int, str], dict] = {}
    for filename in action_files:
        contents = _text(source, filename, problems)
        if contents is not None:
            definitions.update(_action_records(contents))

    references = []
    for filename in menu_files:
        contents = _text(source, filename, problems)
        if contents is not None:
            references.extend(_menu_records(contents, filename))

    external = set()
    missing = set()
    resolved = 0
    for reference in references:
        command = reference["command"]
        if not RE_GUID.fullmatch(command):
            external.add(command)
        elif (reference["section"], command) in definitions:
            resolved += 1
        else:
            missing.add((reference["file"], command))

    unverified = set()
    script_problems = set()
    checked_scripts = 0
    for (section, command), definition in definitions.items():
        if definition["kind"] == "SCR":
            checked_scripts += 1
            resolution = _script_resolution(definition["tail"], saved)
            if resolution != "saved":
                script_problems.add((command, resolution))
        else:
            for token in definition["tail"].split():
                if not token.startswith("_"):
                    continue
                token = token.casefold()
                if RE_GUID.fullmatch(token):
                    if (section, token) not in definitions:
                        missing.add(("Custom Action " + command, token))
                else:
                    unverified.add(token)

    if missing or script_problems:
        status = "missing-dependencies"
    elif problems or unverified or external or not references:
        status = "needs-review"
    else:
        status = "ok"

    return {
        "status": status,
        "action_definitions": len(definitions),
        "script_registrations_checked": checked_scripts,
        "menu_custom_references": len(references),
        "resolved_menu_references": resolved,
        "missing_custom_actions": [
            {"file": f, "command": a} for f, a in sorted(missing)[:MAX_ISSUES]
        ],
        "unverified_extension_commands": sorted(unverified | external)[:MAX_ISSUES],
        "script_registration_issues": [
            {"command": a, "reason": why} for a, why in sorted(script_problems)[:MAX_ISSUES]
        ],
        "parse_problems": problems[:MAX_ISSUES],
        "note": "Static inspection only: verify action registration and native extensions in REAPER after installing.",
    }
