# Release readiness — implemented guarantees

> Current execution order, release gates and audit status live in [ROADMAP.md](ROADMAP.md).
> This document records technical guarantees and historical beta preparation, not a second task list.
> Refreshed 2026-10-14 against code main `c1763a8fdd2fc0612a3c5b71cbe6572b3dedf795`; user smoke-test evidence added after PR #71's docs-only update.

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
inventory remains available in File policies. **Save full report…** exports the
complete JSON result only after the user chooses a path and confirms the private-data
warning. It refuses to write inside the scanned resource tree and never replaces an
existing file. Synthetic tests cover complete contents and cleanup; human file-dialog
checks remain part of clean-machine validation.

Window closing is blocked during active work to avoid interrupting a write.
Cooperative cancellation now checkpoints scanning/copying/verification and before
publication, cleans temporary state and reports cancellation separately from errors.
Per-phase progress replaces the busy indicator where totals are known. Headless
worker/GUI tests cover single-job exclusion, captured inputs, pending/success/error
handling, failed thread startup, the close guard, and bounded/chunked rendering of
large audit reports. The macOS and Windows bundled executable self-tests now also
render a synthetic report above the display cap, require its truncation notice and
both scrollbars, and check completion within ten seconds. On macOS, the packaged
self-test also closes and reopens the custom About window through TkAqua's
tkAboutDialog hook. Clicking the native menu item and checking its visual layout
still need a human smoke test on macOS.

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

## Remaining release validation

PR #70 merged as `c1763a`: Windows source traversal and backup reads now use extended-length paths, with a passing synthetic >260-character scan/backup regression. The GUI resolves the redirected Windows Desktop known folder for its restore destination. On Windows 11 x64, the user ran the PR #70 build from [Actions artifact `desktop-beta-windows-latest`](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38513240558/artifacts/11870727714) (artifact ID `11870727714`, build commit `0a23f23e25fefd6d0e6dc6e95241ed1e5fd8a32f`, artifact-archive SHA-256 `5a8719d4e91272da6db3ccbe0d8748243751368ecac83ca2230011dd50318b5b`). Against the actual REAPER settings folder, Scan / Preview, MIDI Audit, ReaPack Audit, Backup to `testing-zip.zip`, and Verify all completed; the full Verify JSON report was saved. Its saved and stored inventories both show 7,035 keep and 32 review entries, with no policy changes or inspection omissions (12 regenerate and 2 exclude items). For the backup ZIP, `zipfile.testzip()` found no CRC error; all 7,067 schema-2 manifest file hashes matched, there were no unexpected ZIP entries, and the previously failing long-path Lua file was present. This is targeted user-machine evidence, not clean-machine or full release acceptance. Restore UI was attempted on the same archive and failed with `Recovery path exceeds conservative filesystem capacity`. The selected target was 49 characters; archive analysis found a maximum 254-character relative path and 10 combined target/resource paths exceeding 260 characters, matching the current Windows preflight limit. Clean-machine installation and published beta.2 installer retest remain NOT RUN. The release still has the conservative restore-path capacity preflight.

Use [ROADMAP.md — Egyetlen végrehajtási sorrend](ROADMAP.md#egyetlen-végrehajtási-sorrend)
for the current seven-step plan and acceptance criteria. Packaged clean-machine installation and real-volume validation remain without
recorded acceptance evidence in this update. Restore UI has a documented FAIL on this real profile/archive. The separate Verify UI action, three audit buttons and Backup have the targeted user smoke-test evidence above. PR #70 checks Tests run 38513240555 (six platform/Python jobs) and Desktop beta builds run
38513240558 (Windows/macOS packaged self-tests) succeeded. These are candidate CI results, not manual or clean-machine acceptance.
This does not certify a new release. No local suite was run during this review; PR #68
reports 234 local tests passed.

A later limited beta may retain explicit static-audit/read-only migration limits.
Issue #3 toolbar/runtime and issue #4 active apply/rollback remain separate milestones.
Version selection, bilingual documentation, package contents/checksums and final
candidate validation must precede a separate publication decision.
