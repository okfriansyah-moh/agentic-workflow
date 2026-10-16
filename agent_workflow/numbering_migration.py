"""Owner-authorized numbering handoff; historical proof remains untouched."""
from copy import deepcopy
import hashlib
import re
import time
from pathlib import Path

from .coordination_plan import frontmatter, frontmatter_text, task_index
from .coordination_state import CoordinationError, git, read_json, revision, safe_relative


def _mapping(root, spec):
    path = safe_relative(root, spec['mapping'])
    raw = (root / path).read_bytes()
    data = read_json(root / path)
    if data.get('schema_version') != 1 or data.get('target_numbering') != 'sequential':
        raise CoordinationError('Migration requires schema_version 1 and target_numbering sequential')
    source = data.get('source_revision')
    if not isinstance(source, str) or not re.fullmatch(r'[a-f0-9]{40}', source) or revision(root, source) != source:
        raise CoordinationError('Migration requires an existing full source revision')
    if git(root, 'merge-base', '--is-ancestor', source, 'HEAD', check=False).returncode:
        raise CoordinationError('Migration source must be an ancestor of the current revision')
    rows = data.get('tasks')
    if not isinstance(rows, list) or not rows:
        raise CoordinationError('Migration needs task records')
    for field in ('old_id', 'new_id', 'old_path', 'new_path'):
        values = [row.get(field) for row in rows]
        if any(not isinstance(value, str) or not value for value in values) or len(set(values)) != len(values):
            raise CoordinationError(f'Migration {field} must be a one-to-one mapping')
    return path, hashlib.sha256(raw).hexdigest(), data


def _validate_groups(root, data, plan, index):
    old_text = git(root, 'show', f"{data['source_revision']}:{plan}").stdout
    old_plan, _ = frontmatter_text(old_text, plan)
    rows = data.get('groups', [])
    groups = {row['old_id']: row for row in rows}
    if len(groups) != len(rows) or set(groups) != {entry['id'] for entry in old_plan['groups']}:
        raise CoordinationError('Migration must cover every source group exactly once')
    target_groups = {group['id']: group for group in index['groups']}
    source_tasks, targets = set(), set()
    for entry in old_plan['groups']:
        row = groups[entry['id']]
        old_path = (Path(plan).parent / entry['path']).as_posix()
        if row.get('old_path') != old_path:
            raise CoordinationError('Migration source group path disagrees with source plan')
        group_text = git(root, 'show', f"{data['source_revision']}:{old_path}").stdout
        group, _ = frontmatter_text(group_text, old_path)
        source_tasks.update(group['tasks'])
        paths = [(Path(plan).parent / target_groups[identity]['path']).as_posix() for identity in row['new_ids']]
        if row.get('new_paths') != paths or not paths:
            raise CoordinationError('Migration target group paths disagree with target plan')
        targets.update(row['new_ids'])
    if targets != set(target_groups) or source_tasks != {row['old_id'] for row in data['tasks']}:
        raise CoordinationError('Migration must preserve all source tasks and target groups')


def _validate_evidence(root, row, old_text):
    section = r'^## Evidence\n.*?(?=^## |\Z)'
    before_match = re.search(section, old_text, re.M | re.S)
    after_text = (root / safe_relative(root, row['new_path'])).read_text()
    after_match = re.search(section, after_text, re.M | re.S)
    if before_match or after_match or row.get('evidence_sha256'):
        if not before_match or not after_match or before_match[0] != after_match[0]:
            raise CoordinationError('Migration must preserve the complete Evidence section')
        if hashlib.sha256(before_match[0].encode()).hexdigest() != row.get('evidence_sha256'):
            raise CoordinationError('Migration Evidence digest disagrees with source')


def _validate_tasks(root, data, plan):
    meta, _ = frontmatter(root / safe_relative(root, plan))
    if meta.get('numbering') != 'sequential':
        raise CoordinationError('Target plan must declare numbering sequential')
    index = task_index(root / plan)
    if any(not source['matches'] for source in index['sources']):
        raise CoordinationError('Target plan source fingerprints are not ready')
    _validate_groups(root, data, plan, index)
    rows = data['tasks']
    ids = {row['old_id']: row['new_id'] for row in rows}
    if set(ids.values()) != set(index['tasks']):
        raise CoordinationError('Migration must cover every target task exactly once')
    for row in rows:
        old_path = safe_relative(root, row['old_path'])
        old_text = git(root, 'show', f"{data['source_revision']}:{old_path}").stdout
        before, _ = frontmatter_text(old_text, old_path)
        after = index['tasks'][row['new_id']]
        expected = [ids[dep] for dep in before['depends_on']]
        if before['id'] != row['old_id'] or before['group'] != row['old_group']:
            raise CoordinationError('Source task identity disagrees with migration')
        if before['status'] != row['status_before'] or after['status'] != row['status_before']:
            raise CoordinationError('Numbering migration must preserve task status')
        if before['depends_on'] != row['depends_on_before'] or expected != row['depends_on_after'] or after['depends_on'] != expected:
            raise CoordinationError('Migration must preserve dependency edges')
        _validate_evidence(root, row, old_text)
        target = (root / safe_relative(root, row['new_path'])).resolve()
        if target != (root / plan).parent / after['path'] or after['group'] != row['new_group']:
            raise CoordinationError('Target task identity/path disagrees with migration')
    return ids


