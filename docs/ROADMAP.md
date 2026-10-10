# Roadmap / fejlesztési lépések

## Implemented in 0.2.0-dev
- Per-file backup policies with preview (keep/review/regenerate/exclude)
- Cross-platform REAPER resource-directory detection (default installations)
- No-overwrite compressed backup and SHA-256 manifest verification
- Safe restore into a NEW directory with machine-specific files isolated
- ReaPack / SWS settings preserved as source resources
- macOS, Windows and Linux CI workflow (runs after repository push)

## Completed in 0.3.0-dev
- Read-only ReaPack XML repository URL inventory from reapack.ini; display redacts credentials
- Inventory of native SWS/ReaPack plugin files without attempting installation
- MIDI right-click menus and KeyMap file presence tracked in snapshot manifest
- Recovery report records inventory for auditing

## Next: 0.4
- Parse real ReaPack state and compare enabled/disabled repositories with original
- Detect exact installed ReaPack/SWS binaries, architecture and versions
- Add clean installation + configuration merge with a per-key REAPER.ini allowlist
- Back up and validate Custom Action <-> ReaperMenu references
- Assess MIDI workflow bundle redistribution permission before shipping it
- Snapshot exclusion policy UI and signed / auditable reports
- Verify saved ReaPack repository URLs are still current; do not auto-sync without permission

## Later
- Native macOS app packaging and Windows executable + notarization/signing plans
- Managed backups and rollback snapshots; external drive workflows
- Portable REAPER resource installs; compare factory theme files against a matching build
- Automatic integration tests on a *temporary* REAPER installation

## Security constraints
- No upload of personal resource directories or license keys to GitHub
- No silent overwrite of user's active REAPER directory
- No executing untrusted scripts during archive inspection
