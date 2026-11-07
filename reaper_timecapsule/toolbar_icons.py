"""Static MIDI toolbar binding audit, based on REAPER 7.84 native output.

An absent resource PNG may be supplied by REAPER/theme installation: it is a
review finding, never proof that the installed toolbar is broken.
"""
import re
from pathlib import PureWindowsPath

from .operation import checkpoint
from .safe_paths import trusted_resource_file

MAX_DETAILS = 100
MIDI_TOOLBAR = re.compile(r'(?:floating midi toolbar [1-9][0-9]*|midi piano roll toolbar)', re.I)
BINDING = re.compile(r'(item|icon)_([0-9]+)\s*=\s*(.*)', re.I)


def audit_toolbar_icons(source, menus, saved, *, control=None):
    findings, count, bindings, available = [], 0, 0, 0
    def issue(file, section, index, reason, icon=None):
        nonlocal count
        count += 1
        if len(findings) < MAX_DETAILS:
            row = dict(file=file, toolbar=section, button=index, reason=reason)
            # Do not echo arbitrary absolute paths/private content.
            if icon is not None and '/' not in icon and '\\' not in icon and len(icon) < 256:
                row['icon'] = icon
            findings.append(row)
    for filename, text in menus:
        sections, current = [], None
        for line in text.splitlines():
            checkpoint(control, 'Checking MIDI toolbar icons')
            stripped = line.strip()
            if stripped.startswith('[') and stripped.endswith(']'):
                name = stripped[1:-1]
                current = ({'name': name, 'item': {}, 'icon': {}, 'duplicates': set()}
                           if MIDI_TOOLBAR.fullmatch(name) else None)
                if current is not None:
                    sections.append(current)
                continue
            match = BINDING.fullmatch(stripped)
            if match and current is not None:
                kind, index, value = match.groups()
                if len(index) > 9:
                    issue(filename, current['name'], None, 'unsupported-button-index')
                    continue
                kind, index = kind.lower(), int(index)
                if index in current[kind]:
                    current['duplicates'].add(index)
                current[kind][index] = value
        names = set()
        for section in sections:
            name = section['name']
            if name.casefold() in names:
                issue(filename, name, None, 'duplicate-toolbar-section')
            names.add(name.casefold())
            for index, icon in section['icon'].items():
                checkpoint(control, 'Resolving MIDI toolbar icons')
                bindings += 1
                if index in section['duplicates']:
                    issue(filename, name, index, 'duplicate-binding')
                    continue
                if index not in section['item']:
                    issue(filename, name, index, 'icon-without-button')
                    continue
                # Native text icons require no PNG. Other non-PNG encodings
                # remain unverified rather than being guessed.
                if icon in ('text', 'text_wide'):
                    continue
                if (not icon or '/' in icon or '\\' in icon or ':' in icon
                        or PureWindowsPath(icon).drive or icon in ('.', '..')
                        or not icon.lower().endswith('.png')):
                    issue(filename, name, index, 'unsupported-or-unsafe-icon-reference')
                    continue
                relative = 'Data/toolbar_icons/' + icon
                if relative not in saved:
                    issue(filename, name, index, 'not-in-backup-or-provided-by-installation', icon)
                    continue
                try:
                    path = trusted_resource_file(source, relative)
                    # Presence only; never decode or execute an image/plugin.
                    if path.stat().st_size == 0:
                        raise ValueError('empty icon')
                    available += 1
                except (ValueError, OSError):
                    issue(filename, name, index, 'unreadable-or-linked-icon', icon)
    return dict(status='needs-review' if count else 'checked' if bindings else 'not-checked',
                bindings_checked=bindings, saved_icons_available=available,
                issue_count=count, issues=findings, truncated=count > len(findings),
                reason='Static resource-file presence only; installed/theme icons and visual rendering require REAPER validation.')
