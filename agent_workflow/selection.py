"""One durable delivery selection, with bounded repairs and a combined review."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from .coordination_evidence import (digest, validate_evidence, validate_review,
                                    verify_receipt)
from .coordination_plan import task_index
from .coordination_state import (CoordinationError, check_contract, git, input_snapshot,
                                 read_json, registry, repository, revision, safe_relative)

CHECKPOINT_SECONDS = 2700
REPAIR_SECONDS = 1200
REPAIR_ATTEMPTS = 2


def get_selection(state, identity, owner=None):
    item = state.get('selections', {}).get(identity)
    if item is None:
        raise CoordinationError(f'Unknown selection: {identity}')
    if owner is not None and owner != item['owner']:
        raise CoordinationError('Only the recorded selection owner may change it')
    return item


def _strings(value, field, nonempty=True):
    if not isinstance(value, list) or (nonempty and not value):
        raise CoordinationError(f'{field} must be a list of nonempty strings')
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise CoordinationError(f'{field} must be a list of nonempty strings')
    if len(value) != len(set(value)):
        raise CoordinationError(f'{field} must not contain duplicates')
    return value


def _scope(root, spec):
    tasks = set(_strings(spec.get('task_ids', []), 'task_ids', False))
    groups = _strings(spec.get('group_ids', []), 'group_ids', False)
    if groups and not spec.get('plan'):
        raise CoordinationError('Group selections require a plan')
    index = task_index(root / safe_relative(root, spec['plan'])) if spec.get('plan') else None
    if index:
        if index['status'] != 'ok' or index['document_readiness'] != 'Ready':
            raise CoordinationError('Selection plan sources are not ready')
        known = {group['id']: group for group in index['groups']}
        if set(groups) - set(known):
            raise CoordinationError('Selection contains unknown groups')
        for group in groups:
            tasks.update(known[group]['tasks'])
        if tasks - set(index['tasks']):
            raise CoordinationError('Selection contains unknown tasks')
        if any(index['tasks'][task]['readiness'] != 'Ready' for task in tasks):
            raise CoordinationError('Selected task documents are not ready')
    if not tasks:
        raise CoordinationError('Selection must contain tasks or groups')
    dependencies = {task: index['tasks'][task]['depends_on'] for task in tasks} if index else spec.get('dependencies', {})
    completed = [task for task, item in index['tasks'].items() if item['status'] == 'Done'] if index else spec.get('completed_task_ids', [])
    _validate_dependencies(tasks, dependencies, completed)
    return sorted(tasks), dependencies, completed


def _validate_dependencies(tasks, dependencies, completed):
    _strings(completed, 'completed_task_ids', False)
    if not isinstance(dependencies, dict) or set(dependencies) - tasks:
        raise CoordinationError('Dependencies must map selected tasks to task ID lists')
    visited, active = set(), set()
    def visit(task):
        if task in active:
            raise CoordinationError('Selection dependency cycle')
        if task in visited:
            return
        active.add(task)
        for dependency in _strings(dependencies.get(task, []), 'dependencies', False):
            if dependency not in tasks and dependency not in completed:
                raise CoordinationError(f'Unfinished prerequisite outside selection: {dependency}')
            if dependency in tasks:
                visit(dependency)
        active.remove(task)
        visited.add(task)
    for task in tasks:
        visit(task)


def _product_snapshot(root, paths):
    return {name: fingerprint for name, fingerprint in input_snapshot(root)['files'].items()
            if any(name == path or Path(path) in Path(name).parents for path in paths)}


def _pr_head(root, value):
    return revision(root, value) if value is not None else None


def _start(root, spec, state):
    tasks, dependencies, completed = _scope(root, spec)
    if not isinstance(spec.get('owner'), str) or not spec['owner'].strip() or not spec.get('outcome'):
        raise CoordinationError('Selection requires an owner and requested outcome')
    paths = [safe_relative(root, path) for path in _strings(spec.get('product_paths'), 'product_paths')]
    if any(path.startswith(('.ai/evidence', '.ai/state', '.ai/reports', '.git')) for path in paths):
        raise CoordinationError('Product paths cannot be support-tool outputs')
    commands = [check_contract(check) for check in spec.get('required_checks', [])]
    if not commands or len({check['id'] for check in commands}) != len(commands):
        raise CoordinationError('Selection requires distinct nonempty required check contracts')
    existing = state.setdefault('selections', {})
    overlapping = [item for item in existing.values() if set(tasks) & set(item['task_ids'])]
    unfinished = [item['id'] for item in overlapping if item['status'] != 'accepted']
    if unfinished:
        raise CoordinationError(f'Overlapping unfinished selection; resume {unfinished}')
    now, identity = time.time(), 'selection-' + uuid.uuid4().hex[:16]
    budget_ids = {item['repair_budget_id'] for item in overlapping}
    budget_id = _combine_budgets(state, budget_ids) if budget_ids else identity
    state.setdefault('repair_budgets', {}).setdefault(budget_id, {'attempts': []})
    item = {'id': identity, 'owner': spec['owner'], 'task_ids': tasks, 'outcome': spec['outcome'],
            'group_ids': spec.get('group_ids', []), 'dependencies': dependencies,
            'completed_task_ids': completed, 'product_paths': paths, 'required_checks': commands,
            'requirements': spec.get('requirements'), 'status': 'implementing', 'repair_budget_id': budget_id,
            'created_at': now, 'last_checkpoint_at': now, 'branch': git(root, 'branch', '--show-current').stdout.strip(),
            'initial_revision': revision(root), 'last_revision': revision(root), 'pr_head': _pr_head(root, spec.get('pr_head')),
            'product_snapshot': _product_snapshot(root, paths), 'checkpoints': [], 'tested_tasks': {},
            'implementers': [spec['owner']], 'next_action': spec.get('next_action', spec['outcome'])}
    existing[identity] = item
    return {'status': 'ok', 'selection': item}


def _combine_budgets(state, identities):
    target = sorted(identities)[0]
    for other in identities - {target}:
        state['repair_budgets'][target]['attempts'].extend(state['repair_budgets'][other]['attempts'])
        for item in state['selections'].values():
            if item['repair_budget_id'] == other:
                item['repair_budget_id'] = target
        del state['repair_budgets'][other]
    return target


def _budget(state, item, now):
    attempts = state['repair_budgets'][item['repair_budget_id']]['attempts']
    elapsed = sum(max(0, attempt.get('finished_at', now) - attempt['started_at']) for attempt in attempts)
    active = [attempt for attempt in attempts if 'finished_at' not in attempt]
    exhausted = elapsed >= REPAIR_SECONDS or (len(attempts) >= REPAIR_ATTEMPTS and not active)
    return {'attempts': len(attempts), 'elapsed_seconds': elapsed, 'active': bool(active),
            'exhausted': exhausted, 'remaining_seconds': max(0, REPAIR_SECONDS - elapsed)}


def _status(root, item, state):
    now = time.time()
    budget = _budget(state, item, now)
    overdue = item['status'] != 'accepted' and now - item['last_checkpoint_at'] >= CHECKPOINT_SECONDS
    accepted = item['status'] == 'accepted'
    fresh = not accepted or (revision(root) == item['reviewed_revision'] and input_snapshot(root)['fingerprint'] == item['reviewed_fingerprint'])
    status = 'blocked' if not fresh else ('passed' if accepted else ('attention' if overdue or budget['exhausted'] else 'ok'))
    return {'status': status, 'acceptance_current': accepted and fresh, 'selection': item,
            'checkpoint_due': overdue, 'repair_budget': budget,
            'current_revision': revision(root), 'current_branch': git(root, 'branch', '--show-current').stdout.strip(),
            'development_ready': development_ready(root, state, item),
            'next_action': ('Accepted source has changed; start a new selection and obtain fresh combined acceptance.' if not fresh
                            else 'Record a product-progress checkpoint before further support-tool activity.' if overdue else item['next_action'])}


def require_checkpoint(item):
    if time.time() - item['last_checkpoint_at'] >= CHECKPOINT_SECONDS:
        raise CoordinationError('45-minute progress checkpoint is due; record product progress before continuing')


def _repair(root, item, state, spec):
    if item['status'] == 'accepted':
        raise CoordinationError('Accepted selections cannot start evidence repairs')
    attempts = state['repair_budgets'][item['repair_budget_id']]['attempts']
    now = time.time()
    budget = _budget(state, item, now)
    if spec.get('phase') == 'begin':
        require_checkpoint(item)
        if item.get('support_only_checkpoint'):
            raise CoordinationError('Last checkpoint showed support-only activity; return to product work before optional tooling repair')
        if budget['exhausted'] or budget['attempts'] >= REPAIR_ATTEMPTS:
            raise CoordinationError('Optional evidence repair budget exhausted; use sufficient simpler proof or defer media')
        if budget['active']:
            raise CoordinationError('An optional evidence repair is already active; resume or end it')
        if not spec.get('reason'):
            raise CoordinationError('Repair begin requires a reason identifying optional evidence tooling')
        attempts.append({'started_at': now, 'reason': spec['reason'], 'worktree': str(root)})
    elif spec.get('phase') == 'end':
        if not budget['active']:
            raise CoordinationError('There is no active repair to end')
        if not spec.get('outcome'):
            raise CoordinationError('Repair end requires an outcome')
        attempts[-1].update(finished_at=now, outcome=spec['outcome'])
    else:
        raise CoordinationError('Repair phase must be begin or end')
    budget = _budget(state, item, now)
    return {'status': 'blocked' if budget['exhausted'] else 'ok', 'repair_budget': budget,
            'next_action': 'Stop optional tooling repair; return to product work or report a required blocker.' if budget['exhausted'] else 'Continue within the remaining repair budget.'}


def _registered_receipt(root, state, path):
    receipt = read_json(path)
    captured = state.get('receipts', {}).get(receipt.get('id'))
    if not captured or captured['sha256'] != digest(path) or captured['path'] != str(Path(path).resolve()):
        raise CoordinationError('Checks must use an unchanged receipt captured by this registry')
    errors = verify_receipt(root, receipt)
    if errors:
        raise CoordinationError('; '.join(errors))
    return receipt


def _checkpoint(root, item, state, spec):
    if not spec.get('next_action'):
        raise CoordinationError('Checkpoint requires a concrete next_action')
    now, current = time.time(), _product_snapshot(root, item['product_paths'])
    changed = sorted(name for name in set(current) | set(item['product_snapshot']) if current.get(name) != item['product_snapshot'].get(name))
    head = revision(root)
    commits = git(root, 'log', '--format=%H', f"{item['last_revision']}..{head}", '--', *item['product_paths']).stdout.splitlines()
    checked, check_keys = [], []
    for path in spec.get('receipts', []):
        receipt = _registered_receipt(root, state, path)
        if set(receipt['task_ids']) - set(item['task_ids']):
            raise CoordinationError('Checkpoint receipt covers tasks outside the selection')
        checked.append(receipt['id'])
        check_keys.extend(json.dumps([command['contract'], receipt['input_fingerprint']], sort_keys=True) for command in receipt['commands'])
        for task in receipt['task_ids']:
            item['tested_tasks'][task] = {'revision': head, 'receipt': str(Path(path).resolve()), 'inputs': receipt['input_files']}
        if receipt['implementer'] not in item['implementers']:
            item['implementers'].append(receipt['implementer'])
    prior_checks = {check for checkpoint in item['checkpoints'] for check in checkpoint.get('check_keys', [])}
    checkpoint = {'created_at': now, 'product_changes': changed, 'product_commits': commits,
                  'checks': checked, 'check_keys': check_keys, 'local_revision': head, 'pr_head': _pr_head(root, spec.get('pr_head', item['pr_head'])),
                  'pr_metadata_changed': spec.get('pr_metadata_changed', False),
                  'overdue': now - item['last_checkpoint_at'] >= CHECKPOINT_SECONDS,
                  'product_progress': bool(changed or commits or set(check_keys) - prior_checks), 'next_action': spec['next_action']}
    checkpoint['published_source_changed'] = checkpoint['pr_head'] != item['pr_head']
    item['checkpoints'].append(checkpoint)
    item.update(last_checkpoint_at=now, last_revision=head, product_snapshot=current,
                pr_head=checkpoint['pr_head'], support_only_checkpoint=not checkpoint['product_progress'], next_action=spec['next_action'])
    return {'status': 'ok' if checkpoint['product_progress'] else 'attention', 'checkpoint': checkpoint,
            'next_action': spec['next_action'] if checkpoint['product_progress'] else 'Stop support-only activity; implement or diagnose the next requested behavior. ' + spec['next_action']}


def available_tasks(root, item):
    available = set(item['completed_task_ids'])
    current = input_snapshot(root)['files']
    for task, proof in item['tested_tasks'].items():
        fresh = proof.get('inputs') == current
        if fresh and git(root, 'merge-base', '--is-ancestor', proof['revision'], 'HEAD', check=False).returncode == 0:
            available.add(task)
    return available


def development_ready(root, state, item):
    available = available_tasks(root, item)
    return sorted(task for task in item['task_ids'] if set(item['dependencies'].get(task, [])) <= available)


def _accept(root, item, state, spec):
    if item['status'] == 'accepted':
        raise CoordinationError('Selection already has its combined acceptance review')
    require_checkpoint(item)
    if state['corrections'].get(item['id'], 0) >= 2:
        raise CoordinationError('Two correction rounds failed; retain work and report the required blocker')
    if git(root, 'status', '--porcelain', '--untracked-files=no').stdout:
        raise CoordinationError('Commit tracked implementation changes before combined acceptance')
    receipt = _registered_receipt(root, state, spec['receipt'])
    if not spec.get('review') or not Path(spec['review']).is_file():
        raise CoordinationError('Combined independent review is missing')
    review = read_json(spec['review'])
    errors = validate_review(receipt, review)
    if set(receipt['task_ids']) != set(item['task_ids']) or set(review.get('task_ids', [])) != set(item['task_ids']):
        errors.append('Receipt and combined review must cover the entire selection')
    if review.get('reviewer') in item['implementers']:
        errors.append('Combined reviewer must differ from every selection implementer')
    captured = {check['id']: check.get('contract') for check in receipt['commands']}
    if any(captured.get(check['id']) != check for check in item['required_checks']):
        errors.append('Selection required checks are missing or changed')
    if receipt.get('selection_id') != item['id']:
        errors.append('Final checks were not captured for this selection')
    if item.get('requirements'):
        if not spec.get('evidence'):
            raise CoordinationError('Selection functional acceptance evidence is missing')
        result = validate_evidence(root, item['requirements'], read_json(spec['evidence']))
        errors.extend(result['errors'])
    if errors:
        raise CoordinationError('; '.join(errors))
    for attempt in state['repair_budgets'][item['repair_budget_id']]['attempts']:
        if 'finished_at' not in attempt:
            attempt.update(finished_at=time.time(), outcome='Stopped optional tooling at combined acceptance')
    for record in state['integrations']:
        if record.get('selection_id') == item['id'] and record['status'] == 'pending-review':
            if git(root, 'merge-base', '--is-ancestor', record['result_revision'], 'HEAD', check=False).returncode == 0:
                record.update(status='passed', accepted_selection=item['id'])
    item.update(status='accepted', accepted_at=time.time(), reviewed_revision=revision(root),
                reviewed_fingerprint=receipt['input_fingerprint'],
                review={'reviewer': review['reviewer'], 'path': str(Path(spec['review']).resolve()), 'sha256': digest(spec['review'])},
                receipt=spec['receipt'], next_action='Publish the reviewed source commits to the draft PR and report its head.')
    return {'status': 'passed', 'selection': item}


def selection(repo, action, spec):
    root = repository(repo)
    with registry(root) as state:
        if action == 'start':
            return _start(root, spec, state)
        item = get_selection(state, spec['selection_id'], spec.get('owner'))
        if action == 'status':
            return _status(root, item, state)
        if spec.get('owner') != item['owner']:
            raise CoordinationError('Selection mutations require the recorded owner')
        actions = {'checkpoint': _checkpoint, 'repair': _repair, 'accept': _accept}
        if action not in actions:
            raise CoordinationError(f'Unknown selection action: {action}')
        return actions[action](root, item, state, spec)
