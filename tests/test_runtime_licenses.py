"""Offline runtime-notice retry regressions; no network or real Tk window."""
import io
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import runtime_licenses as notices


def http_error(code, retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError("https://example.org/LICENSE", code, "synthetic", headers, io.BytesIO())


def response(data=b"x" * 100):
    result = MagicMock()
    result.__enter__.return_value = result
    result.read.return_value = data
    return result


class RuntimeLicenseTests(unittest.TestCase):
    def test_429_retries_and_preserves_successful_notice(self):
        reply = response()
        with patch.object(notices.urllib.request, "urlopen", side_effect=[http_error(429, "3"), reply]) as open_url, \
             patch.object(notices.time, "sleep") as sleep:
            self.assertEqual(notices.fetch_notice("https://example.org/LICENSE"), b"x" * 100)
        self.assertEqual(open_url.call_count, 2)
        sleep.assert_called_once_with(3)
        self.assertEqual(open_url.call_args.kwargs["timeout"], 30)
        self.assertTrue(open_url.call_args.args[0].get_header("User-agent"))
        reply.read.assert_called_once_with(notices.MAX_NOTICE_BYTES + 1)

    def test_transient_status_uses_bounded_exponential_backoff(self):
        with patch.object(notices.urllib.request, "urlopen", side_effect=[
            http_error(503), http_error(502), response()
        ]), patch.object(notices.time, "sleep") as sleep:
            notices.fetch_notice("https://example.org/LICENSE")
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4])

    def test_http_date_retry_after_and_server_delay_are_bounded(self):
        with patch.object(notices.time, "time", return_value=0):
            self.assertEqual(notices.retry_delay({"Retry-After": "Thu, 01 Jan 1970 00:00:12 GMT"}, 0), 12)
            self.assertEqual(notices.retry_delay({"Retry-After": "Thu, 01 Jan 1970 01:00:00 GMT"}, 0), 30)
        self.assertEqual(notices.retry_delay({"Retry-After": "999999999"}, 0), 30)

    def test_invalid_or_past_retry_after_uses_backoff(self):
        for value in ("invalid", "-1", "NaN", ""):
            with self.subTest(value=value):
                self.assertEqual(notices.retry_delay({"Retry-After": value}, 1), 4)
        with patch.object(notices.time, "time", return_value=100):
            self.assertEqual(notices.retry_delay({"Retry-After": "Thu, 01 Jan 1970 00:00:00 GMT"}, 0), 2)

    def test_permanent_http_failure_is_not_retried(self):
        error = http_error(404)
        with patch.object(notices.urllib.request, "urlopen", side_effect=error) as open_url, \
             patch.object(notices.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                notices.fetch_notice("https://example.org/LICENSE")
        self.assertIs(caught.exception, error)
        open_url.assert_called_once()
        sleep.assert_not_called()

    def test_retry_exhaustion_propagates_failure(self):
        with patch.object(notices.urllib.request, "urlopen", side_effect=[
            http_error(429) for _ in range(notices.MAX_ATTEMPTS)
        ]) as open_url, patch.object(notices.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.HTTPError):
                notices.fetch_notice("https://example.org/LICENSE")
        self.assertEqual(open_url.call_count, 4)
        self.assertEqual(sleep.call_count, 3)

    def test_invalid_response_sizes_are_not_retried(self):
        for data in (b"short", b"x" * (notices.MAX_NOTICE_BYTES + 1)):
            with self.subTest(size=len(data)), \
                 patch.object(notices.urllib.request, "urlopen", return_value=response(data)) as open_url, \
                 patch.object(notices.time, "sleep") as sleep:
                with self.assertRaises(RuntimeError):
                    notices.fetch_notice("https://example.org/LICENSE")
                open_url.assert_called_once()
                sleep.assert_not_called()

    def test_non_http_network_error_is_not_silently_accepted(self):
        with patch.object(notices.urllib.request, "urlopen", side_effect=urllib.error.URLError("synthetic")), \
             patch.object(notices.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.URLError):
                notices.fetch_notice("https://example.org/LICENSE")
        sleep.assert_not_called()

    def test_import_has_no_gui_network_or_file_side_effects(self):
        import runpy
        with patch.object(notices.tkinter, "Tk") as tk, \
             patch.object(notices.urllib.request, "urlopen") as network, \
             patch.object(Path, "mkdir") as mkdir:
            runpy.run_path(notices.__file__, run_name="notice_import_probe")
        tk.assert_not_called()
        network.assert_not_called()
        mkdir.assert_not_called()

    def test_main_collects_all_required_notices_and_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            app = MagicMock()
            app.tk.call.side_effect = ["8.6.16", "8.6.16"]
            with patch.object(notices, "__file__", str(root / "scripts" / "runtime_licenses.py")), \
                 patch.object(notices.tkinter, "Tk", return_value=app), \
                 patch.object(notices.importlib.metadata, "version", return_value="6.16.0"), \
                 patch.object(notices.ssl, "OPENSSL_VERSION", "OpenSSL 3.1.0 synthetic"), \
                 patch.object(notices, "fetch_notice", return_value=b"notice" * 20) as fetch:
                notices.main()
            folder = root / "runtime-licenses"
            self.assertEqual(fetch.call_count, 10)
            sources = (folder / "SOURCES.txt").read_text(encoding="utf-8")
            self.assertEqual(len(sources.splitlines()), 10)
            self.assertEqual(len(list(folder.iterdir())), 11)
            self.assertEqual((folder / "CPython-LICENSE.txt").read_bytes(), b"notice" * 20)
            app.destroy.assert_called_once()

    def test_main_identifies_required_notice_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            app = MagicMock()
            app.tk.call.side_effect = ["8.6.16", "8.6.16"]
            with patch.object(notices, "__file__", str(root / "scripts" / "runtime_licenses.py")), \
                 patch.object(notices.tkinter, "Tk", return_value=app), \
                 patch.object(notices.importlib.metadata, "version", return_value="6.16.0"), \
                 patch.object(notices.ssl, "OPENSSL_VERSION", "OpenSSL 3.1.0 synthetic"), \
                 patch.object(notices, "fetch_notice", side_effect=http_error(429)):
                with self.assertRaisesRegex(RuntimeError, "CPython-LICENSE.txt"):
                    notices.main()
            self.assertFalse((root / "runtime-licenses" / "SOURCES.txt").exists())
