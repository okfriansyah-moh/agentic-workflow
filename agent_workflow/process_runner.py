"""Bounded foreground process capture under a shared resource lease."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

from . import resource_system, resources


class Capture:
    def __init__(self, limit):
        self.limit = limit
        self.lock = threading.Lock()
        self.data = {'stdout': bytearray(), 'stderr': bytearray()}
        self.counts = {'stdout': 0, 'stderr': 0}
        self.hashes = {name: hashlib.sha256() for name in self.data}
        self.used = 0
        self.truncated = False

    def drain(self, name, pipe):
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                with self.lock:
                    self.counts[name] += len(chunk)
                    self.hashes[name].update(chunk)
                    retained = chunk[:max(0, self.limit - self.used)]
                    self.data[name].extend(retained)
                    self.used += len(retained)
                    self.truncated |= len(retained) != len(chunk)
        finally:
            pipe.close()

    def result(self):
        with self.lock:
            return {**{name: bytes(value) for name, value in self.data.items()},
                    'output_bytes': dict(self.counts), 'truncated': self.truncated,
                    **{name + '_sha256': value.hexdigest() for name, value in self.hashes.items()}}


def command_limits(argv, limits, cwd="."):
    """Cooperative per-command controls; monitoring remains the backstop."""
    env = dict(os.environ)
    workers = str(limits['workers'])
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'CMAKE_BUILD_PARALLEL_LEVEL', 'CARGO_BUILD_JOBS'):
        try:
            existing = int(env.get(key, workers))
        except ValueError:
            existing = 1
        env[key] = str(min(int(workers), max(1, existing)))
    argv = list(argv)
    executable = Path(argv[0]).name.lower()
    heap_mib = max(16, limits['memory_bytes'] // (1024 ** 2 * 2 * limits['workers']))
    if executable in {'node', 'node.exe', 'npm', 'npx', 'vitest', 'vitest.mjs'}:
        import re
        options = env.get('NODE_OPTIONS', '')
        existing = re.findall(r'--max[-_]old[-_]space[-_]size[= ](\d+)', options)
        heap_mib = min([heap_mib] + [int(value) for value in existing])
        env['NODE_OPTIONS'] = options + f' --max-old-space-size={heap_mib}'
    if executable in {'gradle', 'gradlew', 'gradlew.bat'}:
        if any(a.startswith('--max-workers') for a in argv):
            raise ValueError('Declare Gradle worker limits through resources, not conflicting argv')
        argv += ['--max-workers=' + workers, '--no-parallel', '--no-daemon', f'-Dorg.gradle.jvmargs=-Xmx{heap_mib}m']
    if executable in {'vitest', 'vitest.mjs'} and 'run' in argv:
        if any(a.startswith('--maxWorkers') for a in argv):
            raise ValueError('Declare Vitest worker limits through resources, not conflicting argv')
        argv += ['--maxWorkers=' + workers, '--no-file-parallelism']
    if executable in {'npm', 'npm.cmd'}:
        from .command_resources import npm_workers
        argv = npm_workers(argv, cwd, workers)
    return argv, env


def group_alive(group):
    try:
        os.killpg(group, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return resource_system.group_members(group) != {}


def cleanup(process, lease):
    """Also remove surviving children after the root process finishes."""
    group = process.pid
    observed = resource_system.process_tree(process.pid, group)
    lease.remember(observed)
    if group_alive(group):
        try:
            os.killpg(group, signal.SIGTERM)
        except ProcessLookupError:
            pass
    # A sampled child may create another group. Signal only refreshed start identities.
    def signal_survivors(value):
        living = resource_system.living_owned(lease.identities) if lease.identities else {}
        if living is None:
            return False
        for raw_pid in living:
            try:
                os.kill(int(raw_pid), value)
            except ProcessLookupError:
                pass
        return True
    known = signal_survivors(signal.SIGTERM)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        process.poll()
        living = resource_system.living_owned(lease.identities) if lease.identities else {}
        if known and living == {} and not group_alive(group):
            return True
        time.sleep(0.05)
    if group_alive(group):
        try:
            os.killpg(group, signal.SIGKILL)
        except ProcessLookupError:
            pass
    known = signal_survivors(signal.SIGKILL) and known
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        return False
    living = resource_system.living_owned(lease.identities) if lease.identities else {}
    return known and living == {} and not group_alive(group)


def _watch(process, cwd, lease, timeout, capture):
    started = time.monotonic()
    next_sample = started
    reason = None
    while process.poll() is None:
        now = time.monotonic()
        if now - started >= timeout:
            reason = 'Command timed out'
            lease.halt(reason)
            break
        if capture.truncated:
            reason = 'Output retention limit exceeded; complete proof unavailable'
            lease.halt(reason)
            break
        if now >= next_sample:
            reading = resource_system.snapshot(cwd)
            if process.poll() is not None:
                break
            tree = resource_system.process_tree(process.pid, process.pid)
            if not tree.get('known') and process.poll() is not None:
                break
            lease.remember(tree)
            reason = resources.active_reason(reading, lease.report['limits'], tree)
            lease.report['last_reading'] = reading
            lease.report['last_tree'] = {k: v for k, v in tree.items() if k != 'pids'}
            if reason:
                lease.halt(reason)
                break
            next_sample = now + resources.INTERVAL
        try:
            process.wait(timeout=min(0.1, max(0.001, timeout - (now - started))))
        except subprocess.TimeoutExpired:
            pass
    return reason


def _execute(argv, cwd, timeout, lease):
    limits = lease.report['limits']
    argv, env = command_limits(argv, limits, cwd)
    capture = Capture(limits['output_bytes'])
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    lease.remember(group_id=process.pid)
    readers = [threading.Thread(target=capture.drain, args=(name, pipe), daemon=True)
               for name, pipe in (('stdout', process.stdout), ('stderr', process.stderr))]
    reason = None
    try:
        for thread in readers:
            thread.start()
        reason = _watch(process, cwd, lease, timeout, capture)
    finally:
        try:
            clean = cleanup(process, lease)
        except OSError as error:
            clean = False
            lease.halt(f'Owned process cleanup failed: {error}')
        for thread in readers:
            if thread.ident is not None:
                thread.join(timeout=1)
        if not clean or any(thread.is_alive() for thread in readers):
            lease.halt('Owned process cleanup or output-drain completion could not be verified')
            reason = lease.report['reason']
    result = capture.result()
    if result['truncated'] and reason is None:
        reason = 'Output retention limit exceeded; complete proof unavailable'
        lease.halt(reason)
    return dict(result, exit_code=124 if reason == 'Command timed out' else process.returncode,
                timed_out=reason == 'Command timed out', reason=reason, cleanup_verified=clean,
                executed_argv=argv)


def run_process(argv, cwd, timeout=90, requirements=None):
    lease = resources.Lease(cwd, requirements)
    base = {'stdout': b'', 'stderr': b'', 'exit_code': None, 'timed_out': False,
            'truncated': False, 'output_bytes': {'stdout': 0, 'stderr': 0}}
    try:
        if os.name != 'posix':
            return dict(base, status='blocked', reason='Process-tree containment unavailable on this platform; no command launched', resources={})
        if not lease.acquire():
            return dict(base, status='blocked', reason=lease.report['reason'], resources=lease.report)
        try:
            result = _execute(argv, cwd, timeout, lease)
            status = 'blocked' if result['reason'] else 'passed' if result['exit_code'] == 0 else 'failed'
            return dict(result, status=status, resources=lease.report)
        except ValueError as error:
            lease.halt('Cannot apply bounded command contract: ' + str(error))
            return dict(base, status='blocked', reason=lease.report['reason'], resources=lease.report)
        except (FileNotFoundError, PermissionError) as error:
            return dict(base, exit_code=127, status='blocked', reason=f'Unavailable executable or directory: {error.filename}', resources=lease.report)
        except BaseException:
            lease.halt('Runner interrupted unexpectedly; inspect owned-process cleanup before recovery')
            raise
    finally:
        lease.release()
