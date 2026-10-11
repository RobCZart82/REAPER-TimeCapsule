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
        wait_for_geometry(app, app.default_width, app.minimum_height)
        about = app._show_about()
        app.update()
        assert app._show_about() is about
        assert all(image.width() > 0 and image.height() > 0 for image in about.images.values())
        about.event_generate('<Escape>')
        app.update()
        if about.winfo_exists():
            about.destroy()
        assert app._show_about() is not about
        app.about_window.destroy()
        assert tuple(map(int, app.resizable())) == (1, 1)
        width, height = app.winfo_width(), app.winfo_height()
        first, last = app.action_buttons[0], app.action_buttons[-1]
        left_margin = first.winfo_rootx() - app.winfo_rootx()
        right_margin = app.winfo_rootx() + width - last.winfo_rootx() - last.winfo_width()
        assert abs(left_margin - right_margin) <= 1, (left_margin, right_margin)
        assert len({entry.winfo_rootx() for entry in app.path_entries}) == 1
        assert len({button.winfo_rootx() for button in app.browse_buttons}) == 1
        label_edge = max(label.winfo_rootx() + label.winfo_width() for label in app.path_labels)
        assert app.path_entries[0].winfo_rootx() - label_edge == 12
        assert app.path_labels[0].winfo_rootx() == first.winfo_rootx()
        assert app.browse_buttons[0].winfo_rootx() + app.browse_buttons[0].winfo_width() == last.winfo_rootx() + last.winfo_width()
        assert app.log.cget('wrap') == 'none'
        app.log.delete('1.0', 'end')
        app.log.insert('1.0', ('X' * 2000 + '\n') * 100)
        for _ in range(3):
            app.update()
        assert app.vertical_scroll.winfo_ismapped() and app.horizontal_scroll.winfo_ismapped()
        app.log.delete('1.0', 'end')
        app.log.insert('1.0', 'Short output')
        for _ in range(3):
            app.update()
        assert not app.vertical_scroll.winfo_ismapped() and not app.horizontal_scroll.winfo_ismapped()
        # A wide line entering/leaving the bottom of the visible viewport
        # previously made auto-hiding bars resize the viewport indefinitely.
        app.log.delete('1.0', 'end')
        app.log.insert('1.0', '\n'.join('X' * 2000 if index == 50 else 'short line'
                                     for index in range(100)))
        app.update()
        viewport = (app.log.winfo_width(), app.log.winfo_height())
        horizontal_states = set()
        for line in list(range(35, 57)) + list(range(56, 34, -1)):
            app.log.yview(f'{line}.0')
            app.update()
            assert (app.log.winfo_width(), app.log.winfo_height()) == viewport
            horizontal_states.add(bool(app.horizontal_scroll.winfo_ismapped()))
        assert horizontal_states == {False, True}
        app.log.delete('1.0', 'end')
        app.log.insert('1.0', 'Short output')
        app.update()
        app.geometry(f'{width + 80}x{height}')
        wait_for_geometry(app, width + 80, height)
        width += 80
        log_height = app.log.winfo_height()
        app._begin_vertical_resize(SimpleNamespace(y_root=0))
        app._drag_vertical_resize(SimpleNamespace(y_root=40))
        wait_for_geometry(app, width, height + 40)
        assert app.winfo_width() == width and app.winfo_height() == height + 40
        assert app.log.winfo_height() > log_height
        app.withdraw()
        app.update_idletasks()
        tcl_version = app.tk.call('info', 'patchlevel')
        tk_version = app.tk.call('package', 'require', 'Tk')
        app.destroy()
        fresh = App()
        wait_for_geometry(fresh, fresh.default_width, fresh.minimum_height)
        assert fresh.winfo_width() == width - 80 and fresh.winfo_height() == height
        fresh.destroy()
    Path(report).write_text(json.dumps(dict(valid=True, version=VERSION, python=sys.version,
                                          tcl=tcl_version, tk=tk_version, synthetic_only=True)), encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        self_test(sys.argv[2])
    elif len(sys.argv) == 1:
        App().mainloop()
    else:
        raise SystemExit('Usage: REAPER-TimeCapsule [--self-test REPORT]')
