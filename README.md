# REAPER Time Capsule

Official application name: **REAPER Time Capsule**. Development builds use this
name; the published beta download filenames below retain their original names.
[Current audit review and priorities](docs/AUDIT_REVIEW_2026-10-11.md).

**Preserve your REAPER setup. Restore with confidence.**

An open-source tool for offline REAPER resource backups, archive verification and
careful recovery on another machine. Keep portable files together and separate
settings that need manual review.

[Magyar](README_HU.md)

![REAPER Time Capsule 0.9.0-beta.2 on macOS showing Scan / Preview results](docs/screenshots/time-capsule-main-macos.png)

*Actual macOS screenshot supplied by the project owner, October 11, 2026.
Scan / Preview lists a filename portability issue; this is not a completed backup.*

![REAPER Time Capsule About window on macOS](docs/screenshots/time-capsule-about-macos.png)

*Development build About window with the new floppy icon, GYR logo and graphic signature. These UI changes are not yet included in the published beta download.*

> **[Download 0.9.0-beta.2](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/tag/v0.9.0-beta.2)**
> — an unsigned public beta. This is a resource snapshot and recovery tool;
> complete one-click REAPER reinstallation is not implemented. Keep an independent backup.

## Download

Download packages from this project's [GitHub Releases](https://github.com/RobCZart82/REAPER-TimeCapsule/releases).

| Platform | Application |
|---|---|
| macOS · Apple Silicon (arm64) | [Unsigned application ZIP](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/download/v0.9.0-beta.2/REAPER-TimeCapsule-0.9.0-beta.2-Darwin-arm64-unsigned.zip) |
| Windows · x64 | [Unsigned application ZIP](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/download/v0.9.0-beta.2/REAPER-TimeCapsule-0.9.0-beta.2-Windows-AMD64-unsigned.zip) |
| Linux | [Source and release notes](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/tag/v0.9.0-beta.2) · Python 3.10+ |

