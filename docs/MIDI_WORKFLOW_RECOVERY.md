# MIDI Workflow Recovery (v0.4.0-dev)

This module **audits**, but does not install, import, run or silently repair, MIDI
Editor actions. It is designed for clean operating-system reinstalls, where
the old action definitions may refer to scripts or native extensions not yet
available on the new machine.

## Data sources

- `reaper-menu.ini`: active REAPER menus and toolbars when present.
- `MenuSets/*.ReaperMenu`: exported menu sets, including the MIDI piano-roll
  right-click chords/scales/arpeggios menu.
- `reaper-kb.ini`: registered Custom Actions and script action definitions.
- `KeyMaps/*.ReaperKeyMap`: exported action sets. **Keep matching Menu and
  KeyMap files together.** Do not import them independently in a clean REAPER.
- `Scripts/`: scripts that have been saved inside the REAPER resource directory.
- `UserPlugins/`: native extensions such as SWS and ReaPack (still quarantined
  under `NeedsReview/` on restore).

## How to run

```console
python -m reaper_timecapsule midi-audit
python -m reaper_timecapsule midi-audit "/path/to/REAPER"
```

Or use **MIDI Audit** in the Time Capsule desktop GUI.

The audit uses the **MIDI piano roll context** REAPER action section (32060).
It resolves `_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` identifiers against saved
`ACT` or `SCR` definitions, finds missing script files, and flags
absolute paths that would need remapping after an OS reinstall.

Other extension actions (for example SWS commands beginning with `_SWS`)
are recorded as **unverified**, not assumed available. Script presence does
not imply the script runs correctly, and matching Custom Action IDs do not
prove the toolbar/menu has been activated by REAPER.

The JSON report states `toolbar_icon_dependencies.status` as
`not-checked` and `runtime_validation.status` as `not-performed`. The saved
toolbar button-to-icon mapping is not currently parsed, so an icon directory or
matching action ID must not be treated as proof that every toolbar icon resolves.
The audit remains static and never executes scripts or loads extensions.

## Scope / known limitations

- No automatic import or action-ID remapping in this release.
- Other REAPER action sections beyond the MIDI piano-roll context are not
  automatically linked to context 32060.
- Dynamic scripts that construct commands at runtime are not analyzed.
- Toolbar button-to-icon references and missing icon files are not yet analyzed.
- Old absolute script paths are reported, not rewritten.
- Some REAPER custom-action formats could require additional parsing.
- A user-supplied Chords/Scales/Arps menu and matching KeyMap were validated
  **locally**: 120/120 menu Custom Action links matched. These third-party
  artifacts are intentionally **not committed** to this repository.
- The original REAPER resource directory is never modified during the audit.

## Restoring to a clean installation

1. Install REAPER for the destination OS and architecture; run once and exit.
2. Use Time Capsule restore into a **new empty folder**, not over the active
   REAPER settings. Review `RESTORE_REPORT.json`.
3. Ensure script dependencies and appropriate ReaPack/SWS extension versions
   are present. Inspect `NeedsReview/` manually.
4. Use a copy of the new REAPER resource folder while testing any imports.
5. Confirm the MIDI right-click menu and every relevant Custom Action in
   the actual REAPER MIDI Editor before relying on the new installation.

Do not upload a private REAPER resource archive to a public GitHub repository.

## Development action graph audit

Duplicates are reported within files and across exports/live definitions. Identical
duplicates require review; conflicting records or cycles produce invalid-action-graph.
All record variants are examined, so conflicts cannot hide earlier dependencies.
Numeric menu/action commands are unverified, not proof of missing commands.
Deep chains use iterative traversal; output samples are capped with total issue counts.
No scripts execute, no identifiers are rewritten, and no commands are installed.
