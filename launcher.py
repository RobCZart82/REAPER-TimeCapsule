"""Standalone GUI entry point; self-test uses synthetic temporary data only."""
import json
import sys
import tempfile
import time
from types import SimpleNamespace
from pathlib import Path

from reaper_timecapsule.core import VERSION, make_backup, verify_backup, restore_backup, preview
from reaper_timecapsule.gui import App
from reaper_timecapsule.operation import OperationControl, OperationCancelled


def wait_for_geometry(app, width, height):
    # Native window-manager configure events can arrive after idle layout.
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        app.update()
        if (app.winfo_width(), app.winfo_height()) == (width, height):
            return
        time.sleep(0.01)
    raise AssertionError((app.winfo_width(), app.winfo_height(), width, height))


def self_test(report):
    with tempfile.TemporaryDirectory(prefix='timecapsule-selftest-') as temporary:
        root = Path(temporary).resolve()
        source = root / 'synthetic-source'
        source.mkdir()
        (source / 'reaper-kb.ini').write_text('synthetic action', encoding='utf-8')
        (source / 'reaper.ini').write_text('[REAPER]\ntinttcp=0\n', encoding='utf-8')
        archive = root / 'synthetic.zip'
        make_backup(source, archive)
        verify_backup(archive)
        destination = root / 'Recovered'
        restore_backup(archive, destination)
        assert (destination / 'REAPER/reaper-kb.ini').read_text() == 'synthetic action'
        assert (destination / 'NeedsReview/reaper.ini').is_file()
        if sys.platform == 'darwin':
            (source / 'presets').mkdir()
            preset = source / 'presets/au-example: Synth-builtin.ini'
            preset.write_text('synthetic preset', encoding='utf-8')
            scanned = preview(source)
            assert scanned['files'] == 3 and not scanned['portable_names_ready']
            assert App._brief(scanned)['portability_issues'][0]['path'] == 'presets/au-example: Synth-builtin.ini'
            try:
                make_backup(source, root / 'not-portable.zip')
            except ValueError as exc:
                assert 'Cannot create a portable backup' in str(exc)
            else:
                raise AssertionError('Nonportable backup was accepted')
            assert not (root / 'not-portable.zip').exists()
            assert preset.read_text() == 'synthetic preset'
            preset.unlink()
        control = OperationControl()
        control.cancel()
        try:
            make_backup(source, root / 'cancelled.zip', control=control)
        except OperationCancelled:
            pass
        else:
            raise AssertionError('Cancellation failed')
        app = App()
        wait_for_geometry(app, app.fixed_width, app.minimum_height)
        assert tuple(map(int, app.resizable())) == (0, 1)
        width, height = app.winfo_width(), app.winfo_height()
        first, last = app.action_buttons[0], app.action_buttons[-1]
        left_margin = first.winfo_rootx() - app.winfo_rootx()
        right_margin = app.winfo_rootx() + width - last.winfo_rootx() - last.winfo_width()
        assert abs(left_margin - right_margin) <= 1, (left_margin, right_margin)
        log_height = app.log.winfo_height()
        app._begin_vertical_resize(SimpleNamespace(y_root=0))
        app._drag_vertical_resize(SimpleNamespace(y_root=80))
        wait_for_geometry(app, width, height + 80)
        assert app.winfo_width() == width and app.winfo_height() == height + 80
        assert app.log.winfo_height() > log_height
        app.withdraw()
        app.update_idletasks()
        tcl_version = app.tk.call('info', 'patchlevel')
        tk_version = app.tk.call('package', 'require', 'Tk')
        app.destroy()
    Path(report).write_text(json.dumps(dict(valid=True, version=VERSION, python=sys.version,
                                          tcl=tcl_version, tk=tk_version, synthetic_only=True)), encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        self_test(sys.argv[2])
    elif len(sys.argv) == 1:
        App().mainloop()
    else:
        raise SystemExit('Usage: REAPER-TimeCapsule [--self-test REPORT]')
