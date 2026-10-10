"""Single-operation worker. No Tk calls from worker threads."""
import queue
import threading


class BackgroundTask:
    def __init__(self):
        self._results = queue.Queue(maxsize=1)
        self._lock = threading.Lock()
        self._active = False

    @property
    def active(self):
        with self._lock:
            return self._active

    def submit(self, action):
        with self._lock:
            if self._active:
                raise RuntimeError('An operation is already running')
            self._active = True
        def run():
            try:
                result = ('success', action())
            except Exception as exc:
                result = ('error', exc)
            self._results.put(result)
        try:
            threading.Thread(target=run, name='TimeCapsule-IO', daemon=False).start()
        except Exception:
            with self._lock:
                self._active = False
            raise

    def poll(self):
        try:
            result = self._results.get_nowait()
        except queue.Empty:
            return None
        with self._lock:
            self._active = False
        return result
