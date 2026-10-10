"""Conservative REAPER resource backup policies.

Never infer that an unknown file is disposable. For this first migration release,
unknown resources are saved but isolated from the automatic restore.
"""
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import PurePosixPath


@dataclass(frozen=True)
class Decision:
    policy: str  # keep, review, regenerate, exclude
    reason: str


REGENERATE_DIRS = {"metadatacaches", "queuedrenders"}
EXCLUDE_DIRS = {".git", "__pycache__", ".svn"}
REVIEW_DIRS = {"userplugins", "osc", "reaper_www_root"}
KEEP_DIRS = {
    "scripts", "keymaps", "menusets", "colorthemes", "data", "effects",
    "presets", "fxchains", "tracktemplates", "projecttemplates",
    "midinotenames", "langpack", "reapack", "cursors", "mousemaps",
    "automationitems", "trackicons", "screensets", "fxpresets",
}
REGENERATE_PATTERNS = (
    "reaper-vstplugins*.ini", "reaper-vstshells*.ini",
    "reaper-auplugins*.ini", "reaper-clap*.ini", "reaper-dxplugins*.ini",
    "reaper-recentfx.ini", "reaper-fxlist.ini", "reaper-install-rev.txt",
    "*.reapeaks", "*.reapeaks64", ".ds_store",
)
EXCLUDE_PATTERNS = (
    "reaper-license.rk", "reaper-reginfo*.ini", ".env", ".env.*",
    "*.key", "*.pem", "id_rsa", "id_ed25519",
)
KEEP_ROOT = {
    "reaper-kb.ini", "reaper-menu.ini", "reaper-mouse.ini",
    "reapack.ini", "s&m.ini", "br.ini", "sws-autocoloricon.ini",
}
REVIEW_ROOT = {
    "reaper.ini", "reaper-midihw.ini", "reaper-wndpos.ini",
    "reaper-extstate.ini", "reaper-fxtags.ini", "reaper-jsfx.ini",
}


def decide(rel_path: str) -> Decision:
    """Classify a normalized relative POSIX-style path, case-insensitively."""
    parts = PurePosixPath(rel_path).parts
    if not parts or any(p in {".", "..", ""} for p in parts):
        raise ValueError("Invalid relative path")
    lower = tuple(p.lower() for p in parts)
    name = lower[-1]
    if any(p in EXCLUDE_DIRS for p in lower[:-1]):
        return Decision("exclude", "development artifacts")
    if any(fnmatchcase(name, x) for x in EXCLUDE_PATTERNS):
        return Decision("exclude", "license or potentially sensitive credential")
    if any(p in REGENERATE_DIRS for p in lower[:-1]) or any(
        fnmatchcase(name, x) for x in REGENERATE_PATTERNS
    ):
        return Decision("regenerate", "cache or generated index should be rebuilt")
    if any(p in REVIEW_DIRS for p in lower[:-1]):
        return Decision("review", "native extension or machine-dependent data")
    if len(parts) == 1 and name in REVIEW_ROOT:
        return Decision("review", "mixed user and machine-dependent settings")
    if len(parts) == 1 and name in KEEP_ROOT:
        return Decision("keep", "portable user REAPER settings")
    if any(p in KEEP_DIRS for p in lower[:-1]):
        return Decision("keep", "personal resource or ReaPack state")
    return Decision("review", "unknown file: preserve without automatic activation")
