# First public beta readiness

Target scope: verified backup, read-only audits and recovery into a new external
folder. Automatic active-configuration migration is outside the first beta scope.

## Completed: atomic backup publication

After building and verifying a private temporary ZIP in the destination directory,
TimeCapsule publishes it using an exclusive hard-link creation. If another process
has created the target file, directory or symlink, publication fails and that entry
is preserved. The temporary link is then removed; successful publication leaves
one verified archive. There is no check-then-rename replacement window for backup
ZIP publication and no rename/copy fallback.

A writable filesystem supporting hard links is required. FAT/exFAT and some network
or restricted filesystems may not support this operation, so backup creation there
fails with an explanation. Create and verify on a supported local filesystem, then
manually copy the completed ZIP elsewhere if needed. No claim of crash durability
or protection against hostile concurrent replacement of staging paths is made.
A process crash may leave a temporary file. Permission and cleanup failures can
also require manual attention.

Tests exercise competing file/directory creation at the actual publication call,
dangling targets, unsupported-operation cleanup and successful archive verification.
The same tests run in the macOS/Windows/Linux Python 3.10/3.12 CI matrix.

## Still required before public beta

- Resolve restore-directory publication races separately; backup hardening does
  not change directory restoration's existing check-and-rename publication.
- Reject cross-platform ambiguous/reserved archive names before restore.
- Broaden tests for disk-full, permissions, cancellation and changing inputs.
- Introduce a usable GUI flow with background work, progress and safe cancellation.
- Validate supported resources in real temporary REAPER profiles on macOS/Windows.
- Build and test standalone macOS/Windows distributions without Python installed.
- Choose source license, record dependency licenses and settle signing/release policy.
- Publish user documentation, limitations, release notes and artifact checksums.
- Test release candidates and resolve all data-loss/basic-workflow blockers.

The repository remains a development preview. Green CI alone does not satisfy
these release gates. Full rollback, active merge and automatic ReaPack installation
remain separate future milestones.
