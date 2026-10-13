"""Read-only MIDI Editor menu, custom-action and script dependency validator.

Checks saved REAPER configurations without running scripts or loading extensions.
An exported .ReaperMenu/.ReaperKeyMap pair is only examined when its files are
already inside the selected REAPER resource directory.
"""
from __future__ import annotations

from .operation import checkpoint
from .safe_paths import trusted_resource_file

import re
from pathlib import Path, PurePosixPath, PureWindowsPath

MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_ISSUES = 100
RE_GUID = re.compile(r"^_[0-9a-fA-F]{32}$")
RE_SCRIPT_ID = re.compile(r"^_RS(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{4}_[0-9a-fA-F]{40})$", re.IGNORECASE)
RE_ACTION = re.compile(
    r'^(ACT|SCR)\s+\d+\s+(\d+)\s+"([a-fA-F0-9]{32})"\s+"(?:[^"\\]|\\.)*"(?:\s+(.*))?$',
    re.IGNORECASE,
)
RE_SCRIPT_ACTION = re.compile(
    r'^SCR\s+\d+\s+(\d+)\s+(RS(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{4}_[0-9a-fA-F]{40}))\s+'
    r'"(?:[^"\\]|\\.)*"\s+"((?:[^"\\]|\\.)*)"$',
    re.IGNORECASE,
)
RE_MENU_ITEM = re.compile(r"^item_\d+\s*=\s*(\S+)", re.IGNORECASE)


def _record_problem(problems: list[dict], total: list[int], issue: dict) -> None:
    """Count every finding while bounding potentially large detail lists."""
    total[0] += 1
    if len(problems) < MAX_ISSUES:
        problems.append(issue)


def _text(source: Path, relative: str, problems: list[dict], problem_count: list[int]) -> str | None:
    """Bound the read and refuse symlinks. Legacy-encoded configs are tolerated."""
    file = source.joinpath(*relative.split("/"))
    try:
        file = trusted_resource_file(source, relative)
        if file.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError("file exceeds 8 MiB parser limit")
        with file.open("rb") as stream:
            data = stream.read(MAX_TEXT_BYTES + 1)
        if len(data) > MAX_TEXT_BYTES:
            raise ValueError("file exceeds 8 MiB parser limit")
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            _record_problem(problems, problem_count, {
                "file": relative,
                "problem": "Invalid UTF-8 bytes replaced for static inspection; text encoding is uncertain.",
                "encoding": "utf-8-sig",
                "decoding": "replacement",
            })
            return data.decode("utf-8-sig", errors="replace")
    except (OSError, ValueError) as exc:
        _record_problem(problems, problem_count, {"file": relative, "problem": str(exc)})
        return None


def _action_records(text: str, filename: str, problems: list[dict], problem_count: list[int], control=None):
    records = []
    for number, line in enumerate(text.splitlines(), 1):
        checkpoint(control, "Parsing MIDI actions", number, 0)
        stripped = line.strip()
        m = RE_ACTION.match(stripped)
        if not m:
            script = RE_SCRIPT_ACTION.match(stripped)
            if script:
                section, action_id, script_path = script.groups()
                key = (int(section), "_" + action_id.lower())
                records.append((key, {"kind": "SCR", "tail": script_path,
                                      "file": filename, "line": number}))
                continue
            if re.match(r'^(ACT|SCR)\s', stripped, re.IGNORECASE):
                _record_problem(problems, problem_count,
                                {"file": filename, "line": number,
                                 "problem": "Unrecognized action record"})
            continue
        kind, section, action_id, tail = m.groups()
        key = (int(section), "_" + action_id.lower())
        records.append((key, {"kind": kind.upper(), "tail": tail or "",
                              "file": filename, "line": number}))
    return records


def _action_cycles(graph, control=None):
    """Return bounded cycle witnesses and the complete DFS back-edge count.

    The count detects cyclic dependencies; it is not an enumeration of all
    simple cycles. Iterative DFS avoids recursion limits on deep action chains.
    """
    state, cycles = {}, []
    count = 0
    for origin in sorted(graph):
        if state.get(origin):
            continue
        path, positions = [origin], {origin: 0}
        state[origin] = 1
        stack = [(origin, iter(sorted(graph[origin])))]
        while stack:
            checkpoint(control, "Checking MIDI dependency graph")
            node, neighbours = stack[-1]
            child = next(neighbours, None)
            if child is None:
                stack.pop()
                state[node] = 2
                positions.pop(node)
                path.pop()
            elif state.get(child) == 1:
                count += 1
                if len(cycles) < MAX_ISSUES:
                    cycle = path[positions[child]:] + [child]
                    cycles.append({"section": child[0], "commands": [x[1] for x in cycle[:MAX_ISSUES]],
                                   "length": len(cycle), "truncated": len(cycle) > MAX_ISSUES})
            elif child in graph and not state.get(child):
                state[child] = 1
                positions[child] = len(path)
                path.append(child)
                stack.append((child, iter(sorted(graph[child]))))
    return cycles, count


def _menu_records(text: str, filename: str, control=None) -> list[dict]:
    entries = []
    section_name = ""
    for line in text.splitlines():
        checkpoint(control, "Parsing MIDI menus")
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
        if command.startswith("_") or command.isdecimal() and int(command) > 0:
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


