"""Read the supported plan frontmatter without evaluating YAML or plan prose."""
from __future__ import annotations

import hashlib
from functools import lru_cache
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


class PlanError(ValueError):
    """A plan cannot be interpreted safely or violates its declared structure."""


def _scalar(value: str):
    value = value.strip()
    if not value:
        return None
    if value.startswith(('&', '*', '!', '|', '>')) or ' # ' in value:
        raise PlanError(f"Unsupported frontmatter expression: {value}")
    if value.startswith('['):
        if not value.endswith(']'):
            raise PlanError('Unclosed inline list')
        inner = value[1:-1].strip()
        return [_scalar(item) for item in inner.split(',')] if inner else []
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'"):
        if not value.endswith("'"):
            raise PlanError('Unclosed quoted scalar')
        return value[1:-1].replace("''", "'")
    if value in ('true', 'false'):
        return value == 'true'
    if value in ('null', '~'):
        return None
    if re.fullmatch(r'-?\d+', value):
        return int(value)
    if value.startswith('{') or '\t' in value:
        raise PlanError('Unsupported mapping or tab in scalar')
    return value


def _pair(text: str):
    match = re.fullmatch(r'([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?', text)
    if not match:
        raise PlanError(f'Expected a simple key/value: {text}')
    return match.group(1), match.group(2) or ''


def _block(lines, pos, indent):
    sequence = lines[pos][1].startswith('- ')
    result = [] if sequence else {}
    while pos < len(lines) and lines[pos][0] == indent:
        text = lines[pos][1]
        if sequence != text.startswith('- '):
            break
        if sequence:
            text = text[2:]
            pos += 1
            if re.match(r'[A-Za-z_][\w-]*:', text):
                key, value = _pair(text)
                item = {key: _scalar(value)}
                if pos < len(lines) and lines[pos][0] > indent:
                    rest, pos = _block(lines, pos, lines[pos][0])
                    if not isinstance(rest, dict) or key in rest:
                        raise PlanError('Unsupported nested sequence mapping')
                    item.update(rest)
                result.append(item)
            else:
                result.append(_scalar(text))
        else:
            key, value = _pair(text)
            if key in result:
                raise PlanError(f'Duplicate frontmatter key: {key}')
            pos += 1
            if not value and pos < len(lines):
                child_indent, child_text = lines[pos]
                if child_indent > indent or (child_indent == indent and child_text.startswith('- ')):
                    result[key], pos = _block(lines, pos, child_indent)
                    continue
            result[key] = _scalar(value)
    return result, pos


def frontmatter(path: Path):
    return frontmatter_text(path.read_text(encoding='utf-8'), path)


def frontmatter_text(text, path='<document>'):
    parts = text.split('---', 2)
    if len(parts) != 3 or parts[0].strip():
        raise PlanError(f'Missing delimited frontmatter: {path}')
    lines = []
    for raw in parts[1].splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        if '\t' in raw:
            raise PlanError(f'Tabs are unsupported in frontmatter: {path}')
        lines.append((len(raw) - len(raw.lstrip()), raw.strip()))
    if not lines:
        raise PlanError(f'Empty frontmatter: {path}')
    data, pos = _block(lines, 0, 0)
    if pos != len(lines) or not isinstance(data, dict):
        raise PlanError(f'Unsupported frontmatter nesting: {path}')
    return data, parts[2]


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _under(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise PlanError(f'Path escapes its package: {relative}')
    return path


def _section(body, heading):
    match = re.search(rf'^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)', body, re.M | re.S)
    return match.group(1) if match else ''


def _table_rows(section):
    for line in section.splitlines():
        if line.startswith('|'):
            row = [cell.strip().strip('`') for cell in line.strip('|').split('|')]
            if row and not all(re.fullmatch(r'[-: ]+', cell) for cell in row):
                yield row


@lru_cache(maxsize=256)
def _anchors(path, modified, size):
    text = Path(path).read_text(encoding='utf-8')
    anchors = set(re.findall(r'\bid=["\']([^"\']+)["\']', text))
    counts = {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.M):
        heading = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', heading)
        heading = re.sub(r'<[^>]+>', '', heading)
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        anchors.add(slug + (f'-{seen}' if seen else ''))
    return anchors


def _local_links(path, body):
    errors = []
    references = []
    for target in re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)', body):
        link = urlsplit(target)
        if link.scheme or link.netloc:
            continue
        destination = (path.parent / unquote(link.path)).resolve() if link.path else path
        references.append({'target': target, 'exists': destination.is_file()})
        if not destination.is_file():
            errors.append(f'{path.name}: missing linked file {target}')
        elif link.fragment and destination.suffix.lower() in ('.md', '.html'):
            stat = destination.stat()
            if unquote(link.fragment) not in _anchors(str(destination), stat.st_mtime_ns, stat.st_size):
                errors.append(f'{path.name}: missing linked section {target}')
    return references, errors


