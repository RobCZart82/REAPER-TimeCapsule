# First public beta readiness

Target scope: verified backup, read-only audits and recovery into a new external
folder. Automatic active-configuration migration is outside the first beta scope.

## Completed: atomic backup publication

After building and verifying a private temporary ZIP in the destination directory,
Time Capsule publishes it using an exclusive hard-link creation. If another process
has created the target file, directory or symlink, publication fails and that entry
is preserved. The temporary link is then removed; successful publication leaves
one verified archive. There is no check-then-rename replacement window for backup
ZIP publication. Development builds now permit a native **exclusive** rename on non-link volumes; plain overwrite-capable rename/copy is never used.

A writable filesystem supporting hard links or native exclusive rename is required.
Real FAT/exFAT validation remains outstanding; unsupported operations fail closed. Create and verify on a supported local filesystem, then
manually copy the completed ZIP elsewhere if needed. No claim of crash durability
or protection against hostile concurrent replacement of staging paths is made.
A process crash may leave a temporary file. Permission and cleanup failures can
also require manual attention.

Tests exercise competing file/directory creation at the actual publication call,
dangling targets, unsupported-operation cleanup and successful archive verification.
The same tests run in the macOS/Windows/Linux Python 3.10/3.12 CI matrix.

## Completed: portable archive namespace preflight

Verification checks every indexed resource path before restore staging begins.
It rejects Windows device names (including extensions and superscript COM/LPT
variants), forbidden characters, controls, trailing spaces/dots, surrogate code
points, case-insensitive/NFC-equivalent collisions and file/directory prefix
conflicts. Shared directories must use consistent spelling. These rules apply on
all platforms; no files are silently renamed or dropped.

The Windows name rules follow [Microsoft filename documentation](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file).
NFC plus casefold matching is a deliberately conservative project portability
policy, not an exact model of every filesystem. Ordinary Unicode names remain
supported. Total destination-path length, filesystem component-size limits and
legacy 8.3 aliases are not fully modeled and remain validation work.

Older snapshots containing newly rejected names fail verification; retain the
original backup and resolve source naming manually before making a new one. Backup
publication also verifies the completed ZIP, so incompatible source names prevent
publication. The inventory scan alone does not apply this namespace preflight.

Synthetic archives exercise these cases without creating invalid filenames on
Windows. Rejected archives are tested to fail before restore creates staging.
Valid Unicode resources are verified and restored in the same cross-platform suite.

## Completed: exclusive restore directory publication

Restoration now publishes the verified staging directory with a no-replace native
operation: macOS `renamex_np(RENAME_EXCL)`, Linux `renameat2(RENAME_NOREPLACE)`,
and Windows `os.rename` (which refuses existing destinations). Competing empty
directories and files are preserved. Unsupported platforms/filesystems fail closed;
there is no ordinary POSIX rename fallback. Temporary restore directories are
cleaned on handled failures. This does not guarantee power-loss durability or
protection against hostile replacement of staging/parent paths.

References: [Apple flags/API](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/sys/stdio.h),
[Linux flags](https://github.com/torvalds/linux/blob/master/include/uapi/linux/fs.h),
[Python rename semantics](https://docs.python.org/3/library/os.html#os.rename).

## Completed: handled archive/I/O failures

Malformed ZIPs, unsupported compression/encryption, invalid manifest encoding/JSON,
non-object manifests and duplicate manifest fields now fail with a controlled
validation error instead of exposing parser/ZIP tracebacks through the CLI. I/O
errors keep their original error type. Synthetic disk-full and permission failures
exercise backup/restore temporary cleanup and preservation of original inputs.

Backup compares each open file's identity, size and modification time before/after
copying and against the current pathname. Detected same-size modification or
replacement aborts publication. This is per-file detection, not a transactional
snapshot or a guarantee against modifications preserving metadata. Close REAPER
and use stable inputs. Crash cleanup and hostile filesystem replacement remain
outside these guarantees.

## Completed: responsive GUI backup/verify/restore

Backup, verify, restore, scan, MIDI audit and ReaPack audit use a single background
worker. Tk field values are captured on the UI thread; workers do not access Tk.
Results/errors are delivered through a queue and rendered by UI polling. Inputs and
operation buttons are locked until completion, with an indeterminate busy indicator.
It shows per-phase completion where known; there is no global ETA. Large report
previews are bounded to 256 KiB and inserted in 8 KiB UI callbacks; long strings,
collections and deep values are shortened in this display-only copy. The full scan
inventory remains available in File policies, and CLI reports are not shortened.

Window closing is blocked during active work to avoid interrupting a write.
Cooperative cancellation now checkpoints scanning/copying/verification and before
publication, cleans temporary state and reports cancellation separately from errors.
Per-phase progress replaces the busy indicator where totals are known. Headless
worker/GUI tests cover single-job exclusion, captured inputs, pending/success/error
handling, failed thread startup, the close guard, and bounded/chunked rendering of
large audit reports. Native screen layout and dialogs have not been visually
validated by these tests.

## Completed: first limited beta preparation

GPL-3.0-only was selected by the user, and unsigned beta packages were explicitly
accepted. The v0.9.0-beta.2 release is published; this section records that release
preparation rather than a pending publication request.
Native desktop CI builds bundle the runtime, matching tracked source and notices,
and execute a synthetic backup/verify/restore/cancellation/Tk self-test using the
actual binary. Release-specific scope and remaining limitations are documented
in FIRST_BETA.md. This limited beta makes no automatic migration/runtime-workflow
compatibility promise. The release artifacts and checksums are linked from the
README; later releases require their own clean validation.

## Development and validation before a later beta

- Smoke-test large MIDI and ReaPack reports in packaged macOS and Windows builds,
  including native scrolling and file dialogs; synthetic Tk tests do not replace this.
- Verify toolbar/icon references from reliable REAPER format evidence and design
  a disposable REAPER integration test. Static audit does not execute or validate actions.
- Keep configuration preview and staging read-only. Expand the two-key allowlist
  only with exact evidence and isolated runtime validation; active apply and rollback
  remain out of scope until separately designed and tested.
- Treat ReaPack 2.x parsing, package installation and synchronization as separate
  future work; the current verified profile/registry support is ReaPack 1.x.
- Validate on clean supported macOS and Windows environments, and broaden checks
  for removable/network filesystems, destination path limits and failure recovery.
- Refresh the bilingual PDF guides, screenshots, release notes and package manifests
  together when the next beta candidate is ready. Do not publish a release from this
  checklist alone.

Green CI and synthetic tests are necessary but do not replace these real-application
and clean-environment checks. Full rollback, active configuration merge and automatic
ReaPack installation remain separate future milestones.
