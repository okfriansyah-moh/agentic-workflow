"""Pinned external runtimes, installed outside the workflow bundle."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]


def read_lock():
    return json.loads((ROOT / 'profiles/tools-lock.json').read_text())


def safe_path(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Tool path must stay under its managed root')
    destination = Path(root) / relative
    for parent in (destination, *destination.parents):
        if parent == Path(root).parent:
            break
        if parent.is_symlink():
            raise ValueError('Managed tool paths cannot traverse symbolic links')
    return destination


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, indent=2) + '\n')
        temp.chmod(0o600)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tree_digest(root):
    result = hashlib.sha256()
    for path in sorted(Path(root).rglob('*')):
        if '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        if path.is_symlink():
            content = 'link:' + os.readlink(path)
        elif path.is_file():
            with path.open('rb') as stream:
                content = hashlib.file_digest(stream, 'sha256').hexdigest()
        else:
            continue
        result.update((path.relative_to(root).as_posix() + '\0' + content + '\n').encode())
    return result.hexdigest()


def run(argv, cwd=None, env=None, timeout=600):
    """Return output only to internal validation, never retain command streams."""
    process = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                             text=True, timeout=timeout, check=False)
    if process.returncode:
        raise RuntimeError(f'Tool command failed with exit {process.returncode}; output was not retained')
    return process.stdout.strip()


def executable(value, candidates):
    paths = [value] if value else candidates
    for candidate in paths:
        found = shutil.which(candidate)
        if found:
            return str(Path(found).resolve())
    raise ValueError('Required executable is unavailable: ' + ', '.join(paths))


def node_runtime(requested=None):
    candidates = ['/opt/homebrew/opt/node/bin/node', 'node']
    node = executable(requested, candidates)
    version = run([node, '--version'], timeout=30)
    if int(version.lstrip('v').split('.')[0]) < read_lock()['playwright-cli']['node_minimum']:
        raise ValueError('Pinned Playwright driver requires Node 20 or later')
    npm = executable(None, ['npm'])
    return node, npm, version


def python_runtime(requested=None):
    python = executable(requested, [sys.executable, 'python3'])
    version = run([python, '-c', 'import platform; print(platform.python_version())'], timeout=30)
    if '.'.join(version.split('.')[:2]) != read_lock()['strix']['python_minor']:
        raise ValueError('This reviewed Strix dependency lock requires Python 3.13')
    return python, version


def runtime_env(node=None, destination=None):
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    env['PIP_NO_CACHE_DIR'] = '1'
    if destination:
        env['HOME'] = str(destination / 'setup-home')
        env['NPM_CONFIG_CACHE'] = str(destination / 'setup-cache')
        env['NPM_CONFIG_USERCONFIG'] = os.devnull
    if node:
        env['PATH'] = str(Path(node).parent) + os.pathsep + env.get('PATH', '')
        env['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
    return env


def install_playwright(destination, node=None):
    lock = read_lock()['playwright-cli']
    node, npm, version = node_runtime(node)
    write_json(destination / 'package.json', lock['package'])
    write_json(destination / 'package-lock.json', lock['package_lock'])
    env = runtime_env(node, destination)
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(destination / 'browsers')
    run([node, npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund',
         '--registry=https://registry.npmjs.org'], destination, env)
    for relative, expected in lock['package_lock']['packages'].items():
        if relative:
            installed = json.loads((destination / relative / 'package.json').read_text())
            if installed['version'] != expected['version']:
                raise ValueError('Installed npm package differs from the reviewed lock')
    browser_metadata = destination / 'node_modules/playwright-core/browsers.json'
    browsers = json.loads(browser_metadata.read_text())['browsers']
    chromium = next(item for item in browsers if item['name'] == 'chromium')
    if chromium['revision'] != lock['browser']['revision']:
        raise ValueError('Installed browser revision differs from the reviewed lock')
    driver = destination / 'node_modules/playwright/cli.js'
    run([node, str(driver), 'install', 'chromium'], destination, env, timeout=900)
    entry = destination / 'node_modules/@playwright/cli/playwright-cli.js'
    actual = run([node, str(entry), '--version'], destination, env, timeout=30)
    if actual != lock['version']:
        raise ValueError('Installed Playwright CLI version differs from the lock')
    smoke_browser(node, destination, env)
    return {'argv': [node, str(entry)], 'environment': {'PLAYWRIGHT_BROWSERS_PATH': env['PLAYWRIGHT_BROWSERS_PATH'],
                            'PLAYWRIGHT_MCP_BROWSER': 'chromium'},
            'runtime': {'node': node, 'node_version': version}, 'browser': lock['browser'],
            'capability': 'browser-launch-verified'}


def smoke_browser(node, destination, env):
    code = "const {chromium}=require('playwright'); (async()=>{const b=await chromium.launch({channel:'chromium'});await b.close()})().catch(()=>process.exit(1))"
    run([node, '-e', code], destination, env, timeout=60)


def install_strix(destination, python=None):
    lock = read_lock()['strix']
    if platform.system() not in ('Darwin', 'Linux'):
        raise ValueError('Strix managed install supports macOS and Linux')
    python, version = python_runtime(python)
    requirements = lock['requirements']
    if digest(requirements.encode()) != lock['requirements_sha256']:
        raise ValueError('Strix dependency lock checksum mismatch')
    env = runtime_env(destination=destination)
    run([python, '-m', 'venv', str(destination / 'venv')], env=env)
    requirements_path = destination / 'requirements.lock'
    requirements_path.write_text(requirements)
    executable_path = destination / 'venv/bin/python'
    run([str(executable_path), '-m', 'pip', 'install', '--require-hashes', '--only-binary=:all:',
         '--disable-pip-version-check', '--index-url', 'https://pypi.org/simple',
         '-r', str(requirements_path)], destination, env, timeout=1200)
    actual = run([str(executable_path), '-c', "import importlib.metadata; print(importlib.metadata.version('strix-agent'))"], env=env)
    if actual != lock['version']:
        raise ValueError('Installed Strix version differs from the lock')
    entry = destination / 'venv/bin/strix'
    if not entry.is_file():
        raise ValueError('Installed Strix console entrypoint is missing')
    run([str(entry), '--help'], destination, env, timeout=60)
    return {'argv': [str(entry)], 'environment': {'PYTHONDONTWRITEBYTECODE': '1'},
            'runtime': {'python': python, 'python_version': version},
            'capability': 'installed-inactive', 'scan_executed': False}


def launcher_bytes(details):
    code = [f'#!{sys.executable}', 'import os, sys',
            'os.environ.update(' + repr(details['environment']) + ')',
            'argv = ' + repr(details['argv']), 'os.execv(argv[0], [*argv, *sys.argv[1:]])', '']
    return '\n'.join(code).encode()


def provision(name, home, node=None, python=None):
    root = safe_path(home, '.local/share/agent-workflow/tools')
    version = read_lock()[name]['version']
    destination = safe_path(root, f'runtimes/{name}-{version}-{uuid.uuid4().hex[:12]}')
    destination.mkdir(parents=True)
    try:
        details = install_playwright(destination, node) if name == 'playwright-cli' else install_strix(destination, python)
        for temporary in ('setup-home', 'setup-cache'):
            shutil.rmtree(destination / temporary, ignore_errors=True)
        details.update({'name': name, 'version': version, 'path': str(destination),
                        'tree_sha256': tree_digest(destination)})
        return details
    except BaseException:
        shutil.rmtree(destination)
        raise


def runtime_status(record):
    path = Path(record['path'])
    if not path.is_dir():
        return {'status': 'missing', 'capability': 'unavailable'}
    if tree_digest(path) != record['tree_sha256']:
        return {'status': 'modified', 'capability': 'integrity-failed'}
    executable_path = Path(record['argv'][0])
    if not executable_path.exists():
        return {'status': 'missing-runtime', 'capability': 'unavailable'}
    return {'status': 'installed', 'version': record['version'], 'capability': record['capability']}
