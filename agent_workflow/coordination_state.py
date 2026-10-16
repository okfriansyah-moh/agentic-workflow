"""Locked ownership shared by all participating worktrees of one Git repository."""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path


class CoordinationError(ValueError):
    """Coordination cannot proceed without violating its recorded boundary."""


def git(repo, *args, check=True):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if check and result.returncode:
        raise CoordinationError(result.stderr.strip() or result.stdout.strip() or 'Git command failed')
    return result


def repository(repo):
    return Path(git(repo, 'rev-parse', '--show-toplevel').stdout.strip()).resolve()


def revision(repo, ref='HEAD'):
    if not isinstance(ref, str) or not ref or ref.startswith('-'):
        raise CoordinationError('Invalid revision')
    return git(repo, 'rev-parse', '--verify', f'{ref}^{{commit}}').stdout.strip()


def common_directory(repo):
    value = git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir').stdout.strip()
    return Path(value).resolve() / 'agent-workflow'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextlib.contextmanager
def registry(repo, timeout=10):
    directory = common_directory(repo)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'registry.lock').open('a+') as lock:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise CoordinationError('Registry is locked by another live operation; retry later')
                time.sleep(0.05)
        try:
            path = directory / 'registry.json'
            data = read_json(path) if path.exists() else {
                'schema_version': 1, 'claims': {}, 'integrations': [], 'corrections': {}}
            if data.get('schema_version') != 1:
                raise CoordinationError('Unsupported registry schema')
            yield data
            write_json(path, data)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def safe_relative(repo, value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise CoordinationError(f'Expected a repository-relative path: {value}')
    root = repository(repo)
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root) or path.parts[0] == '.git':
        raise CoordinationError(f'Path escapes the allowed repository: {value}')
    return path.as_posix().rstrip('/')


def overlaps(first, second):
    a, b = Path(first), Path(second)
    return a == b or a in b.parents or b in a.parents


def owns_path(claim, path):
    return any(path == allowed or Path(allowed) in Path(path).parents for allowed in claim['paths'])


def _validate_brief(spec):
    required = ('owner', 'task_ids', 'base_revision', 'paths', 'resources',
                'source_references', 'acceptance_ids', 'required_checks')
    missing = [key for key in required if key not in spec]
    if missing:
        raise CoordinationError(f'Missing worker brief fields: {missing}')
    if not spec['owner'] or not spec['task_ids'] or (not spec['paths'] and spec.get('role') != 'integrator'):
        raise CoordinationError('Owner, task IDs and writable paths must be nonempty')
    for name in ('task_ids', 'paths', 'resources', 'source_references', 'acceptance_ids'):
        if not isinstance(spec[name], list) or any(not isinstance(v, str) or not v for v in spec[name]):
            raise CoordinationError(f'{name} must be a list of nonempty strings')
    if not spec['source_references'] or not isinstance(spec['required_checks'], list) or not spec['required_checks']:
        raise CoordinationError('Worker brief needs source references and explicit required check contracts')
    checks = [check_contract(check) for check in spec['required_checks']]
    if len({check['id'] for check in checks}) != len(checks):
        raise CoordinationError('Required check IDs must be unique')


