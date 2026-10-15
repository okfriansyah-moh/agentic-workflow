"""Explicit tool lifecycle commands; no scan command or background service."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from . import tool_config, tool_runtime as runtime


NAMES = ('playwright-cli', 'context7', 'strix')


def state_path(home):
    return runtime.safe_path(home, '.local/share/agent-workflow/tools/state.json')


def read_state(home):
    path = state_path(home)
    return json.loads(path.read_text()) if path.exists() else {'schema_version': 1, 'tools': {}, 'context7': []}


@contextmanager
def locked(home):
    path = runtime.safe_path(home, '.local/share/agent-workflow/tools/state.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another tool operation owns the lock; retry after it finishes') from None
        yield


def binary_path(home, name):
    return runtime.safe_path(home, '.local/bin/' + name)


def validate_launcher(home, name, record):
    binary = binary_path(home, name)
    if binary.exists():
        if not record or runtime.digest(binary.read_bytes()) != record.get('launcher_sha256'):
            raise ValueError('Existing tool launcher is unowned or modified; preserved')
    elif record:
        raise ValueError('Managed launcher is missing; remove its record before reinstalling')
    return binary


def install_runtime(name, home, state, node=None, python=None):
    previous = state['tools'].get(name)
    binary = validate_launcher(home, name, previous)
    if previous and previous['version'] == runtime.read_lock()[name]['version']:
        status = runtime.runtime_status(previous)
        if status['status'] != 'installed':
            raise ValueError('Managed runtime is missing or modified; preserved for review')
        return {'name': name, **status, 'reused': True}
    original = binary.read_bytes() if binary.exists() else None
    details = runtime.provision(name, home, node, python)
    launcher = runtime.launcher_bytes(details)
    details['launcher_sha256'] = runtime.digest(launcher)
    details['retired'] = [*previous.get('retired', []), previous] if previous else []
    if previous:
        details['retired'][-1] = {key: value for key, value in previous.items() if key != 'retired'}
    try:
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_bytes(launcher)
        binary.chmod(0o755)
        state['tools'][name] = details
        runtime.write_json(state_path(home), state)
    except BaseException:
        if original is None:
            binary.unlink(missing_ok=True)
        else:
            binary.write_bytes(original)
        shutil.rmtree(details['path'])
        if previous:
            state['tools'][name] = previous
        else:
            state['tools'].pop(name, None)
        raise
    return {'name': name, 'status': 'installed', 'version': details['version'],
            'capability': details['capability'], 'launcher': str(binary)}


def config_scope(records, repo, home):
    expected = {item['path'] for item in tool_config.configs(home, repo)}
    scope = 'repo' if repo else 'global'
    return [item for item in records if item['scope'] == scope and item['path'] in expected]


def install_context(home, state, repo, auth):
    previous = config_scope(state['context7'], repo, home)
    installed = tool_config.install_configs(home, repo, auth, previous)
    retained = [item for item in state['context7'] if item not in previous]
    state['context7'] = retained + installed
    try:
        runtime.write_json(state_path(home), state)
    except BaseException:
        owned_before = {item['path'] for item in previous if item['owned']}
        for item in installed:
            if item['path'] not in owned_before:
                tool_config.remove_config(item)
        state['context7'] = retained + previous
        raise
    return {'name': 'context7', 'status': 'configured',
            'hosts': [tool_config.inspect_config(item) for item in installed],
            'authentication': 'host-oauth-unverified' if auth == 'oauth' else 'anonymous-limited'}


def tool_status(name, home, state, repo=None):
    if name == 'context7':
        records = config_scope(state['context7'], repo, home)
        hosts = [tool_config.inspect_config(item) for item in records]
        good = len(hosts) == 4 and all(item['status'] == 'configured' for item in hosts)
        return {'name': name, 'status': 'configured' if good else 'missing-or-modified', 'hosts': hosts}
    record = state['tools'].get(name)
    if not record:
        return {'name': name, 'status': 'missing'}
    result = {'name': name, **runtime.runtime_status(record)}
    try:
        validate_launcher(home, name, record)
    except ValueError:
        result.update(status='modified-launcher', capability='unavailable')
    return result


def owned_runtime_path(home, record):
    root = runtime.safe_path(home, '.local/share/agent-workflow/tools/runtimes')
    path = Path(record['path'])
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Tool state points outside the managed runtime directory')
    return runtime.safe_path(root, path.relative_to(root))


def remove_runtime(name, home, state):
    record = state['tools'].get(name)
    if not record:
        return {'name': name, 'status': 'already-absent'}
    binary = binary_path(home, name)
    if binary.exists() and runtime.digest(binary.read_bytes()) != record['launcher_sha256']:
        return {'name': name, 'status': 'preserved-modified'}
    records = [record, *record.get('retired', [])]
    for entry in records:
        path = owned_runtime_path(home, entry)
        if path.exists() and runtime.tree_digest(path) != entry['tree_sha256']:
            return {'name': name, 'status': 'preserved-modified'}
    binary.unlink(missing_ok=True)
    for entry in records:
        path = owned_runtime_path(home, entry)
        if path.exists():
            shutil.rmtree(path)
    del state['tools'][name]
    runtime.write_json(state_path(home), state)
    return {'name': name, 'status': 'removed'}


def remove_context(home, state, repo):
    selected = config_scope(state['context7'], repo, home)
    results = []
    for record in selected:
        result = tool_config.remove_config(record)
        results.append({'host': record['host'], 'status': result})
        if result != 'preserved-modified':
            state['context7'].remove(record)
    runtime.write_json(state_path(home), state)
    return {'name': 'context7', 'status': 'blocked' if any(item['status'] == 'preserved-modified' for item in results) else 'removed',
            'hosts': results}


def execute(args):
    home = Path(args.home).expanduser().resolve()
    repo = str(Path(args.repo).resolve()) if args.repo else None
    names = NAMES if args.tool == 'all' else (args.tool,)
    results = []
    with locked(home):
        state = read_state(home)
        for name in names:
            results.append(dispatch(args, name, home, state, repo))
    failed = {'blocked', 'preserved-modified', 'missing', 'missing-or-modified',
              'modified', 'missing-runtime', 'modified-launcher'}
    status = 'blocked' if any(item['status'] in failed for item in results) else 'ok'
    result = {'status': status, 'operation': args.operation, 'tools': results}
    if args.probe and 'context7' in names:
        result['context7_probe'] = tool_config.probe_context7()
        if result['context7_probe']['status'] != 'reachable':
            result['status'] = 'blocked'
    return result


def dispatch(args, name, home, state, repo):
    if args.operation == 'status':
        return tool_status(name, home, state, repo)
    if args.operation == 'remove':
        return remove_context(home, state, repo) if name == 'context7' else remove_runtime(name, home, state)
    if name == 'context7':
        return install_context(home, state, repo, args.auth)
    return install_runtime(name, home, state, args.node, args.python)


def strix_preflight(args):
    home = Path(args.home).expanduser().resolve()
    installed = tool_status('strix', home, read_state(home))
    docker = shutil.which('docker')
    daemon = False
    if docker:
        try:
            runtime.run([docker, 'info', '--format', '{{.ServerVersion}}'], timeout=20)
            daemon = True
        except (OSError, RuntimeError, subprocess.SubprocessError):
            pass
    credential = bool(os.environ.get('LLM_API_KEY'))
    model = bool(os.environ.get('STRIX_LLM'))
    return {'status': 'ok' if installed['status'] == 'installed' and daemon and credential and model else 'blocked',
            'installation': installed, 'docker_available': bool(docker), 'docker_daemon_reachable': daemon,
            'provider_model_in_environment': model, 'provider_key_in_environment': credential,
            'provider_authentication': 'unverified', 'host_stored_credentials': 'not-inspected',
            'scan_executed': False, 'scope_authorized': False,
            'next_action': 'An explicit assessment request and authorized target are required before scanning'}


def strix_report(args):
    path = Path(args.report).resolve()
    if path.name != 'vulnerabilities.json':
        raise ValueError('Select the Strix vulnerabilities.json report and its sibling run.json')
    raw = path.read_bytes()
    run_raw = path.with_name('run.json').read_bytes()
    findings, run = json.loads(raw), json.loads(run_raw)
    if not isinstance(findings, list) or not isinstance(run, dict):
        raise ValueError('Unsupported Strix report structure')
    if run.get('status') != 'completed' or not run.get('end_time'):
        raise ValueError('Strix run is incomplete; preserve it as partial evidence')
    targets = [item.get('original') for item in run.get('targets_info', []) if isinstance(item, dict)]
    if args.target not in targets:
        raise ValueError('Report target does not match the requested scope')
    counts = {level: 0 for level in ('critical', 'high', 'medium', 'low', 'info')}
    ids = set()
    for item in findings:
        if not isinstance(item, dict) or not re.fullmatch(r'vuln-\d+', str(item.get('id', ''))):
            raise ValueError('Report has an invalid finding identifier')
        if item['id'] in ids or item.get('severity') not in counts:
            raise ValueError('Report has duplicate identifiers or unsupported severity')
        ids.add(item['id'])
        counts[item['severity']] += 1
    return {'status': 'ok', 'review_status': 'independent-review-required', 'scan_executed': False,
            'report_sha256': runtime.digest(raw), 'run_sha256': runtime.digest(run_raw),
            'target_matches': True, 'findings': len(findings), 'severity_counts': counts,
            'source_revision_verified': False, 'acceptance_pass': False}


def register(subparsers):
    parser = subparsers.add_parser('tools', help='Manage pinned tools and hosted MCP configuration')
    commands = parser.add_subparsers(dest='operation', required=True)
    for operation in ('install', 'status', 'remove'):
        command = commands.add_parser(operation)
        command.add_argument('tool', choices=(*NAMES, 'all'), nargs='?', default='all')
        command.add_argument('--home', default=str(Path.home()))
        command.add_argument('--repo')
        command.add_argument('--node')
        command.add_argument('--python')
        command.add_argument('--probe', action='store_true')
        command.add_argument('--auth', choices=('oauth', 'anonymous'), default='oauth')
        command.set_defaults(handler=execute)
    preflight = commands.add_parser('strix-preflight')
    preflight.add_argument('--home', default=str(Path.home()))
    preflight.set_defaults(handler=strix_preflight)
    report = commands.add_parser('strix-report')
    report.add_argument('--report', required=True)
    report.add_argument('--target', required=True)
    report.set_defaults(handler=strix_report)
