# Factory theme migration preview

The read-only `theme-preview` command compares direct children of three explicit
ColorThemes directories: the old user's folder, a trusted factory reference, and
an existing destination folder. It prints a JSON report without copying/deleting
resources, changing backup policy, extracting archives, downloading or installing
REAPER. GUI integration is not included in this follow-up.

```sh
python -m reaper_timecapsule theme-preview old/ColorThemes factory/ColorThemes clean/ColorThemes \
  --source-version 7.82 --factory-version 7.82
```

Provide the factory directory yourself from a known clean installation matching
source version/platform/build. Version strings and factory provenance are supplied
by the caller, not independently authenticated. Unknown or different versions
force review. Matching version strings alone cannot prove a matching build.
Use stable private copies; do not upload personal themes, configurations or DMGs.

## Decisions

| Status | Meaning |
| --- | --- |
| `factory_match` | Same case-insensitive normalized name and SHA-256 bytes as factory; packed theme and compatible supplied versions. Review for reuse. |
| `modified_factory` | Same filename as factory but different bytes; preserve personalized variant. |
| `user_theme` | No factory file with that name; preserve user theme. |
| `review` | Destination conflict, unknown/different version, unpacked descriptor or unsupported entry. Preserve source pending review. |

Destination state is separately reported as `absent`, `identical`, or `conflict`.
A conflict always prevents a reuse recommendation, including when the source
matches factory. Only source entries appear in the report; target-only files are
neither listed nor proposed for removal. Renamed copies are conservatively treated
as user themes. `factory_identical` is byte evidence independent of version gates.
Recommendations never cause files to be omitted from snapshots or restore.

Packed `.ReaperThemeZip` files are hashed as opaque bytes. This does not validate
ZIP integrity, resource completeness or theme behavior in REAPER. Repacked but
semantically identical archives will differ and are preserved. `.ReaperTheme`
descriptors always require review: their dependent image folders are not inspected.
Directories, links and unknown extensions are listed for review but never traversed
or hashed. A complete directory comparison is not implemented.

## Bounds and portability

Names match case-insensitively after NFC Unicode normalization. Duplicate normalized
names fail closed to avoid macOS/Windows ambiguity. Backslashes and control characters
in filenames are rejected. Directory roots cannot be symlinks. Each directory has
at most 10,000 direct entries and each recognized theme at most 128 MiB; hashing is
streamed. Detected size/mtime/inode changes during reads fail the preview.

Inputs must remain stable: metadata checks are not a transactional filesystem
snapshot or full protection against concurrent replacement. Reports include source
filenames and SHA-256 digests, but not absolute input paths or file contents. Keep
reports private if filenames disclose personal information.

Synthetic tests cover factory matches, customized/user themes, conflicts, version
changes, normalized filename ambiguity, unsupported dependencies, links, limits,
CLI output and unchanged bytes/mtime. They run in the existing six-job macOS,
Windows and Linux CI matrix. No private user assets are used.

Issue #4 remains open. Actual selective restore, conflict choices and rollback
snapshots must be implemented and tested separately before in-place migration.
