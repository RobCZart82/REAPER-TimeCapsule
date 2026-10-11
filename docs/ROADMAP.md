# REAPER Time Capsule development roadmap

This page describes current `main` capabilities and the remaining work before a
broader public release. It is not a release announcement. The owner asked to keep
accumulating reviewed changes on `main` and publish a later beta only after several
development steps are complete.

## Current capabilities

- Scan a REAPER resource folder, explain file policies, create and verify a
  checksummed capsule, and restore into a new folder without replacing an existing
  destination.
- Report traversal errors, links, reparse points and unsupported names rather than
  silently following or dropping them. Native-name capsule mode is an explicit
  alternative; portable recovery isolates nonportable resources and records their
  mapping.
- Build ReaPack 1.x profile and installed-package reports from recognized
  `reapack.ini` and SQLite formats. Repository order/enabled states and global
  options are inspected read-only; old registry/cache state is not activated.
- Run static MIDI menu and Custom Action checks for duplicate IDs, dependency
  cycles, unresolved references, script paths and unverified numeric/extension
  commands. The audit does not install or execute anything.
- Compare `reaper.ini` files read-only using an exact two-preference allowlist;
  unknown and machine-specific state stays review/excluded. An opt-in staging ZIP
  can carry only selected approved preference data and reverse values. Verification
  is read-only; no command applies this data to REAPER.
- Compare packed themes with an explicitly supplied factory reference without
  copying or deleting anything.
- Run long operations in a background worker. Large GUI output is shortened in a
  display-only copy and rendered in bounded chunks; full scan policy rows remain in
  File policies and CLI report output is complete.
- Build unsigned macOS and Windows beta packages. Linux is source-only. GPL-3.0-only
  and bilingual user documentation have been selected/prepared.

See [the current audit status](AUDIT_REVIEW_2026-10-11.md), [release readiness](RELEASE_READINESS.md)
and the linked issue for each remaining area.

## Ordered development work

### 1. GUI large-report follow-up

- The UI-freeze fix is on `main` in PR #44: bound display data to 256 KiB and insert
  no more than 8 KiB per UI callback.
- The macOS and Windows bundled executable self-tests render a synthetic over-limit
  report and require the truncation notice plus both scrollbars. This covers packaged
  Tk behavior in CI; a visual human check on clean machines remains.
- If the GUI report cap is reached, direct users to the complete local CLI report;
  never silently imply the shortened display is the complete audit.

### 2. ReaPack scope and compatibility

- Keep the verified read-only ReaPack 1.x profile parser and SQLite inventory.
- The read-only ReaPack 1.x work tracked in issue #2 is implemented; keep 2.x,
  package installation and synchronization as separate future work.
- ReaPack 2.x support needs its own verified source-format review and fixtures.
- No repository sync, package download, registry activation or extension install
  without a separately designed explicit opt-in workflow.

### 3. MIDI workflow completeness

- Extend static checking to toolbar/icon references only where the native file
  format and path rules are supported by reliable evidence.
- Keep missing extension binaries, command registration and script execution as
  unverified/manual steps; never execute scripts during an audit.
- Design an isolated disposable REAPER integration test environment before making
  claims that a restored MIDI workflow works end-to-end. Do not commit user bundles
  or copyrighted third-party scripts without redistribution permission.

### 4. Configuration migration safety

- Keep preview and staging verification read-only; continue excluding platform,
  hardware/device, plugin/cache, license and unknown settings.
- Expand the preference allowlist only with exact section/key/value/version
  evidence and isolated runtime validation. Similar names or theme directives are
  not enough.
- Any future apply command requires a separate reviewable design for explicit opt-in,
  an external backup/rollback snapshot, current-target fingerprint and conflict
  handling, atomic replacement, cancellation recovery and tests against temporary
  synthetic files. Never use the developer's real REAPER config as a test input.
- Keep issue #4 open until rollback and a fully tested apply/recovery workflow exist.

### 5. Prepare the next beta after implementation accumulates

- Update both-language PDFs and screenshots to match the then-current GUI and
  explain first-launch macOS Gatekeeper steps without recommending disabling
  platform protections.
- Validate the exact release candidate on clean macOS and Windows environments,
  including the large-report GUI, file chooser behavior, backup/verify/restore,
  app icon and About dialog.
- Reconcile version, changelog, README/About screenshots, artifact checksums and
  documented platform/filesystem limitations. Build the release from the reviewed
  `main` commit and retain the unsigned-beta disclosure.
- Do not publish a new release until these checks are complete and the accumulated
  milestones are ready.

## Guarantees and limits

- No automatic overwrite of an active REAPER resource folder; restore targets a new
  location.
- No executing untrusted scripts, installing extensions, downloading ReaPack
  packages, or uploading personal REAPER profiles, license files or DMGs.
- Checksums are not encryption, signatures or proof of origin. Capsules can contain
  private configuration and filenames and should be stored accordingly.
- Filesystem capacity checks are estimates. Crash durability, every removable or
  network filesystem, complete metadata preservation and every customized REAPER
  environment are not guaranteed.
- Green synthetic CI is necessary but does not replace clean-machine or isolated
  real-REAPER acceptance testing.