def check_contract(check):
    if not isinstance(check, dict) or not check.get('id'):
        raise CoordinationError('A required check needs an explicit object with id, argv, kind and test report when applicable')
    argv = check.get('argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or '\0' in arg for arg in argv):
        raise CoordinationError('Check argv must be a nonempty string array')
    if check.get('kind') not in ('check', 'test'):
        raise CoordinationError('Each check must explicitly declare kind check or test')
    timeout = check.get('timeout', 300)
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 3600:
        raise CoordinationError('Check timeout must be between 0 and 3600 seconds')
    contract = {'id': check['id'], 'argv': argv, 'kind': check['kind'],
                'cwd': check.get('cwd', '.'), 'timeout': timeout}
    if check['kind'] == 'test':
        report = check.get('test_report')
        if not isinstance(report, dict) or not report.get('path') or report.get('format') not in ('junit', 'vitest', 'workflow-test'):
            raise CoordinationError('Test contracts require a supported machine-readable report path/format')
        contract['test_report'] = report
    return contract


def _worker_capacity(root, spec):
    config_path = root / '.ai/config.json'
    config = read_json(config_path) if config_path.is_file() else {}
    limits = (3, config.get('max_workers', 3), spec.get('host_capacity', 3))
    if any(not isinstance(limit, int) or isinstance(limit, bool) or limit < 1 for limit in limits):
        raise CoordinationError('Worker/host capacity limits must be positive integers')
    return min(limits)


def _claim_conflicts(spec, active):
    for claim in active:
        collisions = [(a, b) for a in spec['paths'] for b in claim['paths'] if overlaps(a, b)]
        resources = set(spec['resources']) & set(claim['resources'])
        tasks = set(spec['task_ids']) & set(claim['task_ids'])
        if collisions or resources or tasks:
            raise CoordinationError(f"Claim conflicts with {claim['id']}: paths={collisions}, resources={sorted(resources)}, tasks={sorted(tasks)}")
        if spec.get('role') == 'integrator' and claim.get('role') == 'integrator':
            raise CoordinationError('An integrator already owns the integration lane')


def _shared_resources(paths):
    resources = set()
    for path in paths:
        lowered = path.lower()
        name = Path(path).name
        if not Path(path).suffix:
            resources.update(('shared:migration-allocation', 'shared:dependency-locks', 'shared:build-configuration', 'shared:schemas', 'shared:generators'))
        if '/migration/' in '/' + lowered or '/migrations/' in '/' + lowered:
            resources.add('shared:migration-allocation')
        if name in ('package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'gradle.lockfile'):
            resources.add('shared:dependency-locks')
        if name in ('build.gradle.kts', 'settings.gradle.kts', 'build.gradle', 'settings.gradle', 'gradle.properties', 'package.json'):
            resources.add('shared:build-configuration')
        if Path(path).suffix in ('.proto', '.graphql', '.graphqls') or '/schemas/' in '/' + lowered:
            resources.add('shared:schemas')
        if '/generators/' in '/' + lowered or '/generated/' in '/' + lowered:
            resources.add('shared:generators')
    return resources


def create_claim(repo, spec):
    _validate_brief(spec)
    root = repository(repo)
    base = revision(root, spec['base_revision'])
    if base != revision(root):
        raise CoordinationError('Claim base must equal the checked-out integration revision')
    paths = sorted(set(safe_relative(root, path) for path in spec['paths']))
    if any(path.startswith(('.ai/state', '.ai/evidence', '.ai/reports')) for path in paths):
        raise CoordinationError('Evidence/state outputs are not implementation ownership paths')
    prepared = {**spec, 'paths': paths, 'base_revision': base,
                'resources': sorted(set(spec['resources']) | _shared_resources(paths)),
                'required_checks': [check_contract(check) for check in spec['required_checks']]}
    if spec.get('plan'):
        from .coordination_plan import task_index
        index = task_index(root / safe_relative(root, spec['plan']))
        if index['status'] != 'ok':
            raise CoordinationError('Plan references or source fingerprints are not ready')
        selected = [index['tasks'].get(task) for task in spec['task_ids']]
        _claim_eligibility(root, spec, selected)
        surfaces = [entry['path'].rstrip('/') for task in selected for entry in task['change_surface']]
        if any(not any(path == allowed or Path(allowed) in Path(path).parents for allowed in surfaces) for path in paths):
            raise CoordinationError('Requested paths exceed the selected task change surfaces')
        prepared['depends_on'] = sorted({dep for task in selected for dep in task['depends_on']})
    else:
        prepared['depends_on'] = spec.get('depends_on', [])
        if spec.get('selection_id'):
            _selection_claim(root, spec)
    with registry(root) as state:
        active = [c for c in state['claims'].values() if c['status'] == 'active']
        _claim_conflicts(prepared, active)
        workers = [c for c in active if c.get('role') != 'integrator']
        capacity = _worker_capacity(root, spec)
        if spec.get('role') != 'integrator' and len(workers) >= capacity:
            raise CoordinationError(f'Writing lane capacity {capacity} is reached; reuse or release a lane')
        claim_id = 'lane-' + uuid.uuid4().hex[:16]
        claim = {**prepared, 'id': claim_id, 'status': 'active', 'repository': str(root),
                 'created_at': time.time(), 'updated_at': time.time(), 'worktree': None}
        if spec.get('reuse_worktree'):
            claim.update(worktree=str(root), branch=git(root, 'branch', '--show-current').stdout.strip())
        state['claims'][claim_id] = claim
    return {'status': 'ok', 'claim': claim}


def _claim_eligibility(root, spec, selected):
    if not spec.get('selection_id'):
        if any(task is None or not task['execution_eligible'] for task in selected):
            raise CoordinationError('Selected plan tasks are not execution-eligible')
        return
    if any(task is None or task['readiness'] != 'Ready' for task in selected):
        raise CoordinationError('Selected task documents are not ready')
    _selection_claim(root, spec)


def _selection_claim(root, spec):
    from .selection import available_tasks, get_selection
    with registry(root) as state:
        item = get_selection(state, spec['selection_id'])
        if item['status'] == 'accepted' or set(spec['task_ids']) - set(item['task_ids']):
            raise CoordinationError('Claim must belong to an unfinished selection')
        available = available_tasks(root, item)
        internal = set(spec['task_ids'])
        for task in internal:
            pending = set(item['dependencies'].get(task, [])) - internal
            if pending - available:
                raise CoordinationError('Selection task prerequisites have no tested implementation at this revision')


def get_claim(state, claim_id, owner=None):
    claim = state['claims'].get(claim_id)
    if not claim or claim['status'] != 'active':
        raise CoordinationError(f'Claim is not active: {claim_id}')
    if owner is not None and claim['owner'] != owner:
        raise CoordinationError('Only the recorded owner may change this claim')
    return claim


def release_claim(repo, claim_id, owner, reason):
    if not reason.strip():
        raise CoordinationError('Release needs a recorded reason')
    with registry(repo) as state:
        claim = get_claim(state, claim_id, owner)
        claim.update(status='released', released_at=time.time(), release_reason=reason)
    return {'status': 'ok', 'claim_id': claim_id, 'worktree_retained': claim.get('worktree')}


def create_worktree(repo, claim_id, path, branch, owner):
    target = Path(path).resolve()
    git(repo, 'check-ref-format', '--branch', branch)
    with registry(repo) as state:
        claim = get_claim(state, claim_id, owner)
        if claim.get('worktree'):
            raise CoordinationError('Claim already has a worktree; resume that lane')
        if target.exists():
            raise CoordinationError('Worktree destination already exists')
        if revision(repo) != claim['base_revision']:
            raise CoordinationError('Integration revision changed since the claim was granted')
        git(repo, 'worktree', 'add', '-b', branch, str(target), claim['base_revision'])
        claim.update(worktree=str(target), branch=branch, updated_at=time.time())
    return {'status': 'ok', 'claim': claim}



def cleanup_worktree(repo, claim_id, owner):
    with registry(repo) as state:
        claim = state['claims'].get(claim_id)
        if not claim or claim['owner'] != owner or claim['status'] != 'released':
            raise CoordinationError('Cleanup requires the owner to release the claim first')
        worktree = claim.get('worktree')
        if not worktree or not Path(worktree).is_dir():
            raise CoordinationError('No retained worktree is available for cleanup')
        successful = [record for record in state['integrations'] if record['status'] == 'passed' and claim_id in record['merged_claims']]
        if not successful or git(repo, 'merge-base', '--is-ancestor', revision(worktree), successful[-1]['result_revision'], check=False).returncode:
            raise CoordinationError('Worker contribution has no successful retained integration')
        if git(worktree, 'status', '--porcelain', '--untracked-files=all').stdout:
            raise CoordinationError('Worktree has local files. Archive evidence and inspect other files before cleanup; nothing was deleted.')
        if (Path(worktree) / '.ai/evidence').exists():
            raise CoordinationError('Archive the evidence directory before cleanup, including ignored evidence')
        git(repo, 'worktree', 'remove', worktree)
        claim.update(cleaned_at=time.time(), worktree=None)
    return {'status': 'ok', 'claim_id': claim_id, 'branch_retained': claim.get('branch')}


def _normalized_input(path, data):
    if path.endswith('.md') and re.search(rb'^kind: task\s*$', data, re.M):
        text = data.decode('utf-8')
        text = re.sub(r'(?m)^status: [^\n]*$', 'status: <execution-state>', text, count=1)
        text = re.sub(r'(?ms)^## Evidence\s*\n.*?(?=^## |\Z)', '## Evidence\n<execution-evidence>\n\n', text)
        return text.encode('utf-8')
    return data


OUTPUT_DIRECTORIES = {'node_modules', '.gradle', '.svelte-kit', '__pycache__', '.venv', 'venv',
                      '.cache', 'test-results', 'playwright-report', 'coverage', 'build', 'dist', 'generated'}


def excluded_input(name):
    parts = Path(name).parts
    return (name == '.DS_Store' or Path(name).suffix == '.pyc'
            or name.startswith(('.ai/evidence/', '.ai/state/', '.ai/reports/', '.ai/install-backups/'))
            or bool(set(parts[:-1]) & OUTPUT_DIRECTORIES))


def input_snapshot(repo):
    root = repository(repo)
    names = git(root, 'ls-files', '-c', '-o', '--exclude-standard', '-z').stdout.split('\0')
    files = {}
    for name in sorted(set(filter(None, names))):
        if excluded_input(name):
            continue
        path = root / name
        if path.is_symlink():
            data = os.readlink(path).encode('utf-8')
        elif path.is_file():
            data = _normalized_input(name, path.read_bytes())
        else:
            data = b'<deleted>'
        mode = oct(path.lstat().st_mode & 0o777) if path.exists() or path.is_symlink() else 'absent'
        files[name] = hashlib.sha256(mode.encode('ascii') + b'\0' + data).hexdigest()
    serialized = json.dumps(files, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'fingerprint': hashlib.sha256(serialized).hexdigest(), 'files': files}


def changed_files(repo, base):
    names = git(repo, 'diff', '--name-only', '-z', base).stdout.split('\0')
    untracked = git(repo, 'ls-files', '-o', '--exclude-standard', '-z').stdout.split('\0')
    return sorted(name for name in set(filter(None, names + untracked)) if not excluded_input(name))


def resume(repo, stale_seconds=3600):
    with registry(repo) as state:
        claims = []
        for claim in state['claims'].values():
            if claim['status'] != 'active':
                continue
            item = dict(claim)
            item['stale_attention'] = time.time() - claim['updated_at'] > stale_seconds
            worktree = claim.get('worktree')
            item['next_action'] = 'Continue at the recorded worktree; verify task files and required checks.'
            if worktree and Path(worktree).exists():
                item['current_revision'] = revision(worktree)
                item['input_fingerprint'] = input_snapshot(worktree)['fingerprint']
                item['conflicted_files'] = git(worktree, 'diff', '--name-only', '--diff-filter=U').stdout.splitlines()
                if item['conflicted_files']:
                    item['next_action'] = 'Resolve retained merge conflicts against the task contracts, then rerun required checks.'
            elif worktree:
                item['next_action'] = 'Worktree is missing. Inspect retained branch and explicitly release or recover the claim.'
            else:
                item['next_action'] = 'Create the lane worktree from its recorded base before making edits.'
            claims.append(item)
        return {'status': 'ok', 'integration_revision': revision(repo), 'claims': claims,
                'integrations': state['integrations'], 'corrections': state['corrections'],
                'selections': list(state.get('selections', {}).values()),
                'note': 'Stale timestamps do not release claims or prove success. Task files remain the execution record.'}
