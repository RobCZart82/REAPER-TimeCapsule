"""Cooperative cancellation and bounded latest-progress delivery."""
import threading


class OperationCancelled(Exception):
    pass


class OperationControl:
    def __init__(self):
        self._cancelled = threading.Event()
        self._lock = threading.Lock()
        self._latest = None

    @property
    def cancel_requested(self):
        return self._cancelled.is_set()

    def cancel(self):
        self._cancelled.set()

    def checkpoint(self, phase, completed=0, total=0):
        if self._cancelled.is_set():
            raise OperationCancelled('Operation cancelled; no completed result published')
        with self._lock:
            self._latest = (phase, completed, total)

    def latest(self):
        with self._lock:
            return self._latest


def checkpoint(control, phase, completed=0, total=0):
    if control is not None:
        control.checkpoint(phase, completed, total)
