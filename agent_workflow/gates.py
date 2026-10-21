"""Revision-bound quality gates shared by hooks, manual checks and CI."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from . import gate_reports, gate_selection
from .coordination_state import _normalized_input, input_snapshot

BUNDLE = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', 'node_modules', '.gradle', '.svelte-kit', '__pycache__',
             'build', 'dist', 'coverage', '.venv', 'venv', 'test-results', 'playwright-report', 'generated'}
SKIP_PREFIXES = ('.ai/state/', '.ai/evidence/', '.ai/reports/', '.ai/backups/',
                 '.ai/install-backups/', '.ai/bundles/', '.agents/', '.claude/', '.codex/', '.cursor/',
                 '.github/skills/', '.github/agents/')
SKIP_FILES = {'.ai/install-state.json', '.ai/.install.lock'}
STAGES = {'fast': 0, 'integration': 1, 'delivery': 2}
CODE_SUFFIXES = {'.kt', '.java', '.ts', '.tsx', '.js', '.jsx', '.svelte', '.py', '.go', '.rb', '.rs'}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def inside(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes repository: {name}')
    return path


def input_files(repo):
    for directory, dirs, files in os.walk(repo, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and
                         not (Path(directory) / d).is_symlink() and
                         not ((Path(directory) / d).relative_to(repo).as_posix() + '/').startswith(SKIP_PREFIXES))
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(repo).as_posix()
            if name == '.DS_Store' or relative in SKIP_FILES or relative.startswith(SKIP_PREFIXES):
                continue
            if not path.is_symlink():
                yield relative, path


def fingerprint(repo):
    repo = Path(repo).resolve()
    if git_revision(repo):
        snapshot = input_snapshot(repo)
        return {'sha256': snapshot['fingerprint'], 'files': snapshot['files'], 'boundary': 'git-inputs'}
    digests = {name: hashlib.sha256(_normalized_input(name, path.read_bytes())).hexdigest()
               for name, path in input_files(repo)}
    raw = json.dumps(digests, sort_keys=True, separators=(',', ':')).encode()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'files': digests, 'boundary': 'filesystem-fixture'}


def git_revision(repo):
    result = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def load_registry(repo, override=None):
    config_path = repo / '.ai/config.json'
    config = read_json(config_path) if config_path.exists() else {}
    profile = config.get('profile', 'general')
    if not re.fullmatch(r'[a-z0-9-]+', profile):
        raise ValueError('Invalid profile name')
    candidate = Path(override) if override else repo / '.ai/gates.json'
    registry = read_json(candidate if candidate.exists() else BUNDLE / 'profiles' / f'{profile}.json')
    if registry.get('schema_version') != 1 or not isinstance(registry.get('checks'), list):
        raise ValueError('Invalid gate registry')
    ids = [check['id'] for check in registry['checks']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate gate IDs')
    return registry


def applicable(repo, check):
    patterns = check.get('when', [])
    if not patterns:
        return True
    return any(matches(name, patterns)
               for name, _ in input_files(repo))


def matches(name, patterns):
    return any(fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(name, pattern.replace('**/', ''))
               for pattern in patterns)


def expand_argv(check, repo):
    argv = check.get('argv')
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise ValueError('Gate requires an explicit argv array')
    values = {'bundle': str(BUNDLE), 'repo': str(repo)}
    return [a.replace('{bundle}', values['bundle']).replace('{repo}', values['repo']) for a in argv]


def execute_check(repo, check, output_dir):
    cwd = inside(repo, check.get('cwd', '.'))
    argv = expand_argv(check, repo)
    started = time.time()
    result = {'id': check['id'], 'required': check.get('required', True),
              'component': check.get('component', 'shared'), 'argv': argv,
              'cwd': check.get('cwd', '.'), 'started_at': started}
    from .process_runner import run_process
    from .host_probes import sanitized_output
    captured = run_process(argv, cwd, check.get('timeout_seconds', 600), check.get('resources'))
    result.update(exit_code=captured['exit_code'], status=captured['status'],
                  resources=captured.get('resources'), truncated=captured['truncated'],
                  output_bytes=captured['output_bytes'], cleanup_verified=captured.get('cleanup_verified'), executed_argv=captured.get('executed_argv'))
    if captured.get('reason'):
        result['reason'] = captured['reason']
    if check.get('result_format') and result['status'] == 'passed':
        result.update(scanner_summary(captured['stdout'], check['result_format']))
    output = (sanitized_output(captured['stdout'].decode('utf-8', errors='replace')) + '\n' +
              sanitized_output(captured['stderr'].decode('utf-8', errors='replace'))).encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    log = output_dir / f"{check['id']}.log"
    log.write_bytes(output)
    result.update(log=str(log.relative_to(repo)), log_sha256=hashlib.sha256(output).hexdigest(),
                  duration_seconds=round(time.time() - started, 3))
    if result['status'] == 'passed':
        try:
            validate_outputs(repo, check, result, started)
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
            result.update(status='failed', reason=f'Cannot validate output report: {error}')
    return result


def scanner_summary(output, format_name):
    try:
        report = json.loads(output)
        if format_name == 'osv-json':
            packages = [p['package'] for source in report['results'] for p in source['packages']]
            if not packages or any(not all(p.get(k) for k in ('name', 'version', 'ecosystem')) for p in packages):
                return {'status': 'blocked', 'reason': 'Scanner did not identify a usable dependency inventory'}
            findings = [v for source in report['results'] for p in source['packages'] for v in p.get('vulnerabilities', [])]
            return {'status': 'failed' if findings else 'passed', 'inventory_count': len(packages), 'finding_count': len(findings)}
        if format_name == 'semgrep-json':
            scanned = report.get('paths', {}).get('scanned', [])
            if report.get('errors') or not scanned:
                return {'status': 'blocked', 'reason': 'SAST parse errors or empty scanned selection'}
            return {'status': 'failed' if report['results'] else 'passed', 'scanned_files': len(scanned)}
        raise ValueError('Unsupported scanner result format')
    except (ValueError, KeyError, TypeError):
        return {'status': 'blocked', 'reason': 'Scanner produced an invalid result document'}


def validate_outputs(repo, check, result, started):
    report = check.get('test_report')
    if report:
        paths = sorted(repo.glob(report['glob']))
        if not paths or any(p.stat().st_mtime < started for p in paths):
            result.update(status='failed', reason='Missing or stale test report')
            return
        summary = gate_reports.test_summary(paths, report['format'])
        result['tests'] = summary
        if summary['executed'] <= 0 or summary['failures'] > 0:
            result.update(status='failed', reason='Empty selection or failing tests')
    if check.get('sonar'):
        proof = inside(repo, check['sonar']['report'])
        if not proof.exists():
            result.update(status='blocked', reason='Sonar analysis proof is unavailable')
            return
        data = read_json(proof)
        revision = git_revision(repo)
        if not revision or data.get('revision') != revision or data.get('status') != 'OK':
            result.update(status='failed', reason='Sonar result is stale or quality gate failed')
        if proof.stat().st_mtime < started:
            result.update(status='failed', reason='Sonar proof was not refreshed by this command')


def coverage_result(repo, coverage, base, checks, run_started, threshold=80):
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
        raise ValueError('Project changed coverage threshold must be between 0 and 100')
    component = coverage['component']
    result = {'id': f'{component}-changed-coverage', 'component': component, 'required': True}
    if not base:
        return result | {'status': 'blocked', 'reason': 'Changed coverage requires --base REV'}
    try:
        changes = gate_reports.changed_lines(repo, base, coverage['roots'])
        if not changes:
            return result | {'status': 'not-applicable', 'reason': 'No changed source lines'}
        reports = [p for pattern in coverage['reports'] for p in repo.glob(pattern)]
        valid = {name: sha for check in checks if check.get('reused_from')
                 for name, sha in check.get('artifacts', {}).items()}
        if not reports or any(p.stat().st_mtime < run_started and
                              valid.get(p.relative_to(repo).as_posix()) != hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in reports):
            return result | {'status': 'blocked', 'reason': 'Missing or stale coverage report'}
        lines = gate_reports.coverage_lines(reports, coverage['format'], coverage.get('source_prefix', ''))
        measurement = gate_reports.measure_coverage(repo, changes, lines, coverage.get('exclude', []))
        status = 'passed' if measurement['percent'] >= threshold else 'failed'
        if measurement['missing_files']:
            status = 'failed'
        if measurement['executable'] == 0 and not measurement['missing_files']:
            status = 'not-applicable'
        return result | measurement | {'status': status, 'threshold': threshold}
    except (ValueError, OSError) as error:
        return result | {'status': 'blocked', 'reason': str(error)}


def required_sonar(repo, registry, stage, component=None):
    results = []
    sonar = registry.get('sonar', {})
    if sonar.get('required') and STAGES[stage] >= STAGES['integration']:
        configured = [c for c in registry['checks'] if c.get('sonar') and c.get('required', True)
                      and (not component or c.get('component') in {component, 'shared'})
                      and applicable(repo, c) and STAGES[c.get('stage', 'integration')] <= STAGES[stage]]
        if not configured:
            results.append({'id': 'sonar-required', 'status': 'blocked', 'required': True,
                            'reason': 'Required Sonar analysis has no applicable configured proof command'})
    return results


def source_support(repo, registry):
    supported = registry.get('supported_suffixes', [])
    patterns = [pattern for check in registry['checks'] if check.get('component', 'shared') != 'shared'
                for pattern in check.get('when', [])]
    patterns.extend(registry.get('source_patterns', []))
    unsupported = [name for name, path in input_files(repo)
                   if path.suffix in CODE_SUFFIXES and not matches(name, registry.get('source_exclude', []))
                   and (path.suffix not in supported or not matches(name, patterns))]
    return ([{'id': 'stack-support', 'status': 'blocked', 'required': True,
              'reason': 'No stack-specific checks configured for these sources', 'paths': unsupported}]
            if unsupported else [])


def selected_checks(repo, registry, stage, component, selected):
    for check in registry['checks']:
        if not re.fullmatch(r'[a-z0-9-]+', check['id']):
            raise ValueError('Unsafe gate ID')
        name = check.get('component', 'shared')
        if STAGES[check.get('stage', 'integration')] > STAGES[stage]:
            continue
        if component and name not in {component, 'shared'}:
            continue
        if selected is not None and name != 'shared' and name not in selected:
            continue
        yield check


def check_results(repo, registry, checks, output_dir, files, reuse):
    results, completed = [], {}
    for check in checks:
        if not applicable(repo, check):
            results.append({'id': check['id'], 'status': 'not-applicable', 'reason': 'No matching source inputs'})
            continue
        key = gate_selection.semantic_key(check)
        if key in completed:
            result = dict(completed[key], id=check['id'], component=check.get('component', 'shared'),
                          required=check.get('required', True), deduplicated_from=completed[key]['id'])
        else:
            identity_check = dict(check, argv=expand_argv(check, repo))
            identity = gate_selection.reuse_identity(repo, registry, identity_check, files) if reuse else None
            result = gate_selection.find_reusable(repo, check, identity) if reuse else None
            if result is None:
                result = execute_check(repo, check, output_dir)
                gate_selection.attach_provenance(repo, check, result, identity)
            completed[key] = result
        results.append(result)
        if result.get('resources', {}).get('stopped'):
            results.append({'id': 'resource-batch-stop', 'status': 'blocked', 'required': True,
                            'reason': 'Remaining checks were not launched after resource stop'})
            break
    return results


def run_gates(repo, stage='fast', registry_path=None, component=None, base=None, affected=True, reuse=False):
    repo = Path(repo).resolve()
    registry = load_registry(repo, registry_path)
    components = {check.get('component', 'shared') for check in registry['checks']}
    if component and component not in components - {'shared'}:
        raise ValueError(f'Unknown configured component: {component}')
    selected, selection_reason = gate_selection.select_components(repo, registry, base, affected)
    before = fingerprint(repo)
    output_dir = repo / '.ai/reports' / f'{time.time_ns()}-{os.getpid()}'
    started = time.time()
    results = required_sonar(repo, registry, stage, component)
    checks = selected_checks(repo, registry, stage, component, selected)
    results.extend(check_results(repo, registry, checks, output_dir, before['files'], reuse))
    if STAGES[stage] >= STAGES['integration']:
        for coverage in registry.get('coverage', []):
            if component and component != coverage['component']:
                continue
            if selected is not None and coverage['component'] not in selected:
                continue
            if applicable(repo, coverage):
                results.append(coverage_result(repo, coverage, base, results, started, registry.get('limits', {}).get('changed_coverage_percent', 80)))
    results.extend(source_support(repo, registry))
    after = fingerprint(repo)
    if before != after:
        results.append({'id': 'input-stability', 'status': 'failed', 'required': True,
                        'reason': 'Verification modified implementation inputs; inspect and rerun'})
    failures = [r for r in results if r['status'] in {'failed', 'blocked'} and r.get('required', True)]
    status = 'blocked' if any(r['status'] == 'blocked' for r in failures) else 'failed' if failures else 'passed'
    record = {'schema_version': 1, 'status': status, 'stage': stage,
              'revision': git_revision(repo), 'input_fingerprint': before['sha256'],
              'registry_sha256': hashlib.sha256(json.dumps(registry, sort_keys=True).encode()).hexdigest(),
              'timestamp': datetime.now(timezone.utc).isoformat(), 'results': results,
              'selection': {'affected': affected, 'components': sorted(selected) if selected is not None else None,
                            'reason': selection_reason}, 'reuse_requested': reuse}
    write_json(output_dir / 'result.json', record)
    record['report'] = str((output_dir / 'result.json').relative_to(repo))
    return record


def register(subparsers):
    parser = subparsers.add_parser('gate', help='Run pinned project quality gates')
    parser.add_argument('--repo', default='.')
    parser.add_argument('--stage', choices=STAGES, default='fast')
    parser.add_argument('--registry')
    parser.add_argument('--component')
    parser.add_argument('--base')
    parser.add_argument('--affected', action='store_true', default=True, help='Select affected components and consumers (default)')
    parser.add_argument('--reuse', action='store_true')
    parser.set_defaults(handler=lambda a: run_gates(a.repo, a.stage, a.registry, a.component, a.base, a.affected, a.reuse))
    parser = subparsers.add_parser('fingerprint', help='Hash implementation and requirement inputs')
    parser.add_argument('--repo', default='.')
    parser.set_defaults(handler=lambda a: fingerprint(a.repo))
    parser = subparsers.add_parser('hook', help='Use the same fast gates as explicit verification')
    parser.add_argument('--repo', default='.')
    parser.add_argument('--host', default='manual')
    parser.add_argument('--stage', choices=STAGES, default='fast')
    parser.set_defaults(handler=lambda a: run_gates(a.repo, a.stage))
