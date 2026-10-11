"""Build a native unsigned beta and exercise the actual bundled executable."""
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = 'REAPER-TimeCapsule'


def run(*arguments):
    subprocess.run(arguments, cwd=ROOT, check=True)


def main():
    if sys.platform not in ('darwin', 'win32'):
        raise SystemExit('Desktop beta builds support macOS and Windows')
    run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
        '--noupx', '--name', NAME, '--icon', str(ROOT / 'reaper_timecapsule/assets' /
         ('timecapsule.icns' if sys.platform == 'darwin' else 'timecapsule.ico')),
        '--add-data', 'reaper_timecapsule/assets:reaper_timecapsule/assets',
        '--add-data', 'LICENSE:.', '--add-data', 'README.md:.', 'launcher.py')
    executable = (ROOT / 'dist' / (NAME + '.app') / 'Contents/MacOS' / NAME if sys.platform == 'darwin'
                  else ROOT / 'dist' / NAME / (NAME + '.exe'))
    report = ROOT / 'work' / 'bundled-selftest.json'
    report.parent.mkdir(exist_ok=True)
    subprocess.run([str(executable), '--self-test', str(report)], check=True, timeout=120, cwd=ROOT)
    result = json.loads(report.read_text(encoding='utf-8'))
    if not result.get('valid') or not result.get('synthetic_only'):
        raise SystemExit('Bundled self-test did not pass')
    output = ROOT / 'release-artifacts'
    output.mkdir(exist_ok=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    # Distribution sources are an exact tracked Git snapshot, never local user data.
    source = output / ('source-' + commit[:12] + '.zip')
    run('git', 'archive', '--format=zip', '--output=' + str(source), commit)
    with tempfile.TemporaryDirectory(prefix='timecapsule-package-') as temporary:
        package = Path(temporary) / NAME
        package.mkdir()
        binary = ROOT / 'dist' / (NAME + '.app' if sys.platform == 'darwin' else NAME)
        shutil.copytree(binary, package / binary.name, symlinks=True)
        for filename in ('LICENSE', 'README.md', 'README_HU.md', 'THIRD_PARTY_NOTICES.md'):
            shutil.copy2(ROOT / filename, package / filename)
        shutil.copytree(ROOT / 'docs', package / 'docs')
        shutil.copytree(ROOT / 'runtime-licenses', package / 'runtime-licenses')
        shutil.copy2(source, package / source.name)
        shutil.copy2(report, package / 'bundled-selftest.json')
        artifact = output / f'{NAME}-{result["version"]}-{platform.system()}-{platform.machine()}-unsigned'
        if sys.platform == 'darwin':
            # Preserve .app framework symlinks and executable permissions.
            run('ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(package), str(artifact) + '.zip')
        else:
            shutil.make_archive(str(artifact), 'zip', root_dir=temporary, base_dir=NAME)
    metadata = dict(commit=commit, self_test=result, unsigned=True, platform=platform.system(),
                    architecture=platform.machine())
    (output / 'build-manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    lines = [hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name
             for path in sorted(output.iterdir()) if path.is_file() and path.name != 'SHA256SUMS.txt']
    (output / 'SHA256SUMS.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
