# Isolated REAPER smoke workflow

This optional developer workflow is separate from `midi-audit`, the desktop app
and normal CI. It registers and executes **only a generated synthetic Lua script**
in a newly created temporary profile. It never imports user menus, scripts,
license files, plugin caches or personal settings. An installed REAPER executable
and a graphical desktop session are required; no REAPER binary is distributed.

```sh
python scripts/reaper_smoke.py --reaper /path/to/REAPER-executable --parent /external/test-work
```

The parent must exist. The runner creates a unique workspace with a profile,
synthetic source and external `TimeCapsule-Staging` recovery bundle. It exercises
staged apply before launch, then starts `-newinst -cfgfile ABSOLUTE/reaper.ini`.
REAPER's built-in `-h` describes that an absolute cfgfile selects an alternate
resource directory. The Lua probe asserts `GetResourcePath()` before doing work.
First-run audio/evaluation dialogs may require dismissal; choose no audio-device
setup. No license/configuration should be copied in to bypass those dialogs.

The probe checks:

- The actual REAPER config variable `tinttcp` loads the applied value `0`.
- The custom MIDI toolbar hash exists and differs from the default toolbar.
- A synthetic script registers in MIDI section 32060.
- A newly generated MIDI item opens in the MIDI editor, command dispatch succeeds,
  and the synthetic action writes its expected marker.

The runner terminates **only the process it launched**, after result or timeout.
The synthetic workspace remains for inspection. A timeout/nonzero exit/missing
result is a failure, never a pass. Static `midi-audit` reports continue to state
`runtime_validation: not-performed`; this separate test proves only its synthetic
case and does not validate the user's recovered scripts, extensions or workflow.
Icon PNG presence does not prove successful image decoding or visual appearance.

## Native toolbar-format evidence

On 2026-11-07, a separate REAPER 7.84/macOS-arm64 evaluation instance was launched
with an absolute cfgfile in a disposable profile. In Options → Customize
menus/toolbars → Floating MIDI toolbar 1, the initial Edit me button was assigned
`toolbar_dock_off.png` using REAPER's native icon picker, then Apply was pressed.
The resulting minimal file is committed as `tests/fixtures/midi-toolbar-native.ini`:

```ini
[Floating MIDI toolbar 1]
default=2bcb4157b56ed885
icon_0=toolbar_dock_off.png
item_0=41101 Edit me
```

This directly establishes matching numeric item/icon indices for the MIDI toolbar.
The fixture contains no private workflow, license or third-party script bundle.
The audit uses this form for floating MIDI and MIDI piano-roll toolbars; unrelated
sections retain their existing treatment. Unsupported icon references require
review and are never used as filesystem paths.

## Recorded local validation

2026-11-07: REAPER **7.84/macOS-arm64**, all four probe groups passed. Customized
MIDI toolbar hash with the synthetic extra button: `2ce54e81e87899da`. Native icon
assignment was also confirmed through REAPER's picker/preview. Automated visual
icon rendering, full user workflow recovery and real Windows/Linux REAPER runs
are **not claimed**.

API reference: [official ReaScript API](https://www.reaper.fm/sdk/reascript/reascripthelp.html)
(`GetResourcePath`, `get_config_var_string`, `Menu_GetHash`, `AddRemoveReaScript`,
`MIDIEditor_OnCommand`).
