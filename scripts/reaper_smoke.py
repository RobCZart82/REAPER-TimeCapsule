#!/usr/bin/env python3
"""Prepare/launch a disposable REAPER smoke test; never read the personal profile.

Run explicitly, outside normal tests/CI. First-run REAPER dialogs may need manual
dismissal. Only the generated synthetic script is registered and executed.
"""
import argparse
import json
import subprocess
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare(parent):
    import tempfile
    workspace = Path(tempfile.mkdtemp(prefix='timecapsule-reaper-smoke-', dir=Path(parent).resolve()))
    root = workspace / 'profile'
    root.mkdir()
    (root / 'Scripts').mkdir()
    (root / 'reaper.ini').write_text('[REAPER]\nvst_scan=2\nloadlastproj=0\nverchk=0\ntinttcp=1\npeaksedges=1\n', encoding='utf-8')
    (root / 'reaper-menu.ini').write_text(
        (ROOT / 'tests/fixtures/midi-toolbar-native.ini').read_text() + '\nitem_1=40001 Synthetic extra button\n', encoding='utf-8')
    (root / 'Scripts/synthetic.lua').write_text('''local f = assert(io.open(reaper.GetResourcePath() .. '/action-ran.txt', 'w'))
f:write('synthetic-midi-action-ran')
f:close()
''', encoding='utf-8')
    # Exercise real staged apply before starting REAPER, using synthetic inputs.
    sys.path.insert(0, str(ROOT))
    from reaper_timecapsule.config_staging import export_preferences
    from reaper_timecapsule.config_apply import apply_preferences
    source = workspace / 'source'
    source.mkdir()
    (source / 'reaper.ini').write_text('[REAPER]\ntinttcp=0\n', encoding='utf-8')
    staging = workspace / 'TimeCapsule-Staging'
    staging.mkdir()
    archive = staging / 'review.timecapsule-stage.zip'
    export_preferences(source / 'reaper.ini', root / 'reaper.ini', archive,
                       selections=['REAPER/tinttcp'], source_version='7.84',
                       target_version='7.84', opt_in=True)
    apply_preferences(archive, root / 'reaper.ini', staging / 'recovery',
                      opt_in=True, reaper_closed=True)
    # JSON string literals work for these escaped Lua paths; ensure_ascii avoids
    # locale-dependent script encodings (Lua uses UTF-8 path bytes below).
    expected = json.dumps(str(root).replace('\\', '/'), ensure_ascii=False)
    (root / 'probe.lua').write_text('local expected = ' + expected + '''
local root = reaper.GetResourcePath():gsub('\\\\', '/')
assert(root == expected, 'Refusing to run outside disposable resource profile')
local pref_ok, pref = reaper.get_config_var_string('tinttcp')
assert(pref_ok and pref == '0', 'Applied appearance preference did not load')
local ok, hash = reaper.Menu_GetHash('Floating MIDI toolbar 1', 1)
assert(ok and hash ~= '', 'Native customized MIDI toolbar did not load')
local default_ok, default_hash = reaper.Menu_GetHash('Floating MIDI toolbar 1', 0)
assert(default_ok and hash ~= default_hash, 'Custom toolbar was replaced by default')
local command = reaper.AddRemoveReaScript(true, 32060, root .. '/Scripts/synthetic.lua', true)
assert(command > 0, 'MIDI script registration failed')
reaper.InsertTrackAtIndex(0, false)
local track = reaper.GetTrack(0, 0)
local item = reaper.CreateNewMIDIItemInProj(track, 0, 1, false)
reaper.SetMediaItemSelected(item, true)
reaper.Main_OnCommand(40153, 0)
local editor = reaper.MIDIEditor_GetActive()
assert(editor, 'Synthetic MIDI editor did not open')
assert(reaper.MIDIEditor_OnCommand(editor, command), 'MIDI command dispatch failed')
local function finish()
  local f = io.open(root .. '/action-ran.txt', 'r')
  if not f then reaper.defer(finish); return end
  assert(f:read('*a') == 'synthetic-midi-action-ran', 'Synthetic action result mismatch')
  f:close()
  local out = assert(io.open(root .. '/smoke-result.txt', 'w'))
  out:write('PASS\\n' .. reaper.GetAppVersion() .. '\\n' .. hash .. '\\n')
  out:close()
end
reaper.defer(finish)
''', encoding='utf-8')
    return root


def run(executable, parent, timeout=120):
    root = prepare(parent)
    # This process is always ours and has a fresh absolute resource path.
    with (root / 'process.log').open('wb') as log:
        process = subprocess.Popen([str(Path(executable).resolve()), '-newinst', '-cfgfile',
                                    str(root / 'reaper.ini'), '-nosplash', str(root / 'probe.lua')],
                                   stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                result = root / 'smoke-result.txt'
                if result.exists():
                    lines = result.read_text(encoding='utf-8').splitlines()
                    if len(lines) != 3 or lines[0] != 'PASS':
                        raise ValueError('Invalid smoke result')
                    return dict(passed=True, version=lines[1], toolbar_hash=lines[2],
                                profile=str(root), visual_icon_rendering_verified=False)
                if process.poll() is not None:
                    raise RuntimeError('REAPER exited without a smoke result: ' + str(root))
                time.sleep(0.25)
            raise RuntimeError('Smoke test timed out; inspect first-run dialogs/profile: ' + str(root))
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reaper', type=Path, required=True, help='REAPER executable, not app bundle')
    parser.add_argument('--parent', type=Path, required=True, help='Existing external test directory')
    parser.add_argument('--timeout', type=int, default=120)
    args = parser.parse_args()
    print(json.dumps(run(args.reaper, args.parent, args.timeout), indent=2))
