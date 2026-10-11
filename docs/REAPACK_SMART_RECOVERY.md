# ReaPack Smart Recovery (Time Capsule 0.5.0-dev)

## Why the ReaPack registry cannot be blindly copied

A clean operating system may not have the original JSFX, ReaScripts, SWS,
ReaPack and platform-specific extension binaries yet. Restoring an old
`ReaPack/registry.db` directly can mark packages as installed even when their
files have not been restored or are incompatible with the new OS/CPU.

Time Capsule therefore **does not automatically activate an old registry.db**.
It retains the original registry in `NeedsReview/` and records a read-only list
of installed package identifiers in the snapshot inventory.

## Verified ReaPack 1.x profile format

According to upstream ReaPack 1.x source:
- `reapack.ini` `[remotes]` section includes `size=N` and
  `remote0=name|URL|enabled|autoInstallOverride` (repeated for subsequent
  numbered entries). Repository order, names, URLs and enable state matter.
  Per-repository auto-install override is tri-state: `0`, `1`, or `2`
  (inherit global setting).
- `[install]` contains `autoinstall`, `prereleases`, `promptobsolete`.
- `[browser]` contains `synonyms`.
- Global defaults in the 1.x source are auto-install off, pre-releases off,
  obsolete-package prompt on, synonyms on. Time Capsule distinguishes explicit
  values from defaults, and refuses to guess malformed values.
- `ReaPack/registry.db` is a SQLite database with `entries` (package,
  version, flags) and `files` (installed file ownership).
- `ReaPack/cache/` contains downloaded XML indexes and is regenerated;
  do not migrate old cache files as active data.

**Source references (ReaPack 1.x):**

- https://github.com/cfillion/reapack/blob/master/src/config.cpp
- https://github.com/cfillion/reapack/blob/master/src/remote.cpp
- https://github.com/cfillion/reapack/blob/master/src/registry.cpp
- https://github.com/cfillion/reapack/blob/master/src/path.cpp

ReaPack source development has moved to Codeberg, and the ReaPack v2
configuration format may differ. The parser is intentionally limited to
recognized **1.x** configuration versions (through format version 4).
Unknown versions are kept unchanged in backup, but not claimed to be parsed.

## Backup behavior

| Resource | Action | Rationale |
| --- | --- | --- |
| `reapack.ini` | KEEP | Exact repository configuration remains available |
| `ReaPack/registry.db` | REVIEW | Preserve package history but do not reactivate stale records |
| `ReaPack/registry.db-wal` | REVIEW | Potential uncommitted data: examine offline |
| `ReaPack/registry.db-shm` | REGENERATE | Ephemeral shared-memory state |
| `ReaPack/cache/**` | REGENERATE | Downloaded XML indexes should be refreshed |
| `UserPlugins/reaper_reapack*.dylib/dll/so` | REVIEW | OS and architecture compatibility required |

The snapshot `manifest.json` additionally records:
- Repositories in their original order, URLs with credentials/query strings
  removed from the **report**, enabled/disabled flags and per-repo override.
- Global ReaPack settings and whether they were explicitly configured.
- Read-only installed package inventory from SQLite: repository, category,
  package, version, pinned/prerelease flags and number of owned files.
- Parse warnings when a file is absent, corrupt, too large or unknown.

The original `reapack.ini` is copied **unchanged** into the private
Time Capsule ZIP. It may contain proxy configuration or other sensitive
values: treat the ZIP as private and encrypt it for long-term storage.
Never upload personal snapshots to a public repository.

## How to use

Run REAPER once on the clean OS, then close REAPER before any backup/migration.

```console
python -m reaper_timecapsule reapack-audit
python -m reaper_timecapsule reapack-audit "/path/to/REAPER"
python -m reaper_timecapsule backup snapshot.zip --source "/path/to/REAPER"
python -m reaper_timecapsule verify snapshot.zip
python -m reaper_timecapsule restore snapshot.zip "/path/to/NEW-output-folder"
```

The GUI has a **ReaPack Audit** button. The restore process does NOT
perform package synchronization, create SQLite registry entries,
download packages or install executable extensions.

### In a new REAPER installation

1. Install the destination-architecture ReaPack and SWS versions from their
   official projects (until Time Capsule's guided installer is implemented).
2. Import/restore the compatible ReaPack settings, preserving repository
   enabled/disabled states.
3. Inspect the saved package inventory and decide which packages to reinstall.
4. Only after user approval, synchronize ReaPack to fetch current index files.
5. Confirm MIDI Editor menus/Custom Actions in REAPER via MIDI Audit and
   functional manual testing.

This module provides inspection and safe staging, **not yet one-click install**.
