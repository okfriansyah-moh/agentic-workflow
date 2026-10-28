"""Read-only completion checks for retained full quality verification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import gate_selection, gates, quality
from .coordination_state import CoordinationError, registry as coordination_registry

HARNESS_PATHS = ('agent_workflow/', 'tests/', 'schemas/', 'profiles/', 'skills/', 'docs/',
                 'adapters/', 'prompts/', 'resources/', 'scripts/', 'ops/unit-coverage/', '.ai/', '.agents/',
                 '.claude/', '.cursor/', '.github/')
HARNESS_FILES = {'manifest.json', 'README.md', 'AGENTS.md', 'CLAUDE.md', 'pyproject.toml', 'Makefile', 'ops/bin/coverage.sh', 'ops/bin/coverage-phase.sh'}


def changed_paths(root, item):
    paths = gate_selection.changed_paths(root, item['initial_revision'])
    if paths is None:
        raise CoordinationError('Cannot establish actual selection changes for quality acceptance')
    return paths


def document_only(paths):
    return bool(paths) and all(Path(p).suffix in {'.md', '.rst'} or
                               (p.startswith('docs/') and Path(p).suffix == '.txt') for p in paths)


def validate_maintenance(root, item, review, registry, paths):
    scope = item.get('quality_scope') or {}
    if scope.get('kind') != 'workflow-maintenance':
        return False
    if not scope.get('approval_reference') or not scope.get('reason') or review.get('quality_scope') != scope:
        raise CoordinationError('Workflow maintenance exemption needs approved scope and independent review')
    allowed = scope.get('paths')
    if not isinstance(allowed, list) or not allowed:
        raise CoordinationError('Workflow maintenance requires explicit paths')
    for name in paths:
        if name not in HARNESS_FILES and not name.startswith(HARNESS_PATHS):
            raise CoordinationError('Workflow maintenance exemption contains product paths')
        if not any(name == p or name.startswith(p.rstrip('/') + '/') for p in allowed):
            raise CoordinationError('Actual changes escape approved workflow maintenance scope')
    production = [p for c in registry.get('quality', {}).get('components', []) for p in c.get('production', [])]
    if any(gate_selection.matches(name, production) for name in paths):
        raise CoordinationError('Workflow maintenance exemption cannot cover maintained product runtime')
    return True


def retained_check(root, check, result):
    if result.get('status') != 'passed' or result.get('argv') != gates.expand_argv(check, root):
        raise CoordinationError('Delivery gate omits a required configured command')
    path = (root / result.get('log', '')).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise CoordinationError('Delivery command log is unavailable')
    if hashlib.sha256(path.read_bytes()).hexdigest() != result.get('log_sha256'):
        raise CoordinationError('Delivery command evidence changed')
    outputs = result.get('outputs')
    if not outputs or gate_selection.hash_paths(root, list(outputs)) != outputs:
        raise CoordinationError('Delivery command output artifacts changed or disappeared')
    report = check.get('test_report')
    if report:
        current = gate_selection.hash_paths(root, [report['glob']])
        if any(value is None or outputs.get(name) != value for name, value in current.items()):
            raise CoordinationError('Delivery test report inventory changed')
        paths = [root / name for name in current]
        summary = gates.gate_reports.test_summary(paths, report['format'])
        if summary['executed'] <= 0 or summary['failures'] or summary != result.get('tests'):
            raise CoordinationError('Delivery test selection is empty, failed or changed')


def check_gate_record(root, registry, record):
    expected_hash = hashlib.sha256(json.dumps(registry, sort_keys=True).encode()).hexdigest()
    if record.get('status') != 'passed' or record.get('stage') != 'delivery' or record.get('full_acceptance') is not True:
        raise CoordinationError('Feature acceptance requires a passed full delivery gate')
    if record.get('input_fingerprint') != gates.fingerprint(root)['sha256'] or record.get('registry_sha256') != expected_hash:
        raise CoordinationError('Delivery gate inputs or registry are stale')
    checks = {r['id']: r for r in record.get('results', [])}
    for check in registry['checks']:
        if check.get('required', True) and gates.applicable(root, check):
            retained_check(root, check, checks.get(check['id'], {}))
    if checks.get('component-quality', {}).get('status') != 'passed':
        raise CoordinationError('Delivery gate has no passing per-component quality result')
    current = quality.results(root, registry, record.get('base'), None)
    if not current or any(r['status'] != 'passed' for r in current):
        raise CoordinationError('Current per-component quality proof is missing or invalid')
    if checks['component-quality'].get('components') != current[0].get('components'):
        raise CoordinationError('Delivery quality result differs from current component evidence')


def registered_gate(root, path, state):
    captured = state.get('gate_reports', {}).get(str(path.resolve()))
    if not captured or captured.get('root') != str(root.resolve()):
        raise CoordinationError('Delivery gate was not captured by this repository registry')
    if captured.get('sha256') != hashlib.sha256(path.read_bytes()).hexdigest():
        raise CoordinationError('Registered delivery gate evidence changed')


def validate_acceptance(root, item, review, spec, state=None):
    if state is None:
        with coordination_registry(root) as captured:
            return validate_acceptance(root, item, review, spec, captured)
    paths = changed_paths(root, item)
    registry = gates.load_registry(root)
    if document_only(paths) or validate_maintenance(root, item, review, registry, paths):
        return
    if spec.get('gate_report'):
        candidates = [(root / spec['gate_report']).resolve()]
    else:
        candidates = sorted((root / '.ai/reports').glob('*/result.json'), reverse=True)
    for path in candidates:
        if not path.is_relative_to(root.resolve()):
            raise CoordinationError('Delivery gate proof escapes repository')
        try:
            registered_gate(root, path, state)
            check_gate_record(root, registry, json.loads(path.read_text()))
            return
        except (OSError, ValueError, KeyError, TypeError, CoordinationError):
            continue
    raise CoordinationError('Feature acceptance requires current full delivery gates and component quality proof')
