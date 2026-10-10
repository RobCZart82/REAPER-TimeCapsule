# REAPER TimeCapsule 🎹

Cross-platform (macOS / Windows / Linux) **experimental** REAPER resource snapshot tool.
This is a **development preview**, not a complete one-click workflow migration utility.
Do not use it as your only backup. Close REAPER before any resource snapshot.

## Current milestone (`0.8.0-dev`)

- Uses a policy engine to classify files as `keep`, `review`, `regenerate`, or `exclude`.
- Preserves portable REAPER Scripts, MenuSets, KeyMaps, ReaPack state, SWS configuration,
  LangPack, toolbar resources, themes, and user presets for backups.
- Does NOT import old VST/AU/CLAP plugin scans; rebuild those on the new machine.
- Excludes REAPER registration/license files and obvious credentials from backups by default.
- Saves uncertain machine-specific settings (`reaper.ini`, audio/MIDI devices, UserPlugins)
  but isolates them in `NeedsReview/` when restoring, **not** in the active REAPER folder.
- ZIP snapshots include `manifest.json` with SHA-256 hashes, omission decisions and
  platform information; verification checks every archived file.
- Restores only into a **nonexistent** destination folder by staging/rename; no overwrite,
  no automatic plugin installation, no silent merges into REAPER, no network downloads.
- GUI uses Tkinter; Python 3.10+ required until native .app/.exe builds exist.
- MIDI Editor dependency validator: compare menu Custom Action references with imported .ReaperKeyMap and reaper-kb.ini; report missing actions and missing/nonportable script paths. Results are visible in GUI, CLI and snapshot inventory.
- The validator performs **static inspection only**: it cannot prove runtime script correctness, extension availability or automatic import success.
- Read-only ReaPack/SWS/MIDI inventory embedded in snapshots: recognizable extension
  filenames, menu and keymap files, configured XML repository URLs (credentials redacted
  in the report). The original config is backed up, not edited.
- **ReaPack 1.x profile reader** reads actual repository names, order, URLs,
  enabled states, per-repository auto-install overrides and global options
  from `reapack.ini`; unknown formats are flagged rather than guessed.
- **Installed packages inventory** is read from the ReaPack SQLite registry in
  read-only mode. On clean restore the old registry is isolated in
  `NeedsReview/` and downloaded `ReaPack/cache/` indexes are regenerated.
- Never starts a ReaPack synchronization, writes the installed-package
  registry or installs a native extension without approval.

## Intelligent Configuration Migration (read-only preview)

`config-preview` compares two explicitly selected INI files and outputs a redacted
JSON diff. Only exact approved section/key/value combinations can be candidates;
unknown settings require review and hardware/platform/cache/private state is excluded.
The GUI **Config Preview** button provides the same comparison with explicit file
selection, optional version records and conflict counts.
Preview never writes either file or the REAPER resource folder. No active merge
is implemented. Separate opt-in preference DATA export and read-only verification
are available; see [staging and verification](docs/CONFIGURATION_STAGING.md). See [configuration migration](docs/CONFIGURATION_MIGRATION.md).

## Factory theme preview

`theme-preview` compares explicit source, factory and target ColorThemes folders.
It identifies byte-identical packed factory themes, modified variants, user themes
and destination conflicts. It never copies, deletes or omits backup files. See
[theme migration preview](docs/THEME_MIGRATION.md).

## Preference staging and verification (0.7 / 0.8)

`config-stage` requires explicit opt-in and exact changed preference selections.
It creates a new `.timecapsule-stage.zip` under a dedicated `TimeCapsule-Staging`
folder outside input and recognized REAPER directories. It contains selected
preference DATA, reverse values and fingerprints, not an installable reaper.ini.
`verify-stage` checks integrity, approval policy and optionally the current target
baseline. Neither command applies settings or supports full rollback.

## Run

```bash
python -m reaper_timecapsule config-preview old.ini clean.ini --source-version 7.82 --target-version 7.82
python -m reaper_timecapsule theme-preview old/ColorThemes factory/ColorThemes clean/ColorThemes --source-version 7.82 --factory-version 7.82
python -m reaper_timecapsule config-stage old.ini clean.ini TimeCapsule-Staging/review.timecapsule-stage.zip --select REAPER/tinttcp --source-version 7.82 --target-version 7.82 --opt-in
python -m reaper_timecapsule verify-stage TimeCapsule-Staging/review.timecapsule-stage.zip --target clean.ini
python -m reaper_timecapsule scan
python -m reaper_timecapsule midi-audit
python -m reaper_timecapsule reapack-audit
python -m reaper_timecapsule backup ~/Desktop/my-timecapsule.zip
python -m reaper_timecapsule verify ~/Desktop/my-timecapsule.zip
python -m reaper_timecapsule restore ~/Desktop/my-timecapsule.zip ~/Desktop/RecoveredTimeCapsule
python -m reaper_timecapsule gui
python -m unittest discover -s tests -v
```

Optional `--source /path/to/REAPER` with `backup`, or a source argument with `scan`.
**Close REAPER before backup or restore.**

## Migration safety

Restore produces `RecoveredTimeCapsule/REAPER/` for portable files, plus
`RecoveredTimeCapsule/NeedsReview/` for uncertain settings and native extensions.
This is **not** yet an automatic reinstallation procedure. Review its reports and use a
fresh REAPER installation to regenerate plugin caches and hardware settings.

Third-party script bundles, proprietary plugin executables, and REAPER registration
keys are **not included in this source repository**. A private backup of installed
components is different from legally redistributing them in a public GitHub repo.

This app isn't affiliated with or endorsed by Cockos / REAPER.

## Development status

Repository is intended to start **private**; source license and third-party
redistribution review are pending. See [roadmap](docs/ROADMAP.md),
[ReaPack Smart Recovery](docs/REAPACK_SMART_RECOVERY.md) and
[MIDI Workflow Recovery](docs/MIDI_WORKFLOW_RECOVERY.md).
