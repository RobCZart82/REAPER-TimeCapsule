import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from reaper_timecapsule.background import BackgroundTask
from reaper_timecapsule.gui import App


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
                               status=Mock(), destroy=Mock())

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
            backup.assert_called_once_with('source', 'backup.zip')
        app.runner.active = True
        App._start_io(app, 'backup')
        app.runner.submit.assert_called_once()

    def test_poll_pending_success_and_error_on_ui_thread(self):
        app = self.app()
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
