# Release readiness — implemented guarantees

> Current execution order, release gates and audit status live in [ROADMAP.md](ROADMAP.md).
> This document records technical guarantees and historical beta preparation, not a second task list.
> Refreshed 2026-10-14 against main `2d09b97090bfb2c6f8048bb6efbecbc244a8437e` (functional code baseline `e4e25c82daec1316364669c312fddbdb370e0c9c`); the current 1.0.0 candidate and release gates are summarized in [ROADMAP.md](ROADMAP.md).

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

PR #70 merged as `c1763a`: Windows source traversal and backup reads use extended-length paths, and the GUI resolves the redirected Windows Desktop known folder. On Windows 11 x64, the user ran its [Windows Actions artifact](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38513240558/artifacts/11870727714) (artifact ID `11870727714`, build commit `0a23f23e25fefd6d0e6dc6e95241ed1e5fd8a32f`, artifact-archive SHA-256 `5a8719d4e91272da6db3ccbe0d8748243751368ecac83ca2230011dd50318b5b`). On the actual REAPER settings folder, Scan / Preview, MIDI Audit, ReaPack Audit, Backup, Verify, Restore and File policies completed successfully across the user's tests. The saved and stored Verify inventories both show 7,035 keep and 32 review entries, with no policy changes or inspection omissions (12 regenerate and 2 exclude). The exported private File policies JSON shows 7,035 keep, 32 review, 12 regenerate and 2 exclude entries, with no inspection omissions; the user-provided report was inspected only for aggregate counts and was not added to the repository. The ZIP passed CRC checking; all 7,067 schema-2 manifest hashes matched, with no unexpected entries, and the long-path Lua file was present. These results are targeted user-machine evidence, not clean-machine or full release acceptance.



On macOS, the user reports that the same Scan / Preview, MIDI Audit, ReaPack Audit, Backup, Verify, Restore, File policies and private JSON export flows all succeeded using the PR #73 [macOS Actions artifact](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327518/artifacts/11872227935) (artifact ID `11872227935`, PR head `c7e216dc668aced2578fff66d2c61fe6f64b5eed`, artifact-archive SHA-256 `87a783f52da62dd996de35522cb01e1f96a7a723804782870942a8be7904a5a2`). The macOS version was not provided. No separate macOS report or archive-integrity result was supplied, so the Windows report counts and hashes are not attributed to this run. This is user-reported targeted smoke-test evidence; clean-machine and real-volume validation remain separate gates.

Restore on that PR #70 build failed with `Recovery path exceeds conservative filesystem capacity`. The selected target was 49 characters; the longest relative archive path was 254 characters, and 13 final target paths (max 311 characters) plus 85 staging paths (max 344 characters) exceeded the old 259-character preflight. PR #73 merged as `e4e25c8` and now uses Windows extended-length paths for restore staging while retaining a 255-unit component limit. Its Windows synthetic backup→restore regression proves publication of a path longer than 259 characters. PR checks passed: [Tests run 38516327510](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327510) and [Desktop beta builds run 38516327518](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327518). The Windows artifact is [available here](https://github.com/RobCZart82/REAPER-TimeCapsule/actions/runs/38516327518/artifacts/11872113259) (artifact ID `11872113259`, built from PR head `c7e216dc668aced2578fff66d2c61fe6f64b5eed`, artifact-archive SHA-256 `7d977d90e9e22b44233c03414ce6d004b154b3cdb8829c3df196db581fd1b84a`). The user confirmed running this PR #73 Windows Actions build for the follow-up test. The Restore screenshot shows completion and the saved JSON reports `restored_portable=7035`, `isolated_for_review=32`, `legacy_cache_skipped=0`, and `inspection_omissions=[]`. The new `teszt2-zip.zip` passed CRC checking and all 7,067 schema-2 manifest file SHA-256 values matched (no missing members or hash mismatches). This is a targeted **PASS** on Windows 11 x64 with the actual REAPER profile. The published beta.2 remains unchanged.

Packaged clean-machine installation and real-volume validation remain without recorded acceptance evidence. The old PR #70 Restore UI attempt remains a historical FAIL; the PR #73 build's real-profile Restore retest now passes. The separate Verify UI action, three audit buttons and Backup have the targeted smoke-test evidence above. CI results are not manual or clean-machine acceptance; this does not certify a new release. Local filesystem tests for PR #73 were not run in the sandbox because `Path.resolve` returned WinError 5; the Windows CI run succeeded.

Use [ROADMAP.md — Egyetlen végrehajtási sorrend](ROADMAP.md#egyetlen-végrehajtási-sorrend) for the current seven-step plan and acceptance criteria.
A later limited beta may retain explicit static-audit/read-only migration limits.
Issue #3 toolbar/runtime and issue #4 active apply/rollback remain separate milestones.
The user selected 1.0.0 stable and authorized publication of unsigned packages. Bilingual README, final About label and 1.0.0 release notes are prepared on PR #77. Merge and publication remain contingent on green final-head tests/builds; clean-machine and real-volume validation are disclosed as outstanding limitations.


## 1.0.0 candidate snapshot — 2026-10-14

The current release checklist and execution order remain in [ROADMAP.md](ROADMAP.md).
PR #77 was an unpublished draft candidate at tested revision `42ef450cb9b217ba01906ac4187696a72f1faf9b`.
Its Tests run 38525955324 and Desktop beta builds run 38525955034 passed; both native
platform builds and packaged self-tests succeeded. Current Windows and macOS artifact
IDs and archive digests are recorded in ROADMAP.md.

On the tested Windows 11 x64 candidate, the user-reported Restore succeeded with
7,035 portable files restored, 32 isolated for review, 0 legacy skips and 0
inspection omissions. The supplied Test100.zip passed CRC and all 7,067 schema-2
manifest SHA-256 comparisons. The user also reports the same successful Restore
result on macOS, without a separate report/archive for independent count/hash checks.
The candidate About screen still displays `VERSION 1.0.0 · BETA`; remove that label
and rebuild the final stable package. These targeted profile tests do not complete
clean-machine installation/first-launch or real-filesystem validation. No public
1.0.0 release has been created.


## 1.0.0 stable publication snapshot — 2026-10-14

The user authorized publishing the unsigned 1.0.0 stable release. PR #77 prepares
application and package metadata, removes the candidate-only BETA marker, and aligns
the English/Hungarian download pages and release notes. This candidate is not yet
merged or published. The PR's final-head source tests and both packaged builds must
pass before merge; the exact final package digests and release asset links should be
recorded after publication.

Windows 11 x64 Intel real-profile Restore passed on the prior 1.0.0 candidate build:
7,035 portable files restored, 32 isolated for review, no legacy skips or inspection
omissions; the supplied ZIP passed CRC and all 7,067 manifest SHA-256 checks. The
user reports that the same GUI workflow succeeded on macOS, but supplied no separate
macOS report or archive for independent count/hash verification. The exact final
package (which changes the About text and documentation) has not had a new manual
installation test.

Clean-machine installation/first launch and FAT/exFAT/network-volume testing remain
NOT RUN. Signing/notarization is not available for this release; the user authorized
unsigned publication and the README/release notes disclose this. Issues #3 (MIDI
toolbar/runtime) and #4 (active configuration apply/rollback) remain outside the
1.0.0 scope. Full REAPER runtime integration and automatic plugin installation are
not claimed.
