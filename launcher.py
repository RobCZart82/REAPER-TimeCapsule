"""Standalone GUI entry point; self-test uses synthetic temporary data only."""
import json
import sys
import tempfile
from pathlib import Path

from reaper_timecapsule.core import VERSION, make_backup, verify_backup, restore_backup
from reaper_timecapsule.gui import App
from reaper_timecapsule.operation import OperationControl, OperationCancelled


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
        control = OperationControl()
        control.cancel()
        try:
            make_backup(source, root / 'cancelled.zip', control=control)
        except OperationCancelled:
            pass
        else:
            raise AssertionError('Cancellation failed')
        app = App()
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
