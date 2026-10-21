"""Conservative affected-component selection and reuse of existing gate reports."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from .coordination_state import excluded_input


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def matches(name, patterns):
    return any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(name, p.replace('**/', '')) for p in patterns)


def component_graph(registry):
    names = {c.get('component', 'shared') for c in registry['checks']} - {'shared'}
    inputs = registry.get('component_inputs', {})
    graph = registry.get('component_dependencies', {})
    if not isinstance(inputs, dict) or not isinstance(graph, dict) or set(inputs) != names or set(graph) != names:
        return None
    if any(not isinstance(v, list) or not v or not all(isinstance(p, str) for p in v) for v in inputs.values()):
        return None
    if any(not isinstance(v, list) or not all(isinstance(p, str) for p in v) or not set(v) <= names
           for v in graph.values()):
        return None
    pending = set(names)
    while pending:
        ready = {n for n in pending if not set(graph[n]) & pending}
        if not ready:
            return None
        pending -= ready
    return graph


def changed_paths(repo, base):
    if not base:
        return None
    commands = [['diff', '--name-only', '-z', base, '--'], ['ls-files', '--others', '--exclude-standard', '-z']]
    paths = set()
    for command in commands:
        result = subprocess.run(['git', '-C', str(repo), *command], capture_output=True)
        if result.returncode:
            return None
        paths.update(os.fsdecode(p) for p in result.stdout.split(b'\0') if p)
    return {p for p in paths if not excluded_input(p)}


def select_components(repo, registry, base, affected):
    if not affected:
        return None, 'Full configured selection'
    graph = component_graph(registry)
    paths = changed_paths(repo, base)
    if graph is None or paths is None:
        return None, 'Missing base or uncertain component graph; full selection'
    selected = set()
    shared = registry.get('shared_input_patterns', [])
    for name in paths:
        owners = {c for c, patterns in registry['component_inputs'].items() if matches(name, patterns)}
        if matches(name, shared):
            return None, 'Shared build or policy input; full selection'
        if Path(name).suffix.lower() in {'.md', '.rst'} or (name.startswith('docs/') and Path(name).suffix == '.txt'):
            continue
        if not owners:
            return None, 'Shared or unclassified change; full selection'
        selected.update(owners)
    while True:
        consumers = {c for c, producers in graph.items() if selected & set(producers)}
        if consumers <= selected:
            return selected, 'Changed components and downstream consumers'
        selected.update(consumers)


def semantic_key(check):
    return digest({k: v for k, v in check.items() if k not in {'id', 'component', 'required', 'stage', 'when'}})


def input_patterns(registry, component):
    graph = component_graph(registry)
    if not graph or component == 'shared':
        return None
    upstream = {component}
    while True:
        producers = {p for c in upstream for p in graph[c]}
        if producers <= upstream:
            break
        upstream.update(producers)
    return [p for c in upstream for p in registry['component_inputs'][c]] + registry.get('shared_input_patterns', [])


def hash_paths(repo, patterns):
    repo = Path(repo).resolve()
    paths = {}
    for pattern in patterns:
        found = sorted(repo.glob(pattern))
        if not any(p.is_file() for p in found):
            paths[pattern] = None
        for path in found:
            if path.is_symlink() or not path.resolve().is_relative_to(repo):
                raise ValueError('Unsafe reuse artifact')
            if path.is_file():
                paths[path.relative_to(repo).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return paths


def executable_identity(repo, check):
    argv = check['argv']
    executable = argv[0].replace('{repo}', str(repo))
    if '/' in executable:
        executable = str((repo / check.get('cwd', '.') / executable).resolve())
    else:
        executable = shutil.which(executable)
    if not executable or not Path(executable).is_file() or not os.access(executable, os.X_OK):
        return None
    return {'path': executable, 'mode': Path(executable).stat().st_mode,
            'sha256': hashlib.sha256(Path(executable).read_bytes()).hexdigest()}


def reuse_identity(repo, registry, check, files):
    policy = check.get('reuse', {})
    if (not isinstance(policy, dict) or not isinstance(policy.get('max_age_seconds'), int)
            or policy['max_age_seconds'] <= 0 or check.get('result_format') or check.get('sonar')
            or Path(check['argv'][0]).name in {'gitleaks', 'semgrep', 'osv-scanner', 'trivy', 'strix'}):
        return None
    patterns = input_patterns(registry, check.get('component', 'shared'))
    if patterns is None:
        selected = files
    else:
        selected = {n: h for n, h in files.items()
                    if '/' not in n or n.startswith(('.ai/', '.github/')) or matches(n, patterns)
                    or not any(matches(n, values) for values in registry['component_inputs'].values())}
    if any((repo / name).is_symlink() for name in selected):
        return None
    tool = executable_identity(repo, check)
    toolchain = hash_paths(repo, policy.get('toolchain_files', []))
    if tool is None or any(value is None for value in toolchain.values()):
        return None
    return digest({'inputs': selected, 'registry': registry, 'check': check,
                   'environment': dict(os.environ), 'tool': tool,
                   'toolchain': toolchain,
                   'runtime': [sys.version, sys.executable, platform.platform()],
                   'helpers': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                               for name in ['gate_selection.py', 'gates.py', 'gate_reports.py']}})


def artifact_hashes(repo, check, result):
    patterns = [result['log']]
    if check.get('test_report'):
        patterns.append(check['test_report']['glob'])
    if check.get('sonar'):
        patterns.append(check['sonar']['report'])
    patterns.extend(check.get('reuse', {}).get('artifacts', []))
    artifacts = hash_paths(repo, patterns)
    if not artifacts or any(value is None for value in artifacts.values()):
        return None
    return artifacts


def attach_provenance(repo, check, result, identity):
    if result['status'] != 'passed' or not identity:
        return result
    try:
        artifacts = artifact_hashes(repo, check, result)
        if artifacts:
            result.update(reuse_identity=identity, artifacts=artifacts)
    except (OSError, ValueError):
        pass
    return result


def find_reusable(repo, check, identity):
    if not identity:
        return None
    max_age = check['reuse']['max_age_seconds']
    reports = sorted((repo / '.ai/reports').glob('*/result.json'), reverse=True)[:100]
    for path in reports:
        try:
            report = json.loads(path.read_text())
            if report.get('status') != 'passed':
                continue
            for result in report['results']:
                if reusable(repo, result, identity, max_age):
                    return dict(result, id=check['id'], component=check.get('component', 'shared'),
                                required=check.get('required', True), reused_from=str(path.relative_to(repo)))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None


def reusable(repo, result, identity, max_age):
    if result.get('status') != 'passed' or result.get('reuse_identity') != identity:
        return False
    if not 0 <= time.time() - result['started_at'] <= max_age:
        return False
    artifacts = result.get('artifacts', {})
    if not artifacts or result.get('tests', {}).get('executed', 1) <= 0:
        return False
    return all(value and hash_paths(repo, [name]) == {name: value} for name, value in artifacts.items())
