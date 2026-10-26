"""Shared admission, machine budgets and explicit recovery for foreground work."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import contextlib
import time

from . import resource_system

GIB = 1024 ** 3
INTERVAL = 5
LIMIT_KEYS = {'memory_bytes', 'memory_reserve_bytes', 'disk_reserve_bytes', 'workers',
              'descendants', 'output_bytes'}


def configuration(cwd):
    path = Path(cwd).resolve()
    candidates = [p / '.ai/config.json' for p in (path, *path.parents)]
    candidates.append(Path.home() / '.local/share/agent-workflow/config.json')
    for candidate in candidates:
        if candidate.is_file():
            config = json.loads(candidate.read_text())
            value = config.get('resources', {})
            if not isinstance(value, dict):
                raise ValueError('resources must be an object')
            return value
    return {}


def budgets(reading, overrides=None):
    overrides = overrides or {}
    total = reading.get('memory_total_bytes') or 0
    available = reading.get('memory_available_bytes') or 0
    disk = reading.get('disk_total_bytes') or 0
    reserve = max(GIB, math.ceil(total / 4))
    defaults = {'memory_reserve_bytes': reserve, 'disk_reserve_bytes': max(GIB, min(5 * GIB, math.ceil(disk / 20))),
                'memory_bytes': max(0, min(4 * GIB, total // 4, available - reserve)),
                'workers': 1 if (reading.get('cpu_count') or 0) < 4 else 2,
                'descendants': 64, 'output_bytes': 4 * 1024 ** 2}
    unknown = set(overrides) - LIMIT_KEYS - {'increase_authorized'}
    if unknown:
        raise ValueError('Unknown resource settings: ' + ', '.join(sorted(unknown)))
    limits = dict(defaults)
    for key in LIMIT_KEYS & overrides.keys():
        value = overrides[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f'Resource {key} must be a positive integer')
        increased = value < defaults[key] if 'reserve' in key else value > defaults[key]
        if increased and overrides.get('increase_authorized') is not True:
            raise ValueError(f'Resource {key} increases capacity; explicit increase_authorized is required')
        limits[key] = value
    # An authorized ceiling never manufactures currently available memory.
    limits['memory_bytes'] = max(0, min(limits['memory_bytes'], available - limits['memory_reserve_bytes']))
    limits['workers'] = min(limits['workers'], max(1, math.floor(reading.get('cpu_count') or 1)))
    return limits


def admission_reason(reading, limits, requirements=None):
    required = requirements or {}
    if not isinstance(required, dict) or set(required) - {'minimum_memory_bytes', 'temporary_disk_bytes'}:
        raise ValueError('Command resources support minimum_memory_bytes and temporary_disk_bytes only')
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in required.values()):
        raise ValueError('Command resource requirements must be nonnegative integers')
    for key in ('cpu_count', 'memory_total_bytes', 'memory_available_bytes', 'disk_total_bytes', 'disk_free_bytes'):
        if reading.get(key) is None or reading[key] <= 0:
            return f'Essential resource measurement unavailable: {key}'
    if reading.get('pressure') not in {'normal'}:
        return 'Memory pressure is elevated or unknown'
    if reading.get('thermal') in {'warning', 'critical'}:
        return 'Thermal pressure is elevated'
    if reading['memory_available_bytes'] <= limits['memory_reserve_bytes']:
        return 'Available memory is below the reserve'
    if reading['disk_free_bytes'] < limits['disk_reserve_bytes'] + required.get('temporary_disk_bytes', 0):
        return 'Insufficient disk headroom'
    if reading.get('load_1m') is not None and reading['load_1m'] > reading['cpu_count']:
        return 'System load exceeds effective CPU capacity'
    if required.get('minimum_memory_bytes', 0) > limits['memory_bytes'] or not limits['memory_bytes']:
        return 'Command minimum memory exceeds the available workload budget'
    return None


def active_reason(reading, limits, tree):
    if reading.get('pressure') == 'critical' or reading.get('thermal') == 'critical':
        return 'Critical system pressure'
    if reading.get('memory_available_bytes') is None or reading['memory_available_bytes'] < limits['memory_reserve_bytes']:
        return 'Memory reserve exhausted or measurement lost'
    if reading.get('disk_free_bytes') is None or reading['disk_free_bytes'] < limits['disk_reserve_bytes']:
        return 'Disk reserve exhausted or measurement lost'
    if not tree.get('known'):
        return 'Owned process measurements unavailable'
    if tree['rss_bytes'] > limits['memory_bytes']:
        return 'Owned process memory budget exceeded'
    if tree['descendants'] > limits['descendants']:
        return 'Owned descendant limit exceeded'
    return None


def state_directory():
    import hashlib
    import platform
    device = hashlib.sha256(platform.node().encode()).hexdigest()[:16]
    return Path.home() / '.local/state/agent-workflow/resources' / device


def confirm_health(cwd, overrides=None, requirements=None):
    first = resource_system.snapshot(cwd)
    limits = budgets(first, overrides)
    reason = admission_reason(first, limits, requirements)
    if reason:
        return {'status': 'blocked', 'reason': reason, 'reading': first, 'limits': limits}
    time.sleep(INTERVAL)
    second = resource_system.snapshot(cwd)
    limits = budgets(second, overrides)
    reason = admission_reason(second, limits, requirements)
    return {'status': 'blocked' if reason else 'passed', 'reason': reason,
            'reading': second, 'limits': limits, 'healthy_samples': 2 if not reason else 1}


@contextlib.contextmanager
def ownership_guard(directory):
    """OS-released short lock serializes admission and explicit recovery."""
    import fcntl
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o022:
        raise ValueError('Unsafe resource state directory ownership or permissions')
    descriptor = os.open(directory / '.guard', os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(descriptor, 'a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
        else:
            try:
                yield True
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)


class Lease:
    """One shared user/machine slot, with a persistent stop after unsafe exit."""
    def __init__(self, cwd, requirements=None, directory=None):
        self.cwd = Path(cwd)
        self.requirements = requirements or {}
        self.directory = Path(directory) if directory else state_directory()
        self.lock = self.directory / 'active.json'
        self.stop = self.directory / 'stopped.json'
        self.owned = False
        self.report = {}
        self.identities = {}
        self.group_id = None

    def acquire(self):
        with ownership_guard(self.directory) as owned:
            if not owned:
                self.report = {'status': 'blocked', 'reason': 'Resource admission or recovery is already in progress'}
                return False
            return self._acquire_locked()

    def _acquire_locked(self):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.directory.is_symlink() or (hasattr(os, 'getuid') and self.directory.stat().st_uid != os.getuid()):
            raise ValueError('Unsafe resource state directory ownership')
        if self.stop.is_symlink() or self.lock.is_symlink():
            raise ValueError('Resource ownership files must not be symlinks')
        if self.stop.exists():
            self.report = {'status': 'blocked', 'reason': 'Resource batch stopped; inspect resources --resume after recovery'}
            return False
        try:
            fd = os.open(self.lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return self._existing_owner()
        self.owned = True
        with os.fdopen(fd, 'w') as stream:
            json.dump({'pid': os.getpid(), 'started_at': time.time()}, stream)
        self.report = confirm_health(self.cwd, configuration(self.cwd), self.requirements)
        return self.report['status'] == 'passed'

    def _existing_owner(self):
        try:
            owner = json.loads(self.lock.read_text())['pid']
            os.kill(owner, 0)
            reason = 'Another harness workload holds the machine resource slot'
        except ProcessLookupError:
            reason = 'Previous resource owner exited unexpectedly; inspect before resuming'
            previous = json.loads(self.lock.read_text())
            self.identities = previous.get('identities', {})
            self.group_id = previous.get('group_id')
            self.halt(reason)
        except (OSError, ValueError, KeyError):
            reason = 'Resource ownership cannot be verified; inspect before resuming'
        self.report = {'status': 'blocked', 'reason': reason}
        return False

    def remember(self, tree=None, group_id=None):
        if tree:
            self.identities.update(tree.get('identities', {}))
        if group_id is not None:
            self.group_id = group_id
        state = {'pid': os.getpid(), 'started_at': time.time(),
                 'identities': self.identities, 'group_id': self.group_id}
        temporary = self.lock.with_suffix('.tmp')
        temporary.write_text(json.dumps(state) + '\n')
        temporary.replace(self.lock)

    def halt(self, reason):
        self.stop.write_text(json.dumps({'reason': reason, 'timestamp': time.time(), 'identities': self.identities, 'group_id': self.group_id}) + '\n')
        self.report.update(status='blocked', reason=reason, stopped=True)

    def release(self):
        if self.owned:
            self.lock.unlink(missing_ok=True)
            self.owned = False


def inspect_resources(cwd, resume=False):
    directory = state_directory()
    reading = resource_system.snapshot(cwd)
    report = {'status': 'healthy', 'reading': reading, 'limits': budgets(reading, configuration(cwd)),
              'enforcement': 'Shared runner only; cooperative workers and sampled process RSS; no OS hard CPU quota',
              'stopped': (directory / 'stopped.json').exists(), 'active': (directory / 'active.json').exists()}
    reason = admission_reason(reading, report['limits'])
    if reason:
        report.update(status='blocked', reason=reason)
    if resume:
        if os.name != 'posix':
            return dict(report, status='blocked', reason='Safe resource recovery unavailable on this platform')
        with ownership_guard(directory) as owned:
            if not owned:
                return dict(report, status='blocked', reason='Resource admission or recovery already in progress')
            return _resume_resources(cwd, report, directory)
    elif report['stopped']:
        report.update(status='blocked', reason='Batch remains stopped pending explicit recovery')
    return report


def _resume_resources(cwd, report, directory):
    lock = directory / 'active.json'
    directory.mkdir(parents=True, exist_ok=True)
    previous = {}
    stopped = directory / 'stopped.json'
    if stopped.exists():
        previous = json.loads(stopped.read_text())
    if lock.exists():
        previous = json.loads(lock.read_text())
        try:
            os.kill(previous['pid'], 0)
            return dict(report, status='blocked', reason='An active owner prevents recovery')
        except ProcessLookupError:
            pass
        except (OSError, ValueError, KeyError):
            return dict(report, status='blocked', reason='Cannot verify previous owner')
    identities = previous.get('identities', {})
    survivors = resource_system.living_owned(identities) if identities else {}
    if survivors is None or survivors:
        return dict(report, status='blocked', reason='Recorded descendants remain alive or cannot be verified')
    group = previous.get('group_id')
    if group and os.name == 'posix':
        try:
            os.killpg(group, 0)
            return dict(report, status='blocked', reason='Previous owned process group still exists; inspect before recovery')
        except ProcessLookupError:
            pass
    lock.unlink(missing_ok=True)
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return dict(report, status='blocked', reason='Another resource owner won recovery admission')
    with os.fdopen(fd, 'w') as stream:
        json.dump({'pid': os.getpid(), 'started_at': time.time()}, stream)
    try:
        health = confirm_health(cwd, configuration(cwd))
        if health['status'] != 'passed':
            return health
        (directory / 'stopped.json').unlink(missing_ok=True)
        report.update(status='healthy', stopped=False, active=False, recovery=health)
    finally:
        lock.unlink(missing_ok=True)
    return report


def register(subparsers):
    parser = subparsers.add_parser('resources', help='Inspect execution-device budgets or explicitly recover a stopped batch')
    parser.add_argument('--repo', default='.')
    parser.add_argument('--resume', action='store_true', help='After inspecting the limiting condition, require two healthy readings before clearing the stop')
    parser.set_defaults(handler=lambda a: inspect_resources(a.repo, a.resume))
    run = subparsers.add_parser('run', help='Run a foreground command under the shared device lease')
    run.add_argument('--repo', default='.')
    run.add_argument('--timeout', type=int, default=7200)
    run.add_argument('--log', default='.ai/reports/foreground.log')
    run.add_argument('argv', nargs=__import__('argparse').REMAINDER)
    run.set_defaults(handler=run_foreground)


def run_foreground(args):
    """Run an explicit argv under the shared device lease; retain bounded logs."""
    from .process_runner import run_process
    argv = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
    if not argv:
        raise ValueError('A foreground command is required')
    repo = Path(args.repo).resolve()
    log = (repo / args.log).resolve()
    if not log.is_relative_to(repo):
        raise ValueError('Foreground log must stay within the repository')
    result = run_process(argv, repo, args.timeout)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_bytes(result.pop('stdout') + result.pop('stderr'))
    return dict(result, log=str(log.relative_to(repo)))
