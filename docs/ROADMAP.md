# REAPER Time Capsule development roadmap

This page describes current `main` capabilities and the ordered work required
before the first stable `1.0.0` release. It is a development plan, not a release
announcement. Status was checked against GitHub on 2026-10-11: `main` is the default
branch, there are no open pull requests, and issues #3 and #4 remain open. The last
published version recorded by this project is `0.9.0-beta.2`; newer fixes on `main`
still need validation in fresh packaged applications. No `1.0.0` release is ready
or published.

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

## Ordered work before `1.0.0`

### 1. Lock the first-release scope

- The 1.0.0 core promise is a safe workflow to scan, back up, verify and restore a
  capsule into a new folder without replacing an existing destination.
- MIDI and ReaPack functions are static/read-only audits. Configuration migration
  is a read-only preview with optional external staging. These features must report
  what they did and what they could not verify.
- Keep active `reaper.ini` editing, automatic ReaPack installation/synchronization,
  script execution, and claims of end-to-end MIDI workflow compatibility outside
  1.0.0 unless their separate safety and validation requirements are completed.

### 2. Re-check restore and archive safety

- Current `main` rejects an empty snapshot selection and a directory supplied as a
  snapshot before verification or restore. This addresses the reported
  `[Errno 21] Is a directory: '/'` case caused by starting Restore without a ZIP.
- Verify the behavior in the packaged GUI, not only through unit tests. Cover an
  empty selection, directory, corrupt archive, existing destination, cancellation,
  and a valid backup/verify/restore cycle.
- Compare the restored files with the manifest and hashes. Run only against
  synthetic fixtures or disposable profiles; do not add the user's capsule or
  configuration to the repository.

### 3. Acceptance-test the current packaged GUI

- Build fresh macOS and Windows applications from the reviewed `main` commit.
- Exercise Scan / Preview, MIDI Audit, ReaPack Audit, Config Preview, Backup,
  Verify, Restore, full-report export, all file choosers, and cancellation.
- Recheck the earlier “Unexpected source path” report, long-output scrolling and
  responsiveness, plus the macOS native About menu and displayed version.
- CI already has synthetic bundled-app checks for oversized output and macOS About
  hook behavior. A clean-machine visual/manual pass is still required.

### 4. Finish or explicitly bound the MIDI audit (#3)

- Evaluate remaining ReaScript registration formats with synthetic fixtures and
  make sure summary counts stay complete when detailed findings are capped.
- Verify toolbar-to-icon parsing only if the saved file format and path rules are
  supported by reliable REAPER evidence. Otherwise keep the result explicitly
  `not-checked`.
- Keep numeric/external commands, runtime registration and action behavior marked
  unverified unless an isolated disposable REAPER test proves them. Never execute
  scripts or install extensions during a static audit.
- Close issue #3 only when its acceptance criteria are met or its remaining limits
  are clearly narrowed and documented for 1.0.0.

### 5. Preserve configuration-migration safety (#4)

- Keep the exact preference allowlist, hardware/platform/plugin/cache exclusions,
  unknown-value review, and explicit external staging behavior.
- Make clear that staged reverse values cover selected keys only; staging is not a
  complete destination backup or rollback snapshot.
- Do not add an apply-to-active-profile command for 1.0.0 without a separate design
  for explicit opt-in, complete verified external rollback, target fingerprint and
  conflict checks, atomic replacement, failure recovery, and disposable-profile
  tests. Keep issue #4 open while those criteria are incomplete.

### 6. Make report and ReaPack outcomes understandable

- Explain in the GUI and documentation which files are restored automatically and
  which are placed under `NeedsReview/`.
- State that the ReaPack database is review-only under current policy; its presence
  in a backup does not mean installed packages or registry state are activated.
- Confirm reports distinguish complete counts from capped detail lists, and clearly
  label checks that were not performed.

### 7. Refresh the English and Hungarian user documentation

- Keep both README languages equal in scope and detail, and update the illustrated
  PDF guides and screenshots to match the 1.0.0 interface.
- Explain the first-launch macOS flow for an unsigned application, including the
  operating-system approval prompts seen during testing. Distinguish those prompts
  from Time Capsule's normal operation and do not advise disabling platform
  protections.
- Document the standard backup, verify and new-folder restore flows, `NeedsReview/`,
  ReaPack review-only behavior, privacy of reports/capsules, and known limitations.
- Do not include personal paths, REAPER profiles, licenses, private reports, or DMGs.

### 8. Complete platform and CI checks

- Run the full Python test matrix and native macOS/Windows packaged-app self-tests
  on the release candidate. Fix all failures before merging or tagging.
- Protect `main` with pull-request-based changes and required green CI checks; block
  force-pushes and branch deletion. Review the repository rules before treating this
  gate as complete.
- Record supported platforms and filesystems accurately. Linux is source-only unless
  a desktop package and its acceptance tests are added; removable/network filesystem
  limitations must remain visible.
- Confirm GPL-3.0-only notices, app version/About text, icons, and artifact contents.

### 9. Prepare and validate a release candidate

- Bump the application version to `1.0.0`, update the changelog, release notes,
  download links and bilingual documentation together.
- Build from the reviewed `main` commit. Publish checksums for each downloadable
  artifact and state clearly whether it is signed/notarized; do not imply signing
  that has not occurred.
- Install and exercise the candidate on clean supported macOS and Windows systems,
  with a disposable REAPER profile. Verify the actual downloaded packages, not only
  CI artifacts or source tests.

### 10. Apply the release go/no-go gate

Publish `1.0.0` only when all of the following are true:

- Required CI and packaged-app self-tests pass.
- The clean-machine backup, verification and restore acceptance tests pass on every
  supported desktop platform.
- No known critical or high-severity defect remains in the promised workflows.
- The release notes and both language guides match the shipped behavior and state
  the remaining MIDI, ReaPack, migration, signing and filesystem limitations.
- The release artifacts contain no personal REAPER data, licenses, user bundles or
  private test reports.

## Post-1.0.0 candidates

- ReaPack 2.x support requires source-format verification and independent fixtures.
- Applying staged preferences or providing full migration rollback is a separate
  high-risk feature and remains out of scope until issue #4's acceptance criteria
  can be met.
- Broader toolbar/action runtime validation is separate from the static MIDI audit
  and must use disposable REAPER profiles.
- Signing/notarization and additional packaged platforms can be revisited as
  distribution improvements; current release metadata must describe actual status.

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
