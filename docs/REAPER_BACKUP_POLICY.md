# Rules (initial conservative classification)

| Example | Policy | Reason |
| --- | --- | --- |
| `Scripts/`, `MenuSets/`, `KeyMaps/`, `Data/toolbar_icons/` | keep | Personalized actions, menus and icons |
| `ReaPack/`, `reapack.ini` | keep | Offline package records, repositories, options |
| `S&M.ini`, `BR.ini`, `sws-autocoloricon.ini` | keep | SWS settings |
| `LangPack/`, `ColorThemes/`, `Effects/`, `presets/` | keep | Installed/customized resources; factory comparison TODO |
| `reaper-kb.ini`, `reaper-menu.ini`, `reaper-mouse.ini` | keep | Actions, menus, mouse modifiers |
| `reaper.ini`, `reaper-midihw.ini`, `reaper-wndpos.ini` | review | May hold hardware, monitor or path-specific settings |
| `UserPlugins/` | review | Binary ABI and third-party redistribution require checking |
| `reaper-auplugins*.ini`, `reaper-vstplugins*.ini`, `reaper-clap*.ini` | regenerate | Outdated plugin scan caches |
| `MetadataCaches/`, `QueuedRenders/` | regenerate | Temporary/generated artifacts |
| `reaper-license.rk`, `reaper-reginfo*.ini` | exclude | REAPER registration material |
| unknown files | review | Avoid silently losing potentially personal data |

**Warning:** 0.2 is intentionally conservative. Until tested against user-specific
REAPER installations, it cannot guarantee complete automated restoration of every
workflow dependency or every SWS/ReaPack setting.
