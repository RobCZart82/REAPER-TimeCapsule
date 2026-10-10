# Intelligent Configuration Migration — 0.6.0-dev

This milestone is a **read-only comparison**, available through CLI, the GUI **Config Preview** button and the Python
`preview_migration` API. It does not modify either input, merge configuration,
export a staged INI, invoke REAPER, inspect a DMG, or scan the user's resource folder.
The GUI asks for both files explicitly, then for source and target versions. Blank
versions mean unknown; canceling any dialog stops the comparison. Results appear
in the existing report pane with status and change counts. CLI JSON is printed to
stdout; callers may save that redacted report themselves outside the active
resource folder.

```sh
python -m reaper_timecapsule config-preview old.ini clean.ini \
  --source-version 7.82 --target-version 7.82
```

Supply versions from your own installation records. They are provenance supplied by
the caller, not independently verified executable versions. If omitted, malformed,
older than REAPER 5, or different (even a minor-version change), all otherwise approved
preferences require review. Identical version strings are a conservative eligibility
gate, not proof of runtime compatibility.

## Approved preference policy

| Exact section/key (case-insensitive) | Accepted literal values | Scope |
| --- | --- | --- |
| `[REAPER] tinttcp` | `0`, `1` | Track color appearance |
| `[REAPER] peaksedges` | `0`, `1` | Peak edge appearance |

The key names and their reaper.ini relationship are documented by
[Cockos theme reference](https://www.cockos.com/reaper/sdk/walter/images.php).
The binary subset is a deliberately narrow project policy: this is **not** a complete
REAPER schema or a claim that other bitmask values are invalid in REAPER. Values
outside this subset require review. Themes may override these preferences; no
visual or REAPER runtime validation has been performed. No wildcard approval,
caller-supplied allowlist extension, or unknown-key fallback exists.

Candidates require both files to explicitly contain supported values and identical
supported versions. Each entry reports `same`, `conflict`, `source_only` or
`target_only`; no inferred defaults, source-only additions or target-only deletions
are proposed. `candidate` is an eligibility label requiring manual review, not an
authorization or executable migration plan. Unchanged candidates are marked `same`.

Recognized audio/MIDI/device/driver, plugin/cache, path, platform, CPU/display and
credential/license identities are `exclude`. The exclusion heuristics are not a
complete REAPER schema: unrecognized identities always remain `review`, never
candidates. Unknown sections cannot borrow an approved key name. Only validated
approved literals are displayed; all unknown/excluded values are omitted. Section
and key names remain visible, so treat reports as private metadata.

## Parsing and safety

- Explicit regular files only, no symlink file inputs; no automatic file discovery.
- UTF-8 with optional BOM, LF/CRLF and full-line `;`/`#` comments supported.
- Maximum 4 MiB per input. Legacy encodings require conversion of a private copy.
- Duplicate case-insensitive sections/keys, DEFAULT inheritance, NUL, bare keys,
  malformed section headers, indented entries/continuation lines and unsupported
  control characters fail closed. Convert indented INIs in a private copy before use.
- No interpolation, inline-comment stripping, execution, network or write calls.
- Parsing errors disclose line numbers, not input content.
- Inputs should be stable private copies. There is no transactional snapshot or
  guarantee against another process changing files while they are read.

Tests use only synthetic data, including macOS, Windows and UNC paths, version
changes, sensitive values, malformed files, CLI failures and byte/mtime preservation. Headless GUI interaction tests cover all cancellation
points, blank versions, sensitive-value omission and safe error reporting. These
mocked interaction tests do not verify native dialog rendering or screen layout.
The existing CI runs them on macOS/Windows/Linux with Python 3.10 and 3.12.

## Remaining scope of issue #4

Factory theme identity comparison and preservation of customized variants, explicit
conflict resolution, rollback snapshots and an actual configuration merge remain
unimplemented. Issue #4 must remain open. The later 0.7/0.8 [staging commands](CONFIGURATION_STAGING.md) export selected
preference DATA only, with separate destination protections and verification.
There is still no staged INI or active configuration writer. Never use this preview as a replacement for a backup.