Both application ZIPs include matching source, GPL and runtime license notices,
a bundled self-test report and documentation. The release also provides
[SHA-256 checksums](https://github.com/RobCZart82/REAPER-TimeCapsule/releases/download/v0.9.0-beta.2/SHA256SUMS.txt)
and platform build manifests. Windows source uses CRLF line endings.
Development on `main` may differ from the published packages.


### Development: traversal and destination safety

Directory traversal and file-metadata errors abort scanning/backup; no successful
archive is published from that failed scan. Symbolic links, Windows reparse points
and special entries are listed as excluded in `skipped_entries` and the manifest’s
omitted list. Their targets are not followed or copied; zero size means the target
content was not measured. Review these omissions before relying on a backup.

Backup resolves and pins the actual destination parent, rejects aliases into the
source, and rechecks the parent before exclusive publication. This is not a
transactional filesystem snapshot or protection against arbitrary hostile directory
replacement. Snapshot-consistent inventory and inventory-reader boundaries remain
separate fixes. These changes are on main, not in the published beta.

### Development: archived inventory and restore preview

New backups build their ReaPack/MIDI inventory from private copies of the exact
bytes written to the ZIP, not from later live source reads. Copies are removed
on success, cancellation or handled failure. Parser-size omissions are reported;
the original resource remains archived. This requires extra temporary disk space
for bounded parser inputs and is not a simultaneous filesystem snapshot.

Inventory and the resource-based ReaPack/MIDI audits reject linked parent paths.
Restore preview reports effective current policies, stored counts and explained
policy changes. Older inventories are labelled as having an unverified source
basis; their original files are preserved and current restore safety rules apply.
These changes are on main and are not yet in the published beta.

## Features

- File policies classify resources as `keep`, `review`, `regenerate` or `exclude`.
- Backups preserve portable Scripts, MenuSets, KeyMaps, LangPack, toolbar resources,
  themes, user presets, SWS configuration and selected ReaPack state.
- A ZIP manifest records SHA-256 hashes, omissions and platform information;
  verification checks every archived file.
- Recovery creates a new external folder, separating portable resources in
  `REAPER/` from uncertain configuration and native extensions in `NeedsReview/`.
- Background Backup, Verify and Restore offer per-phase progress and cooperative
  Cancel. One operation runs at a time; closing waits for completion or cleanup.
- Static MIDI audit checks menu Custom Action references against keymaps and
  `reaper-kb.ini`, reporting missing actions and missing or nonportable script paths.
- ReaPack 1.x audit reads repository names, order, URLs, enabled states,
  per-repository auto-install overrides and global options. Installed packages,
  versions and pinned versions are inventoried from the SQLite registry read-only.
- Read-only configuration and theme previews identify candidates and conflicts;
  explicitly selected preferences can be exported separately as review data.

Development on `main` starts every window at the approved action-row-based default
size without saving resized dimensions. Both directions are resizable, with a
minimum width that keeps the action row visible. Shared columns align the resource
fields and Browse buttons. Output lines do not wrap; horizontal and vertical
scrollbars appear only when needed. The bottom ↓ handle expands the output area
without changing the current width. These layout changes are not included in
the published 0.9.0-beta.2 packages. Main also adds a floppy application icon
with the REAPER symbol and a non-modal About window using the creator's GYR mark
and handwritten signature, without a civil-name text credit.

## System requirements

The macOS and Windows application downloads do not require Python or a compiler.
The published binaries target Apple Silicon and Windows x64 respectively; Intel
macOS and Windows ARM compatibility is not claimed. Linux is source-only.
Minimum OS and clean-machine acceptance are not fully validated; consult the
[first beta guide](docs/FIRST_BETA.md) and release manifests for actual build environments.

Source use requires Python 3.10+; the desktop interface also requires Tkinter/Tk.
Close REAPER before taking a resource snapshot and keep the source unchanged
throughout the operation. Portable REAPER installations need their own resource path.

## Installation and first backup

1. Download the ZIP for your platform and extract the complete package. Keep the
   application's companion files together. Start the included `.app` on macOS or
   `REAPER-TimeCapsule.exe` inside its application folder on Windows.
2. Close REAPER. Find its resource directory through REAPER's resource-path menu
   and choose that directory in Time Capsule.
3. Use **Scan / Preview**, then **Choose new backup ZIP** to select a new archive
   outside the resource directory. Choose **Backup** and wait for verification.
4. Use **Open existing snapshot** and **Verify** to inspect a saved archive.
5. Choose a recovery folder that does not yet exist, then **Restore**. Review
   `REAPER/`, `NeedsReview/` and the reports before manually importing resources.

These packages have no developer certificate or notarization. Gatekeeper or
SmartScreen may display warnings. Check the official download and checksum;
do not disable system security globally. See the [beta guide](docs/FIRST_BETA.md).

## Configuration and theme previews

**Config Preview** in the GUI and `config-preview` in the CLI compare explicitly
selected INI files and produce a redacted diff. Only exact approved section,
key and value combinations are candidates; unknown keys require review, while
hardware, platform, plugin-cache and private state are excluded. Neither input
nor the active REAPER resource directory is modified. No active merge is implemented.

`theme-preview` compares source, factory and target ColorThemes directories,
identifying byte-identical packed factory themes, modified variants, user themes
and destination conflicts. It does not copy, delete or omit backup files.

`config-stage` requires explicit opt-in, version records and exact preference
selections. It creates a new `.timecapsule-stage.zip` in a dedicated external
`TimeCapsule-Staging` directory. This contains preference data, reverse values and
fingerprints, not an installable `reaper.ini`. `verify-stage` checks integrity,
approval policy and optionally the target baseline. Neither command applies
settings or provides full rollback.

## Safety and limitations

Recovery never overwrites an existing destination or merges into the active
REAPER directory. Old VST/AU/CLAP scan caches and downloaded ReaPack indexes are
regenerated; the old installed-package registry is isolated in `NeedsReview/`.
Time Capsule does not synchronize ReaPack, edit its registry, install plugins or
native extensions, transfer licenses or download components automatically.

Registration/license files and obvious credentials are excluded from backups by
default. Inventory reports redact credentials in recognizable repository URLs;
original backed-up configuration can still be private. Keep your archives private
and do not attach full profiles or credentials to public issues.

Backup creation requires writable storage with hard-link support. FAT/exFAT
creation fails closed; create and verify locally, then copy the ZIP elsewhere.
Restore requires exclusive-rename support. Windows-invalid filenames,
case/Unicode collisions and file/directory conflicts are rejected on every
platform rather than renamed or dropped. Scan / Preview accepts native names
(such as macOS AU presets containing a colon) and reports portability issues
with file paths. Affected files remain listed; portable backup is blocked before
creating an archive. No silent exclusion or renaming is performed.

Cancellation waits for safe checkpoints and can arrive after final publication;
an already completed result is reported as success. Progress is per phase, not
an overall percentage or ETA. Audits and other scans remain synchronous. There
is no full transactional snapshot, power-loss durability or hostile filesystem-race
guarantee; unusual filesystems and path-length limits need further validation.

Static audits and green CI do not prove that every script, theme, extension or
MIDI workflow works inside REAPER. Keep an independent backup and review recovery
results in a fresh REAPER installation.

## Documentation

- [First beta guide and package limitations](docs/FIRST_BETA.md)
- [Backup policy](docs/REAPER_BACKUP_POLICY.md)
- [Configuration migration preview](docs/CONFIGURATION_MIGRATION.md)
- [Preference staging and verification](docs/CONFIGURATION_STAGING.md)
- [Theme migration preview](docs/THEME_MIGRATION.md)
- [MIDI Workflow Recovery](docs/MIDI_WORKFLOW_RECOVERY.md)
- [ReaPack Smart Recovery](docs/REAPACK_SMART_RECOVERY.md)
- [Release readiness](docs/RELEASE_READINESS.md) and [roadmap](docs/ROADMAP.md)

These detailed technical documents are currently English. This README and its
[Hungarian counterpart](README_HU.md) cover the same features, instructions and limitations.

## Running from source

From the extracted source directory, start the GUI or use the CLI:

```bash
python -m reaper_timecapsule gui
python -m reaper_timecapsule scan
python -m reaper_timecapsule midi-audit
python -m reaper_timecapsule reapack-audit
python -m reaper_timecapsule backup my-timecapsule.zip --source /path/to/REAPER
python -m reaper_timecapsule verify my-timecapsule.zip
python -m reaper_timecapsule restore my-timecapsule.zip RecoveredTimeCapsule
```

`scan`, `midi-audit` and `reapack-audit` accept an optional source directory.
Without one, they inspect the platform's default REAPER resource path.
Use explicit paths for portable installations. Preview and staging examples:

```bash
python -m reaper_timecapsule config-preview old.ini clean.ini --source-version 7.82 --target-version 7.82
python -m reaper_timecapsule theme-preview old/ColorThemes factory/ColorThemes clean/ColorThemes --source-version 7.82 --factory-version 7.82
python -m reaper_timecapsule config-stage old.ini clean.ini TimeCapsule-Staging/review.timecapsule-stage.zip --select REAPER/tinttcp --source-version 7.82 --target-version 7.82 --opt-in
python -m reaper_timecapsule verify-stage TimeCapsule-Staging/review.timecapsule-stage.zip --target clean.ini
```

Paths and REAPER versions above are examples; provide your actual selected inputs.
Run automated tests with `python -m unittest discover -s tests -v`.
The release passed 112 tests across macOS, Windows and Linux on Python 3.10/3.12;
both bundled desktop executables passed synthetic backup/verify/recovery and Tk
startup checks. This does not replace full REAPER integration testing.

## About and license

Developed by **RobCZart82**. Report bugs in [GitHub Issues](https://github.com/RobCZart82/REAPER-TimeCapsule/issues)
with the version, OS, architecture and reproduction steps using reduced or synthetic examples.

Time Capsule source is [GPL-3.0-only](LICENSE), provided without warranty.
Bundled runtimes retain their own terms; see [third-party notices](THIRD_PARTY_NOTICES.md).
REAPER, proprietary plugins, third-party script bundles, personal profiles and
registration keys are not distributed with this project. The project is not
affiliated with or endorsed by Cockos / REAPER.

MIDI Audit now reports duplicate/conflicting definitions, dependency cycles and unverified numeric commands. Resolving a menu reference does not prove its execution chain works in REAPER. Numeric commands remain unverified without an authoritative runtime action catalog.

Development audits now run on the shared background worker: Scan / Preview, MIDI Audit and ReaPack Audit keep the interface responsive and support cooperative cancellation. Read-only ReaPack SQL inspection has a five-second query budget and reports `timed-out` separately from invalid data. Cancellation can wait for an active operating-system file read; it is not forced thread termination.

Native filenames, including macOS colons, can now be preserved through an explicit schema-3 backup. Original-name restoration requires the same platform; optional portable recovery isolates all files and records a reversible name map. See [native filename recovery](docs/NATIVE_FILENAMES.md) for commands, GUI opt-in and compatibility limits.
