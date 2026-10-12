"""Collect upstream notices for the concrete Python/Tcl/Tk build runtime."""
import sys
import ssl
import http.client
import time
import tkinter
import urllib.error
import urllib.request
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import importlib.metadata

MAX_ATTEMPTS = 4
MAX_RETRY_DELAY = 30
MAX_NOTICE_BYTES = 1024 * 1024
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


def retry_delay(headers, attempt):
    """Bound server Retry-After (delta seconds or HTTP date) and backoff."""
    delay = 2 ** (attempt + 1)
    value = headers.get("Retry-After") if headers else None
    if value:
        try:
            if value.isascii() and value.isdecimal():
                requested = int(value)
            else:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                requested = max(0, date.timestamp() - time.time())
            delay = max(delay, requested)
        except (ValueError, TypeError, OverflowError):
            pass
    return min(delay, MAX_RETRY_DELAY)


def fetch_notice(url):
    """Retry transient HTTP failures only; never bypass missing notices."""
    request = urllib.request.Request(
        url, headers={"User-Agent": "REAPER-TimeCapsule-runtime-license-collector/1"}
    )
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read(MAX_NOTICE_BYTES + 1)
            if not 100 <= len(data) <= MAX_NOTICE_BYTES:
                raise RuntimeError("Runtime license response is missing or exceeds the size limit")
            return data
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE_HTTP_STATUS or attempt + 1 == MAX_ATTEMPTS:
                raise
            delay = retry_delay(exc.headers, attempt)
            code = exc.code
            exc.close()
            print(f"Runtime notice HTTP {code}; retry {attempt + 2}/{MAX_ATTEMPTS} "
                  f"after {delay:g}s", file=sys.stderr)
            time.sleep(delay)


def main():
    root = Path(__file__).resolve().parents[1] / 'runtime-licenses'
    root.mkdir(exist_ok=True)
    app = tkinter.Tk()
    app.withdraw()
    versions = dict(tcl=app.tk.call('info', 'patchlevel'), tk=app.tk.call('package', 'require', 'Tk'))
    app.destroy()
    python_version = '.'.join(map(str, sys.version_info[:3]))
    urls = {'CPython-LICENSE.txt': f'https://raw.githubusercontent.com/python/cpython/v{python_version}/LICENSE',
            'PyInstaller-COPYING.txt': f'https://raw.githubusercontent.com/pyinstaller/pyinstaller/v{importlib.metadata.version("pyinstaller")}/COPYING.txt'}
    # Runtime-library upstream notices; system versions are recorded separately.
    urls.update({
        'zlib-LICENSE.txt': 'https://raw.githubusercontent.com/madler/zlib/master/LICENSE',
        'libffi-LICENSE.txt': 'https://raw.githubusercontent.com/libffi/libffi/master/LICENSE',
        'bzip2-LICENSE.txt': 'https://sourceware.org/git/?p=bzip2.git;a=blob_plain;f=LICENSE;hb=bzip2-1.0.8',
        'xz-COPYING.txt': 'https://raw.githubusercontent.com/tukaani-project/xz/master/COPYING',
        'sqlite-COPYRIGHT.html': 'https://www.sqlite.org/copyright.html',
    })
    openssl = ssl.OPENSSL_VERSION.split()[1]
    if openssl.startswith('3.'):
        urls['OpenSSL-LICENSE.txt'] = f'https://raw.githubusercontent.com/openssl/openssl/openssl-{openssl}/LICENSE.txt'
    else:
        raise RuntimeError('Review OpenSSL runtime notices for this version')
    for library, version in versions.items():
        tag = 'core-' + version.replace('.', '-')
        urls[library + '-license.terms'] = f'https://raw.githubusercontent.com/tcltk/{library}/{tag}/license.terms'
    for name, url in urls.items():
        try:
            data = fetch_notice(url)
        except (OSError, RuntimeError, http.client.HTTPException) as exc:
            raise RuntimeError("Could not collect required runtime notice: " + name) from exc
        (root / name).write_bytes(data)
    (root / 'SOURCES.txt').write_text('\n'.join(name + ': ' + url for name, url in urls.items()) + '\n', encoding='utf-8')


if __name__ == "__main__":
    main()

