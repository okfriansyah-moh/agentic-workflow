"""Validate retained, component-scoped quality evidence against measured inputs."""
from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from . import gate_reports, gate_selection


def count(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('Quality counters must be nonnegative integers')
    return value


def ratio(value, label, empty=False):
    covered, total = count(value['covered']), count(value['total'])
    if covered > total or (not total and not empty):
        raise ValueError(f'Invalid {label} counters')
    if total and covered * 100 < total * 80:
        raise ValueError(f'{label} is below 80%')
    return covered, total


def snapshot(repo, patterns):
    if not isinstance(patterns, list) or not patterns or not all(isinstance(p, str) and p for p in patterns):
        raise ValueError('Quality input patterns must be nonempty')
    value = gate_selection.hash_paths(repo, patterns)
    if not value or any(v is None for v in value.values()):
        raise ValueError('Missing quality inputs or toolchain files')
    return value


def report_paths(repo, patterns):
    paths = []
    for pattern in patterns:
        found = [p for p in repo.glob(pattern) if p.is_file()]
        if not found:
            raise ValueError('Missing quality report')
        paths.extend(found)
    return sorted(set(paths))


def validate_classifications(repo, items):
    if not isinstance(items, list):
        raise ValueError('Invalid analyzer classifications')
    issues = [item.get('issue') for item in items if isinstance(item, dict)]
    if len(issues) != len(items) or len(issues) != len(set(issues)):
        raise ValueError('Analyzer classifications must identify unique issues')
    for item in items:
        required = ('issue', 'rule', 'source_sha256', 'rationale', 'evidence', 'reviewer', 'reviewed_at')
        if item.get('status') != 'FALSE_POSITIVE' or any(not item.get(k) for k in required):
            raise ValueError('Classification lacks independent review evidence')
        if item.get('reviewer') == item.get('author') or not item.get('author'):
            raise ValueError('Classification review must be independent')
        source = snapshot(repo, [item['source']])
        if source != {item['source']: item['source_sha256']}:
            raise ValueError('Classification source is stale')
        evidence = snapshot(repo, [item['evidence']])
        if evidence != {item['evidence']: item.get('evidence_sha256')}:
            raise ValueError('Classification evidence is missing or changed')
        reviewed = datetime.fromisoformat(item['reviewed_at'].replace('Z', '+00:00'))
        if reviewed.tzinfo is None or reviewed > datetime.now(timezone.utc):
            raise ValueError('Classification review time is invalid')


def validate_analyzer(repo, value):
    if value['status'] != 'SUCCESS' or value['gate'] != 'OK' or not value['analysis_id']:
        raise ValueError('Analyzer execution or gate is unfinished or failed')
    lines = ratio(value['lines'], 'Analyzer line coverage')
    conditions = (count(value['conditions']['covered']), count(value['conditions']['total']))
    if conditions[0] > conditions[1]:
        raise ValueError('Invalid condition counters')
    ratio({'covered': sum((lines[0], conditions[0])), 'total': sum((lines[1], conditions[1]))}, 'Analyzer combined coverage')
    for name in ('security_issues', 'reliability_issues', 'duplicated_lines', 'duplicated_blocks'):
        if count(value[name]) != 0:
            raise ValueError(f'Analyzer {name} must be exactly zero')
    classifications = value['classifications']
    validate_classifications(repo, classifications)
    inventory = value['classified_issue_ids']
    if not isinstance(inventory, list) or inventory != sorted({item['issue'] for item in classifications}):
        raise ValueError('Analyzer disposition inventory differs from reviewed classifications')


def validate_provenance(repo, contract, proof):
    measured = datetime.fromisoformat(proof['measured_at'].replace('Z', '+00:00'))
    age = (datetime.now(timezone.utc) - measured).total_seconds()
    if not proof['revision'] or not 0 <= age <= contract.get('max_age_seconds', 86400):
        raise ValueError('Quality measurement is stale or undated')
    execution = proof['execution']
    if execution['runtime'] != 'docker' or not execution['tests_separate_from_analysis']:
        raise ValueError('Quality workloads require separate Docker phases')
    if not execution['images'] or any(not isinstance(image, str) or not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}', image) for image in execution['images']):
        raise ValueError('Quality Docker images must be pinned by digest')
    if count(execution['memory_bytes']) <= 0 or count(execution['workers']) <= 0:
        raise ValueError('Quality workloads require memory and worker bounds')
    if proof['contract_sha256'] != gate_selection.digest(contract):
        raise ValueError('Quality configuration changed since measurement')
    for name in ('inputs', 'toolchain_files'):
        if proof[name] != snapshot(repo, contract[name]):
            raise ValueError(f'Stale quality {name}')
    if not contract['commands'] or proof['commands'] != contract['commands']:
        raise ValueError('Quality commands differ from configured producers')
    if any(not isinstance(argv, list) or not argv or not all(isinstance(a, str) and a for a in argv) for argv in contract['commands']):
        raise ValueError('Quality commands require argv arrays')


def validate_unit(repo, contract, proof):
    production = snapshot(repo, contract['production'])
    production = {p: h for p, h in production.items() if not gate_selection.matches(p, contract.get('exclude', []))}
    if not production or sorted(proof['production_files']) != sorted(production):
        raise ValueError('Maintained production files are omitted')
    hashes = proof['reports']
    if not hashes or gate_selection.hash_paths(repo, list(hashes)) != hashes:
        raise ValueError('Missing or modified quality artifacts')
    unit_report = contract['unit_report']
    unit_paths = report_paths(repo, unit_report['reports'])
    test_report = contract['test_report']
    test_paths = report_paths(repo, [test_report['glob']])
    if any(p.relative_to(repo).as_posix() not in hashes for p in unit_paths + test_paths):
        raise ValueError('Raw unit reports are not retained in proof')
    validate_producer(repo, proof, unit_paths + test_paths)
    lines = gate_reports.coverage_lines(unit_paths, unit_report['format'], unit_report.get('source_prefix', ''))
    if set(production) - set(lines):
        raise ValueError('Untested production files absent from instrumentation')
    measured = {p: lines[p] for p in production}
    counters = {'covered': sum(sum(v.values()) for v in measured.values()), 'total': sum(len(v) for v in measured.values())}
    for value in proof['unit']['lines'].values():
        count(value)
    for value in proof['unit']['tests'].values():
        count(value)
    if proof['unit']['kind'] != 'unit' or counters != proof['unit']['lines']:
        raise ValueError('Unit-only counters differ from raw reports')
    ratio(counters, 'Unit line coverage')
    tests = gate_reports.test_summary(test_paths, test_report['format'])
    if tests['executed'] <= 0 or tests['failures'] or proof['unit']['tests'] != tests:
        raise ValueError('Failed, empty or mismatched unit selection')
    return lines, counters


def validate_changed(repo, contract, proof, base, lines):
    if not base or proof['changed']['base'] != base:
        raise ValueError('Changed coverage requires matching base')
    changes = gate_reports.changed_lines(repo, base, contract['roots'])
    changed = gate_reports.measure_coverage(repo, changes, lines, contract.get('exclude', []))
    expected = {'base': base, 'covered': changed['covered'], 'total': changed['executable'], 'missing_files': changed['missing_files']}
    count(proof['changed']['covered'])
    count(proof['changed']['total'])
    if proof['changed'] != expected or changed['missing_files']:
        raise ValueError('Changed coverage differs from source or omits files')
    ratio(expected, 'Changed line coverage', empty=True)
    return expected


def validate_producer(repo, proof, unit_paths):
    name = proof['producer_report']
    if name not in proof['reports']:
        raise ValueError('Producer receipt is not retained')
    path = (repo / name).resolve()
    if not path.is_relative_to(repo.resolve()):
        raise ValueError('Producer receipt escapes repository')
    receipt = json.loads(path.read_text())
    for key in ('inputs', 'toolchain_files', 'commands', 'contract_sha256', 'revision', 'measured_at'):
        if receipt[key] != proof[key]:
            raise ValueError('Producer provenance differs from normalized proof')
    hashes = {p.relative_to(repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in unit_paths}
    if receipt['unit_reports'] != hashes:
        raise ValueError('Producer receipt does not bind raw unit reports')
    started = datetime.fromisoformat(receipt['measured_at'].replace('Z', '+00:00')).timestamp()
    finished = datetime.fromisoformat(receipt['finished_at'].replace('Z', '+00:00')).timestamp()
    if not started <= finished <= datetime.now(timezone.utc).timestamp():
        raise ValueError('Invalid producer measurement interval')
    if any(not started <= p.stat().st_mtime <= finished for p in unit_paths):
        raise ValueError('Raw reports predate producer measurement')
    if proof['analyzer']['input_sha256'] != gate_selection.digest(proof['inputs']):
        raise ValueError('Analyzer measured different source inputs')
    if proof['analyzer']['producer_sha256'] != proof['reports'][name]:
        raise ValueError('Analyzer did not consume the measured unit receipt')


def retained_analyzer(repo, proof):
    hashes = proof['reports']
    analyzer_path = proof['analyzer_report']
    if analyzer_path not in hashes:
        raise ValueError('Raw analyzer report is not retained')
    raw = (repo / analyzer_path).resolve()
    if not raw.is_relative_to(repo.resolve()) or json.loads(raw.read_text()) != proof['analyzer']:
        raise ValueError('Analyzer counters differ from retained report')
    validate_analyzer(repo, proof['analyzer'])


def validate_component(repo, contract, proof, base):
    validate_provenance(repo, contract, proof)
    lines, counters = validate_unit(repo, contract, proof)
    changed = validate_changed(repo, contract, proof, base, lines)
    retained_analyzer(repo, proof)
    return {'component': contract['id'], 'unit': counters, 'changed': changed, 'analyzer': proof['analyzer']}


def results(repo, registry, base, selected=None):
    """Require all maintained components; affected selection only exempts documentation."""
    if selected == set():
        return []
    result = {'id': 'component-quality', 'required': True}
    try:
        contract = registry.get('quality')
        if not contract or contract.get('schema_version') != 1 or contract.get('required') is not True:
            raise ValueError('Required per-component quality contract is not configured')
        components = contract['components']
        ids = [c['id'] for c in components]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError('Quality components must be complete and unique')
        configured = registry.get('runtime_components')
        if not isinstance(configured, list) or not configured or len(configured) != len(set(configured)) or set(ids) != set(configured):
            raise ValueError('Quality contract omits configured components')
        path = (repo / contract['proof']).resolve()
        if not path.is_relative_to(repo.resolve()):
            raise ValueError('Quality proof escapes repository')
        proof = json.loads(path.read_text())
        if proof.get('schema_version') != 1 or set(proof['components']) != set(ids):
            raise ValueError('Invalid quality proof version or component inventory')
        for item in proof['components'].values():
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(item['measured_at'].replace('Z', '+00:00'))).total_seconds()
            if age > contract.get('max_age_seconds', 86400):
                raise ValueError('Quality proof exceeds policy maximum age')
        values = [validate_component(repo, c, proof['components'][c['id']], base) for c in components]
        return [result | {'status': 'passed', 'components': values}]
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [result | {'status': 'blocked', 'reason': str(error)}]
