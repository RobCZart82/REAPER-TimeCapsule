# Preference staging (0.7) and verification (0.8.0-dev)

These milestones add a separate opt-in export and a read-only verifier. They do
**not** modify a REAPER configuration, export an installable INI, deploy preferences
or provide complete rollback. Existing preview commands remain read-only.

## Export

Create a dedicated `TimeCapsule-Staging` directory outside your input/resource
folders. It must already exist, with that exact name and no symlink ancestors.
Use canonical paths (for example `/private/tmp` rather than macOS's `/tmp` link).

```sh
python -m reaper_timecapsule config-stage old.ini clean.ini \
  TimeCapsule-Staging/review.timecapsule-stage.zip \
  --select REAPER/tinttcp --source-version 7.82 --target-version 7.82 --opt-in
```

Each `--select` authorizes exactly one changed approved preference. Repeat it for
additional keys. Selections must be unique. Unknown/excluded keys, unsupported
values, missing keys, unchanged values and unknown/different versions are rejected.
The current allowlist remains the conservative binary `tinttcp`/`peaksedges` subset.
Version provenance remains caller-supplied, not independently authenticated.

The exporter reads both inputs once, compares those snapshots and fingerprints
the same bytes with SHA-256. It creates a new ZIP exclusively, never overwrites,
never creates directories and never copies complete inputs. It rejects destination
ancestry under either input directory, the detected default resource directory,
any directory named REAPER, or directories with recognized resource/install markers
(`reaper.ini`, `reaper-kb.ini`, `reaper.exe`, `REAPER.app`, case-insensitive).

Custom resource/install layouts without these markers cannot be identified with
certainty: choose a dedicated external working directory. Inputs and destination
parents must remain stable; this is not protection against hostile concurrent
filesystem replacement. A failed write attempts to remove only its own partially
created archive. A process crash can leave a partial archive; verification rejects
it. No automatic REAPER-folder writes exist.

## Package contents

| Member | Contents |
| --- | --- |
| `preferences.json` | Selected section/key/source-value data; `apply_supported=false`. |
| `rollback-preferences.json` | Selected target values before the proposal; not a full target snapshot. |
| `manifest.json` | Input SHA-256 fingerprints, supplied versions, explicit choices and payload checksums. |

No raw unknown values, passwords, license material, input paths, DMGs or theme
assets are included. Fingerprints are hashes of input bytes, not copies of those
bytes. Reports/packages still expose selected preferences and should remain private.
There is no command that applies either preference payload or reverse payload.

## Verify

```sh
python -m reaper_timecapsule verify-stage TimeCapsule-Staging/review.timecapsule-stage.zip
python -m reaper_timecapsule verify-stage TimeCapsule-Staging/review.timecapsule-stage.zip --target clean.ini
```

Verification reads without extraction and checks exact member names/counts, duplicate
entries/JSON fields, bounds, checksums, payloads, versions and current allowlist.
It reconstructs expected payload bytes from validated selections, so merely changing
a checksum cannot authorize a new key. `--target` fingerprints current target bytes;
any change, including comments/line endings, rejects the stale baseline. Omitting it
returns `target_baseline_matches=null`, not a claim that the target is unchanged.

Checksums are integrity evidence, not signatures or origin authentication. A wholly
rewritten but policy-valid package can pass verification. Baseline matching does
not authorize application, and no application mechanism is implemented. ZIP input
is bounded to 128 KiB; each member is bounded to 128 KiB. Configuration parsing keeps
its existing 4 MiB limit. Symlink archive inputs are rejected.

## Validation and remaining milestones

Synthetic cross-platform tests cover selection authorization, no overwrite,
resource/destination guards, private-value omission, input preservation, reverse
values, stale target detection, forged keys, duplicate members/JSON fields, size
limits, partial-write cleanup and CLI opt-in behavior. Existing CI runs on macOS,
Windows and Linux with Python 3.10/3.12. No user configuration or license is uploaded.

Issue #4 remains open for full rollback and actual merge. GUI staging, native
REAPER runtime validation, and complete portable-resource identification remain
future work. The staging bundle is reviewable DATA, not a ready-to-install recovery.
