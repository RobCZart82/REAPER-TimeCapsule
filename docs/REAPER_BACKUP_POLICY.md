# Rules (initial conservative classification)

| Example | Policy | Reason |
| --- | --- | --- |
| `Scripts/`, `MenuSets/`, `KeyMaps/`, `Data/toolbar_icons/` | keep | Personalized actions, menus and icons |
| `reapack.ini` | keep | ReaPack repository names, URLs, enable states and options |
| `ReaPack/registry.db` | review | Historical installed package database could be stale or platform-specific |
| `ReaPack/cache/**` | regenerate | Downloaded XML indexes, not personal workflow |
| `ReaPack/registry.db-shm` | regenerate | SQLite ephemeral shared memory |
| `S&M.ini`, `BR.ini`, `sws-autocoloricon.ini` | keep | SWS settings |
| `LangPack/`, `ColorThemes/`, `Effects/`, `presets/` | keep | Installed/customized resources; packed themes can be compared with an explicitly supplied factory copy |
| `reaper-kb.ini`, `reaper-menu.ini`, `reaper-mouse.ini` | keep | Actions, menus, mouse modifiers |
| `reaper.ini`, `reaper-midihw.ini`, `reaper-wndpos.ini` | review | May hold hardware, monitor or path-specific settings |
| `UserPlugins/` | review | Binary ABI and third-party redistribution require checking |
| `reaper-auplugins*.ini`, `reaper-vstplugins*.ini`, `reaper-clap*.ini` | regenerate | Outdated plugin scan caches |
| `MetadataCaches/`, `QueuedRenders/` | regenerate | Temporary/generated artifacts |
| `reaper-license.rk`, `reaper-reginfo*.ini` | exclude | REAPER registration material |
| unknown files | review | Avoid silently losing potentially personal data |

**Warning:** Policies are cautious defaults, not proof that every saved item will
work after recovery. Factory-theme comparison is read-only and advisory; it never
omits a resource. MIDI actions, plugin binaries, ReaPack packages and hardware
settings require manual review. Restore remains isolated in a new directory and
does not install or activate workflow dependencies.
