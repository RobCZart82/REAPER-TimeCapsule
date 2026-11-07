# Offline configuration apply and recovery (development)

Close **all REAPER instances using the target profile** before applying or rolling
back. These CLI-only commands change an explicitly selected configuration file;
they do not modify a running REAPER process. Preview, staging, verification and
the GUI remain read-only with respect to the input configuration.

Only existing, changed, approved `REAPER/tinttcp` and `REAPER/peaksedges` binary
values are eligible. The staged source/target versions must match. No allowlist
expansion, hardware/cache migration or plugin installation is included.

## Procedure

1. Review `config-preview`, then explicitly select keys using `config-stage`.
2. Close REAPER. Choose a **new** recovery directory under an existing external
   `TimeCapsule-Staging` directory, outside the source and destination profiles.
3. Apply the verified staging package:

```sh
python -m reaper_timecapsule config-apply \
  /external/TimeCapsule-Staging/review.timecapsule-stage.zip \
  /disposable/profile/reaper.ini \
  /external/TimeCapsule-Staging/recovery-001 --opt-in --reaper-closed
```

The command validates the archive, hashes the entire target against its staged
baseline and prepares the change in memory. It keeps every unselected byte,
including private/unknown keys, comments, UTF-8 BOM and line endings. Duplicate
sections/keys, unsupported encodings and missing selections fail closed.

Before writing the target it creates an exclusive recovery directory with:

- `original.ini`: the **complete original target file**, not only selected keys.
- `applied.ini`: the complete intended result.
- `manifest.json`: schema and SHA-256 fingerprints for both complete files.

**These recovery files contain private configuration values. Keep them local and
private; do not attach them to public issues.** Directory/file modes restrict
access on POSIX. Windows access follows the parent directory's ACL. This is a
full backup of the selected file, not a backup of the whole REAPER resource tree,
ACLs, ownership, extended attributes or plugins. Checksums detect corruption;
they do not authenticate who supplied a recovery bundle.

The recovery files are flushed and read back before apply. An exclusive adjacent
`.timecapsule-lock` prevents cooperating TimeCapsule writers. A same-directory
temporary file is flushed, the full target is checked again, and `os.replace`
atomically swaps the file. Original mode bits are retained. Any failure before
replacement leaves the target unchanged; a failed preparation leaves its recovery
directory for inspection, and retry requires a new directory name.

## Rollback and interrupted operations

```sh
python -m reaper_timecapsule config-rollback \
  /external/TimeCapsule-Staging/recovery-001 \
  /disposable/profile/reaper.ini --opt-in --reaper-closed
```

Rollback verifies the complete recovery files and restores the original bytes
only when the target still exactly matches `applied.ini`. Already-original targets
succeed without writing. Later changes, including REAPER rewriting settings on
exit, stop rollback: preserve those edits and compare the saved original manually.
There is no force-overwrite option.

A process crash can leave a lock or temporary file. Close REAPER, inspect the
recovery bundle and target, then remove only the known stale lock/temp. Rollback
can recover an interrupted apply whose target equals the saved applied bytes.
A partial recovery bundle is rejected. Cleanup errors can leave a safe stale lock;
they do not turn a completed replacement into a reported failed apply.

Use stable local directories. This is not protection against hostile filesystem
replacement or non-cooperating writers racing after the final check; REAPER-closed
confirmation is caller-supplied. Atomic visibility is not a claim of power-loss
durability on every filesystem. Network/removable-volume behavior is unvalidated.
Symlink/reparse-point ancestors and multiply-linked target/recovery files fail
closed. No tests use a personal active profile.

## Validation

Synthetic tests cover complete byte-for-byte rollback, BOM/CRLF/comment/private
value preservation, mode preservation, CLI consent, stale baselines, external
backup guards, duplicate bundles, cooperative locks, final-check races, backup
write/replace failures, symlinks/hardlinks, corruption and later-edit rejection.
The separate [REAPER smoke workflow](REAPER_SMOKE_TEST.md) loads an applied
`tinttcp=0` in an isolated real REAPER instance. Windows/Linux/macOS source checks
are run by the existing PR CI; real REAPER validation is recorded separately.
