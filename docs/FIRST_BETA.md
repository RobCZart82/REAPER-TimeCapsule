# Public beta guide: 0.9.0-beta.2

## Scope

This beta offers offline resource snapshots, checksum verification, recovery into
a new external folder, static audits and read-only migration previews. It is not
one-click REAPER reinstallation. No active configuration merge, automatic plugin
installation or license transfer is included. Keep your original independent backup.

Standalone unsigned macOS/Windows builds do not require Python. Source use requires
Python 3.10+. Binary architecture and concrete runtime versions are recorded in
each build manifest. Builds are native to their runner; no universal macOS or
Windows ARM compatibility is claimed. Linux remains source-only.

## Basic use

1. Close REAPER and choose its resource folder (use REAPER's resource-path menu if
   you use a portable installation).
2. Select a NEW snapshot ZIP outside that folder and choose Backup.
3. Wait through copying and verification. A completed archive is published only
   after verification. A Cancel request waits for a safe checkpoint and cleanup.
4. Choose Verify to check a saved ZIP. Use the existing-archive Open button.
5. Choose a NEW recovery folder and Restore. Portable data is under REAPER/;
   uncertain configuration/native extensions are under NeedsReview/.
6. Review conflicts manually before importing anything into a clean, closed REAPER.

Progress is per phase (copying, verifying, restoring), not a global percentage or
ETA. Cancellation is cooperative: scans, metadata inspection and large reads may
not stop immediately. At the final publication boundary the operation can already
complete before the request is observed; a completed result is reported as success.
Never kill the process to emulate cancellation. Inputs should remain stable.

## Signing and limitations

These are unsigned beta distributions; macOS may show Gatekeeper warnings and
Windows may show SmartScreen warnings. No developer identity/notarization claim
is made. Do not disable system security globally. The user explicitly accepted an
unsigned first beta. Signing is a later release milestone.

Backup publication requires hard-link-capable storage; FAT/exFAT direct backup
creation fails closed. Use supported local storage then copy the verified archive
elsewhere. Restore requires the platform's exclusive-rename support. Incompatible
filenames and archives fail rather than being renamed/dropped. Scan accepts native
filenames and reports portability issues with paths; portable backup rejects them
before creating any archive, without renaming or silently excluding user files. Length limits and
unusual filesystems/portable layouts are not exhaustively validated.

Automated packaged tests use synthetic temporary profiles and instantiate Tk.
They do not prove every theme, script, ReaPack workflow or plugin functions inside
REAPER, and do not prove visual quality on every display. Audits/scans other than
backup/verify/restore remain synchronous. No full transactional profile snapshot,
power-loss durability or hostile filesystem-race guarantee is provided.

## License and source

Time Capsule is GPL-3.0-only. Each binary archive includes the matching tracked
source snapshot, GPL text, upstream runtime notices, build provenance, checksums
and self-test report. REAPER, proprietary plugins, personal profiles, licenses and
third-party workflow bundles are not shipped. Report bugs with synthetic/reduced
examples; do not attach credentials or full private resource folders.

## Publication checks

- All unit-test CI jobs pass for the exact release commit.
- Both native desktop builds and actual bundled executable self-tests pass.
- Artifact versions, source commit, checksums and runtime notices are inspected.
- Release notes clearly mark beta, unsigned status and limitations.
- Publishing private repository history is a separate explicit visibility decision.
