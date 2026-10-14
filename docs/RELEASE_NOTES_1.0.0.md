# REAPER Time Capsule 1.0.0

First stable release of REAPER Time Capsule, licensed GPL-3.0-only. The Windows x64 and macOS Apple Silicon application packages are unsigned and include their matching source snapshot, license notices, documentation, build manifest and bundled self-test report. Linux remains source-only.

## Highlights

- Create an offline ZIP snapshot of portable REAPER resources, verify every archived file against SHA-256, and restore into a new folder without overwriting existing data.
- Inspect file policies, MIDI actions, ReaPack state, and selected configuration/theme settings with read-only previews and reports.
- Preserve supported native filenames in the opt-in schema-3 archive format; restoring original native names requires a compatible platform. Portable extraction is available with an explicit reversible filename mapping.
- Improve Windows long-path restore handling and selection of redirected/localized Desktop folders.
- Provide responsive, cancellable GUI operations, bounded report previews, complete private report export, and branded About information.

## Scope and limitations

This is a resource backup and recovery tool, not a complete REAPER migration or reinstall system. It does not install plugins or native extensions, transfer plugin licenses, synchronize ReaPack, run MIDI actions inside REAPER, or apply configuration changes to an active REAPER installation. Review `NeedsReview/` and all inspection omissions before using recovered files.

The Windows x64 and macOS Apple Silicon packages are unsigned; Windows SmartScreen or macOS Gatekeeper may show a warning. Intel macOS and Windows ARM are not claimed. Linux is source-only. Clean-machine installation and unusual-volume validation (including FAT/exFAT and network volumes) have not been completed. Use a supported local filesystem and keep an independent backup.

## Validation evidence

The release CI runs the cross-platform source test suite and builds/tests each bundled desktop executable. The maintainer reported a successful Windows 11 x64 Intel real-profile workflow, including Restore (7,035 portable files restored, 32 isolated for review, no legacy skips or inspection omissions); the supplied archive passed CRC and all 7,067 manifest SHA-256 checks. The maintainer also reported successful end-to-end GUI workflows on macOS; no separate macOS report or archive was supplied for independent count/hash verification. These are targeted user-machine tests, not clean-machine acceptance. See [release readiness](docs/RELEASE_READINESS.md) and [roadmap](docs/ROADMAP.md) for the exact evidence and remaining limits.
