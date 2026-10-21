"""Conservative worker controls for known package-manager command contracts."""
import json
from pathlib import Path
import shlex


def _workspace(argv, cwd):
    root = Path(cwd).resolve()
    for index, item in enumerate(argv):
        if item in {'--workspace', '-w'}:
            if index + 1 >= len(argv):
                raise ValueError('Workspace option has no value')
            candidate = (root / argv[index + 1]).resolve()
            if not candidate.is_relative_to(root):
                raise ValueError('Workspace resource lookup escapes command directory')
            return candidate
        if item.startswith('--workspace='):
            candidate = (root / item.split('=', 1)[1]).resolve()
            if not candidate.is_relative_to(root):
                raise ValueError('Workspace resource lookup escapes command directory')
            return candidate
    return root


def npm_workers(argv, cwd, workers):
    """Read scripts as data; never evaluate package text to discover a runner."""
    if len(argv) < 2:
        return argv
    if argv[1] == 'exec' and '--' in argv:
        offset = argv.index('--') + 1
        command = argv[offset:]
        if command[:2] == ['playwright', 'test']:
            if any(a.startswith('--workers') for a in command):
                raise ValueError('Conflicting Playwright workers; use resource configuration')
            return argv + [f'--workers={workers}']
        if command[:2] == ['vitest', 'run']:
            return _vitest(argv, workers)
        return argv
    if argv[1] == 'test':
        script_name = 'test'
    elif argv[1] in {'run', 'run-script'} and len(argv) >= 3:
        script_name = argv[2]
    else:
        return argv
    package = _workspace(argv, cwd) / 'package.json'
    if not package.is_file() or package.stat().st_size > 1024 * 1024:
        raise ValueError('Cannot resolve bounded npm script resource contract')
    script = json.loads(package.read_text()).get('scripts', {}).get(script_name)
    if not isinstance(script, str):
        raise ValueError('Selected npm script is unavailable for resource inspection')
    words = shlex.split(script)
    if words[:2] == ['vitest', 'run'] and not any(any(c in word for c in [';', '|', '&', '$', '`', '\n', '>']) for word in words):
        return _vitest(argv if '--' in argv else argv + ['--'], workers)
    if words[:2] == ['playwright', 'test'] and not any(any(c in word for c in [';', '|', '&', '$', '`', '\n', '>']) for word in words):
        return (argv if '--' in argv else argv + ['--']) + [f'--workers={workers}']
    # A nested script may hide a worker pool. Do not guess arguments for compound tests.
    if script_name.startswith('test') or any('vitest' in word or 'playwright' in word for word in words):
        raise ValueError('Compound or indirect test worker contract requires an explicit bounded command')
    return argv


def _vitest(argv, workers):
    if any(a.startswith('--maxWorkers') or a.startswith('--max-workers') for a in argv):
        raise ValueError('Conflicting Vitest workers; use resource configuration')
    return argv + [f'--maxWorkers={workers}', '--no-file-parallelism']
