"""Parse actual test and line coverage reports without executing report content."""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET


def test_summary(paths, format_name):
    executed = failures = skipped = 0
    for path in paths:
        if format_name == 'junit':
            root = ET.parse(path).getroot()
            cases = list(root.iter('testcase'))
            skipped += sum(case.find('skipped') is not None for case in cases)
            executed += sum(case.find('skipped') is None for case in cases)
            failures += sum(case.find('failure') is not None or case.find('error') is not None for case in cases)
        elif format_name == 'vitest':
            report = json.loads(path.read_text())
            executed += report['numPassedTests'] + report['numFailedTests']
            failures += report['numFailedTests']
            skipped += report.get('numPendingTests', 0)
        else:
            raise ValueError(f'Unsupported test report format: {format_name}')
    return {'executed': executed, 'failures': failures, 'skipped': skipped}


def normalize_source(value, prefix=''):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Coverage source paths must be repository relative')
    return (Path(prefix) / path).as_posix().removeprefix('./')


def lcov_lines(path, prefix):
    result = {}
    source = None
    for line in path.read_text().splitlines():
        if line.startswith('SF:'):
            source = normalize_source(line[3:], prefix)
            result.setdefault(source, {})
        elif line.startswith('DA:') and source:
            number, hits, *_ = line[3:].split(',')
            result[source][int(number)] = int(hits) > 0
    return result


def jacoco_lines(path, prefix):
    result = {}
    root = ET.parse(path).getroot()
    for package in root.findall('package'):
        for source in package.findall('sourcefile'):
            name = normalize_source(str(Path(package.attrib['name']) / source.attrib['name']), prefix)
            result[name] = {int(line.attrib['nr']): int(line.attrib['ci']) > 0
                            for line in source.findall('line')}
    return result


def coverage_lines(paths, format_name, prefix=''):
    parser = {'lcov': lcov_lines, 'jacoco': jacoco_lines}.get(format_name)
    if not parser:
        raise ValueError(f'Unsupported coverage report format: {format_name}')
    result = {}
    for path in paths:
        for name, lines in parser(path, prefix).items():
            target = result.setdefault(name, {})
            for number, hit in lines.items():
                target[number] = target.get(number, False) or hit
    return result


def changed_lines(repo, base, roots):
    if not base or base.startswith('-'):
        raise ValueError('Invalid coverage base revision')
    valid = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', f'{base}^{{commit}}'],
                           capture_output=True, text=True)
    if valid.returncode:
        raise ValueError('Coverage base is not a resolvable commit')
    diff = subprocess.run(['git', '-C', str(repo), '-c', 'core.quotepath=false', 'diff', '--no-ext-diff', '--unified=0',
                           valid.stdout.strip(), '--', *roots], capture_output=True, text=True, check=True)
    result = {}
    source = None
    for line in diff.stdout.splitlines():
        if line.startswith('+++ b/'):
            source = line[6:]
        elif line.startswith('+++ /dev/null'):
            source = None
        elif source and line.startswith('@@'):
            match = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if match:
                start, count = int(match[1]), int(match[2] or 1)
                result.setdefault(source, set()).update(range(start, start + count))
    untracked = subprocess.run(['git', '-C', str(repo), 'ls-files', '--others', '--exclude-standard', '-z', '--', *roots],
                               capture_output=True, check=True)
    for name in untracked.stdout.decode().split('\0'):
        if name:
            result[name] = set(range(1, len((Path(repo) / name).read_text().splitlines()) + 1))
    return {name: lines for name, lines in result.items() if lines}


def measure_coverage(repo, changes, reports, exclusions=()):
    executable = covered = 0
    missing = []
    for name, changed in changes.items():
        if any(fnmatch.fnmatch(name, pattern) for pattern in exclusions):
            continue
        if Path(name).suffix not in {'.kt', '.java', '.ts', '.js', '.tsx', '.jsx', '.svelte'}:
            continue
        if name not in reports:
            missing.append(name)
            continue
        measured = changed & reports[name].keys()
        executable += len(measured)
        covered += sum(reports[name][line] for line in measured)
    return {'executable': executable, 'covered': covered,
            'percent': round(covered / executable * 100, 3) if executable else 100,
            'missing_files': missing}
