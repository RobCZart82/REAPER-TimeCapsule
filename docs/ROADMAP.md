# Roadmap / fejlesztési lépések

## Implemented in 0.2.0-dev
- Per-file backup policies with preview (keep/review/regenerate/exclude)
- Cross-platform REAPER resource-directory detection (default installations)
- No-overwrite compressed backup and SHA-256 manifest verification
- Safe restore into a NEW directory with machine-specific files isolated
- ReaPack / SWS settings preserved as source resources
- macOS, Windows and Linux CI workflow (runs after repository push)

## Completed in 0.3.0-dev
- Read-only ReaPack XML repository URL inventory from reapack.ini; display redacts credentials
- Inventory of native SWS/ReaPack plugin files without attempting installation
- MIDI right-click menus and KeyMap file presence tracked in snapshot manifest
- Recovery report records inventory for auditing

## Outstanding work from the early roadmap
- Support ReaPack v2 if/when its storage format is documented; compare repository state with a clean destination
- Detect exact installed ReaPack/SWS binaries, architecture and versions
- Add clean installation + configuration merge with a per-key REAPER.ini allowlist
- Enhance static action validation with REAPER runtime post-restore integration tests
- Assess MIDI workflow bundle redistribution permission before shipping it
- Snapshot exclusion policy UI and signed / auditable reports
- Verify saved ReaPack repository URLs are still current; do not auto-sync without permission

## Implemented in 0.4.0-dev (MIDI audit)
- Static validation of MIDI piano roll context menu Custom Action references against imported/registered action definitions
- Detection of missing scripts and registrations tied to old OS absolute paths
- Identification of external commands requiring ReaPack/SWS verification
- CLI `midi-audit` and GUI audit button; summary embedded in snapshot metadata
- Synthetic tests for successful/missing/wrong-section actions and script portability

## Implemented in 0.5.0-dev (ReaPack Smart Recovery: inspection)
- Parse ReaPack 1.x configured repository list and enabled/disabled states from the
  verified `[remotes] remoteN=name|URL|enabled|override` format.
- Preserve global option values with explicit-vs-default provenance.
- Read the installed package inventory from `ReaPack/registry.db` in SQLite
  read-only mode; never silently copy a stale database into an active fresh REAPER.
- Exclude old `ReaPack/cache/` downloaded indexes from clean migrations.
- Add `reapack-audit` CLI / GUI button and cross-platform regression tests.

## Implemented in 0.6.0-dev (Intelligent Configuration Migration: preview)
- Explicit-file, read-only reaper.ini diff with exact per-section/key/value allowlist.
- Appearance candidates, excluded machine/private state, unknown-key review.
- Version mismatch/unknown, missing keys and unsupported values require review.
- Fail-closed malformed input handling; no raw unknown values in reports/errors.
- Synthetic cross-platform tests run on the existing macOS/Windows/Linux matrix.
- GUI Config Preview with explicit file selection, cancellation and version prompts.
- Change counts distinguish conflicts, unchanged, source-only and target-only entries.
- Parser rejects ambiguous indentation and unsupported control characters.
- Issue #4 remains open: rollback and actual merge remain future work; factory
  comparison is available through the separate follow-up below. No staging export or in-place writer is introduced.

## Factory theme comparison follow-up
- Read-only `theme-preview` compares explicit source/factory/target directories.
- Byte-identical packed themes can be reviewed for factory reuse; modified and user
  themes are marked for preservation. Existing target conflicts always need review.
- Case-insensitive NFC filename matching with ambiguous-name rejection.
- Unpacked dependencies, unknown files and symlinks stay review-only.
- Backup and restore retain all previous behavior; no automatic deduplication.
- Issue #4 remains open for actionable restore/rollback and unpacked dependency handling.

## Implemented in 0.7 (selective preference staging)
- Separate CLI opt-in export with exact changed approved key selection.
- Exclusive new ZIP creation in a dedicated external TimeCapsule-Staging folder.
- Selected preference DATA and reverse values only; no full INI or unknown values.
- Input-content fingerprints; no writes to source/target or active resource files.
- Partial write failure cleanup of the archive owned by this operation.

## Implemented in 0.8.0-dev (staging verification)
- Read-only bounded ZIP verification without extraction.
- Exact members, checksum/content checks and current allowlist enforcement.
- Reject duplicate entries/JSON fields, unsupported values, versions and forged keys.
- Optional target fingerprint check detects changes after staging.
- These two milestones ship together; no apply/deploy command is provided.
- Full rollback snapshots, executable migration and staging GUI remain future work.

## Release readiness: backup publication hardening
- Replace check-then-rename backup publication with atomic exclusive hard-link creation.
- Preserve concurrent destination files/directories and reject dangling symlink targets.
- Unsupported destination filesystems fail closed, without rename/copy fallback.
- Regression tests cover concurrent creation, failure cleanup and verified success.
- Restore directory publication, cross-platform archive-name validation, GUI progress,
  real REAPER tests and native packaging remain release blockers.

## Release readiness: portable archive paths
- Preflight all indexed paths before restore creates a staging directory.
- Reject Windows reserved/invalid names, case/NFC collisions and file-directory conflicts.
- No automatic filename rewriting; valid Unicode resource paths are preserved.
- Older incompatible archives fail closed; length/filesystem limits remain future work.

## Release readiness: exclusive restore publication
- Native exclusive directory rename on macOS/Linux/Windows; no overwrite fallback.
- Competing empty directories/files preserved; unsupported-operation cleanup tested.
- Publication APIs exercised on each native CI platform.

## Later
- Native macOS app packaging and Windows executable + notarization/signing plans
- Managed backups and rollback snapshots; external drive workflows
- Portable REAPER resource installs; compare factory theme files against a matching build
- Automatic integration tests on a *temporary* REAPER installation

## Security constraints
- No upload of personal resource directories or license keys to GitHub
- No silent overwrite of user's active REAPER directory
- No executing untrusted scripts during archive inspection
