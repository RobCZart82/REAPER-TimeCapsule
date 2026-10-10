# User-requested functionality (reference only)

## REAPER workflow

- Maintain full customized Main + MIDI Editor toolbar / icons.
- Restore chord display and composing scripts (Chordbox, Lil Chordbox, Gridbox, ChordGun).
- Preserve MIDI Editor right-click chords/scales/arpeggios menu **and** its matching
  ReaperKeyMap custom actions and ID mapping. Original third-party archive remains
  outside the distributable source tree until redistribution permission is verified.
- Restore ReaPack repositories, enabled states, and global options.
- Preserve SWS configurations; detect architecture/version of ReaPack and SWS binaries
  before reinstalling (platform compatibility required).
- Preserve Hungarian LangPack and personalized themes, while preferring factory files
  from fresh REAPER installation wherever possible.
- Old plugin discovery cache files MUST NOT be restored into fresh REAPER.

## ReaPack repository screenshot (2026-10-10)

These entries reflect a *user-provided screenshot*, not a parsed live ReaPack database.
Future scanner should derive the actual enabled state from the installed REAPER resources.

| Label | Enabled | Index URL |
| --- | --- | --- |
| ReaPack | yes | https://reapack.com/index.xml |
| ReaTeam Scripts | yes | https://github.com/ReaTeam/ReaScripts/raw/master/index.xml |
| ReaTeam JSFX | yes | https://github.com/ReaTeam/JSFX/raw/master/index.xml |
| ReaTeam Themes | no | https://github.com/ReaTeam/Themes/raw/master/index.xml |
| ReaTeam LangPacks | no | https://github.com/ReaTeam/LangPacks/raw/master/index.xml |
| ReaTeam Extensions | yes | https://github.com/ReaTeam/Extensions/raw/master/index.xml |
| MPL Scripts | yes | https://github.com/MichaelPilyavskiy/ReaScripts/raw/master/index.xml |
| X-Raym Scripts | yes | https://github.com/X-Raym/REAPER-ReaScripts/raw/master/index.xml |
| FTC Tools | yes | https://raw.githubusercontent.com/iliaspoulakis/Reaper-Tools/master/index.xml |
| TK Scripts | yes | https://raw.githubusercontent.com/TouristKiller/TK-Scripts/master/index.xml |

Global options: install new packages when synchronizing ON; enable pre-releases globally OFF;
prompt to uninstall obsolete packages ON; search synonyms of common words ON.
Never run automatic post-restore repository synchronization without explicit permission.
