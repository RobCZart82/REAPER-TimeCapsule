import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from reaper_timecapsule.background import BackgroundTask
from reaper_timecapsule.gui import (
    App, GUI_REPORT_CHUNK_CHARS, GUI_REPORT_MAX_CHARS, _bounded_report,
)


class BackgroundTaskTests(unittest.TestCase):
    def test_nonblocking_single_job_result_and_reuse(self):
        runner = BackgroundTask()
        entered, release = threading.Event(), threading.Event()
        def work():
            entered.set()
            if not release.wait(3):
                raise RuntimeError('test timeout')
            return 42
        try:
            runner.submit(work)
            self.assertTrue(entered.wait(3))
            self.assertIsNone(runner.poll())
            with self.assertRaises(RuntimeError):
                runner.submit(lambda: 0)
        finally:
            release.set()
        result = runner._results.get(timeout=3)
        runner._results.put(result)
        self.assertEqual(runner.poll(), ('success', 42))
        self.assertFalse(runner.active)
        runner.submit(lambda: 9)
        result = runner._results.get(timeout=3)
        runner._results.put(result)
        self.assertEqual(runner.poll(), ('success', 9))

    def test_worker_exception_is_delivered_not_raised_on_submit(self):
        runner = BackgroundTask()
        def fail():
            raise OSError('synthetic failure')
        runner.submit(fail)
        result = runner._results.get(timeout=3)
        runner._results.put(result)
        kind, error = runner.poll()
        self.assertEqual(kind, 'error')
        self.assertIsInstance(error, OSError)

    def test_thread_start_failure_resets_active_state(self):
        runner = BackgroundTask()
        with patch('reaper_timecapsule.background.threading.Thread.start', side_effect=RuntimeError('start')):
            with self.assertRaises(RuntimeError):
                runner.submit(lambda: None)
        self.assertFalse(runner.active)


class GUIBackgroundTests(unittest.TestCase):
    def app(self):
        return SimpleNamespace(runner=Mock(active=False), source=Mock(), archive=Mock(), destination=Mock(),
                               _set_busy=Mock(), after=Mock(), _poll_io=Mock(), _do=Mock(),
                               status=Mock(), destroy=Mock(), operation_control=Mock(), progress=Mock())

    def test_inputs_captured_before_worker_and_only_one_submission(self):
        app = self.app()
        app.source.get.return_value = 'source'
        app.archive.get.return_value = 'backup.zip'
        app.destination.get.return_value = 'new-folder'
        with patch('reaper_timecapsule.gui.make_backup') as backup:
            App._start_io(app, 'backup')
            action = app.runner.submit.call_args.args[0]
            for variable in (app.source, app.archive, app.destination):
                variable.get.side_effect = AssertionError('Tk read from worker')
            action()
            backup.assert_called_once_with('source', 'backup.zip', control=app.operation_control)
        app.runner.active = True
        App._start_io(app, 'backup')
        app.runner.submit.assert_called_once()

    def test_poll_pending_success_and_error_on_ui_thread(self):
        app = self.app()
        app.operation_control.latest.return_value = None
        app.runner.poll.return_value = None
        App._poll_io(app)
        app.after.assert_called_once()
        app.runner.poll.return_value = ('success', {'saved': 1})
        App._poll_io(app)
        self.assertEqual(app._do.call_args.args[0](), {'saved': 1})
        app.runner.poll.return_value = ('error', OSError('disk'))
        with patch('reaper_timecapsule.gui.messagebox.showerror') as error:
            App._poll_io(app)
            error.assert_called_once()
        app._set_busy.assert_called_with(False)

    def test_close_blocked_during_job_then_allowed(self):
        app = self.app()
        app.runner.active = True
        with patch('reaper_timecapsule.gui.messagebox.showinfo') as info:
            App._on_close(app)
            info.assert_called_once()
        app.destroy.assert_not_called()
        app.runner.active = False
        App._on_close(app)
        app.destroy.assert_called_once()

    def test_all_audits_capture_input_and_use_same_worker(self):
        for operation, target in [('scan', 'preview'), ('midi', 'validate_midi_workflow'), ('reapack', 'audit_reapack')]:
            with self.subTest(operation=operation):
                app = self.app()
                app.source.get.return_value = 'synthetic-source'
                with patch('reaper_timecapsule.gui.' + target) as audit, patch('reaper_timecapsule.gui.scan', return_value=[]):
                    App._start_io(app, operation)
                    action = app.runner.submit.call_args.args[0]
                    app.source.get.side_effect = AssertionError('Worker accessed Tk')
                    audit.return_value = {key: [] for key in ('files', 'counts', 'bytes', 'portable_names_ready', 'portability_issues', 'skipped_entries')}
                    action()
                    self.assertIs(audit.call_args.kwargs['control'], app.operation_control)

    def test_large_report_display_is_bounded_and_rendered_in_ui_chunks(self):
        callbacks = []
        log = Mock()
        app = SimpleNamespace(log=log, after=Mock(), _report_generation=0)
        app._append_report_chunk = lambda generation: App._append_report_chunk(app, generation)
        app.after.side_effect = lambda delay, callback: callbacks.append(callback)
        report = {'items': ['x' * 3000 for _ in range(500)]}

        App._do(app, lambda: report)
        while callbacks:
            callbacks.pop(0)()

        writes = [call.args[1] for call in log.insert.call_args_list]
        displayed = ''.join(writes)
        self.assertTrue(writes)
        self.assertTrue(all(len(part) <= GUI_REPORT_CHUNK_CHARS for part in writes[:-1]))
        self.assertLess(len(displayed), GUI_REPORT_MAX_CHARS + 256)
        self.assertIn('Display shortened at 256 KiB', displayed)

    def test_bounded_report_limits_large_strings_lists_and_nested_values(self):
        nested = 'too deep'
        for _ in range(20):
            nested = [nested]
        report = _bounded_report({
            'text': 'x' * 5000,
            'items': list(range(250)),
            'nested': nested,
        })
        self.assertIn('characters omitted', report['text'])
        self.assertIn('additional items omitted', report['items'][-1])
        nested = report['nested']
        while isinstance(nested, list):
            nested = nested[0]
        self.assertEqual(nested, '[nested value omitted: display depth limit]')

    def test_nonportable_backup_never_retries_without_explicit_opt_in(self):
        from reaper_timecapsule.core import NonPortableNames
        app = self.app()
        app._start_io = Mock()
        app.operation_control.latest.return_value = None
        app.runner.poll.return_value = ('error', NonPortableNames('synthetic'))
        with patch('reaper_timecapsule.gui.messagebox.askyesno', return_value=False):
            App._poll_io(app)
        app._start_io.assert_not_called()
        with patch('reaper_timecapsule.gui.messagebox.askyesno', return_value=True):
            App._poll_io(app)
        app._start_io.assert_called_once_with('native-backup')
