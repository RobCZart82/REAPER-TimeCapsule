"""Collect upstream notices for the concrete Python/Tcl/Tk build runtime."""
import sys
import tkinter
import urllib.request
from pathlib import Path
import importlib.metadata

root = Path(__file__).resolve().parents[1] / 'runtime-licenses'
root.mkdir(exist_ok=True)
app = tkinter.Tk()
app.withdraw()
versions = dict(tcl=app.tk.call('info', 'patchlevel'), tk=app.tk.call('package', 'require', 'Tk'))
app.destroy()
python_version = '.'.join(map(str, sys.version_info[:3]))
urls = {'CPython-LICENSE.txt': f'https://raw.githubusercontent.com/python/cpython/v{python_version}/LICENSE',
        'PyInstaller-COPYING.txt': f'https://raw.githubusercontent.com/pyinstaller/pyinstaller/v{importlib.metadata.version("pyinstaller")}/COPYING.txt'}
for library, version in versions.items():
    tag = 'core-' + version.replace('.', '-')
    urls[library + '-license.terms'] = f'https://raw.githubusercontent.com/tcltk/{library}/{tag}/license.terms'
for name, url in urls.items():
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    if len(data) < 100:
        raise RuntimeError('Missing runtime license: ' + name)
    (root / name).write_bytes(data)
(root / 'SOURCES.txt').write_text('\n'.join(name + ': ' + url for name, url in urls.items()) + '\n', encoding='utf-8')
