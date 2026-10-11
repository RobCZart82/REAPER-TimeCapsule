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
NAME = 'REAPER Time Capsule'
sys.path.insert(0, str(ROOT))
from reaper_timecapsule.core import VERSION


def run(*arguments):
    subprocess.run(arguments, cwd=ROOT, check=True)


def main():
    if sys.platform not in ('darwin', 'win32'):
        raise SystemExit('Desktop beta builds support macOS and Windows')
    options = ['--onedir', '--windowed', '--noupx', '--name', NAME,
               '--icon', str(ROOT / 'reaper_timecapsule/assets' /
                ('timecapsule.icns' if sys.platform == 'darwin' else 'timecapsule.ico')),
               '--add-data', 'reaper_timecapsule/assets:reaper_timecapsule/assets',
               '--add-data', 'LICENSE:.', '--add-data', 'README.md:.', 'launcher.py']
    if sys.platform == 'darwin':
        # Generate the spec first so BUNDLE writes metadata before ad-hoc signing.
        run(sys.executable, '-m', 'PyInstaller.utils.cliutils.makespec', *options)
        spec = ROOT / (NAME + '.spec')
        text = spec.read_text(encoding='utf-8')
        marker = '    bundle_identifier=None,'
        if text.count(marker) != 1:
            raise SystemExit('Unexpected PyInstaller BUNDLE template')
        metadata = {'CFBundleName': NAME, 'CFBundleDisplayName': NAME,
                    'CFBundleShortVersionString': VERSION,
                    'CFBundleVersion': VERSION.replace('-beta.', '.')}
        text = text.replace(marker, "    bundle_identifier='org.robczart82.reaper-time-capsule',"
                            + '\n    info_plist=' + repr(metadata) + ',')
        spec.write_text(text, encoding='utf-8')
        run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', str(spec))
        import plistlib
        plist = ROOT / 'dist' / (NAME + '.app') / 'Contents/Info.plist'
        with plist.open('rb') as stream:
            actual = plistlib.load(stream)
        assert all(actual.get(key) == value for key, value in metadata.items())
    else:
        run(sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', *options)
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
