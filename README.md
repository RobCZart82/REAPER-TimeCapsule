# REAPER TimeCapsule 🎹

Cross-platform (macOS / Windows / Linux) **experimental** REAPER resource snapshot tool.
This is a **development preview**, not a complete one-click workflow migration utility.

## First milestone (`0.2.0-dev`)

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

## Run

```bash
python -m reaper_timecapsule scan
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
redistribution review are pending. See [roadmap](docs/ROADMAP.md).
