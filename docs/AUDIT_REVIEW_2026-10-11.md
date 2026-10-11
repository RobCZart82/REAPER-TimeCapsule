# REAPER Time Capsule — audit finding status

Reviewed against code at `6d6da95` (2026-10-11). The supplied audit examined an
older revision (`a56fde0`); its findings are useful historical evidence, but its
“still broken” labels and proposed work are not current status. This page tracks
what was confirmed, what has since changed, and what remains outside the product's
verified scope. Synthetic tests do not prove recovery of every real REAPER profile.

## Confirmed code defects now fixed

| ID | Current behavior | Evidence |
|---|---|---|
| TC-001 | Filesystem traversal and metadata errors stop a scan; backup does not publish a partial capsule. | `tests/test_scan_reliability.py`, `tests/test_traversal.py` |
| TC-002 | Links, reparse points and special entries are reported and excluded without following their targets. | `tests/test_scan_reliability.py`, `tests/test_symlink.py` |
| TC-004 | ReaPack and MIDI inventory parsers consume bounded bytes captured from the same stream as archived files, rather than reopening later source contents. | `tests/test_snapshot_inventory.py` |
| TC-005 | Verify/restore preview uses the effective restore policy, and reports changes from the stored choice. | `tests/test_restore_publication.py`, `tests/test_reapack_profile.py` |
| TC-006 | Resource readers validate the selected file and each parent component; linked parents and unsafe SQLite sidecars are rejected. | `tests/test_snapshot_inventory.py`, `tests/test_symlink.py` |
| TC-007 | MIDI checks report duplicate definitions, unverified numeric commands, unresolved dependencies and cycles instead of silently choosing a definition. | `tests/test_midi_validation.py` |
| TC-010 | Source/destination aliases are checked before backup publication; final ZIP and restore-directory publication use exclusive operations. | `tests/test_scan_reliability.py`, `tests/test_no_overwrite.py`, `tests/test_restore_publication.py` |
| TC-011 | Scan, MIDI/ReaPack audit, backup, verify and restore run on one background worker. Large GUI reports are copied into a bounded display preview and inserted in 8 KiB UI callbacks, up to 256 KiB. | `tests/test_background.py`; PR #44 |
| TC-018 | ReaPack SQLite inspection has size/row bounds, a query deadline and cooperative cancellation via SQLite progress handling. | `tests/test_audit_cancellation.py`, `tests/test_reapack_profile.py` |

For TC-011, this fixes the synchronous large-result display path implicated by the
reported GUI freeze. Long strings, lists, dictionaries and nested values can be
shortened in the GUI display copy. The full scan inventory remains available in
**File policies**, and CLI output is not shortened. Synthetic/headless tests verify
the bounds and scheduling; native macOS/Windows interaction with a very large live
MIDI audit still needs user-side smoke testing.

## Confirmed limitations and remaining work

| ID | Status and boundary |
|---|---|
| TC-003 | Native-name capsules and isolated portable recovery are available, including a local name-mapping report. Script/menu paths are not rewritten, resource activation is not automatic, and some names or destination filesystems remain unsupported. This is not a bit-for-bit filesystem image. |
| TC-008 | Resource guards now bound file counts, archive members, manifest and payload sizes, parser input, and estimated free space. Estimates are not reservations; filesystem quotas, arbitrary process exhaustion and every remote-volume behavior are not eliminated. See `RESOURCE_BUDGETS.md`. |
| TC-009 | Capsules are not encrypted or signed. SHA-256 detects content mismatch; it does not provide secrecy or prove who made a capsule. Keep backups private and use separately managed encryption if required. |
| TC-012 | Configuration migration deliberately approves only two documented binary `reaper.ini` preferences. Unknown, device, platform, plugin/cache and private state remain review/excluded. Expanding the allowlist requires exact key/value/version evidence and runtime validation. |
| TC-013 | MIDI audit is static. It does not install scripts/extensions, prove commands are registered at runtime, or test actions inside REAPER. Toolbar/icon dependencies and isolated REAPER integration tests remain open. Third-party action bundles are not redistributed. |
| TC-014 | ReaPack inspection supports verified 1.x configuration versions and a recognized SQLite registry schema. ReaPack 2.x is not claimed; package installation, downloads and synchronization are not performed. |
| TC-015 | Backup publication uses hard-link or native exclusive-rename primitives and fails closed when neither is supported. CI exercises platform primitives; real removable, FAT/exFAT and network volumes are not fully validated. |
| TC-016 | Scan reports are versioned and record inspection basis, summary, policy entries, inventory and manual steps. Reports are local/private and are not signed. Broader provenance and portable audit export are future work. |
| TC-017 | Restore preflights portable namespace conflicts and path limits conservatively. Very long paths, unusual filesystem limits and legacy aliases may still be rejected or require manual remediation. |
| TC-019 | Source timestamp and permission bits are informational. Restore uses fresh-file defaults; ACLs, ownership, extended attributes and Finder metadata are not preserved. |
| TC-020 | Free-space estimates and handled-error cleanup exist. A crash or forced termination can leave temporary data; no crash-durability or transaction guarantee is made. |
| TC-021 | Regression suites include malformed archives, boundary cases, races and synthetic failure injection. They are not a proof against every hostile concurrent filesystem change, nor a substitute for real-user-profile testing. |
| TC-022 | GitHub Actions references are pinned to reviewed commit SHAs. Runner images and bundled OS toolchains can still change; build artifacts are not reproducibly identical across time. |
| TC-023 | The owner accepted unsigned beta packages. Signing/notarization remains a distribution improvement, not a requirement for the already authorized beta. |
| TC-024 | License selection, bilingual documentation and illustrated beta guides are present. Before another beta, the PDF screenshots/instructions and release readiness details must match the then-current GUI. |

## Ordered remaining development

1. The read-only ReaPack 1.x parser tracked by issue #2 is implemented. Keep 2.x,
   package installation and synchronization as separate future work.
2. Extend the MIDI static audit to toolbar/icon references where the saved REAPER
   formats can be verified. Preserve the explicit warning that static presence is
   not runtime functionality; plan isolated REAPER smoke tests separately.
3. Keep configuration changes read-only by default. Add preference keys only when
   exact source evidence justifies them. Any future apply operation needs a new
   design for opt-in, target fingerprint/conflict checks, rollback and recovery;
   it must never run against a real user profile as a development test.
4. Refresh the bilingual user guide, screenshots, limitations and release notes
   together when the next beta scope is ready. No release is part of this work.

Historical findings were not adopted as requirements merely because the external
report listed them. Missing future features are distinct from demonstrated defects;
all real profiles, licenses and DMG/configuration files remain local and private.

## Official display name

**REAPER Time Capsule** is the display name. The Python package name, repository
URL, capsule identifiers and existing beta filenames remain compatible.