def validate_midi_workflow(source: Path, items: list[dict], *, control=None) -> dict:
    """Statically check custom MIDI menus and action registrations.

    Only the existence of named files and references is verified. A successful
    result does NOT attest that ReaPack/SWS binaries, command IDs or Lua
    scripts have been activated correctly by REAPER.
    """
    checkpoint(control, "Inspecting MIDI workflow")
    source = Path(source)
    saved = {x["path"] for x in items if x["policy"] == "keep"}
    problems: list[dict] = []
    problem_count = [0]
    menu_files = sorted(p for p in saved if (
        p.casefold() == "reaper-menu.ini" or
        (p.casefold().startswith("menusets/") and p.casefold().endswith(".reapermenu"))
    ))
    keymap_files = sorted(p for p in saved if (
        p.casefold().startswith("keymaps/") and p.casefold().endswith(".reaperkeymap")
    ))
    action_files = keymap_files + (["reaper-kb.ini"] if "reaper-kb.ini" in saved else [])

    definitions: dict[tuple[int, str], dict] = {}
    all_records, duplicates = [], []
    for filename in action_files:
        checkpoint(control, "Reading MIDI registrations")
        contents = _text(source, filename, problems, problem_count)
        if contents is not None:
            for key, record in _action_records(contents, filename, problems, problem_count, control):
                previous = definitions.get(key)
                if previous is not None:
                    duplicates.append({"section": key[0], "command": key[1],
                                       "first_file": previous["file"], "first_line": previous["line"],
                                       "file": record["file"], "line": record["line"],
                                       "conflicting": (previous["kind"], previous["tail"]) != (record["kind"], record["tail"])})
                else:
                    definitions[key] = record
                all_records.append((key, record))

    references = []
    for filename in menu_files:
        checkpoint(control, "Reading MIDI menus")
        contents = _text(source, filename, problems, problem_count)
        if contents is not None:
            references.extend(_menu_records(contents, filename, control))

    external = set()
    numeric = set()
    missing = set()
    resolved = 0
    for reference in references:
        checkpoint(control, "Checking MIDI references")
        command = reference["command"]
        if command.isdecimal():
            numeric.add((reference["section"], command))
        elif not RE_GUID.fullmatch(command) and not RE_SCRIPT_ID.fullmatch(command):
            external.add(command)
        elif (reference["section"], command) in definitions:
            resolved += 1
        else:
            missing.add((reference["file"], command))

    unverified = set()
    script_problems = set()
    checked_scripts = 0
    graph = {key: set() for key in definitions}
    for (section, command), definition in all_records:
        checkpoint(control, "Checking MIDI registrations")
        if definition["kind"] == "SCR":
            checked_scripts += 1
            resolution = _script_resolution(definition["tail"], saved)
            if resolution != "saved":
                script_problems.add((command, resolution))
        else:
            for token in definition["tail"].split():
                checkpoint(control, "Checking MIDI dependencies")
                if token.isdecimal():
                    numeric.add((section, token))
                    continue
                if not token.startswith("_"):
                    _record_problem(problems, problem_count,
                                    {"file": definition["file"], "line": definition["line"],
                                     "problem": "Unrecognized action dependency"})
                    continue
                token = token.casefold()
                if RE_GUID.fullmatch(token) or RE_SCRIPT_ID.fullmatch(token):
                    if (section, token) not in definitions:
                        missing.add(("Custom Action " + command, token))
                    else:
                        graph[(section, command)].add((section, token))
                else:
                    unverified.add(token)

    cycles, cycle_count = _action_cycles(graph, control)
    if cycle_count or any(x["conflicting"] for x in duplicates):
        status = "invalid-action-graph"
    elif missing or script_problems:
        status = "missing-dependencies"
    elif problems or unverified or external or numeric or duplicates or not references:
        status = "needs-review"
    else:
        status = "ok"

    return {
        "status": status,
        "toolbar_icon_dependencies": {
            "status": "not-checked",
            "reason": "Toolbar button-to-icon bindings are not parsed; icon-file presence does not prove that referenced icons resolve.",
        },
        "runtime_validation": {
            "status": "not-performed",
            "reason": "No REAPER action registration, extension loading, script execution or toolbar activation was tested.",
        },
        "action_definitions": len(definitions),
        "script_registrations_checked": checked_scripts,
        "menu_custom_references": sum(x["command"].startswith("_") for x in references),
        "duplicate_definitions": duplicates[:MAX_ISSUES],
        "dependency_cycles": cycles,
        "cycle_count_semantics": "DFS back edges; not all simple cycles. Cycle witnesses may be truncated.",
        "unverified_numeric_commands": [{"section": section, "command": cmd}
                                        for section, cmd in sorted(numeric)[:MAX_ISSUES]],
        "issue_counts": {"duplicates": len(duplicates), "cycles": cycle_count,
                         "unverified_numeric": len(numeric), "missing": len(missing),
                         "script_issues": len(script_problems),
                         "parse_problems": problem_count[0]},
        "issue_detail_limit": MAX_ISSUES,
        "truncated_issue_details": {
            "duplicates": len(duplicates) > MAX_ISSUES,
            "cycles": cycle_count > len(cycles),
            "unverified_numeric": len(numeric) > MAX_ISSUES,
            "missing": len(missing) > MAX_ISSUES,
            "script_issues": len(script_problems) > MAX_ISSUES,
            "extension_commands": len(unverified | external) > MAX_ISSUES,
            "parse_problems": problem_count[0] > len(problems),
        },
        "resolved_menu_references": resolved,
        "missing_custom_actions": [
            {"file": f, "command": a} for f, a in sorted(missing)[:MAX_ISSUES]
        ],
        "unverified_extension_commands": sorted(unverified | external)[:MAX_ISSUES],
        "script_registration_issues": [
            {"command": a, "reason": why} for a, why in sorted(script_problems)[:MAX_ISSUES]
        ],
        "parse_problems": problems[:MAX_ISSUES],
        "note": "Static inspection only. Toolbar/icon bindings are not checked; verify action registration, icons and native extensions in REAPER after installing.",
    }