def _task(path, root):
    meta, body = frontmatter(path)
    if meta.get('kind') != 'task' or not re.fullmatch(r'T\d+', str(meta.get('id', ''))):
        raise PlanError(f'Invalid task identity: {path}')
    required = ('group', 'depends_on', 'readiness', 'status', 'test_strategy', 'visual_review')
    missing = [key for key in required if key not in meta]
    if missing or not isinstance(meta.get('depends_on'), list):
        raise PlanError(f'{path.name}: missing task fields or invalid dependencies: {missing}')
    if meta['status'] not in ('Not started', 'In progress', 'In review', 'Blocked', 'Done'):
        raise PlanError(f'{path.name}: unsupported execution status')
    surfaces = list(_table_rows(_section(body, 'Change surface')))[1:]
    refs, errors = _local_links(path, body)
    return {
        **meta, 'path': str(path.relative_to(root)), 'sha256': _hash(path),
        'change_surface': [{'repository': r[0], 'action': r[1], 'path': r[2]}
                           for r in surfaces if len(r) >= 3],
        'acceptance_ids': sorted(set(re.findall(r'\bT\d+-A\d+\b', _section(body, 'Acceptance')))),
        'source_ids': sorted(set(re.findall(r'\b(?:ATDD-\d+|TD-C-\d+|REQ-\d+|NFR-\d+)\b', body))),
        'references': refs, 'reference_errors': errors,
    }


def _order(tasks):
    ordered, active = [], set()
    def visit(task_id):
        if task_id in active:
            raise PlanError(f'Dependency cycle includes {task_id}')
        if task_id in ordered:
            return
        if task_id not in tasks:
            raise PlanError(f'Unknown task dependency {task_id}')
        active.add(task_id)
        for dependency in tasks[task_id]['depends_on']:
            visit(dependency)
        active.remove(task_id)
        ordered.append(task_id)
    for task_id in tasks:
        visit(task_id)
    return ordered


def task_index(plan):
    path = Path(plan).resolve()
    meta, body = frontmatter(path)
    if meta.get('kind') != 'plan' or meta.get('schema_version') != 1:
        raise PlanError('Only kind: plan / schema_version: 1 is supported')
    root = path.parent
    plan_root = _under(root, meta['plan_root'])
    tasks = {}
    for task_path in sorted(plan_root.glob('*/tasks/*.md')):
        item = _task(task_path, root)
        if item['id'] in tasks:
            raise PlanError(f"Duplicate task {item['id']}")
        tasks[item['id']] = item
    if not tasks:
        raise PlanError('The plan selects no task files')
    groups, membership = [], {}
    for entry in meta.get('groups', []):
        group_path = _under(root, entry['path'])
        group, group_body = frontmatter(group_path)
        _validate_group(group, entry, tasks, membership)
        _, failures = _local_links(group_path, group_body)
        groups.append({**group, 'path': entry['path'], 'reference_errors': failures})
    if set(membership) != set(tasks):
        raise PlanError(f'Unowned tasks: {sorted(set(tasks) - set(membership))}')
    _sequential(meta, groups, tasks)
    sources = _sources(meta.get('sources', []), root)
    _, errors = _local_links(path, body)
    errors += [error for item in [*tasks.values(), *groups] for error in item['reference_errors']]
    errors += [f"Source changed or missing: {item['id']}" for item in sources if not item['matches']]
    ordered = _order(tasks)
    for item in tasks.values():
        pending = [dep for dep in item['depends_on'] if tasks[dep]['status'] != 'Done']
        item['execution_eligible'] = item['readiness'] == 'Ready' and not pending and item['status'] != 'Done'
        item['pending_dependencies'] = pending
    return {'status': 'ok' if not errors else 'blocked', 'schema_version': 1,
            'document_readiness': meta.get('readiness'), 'plan': str(path),
            'task_count': len(tasks), 'group_count': len(groups), 'sources': sources,
            'tasks': tasks, 'groups': groups, 'dependency_order': ordered, 'errors': errors,
            'note': 'Indexing does not dispatch work or change task status; runtime prerequisites remain to be checked.'}


def _validate_group(group, entry, tasks, membership):
    if group.get('kind') != 'group' or group.get('id') != entry['id']:
        raise PlanError(f"Group identity mismatch: {entry['id']}")
    members = group.get('tasks', [])
    if not members or group.get('integration_owner') not in members:
        raise PlanError(f"Invalid integration owner in {entry['id']}")
    for member in members:
        if member in membership or member not in tasks:
            raise PlanError(f'Duplicate or unknown group member: {member}')
        if tasks[member]['group'] != group['id']:
            raise PlanError(f'Task/group ownership mismatch: {member}')
        membership[member] = group['id']


def _sources(entries, root):
    sources = []
    for entry in entries:
        source = _under(root, entry['path'])
        digest = _hash(source) if source.is_file() else None
        sources.append({**entry, 'actual_sha256': digest, 'matches': digest == entry.get('sha256')})
    return sources


def _sequential(meta, groups, tasks):
    if meta.get('numbering') is None:
        return
    if meta['numbering'] != 'sequential':
        raise PlanError('Unsupported numbering mode')
    offset = 1
    width = max(2, len(str(len(groups))))
    for number, group in enumerate(groups, 1):
        prefix = f'{number:0{width}d}'
        if group['id'] != f'G{prefix}' or not Path(group['path']).parent.name.startswith(prefix + '-'):
            raise PlanError('Sequential group ID and folder prefix must match their position')
        expected = [f'T{n:03d}' for n in range(offset, offset + len(group['tasks']))]
        if group['tasks'] != expected:
            raise PlanError('Sequential stages require contiguous task ID ranges')
        offset += len(expected)
    for identity, task in tasks.items():
        for dependency in task['depends_on']:
            if dependency not in tasks or int(dependency[1:]) >= int(identity[1:]):
                raise PlanError('Sequential prerequisites must precede their consumers')