def _translate_checks(checks, ids):
    result = deepcopy(checks)
    for check in result:
        args = check.get('argv', [])
        for number, arg in enumerate(args):
            if number and args[number - 1] == '--task' and arg in ids:
                args[number] = ids[arg]
            elif arg.startswith('--task=') and arg[7:] in ids:
                args[number] = '--task=' + ids[arg[7:]]
    return result


def _translate_live(item, ids, paths, groups):
    result = deepcopy(item)
    for field in ('task_ids', 'completed_task_ids', 'depends_on'):
        if field in result:
            result[field] = [ids[value] for value in result[field]]
    if 'dependencies' in result:
        result['dependencies'] = {ids[key]: [ids[dep] for dep in deps] for key, deps in result['dependencies'].items()}
    if 'tested_tasks' in result:
        result['tested_tasks'] = {ids[key]: value for key, value in result['tested_tasks'].items()}
    if 'group_ids' in result:
        result['group_ids'] = list(dict.fromkeys(new for old in result['group_ids'] for new in groups[old]))
    if 'acceptance_ids' in result:
        result['acceptance_ids'] = [re.sub(r'^T\d+(?=-A\d+$)', lambda m: ids[m[0]], value) for value in result['acceptance_ids']]
    for field in ('paths', 'source_references', 'product_paths'):
        if field in result:
            result[field] = [paths.get(value, value) for value in result[field]]
    if 'required_checks' in result:
        result['required_checks'] = _translate_checks(result['required_checks'], ids)
    return result


def _rebind_branch(root, item, claims, spec):
    if 'rebind_branch' in spec and type(spec['rebind_branch']) is not bool:
        raise CoordinationError('rebind_branch must be a boolean')
    if not spec.get('rebind_branch'):
        return None
    if git(root, 'status', '--porcelain', '--untracked-files=all').stdout.strip():
        raise CoordinationError('Branch rebinding requires a clean repository including untracked files')
    branch = git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD', check=False)
    if branch.returncode or not branch.stdout.strip():
        raise CoordinationError('Branch rebinding requires a named branch, not detached HEAD')
    for claim in claims:
        location = claim.get('worktree')
        if not isinstance(location, str) or Path(location).resolve() != root.resolve():
            raise CoordinationError('Branch rebinding requires every active claim in the current worktree')
    target = branch.stdout.strip()
    return {'selection': {'before': item.get('branch'), 'after': target},
            'claims': {claim['id']: {'before': claim.get('branch'), 'after': target} for claim in claims}}


def migrate(root, item, state, spec):
    path, fingerprint, data = _mapping(root, spec)
    previous = item.get('numbering_migrations', [])
    if any(record['sha256'] == fingerprint for record in previous):
        return {'status': 'ok', 'idempotent': True, 'selection': item}
    if item['status'] == 'accepted' or spec.get('idle_acknowledged') is not True:
        raise CoordinationError('Migration requires an unfinished selection and idle acknowledgment')
    if previous:
        raise CoordinationError('This selection already has a different numbering migration')
    ids = _validate_tasks(root, data, spec['plan'])
    paths = {row['old_path']: row['new_path'] for row in data['tasks']}
    groups = {row['old_id']: row['new_ids'] for row in data['groups']}
    if len(groups) != len(data['groups']):
        raise CoordinationError('Duplicate source group in migration')
    expected = {}
    for row in data['tasks']:
        expected.setdefault(row['old_group'], set()).add(row['new_group'])
    if {key: set(value) for key, value in groups.items()} != expected:
        raise CoordinationError('Group lineage must agree with task mappings')
    active = [claim for claim in state['claims'].values() if claim['status'] == 'active']
    affected = [claim for claim in active if set(claim['task_ids']) & set(item['task_ids'])]
    if any(claim['owner'] != item['owner'] or claim.get('selection_id') != item['id'] for claim in affected):
        raise CoordinationError('Affected active claims must belong to this selection owner')
    bindings = _rebind_branch(root, item, affected, spec)
    migrated = _translate_live(item, ids, paths, groups)
    claims = {claim['id']: _translate_live(claim, ids, paths, groups) for claim in affected}
    migrated['numbering_migrations'] = [{'mapping': path, 'sha256': fingerprint,
        'source_revision': data['source_revision'], 'target_revision': revision(root),
        'owner': item['owner'], 'created_at': time.time()}]
    if bindings is not None:
        migrated['branch'] = bindings['selection']['after']
        for identity, binding in bindings['claims'].items():
            claims[identity]['branch'] = binding['after']
        migrated['numbering_migrations'][0]['branch_bindings'] = bindings
    state['selections'][item['id']] = migrated
    state['claims'].update(claims)
    return {'status': 'ok', 'idempotent': False, 'selection': migrated, 'claims': list(claims)}
