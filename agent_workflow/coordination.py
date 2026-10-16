"""CLI entrypoints for native-agent ownership, integration, and evidence."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

from .coordination_evidence import (_receipt_errors, _run, capture_receipt, digest, validate_evidence,
                                    validate_review, verify_receipt)
from .coordination_plan import task_index
from .coordination_state import (_shared_resources, CoordinationError, check_contract, cleanup_worktree, create_claim, create_worktree, get_claim,
                                 git, input_snapshot, owns_path, read_json, registry,
                                 release_claim, repository, resume, revision, write_json)


def _worker_order(workers, claims, completed):
    ordered, visiting = [], set()
    by_task = {}
    for worker in workers:
        for task in claims[worker['claim_id']]['task_ids']:
            by_task[task] = worker
    def visit(worker):
        identity = worker['claim_id']
        if identity in visiting:
            raise CoordinationError('Integration dependency cycle')
        if worker in ordered:
            return
        visiting.add(identity)
        dependencies = set(worker.get('depends_on', [])) | set(claims[identity].get('depends_on', []))
        for task in sorted(dependencies):
            if task in by_task:
                if by_task[task] is worker:
                    continue
                visit(by_task[task])
            elif task not in completed:
                raise CoordinationError(f'Unproven integration dependency: {task}')
        visiting.remove(identity)
        ordered.append(worker)
    for worker in workers:
        visit(worker)
    return ordered


def _accepted_worker(worker, state, require_review=True):
    claim = get_claim(state, worker['claim_id'])
    worktree = claim.get('worktree')
    if not worktree or not Path(worktree).is_dir():
        raise CoordinationError('Accepted lane worktree is missing')
    commit = revision(worktree, worker['commit'])
    if git(worktree, 'branch', '--show-current').stdout.strip() != claim.get('branch'):
        raise CoordinationError('Worker checkout is not on its claimed branch')
    if commit != revision(worktree):
        raise CoordinationError('Worker commit differs from the reviewed worktree revision')
    receipt = read_json(worker['receipt'])
    if receipt.get('claim_id') != claim['id'] or receipt.get('implementer') != claim['owner']:
        raise CoordinationError('Receipt does not belong to this worker claim')
    errors = verify_receipt(worktree, receipt)
    captured = state.get('receipts', {}).get(receipt.get('id'), {})
    if not require_review and (captured.get('sha256') != digest(worker['receipt'])
                               or captured.get('path') != str(Path(worker['receipt']).resolve())):
        errors.append('Selection composition requires an unchanged registry-captured worker receipt')
    if require_review:
        errors += validate_review(receipt, read_json(worker['review']))
    required = {check['id']: check for check in claim['required_checks']}
    captured = {check['id']: check.get('contract') for check in receipt.get('commands', [])}
    if any(captured.get(identity) != contract for identity, contract in required.items()):
        errors.append('Required worker check contracts are missing or changed')
    if git(worktree, 'status', '--porcelain', '--untracked-files=no').stdout:
        errors.append('Worker has uncommitted tracked changes')
    if git(worktree, 'merge-base', '--is-ancestor', claim['base_revision'], commit, check=False).returncode:
        errors.append('Worker no longer descends from its recorded base')
    paths = git(worktree, 'diff', '--name-only', claim['base_revision'], commit).stdout.splitlines()
    undeclared_resources = _shared_resources(paths) - set(claim['resources'])
    if undeclared_resources:
        errors.append(f'Worker changed shared resources without ownership: {sorted(undeclared_resources)}')
    unauthorized = [path for path in paths if not owns_path(claim, path)]
    if unauthorized:
        errors.append(f'Worker changed unclaimed paths: {unauthorized}')
    if errors:
        raise CoordinationError('; '.join(errors))
    return claim, commit


def _check_integration_lane(repo, spec, state):
    claim = get_claim(state, spec['integration_claim_id'], spec['owner'])
    if claim.get('role') != 'integrator' or claim.get('worktree') != str(repository(repo)):
        raise CoordinationError('Integration must run in its explicitly owned integrator worktree')
    if git(repo, 'branch', '--show-current').stdout.strip() != claim.get('branch'):
        raise CoordinationError('Integration checkout is not on its claimed branch')
    if revision(repo) != spec['expected_head']:
        raise CoordinationError('Integration head changed; inspect the new revision before retrying')
    if git(repo, 'status', '--porcelain', '--untracked-files=no').stdout:
        raise CoordinationError('Integration worktree has tracked changes or conflicts; preserve and resolve them first')
    if git(repo, 'rev-parse', '-q', '--verify', 'MERGE_HEAD', check=False).returncode == 0:
        raise CoordinationError('An unresolved merge is retained; resolve it before another integration attempt')
    group = spec['group_id']
    correction_key = spec.get('selection_id', group)
    if state['corrections'].get(correction_key, 0) >= 2:
        raise CoordinationError('Two correction rounds failed. Retain branches and request a revised work-group decision.')
    if not spec.get('workers') or not spec.get('commands'):
        raise CoordinationError('Integration requires workers and checks for the combined result')
    required = {check['id']: check for check in claim['required_checks']}
    supplied = {command.get('id'): check_contract(command) for command in spec['commands']}
    if any(supplied.get(identity) != contract for identity, contract in required.items()):
        raise CoordinationError('Combined checks do not match the integrator brief contracts')
    for command in spec['commands']:
        argv = command.get('argv')
        if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) for arg in argv):
            raise CoordinationError('Combined checks require valid argv arrays before merging')
    return claim


def _merge_workers(repo, workers, state, record, require_review=True):
    for worker in workers:
        claim, commit = _accepted_worker(worker, state, require_review)
        if git(repo, 'merge-base', '--is-ancestor', commit, 'HEAD', check=False).returncode == 0:
            record['merged_claims'].append(claim['id'])
            continue
        merged = git(repo, 'merge', '--no-ff', '--no-edit', commit, check=False)
        if merged.returncode:
            record.update(status='blocked', conflict_claim=claim['id'],
                          conflicted_files=git(repo, 'diff', '--name-only', '--diff-filter=U').stdout.splitlines(),
                          next_action='Inspect retained Git merge state, preserve both intended contributions, resolve against contracts, commit, and rerun integration checks.',
                          git_output=merged.stdout + merged.stderr)
            return False
        record['merged_claims'].append(claim['id'])
    return True


def integrate(repo, spec):
    root = repository(repo)
    with registry(root) as state:
        claim = _check_integration_lane(root, spec, state)
        selected = _composition_selection(root, spec, state)
        completed = set()
        for prior in state['integrations']:
            eligible = prior['status'] == 'passed' or (selected is not None and prior.get('selection_id') == selected['id'] and prior['status'] == 'pending-review')
            if eligible and git(root, 'merge-base', '--is-ancestor', prior['result_revision'], 'HEAD', check=False).returncode == 0:
                for identity in prior['merged_claims']:
                    completed.update(state['claims'][identity]['task_ids'])
        workers = _worker_order(spec['workers'], state['claims'], completed)
        # Validate every lane before changing the integration branch.
        for worker in workers:
            _accepted_worker(worker, state, require_review=selected is None)
        record = {'id': 'integration-' + uuid.uuid4().hex, 'group_id': spec['group_id'],
                  'owner': spec['owner'], 'initial_revision': revision(root), 'merged_claims': [],
                  'started_at': time.time(), 'status': 'running'}
        merged = _merge_workers(root, workers, state, record, require_review=selected is None)
        if merged:
            output = root / '.ai/evidence' / record['id']
            output.mkdir(parents=True)
            before = input_snapshot(root)
            results = [_run(root, command, output, n) for n, command in enumerate(spec['commands'])]
            errors = _receipt_errors(results, before, input_snapshot(root))
            record.update(status='passed' if not errors else 'blocked', commands=results,
                          errors=errors, input_fingerprint=before['fingerprint'], input_files=before['files'],
                          next_action='Independent review and feature acceptance evidence are still required.' if not errors else 'Correct the integrated behavior and rerun the affected combined checks.')
        record.update(result_revision=revision(root), finished_at=time.time())
        if record['status'] != 'passed':
            key = spec.get('selection_id', spec['group_id'])
            state['corrections'][key] = state['corrections'].get(key, 0) + 1
        if selected is not None:
            _record_composition(selected, record, workers, state)
        state['integrations'].append(record)
        claim['updated_at'] = time.time()
        path = root / '.ai/evidence' / record['id'] / 'integration.json'
        write_json(path, record)
    return {'status': record['status'], 'record': str(path), 'result': record}


def _composition_selection(repo, spec, state):
    if not spec.get('selection_id'):
        return None
    from .selection import get_selection, require_checkpoint
    item = get_selection(state, spec['selection_id'], spec['owner'])
    require_checkpoint(item)
    if item['status'] == 'accepted':
        raise CoordinationError('Accepted selection cannot compose additional workers')
    for worker in spec['workers']:
        tasks = state['claims'][worker['claim_id']]['task_ids']
        if set(tasks) - set(item['task_ids']):
            raise CoordinationError('Worker tasks are outside the delivery selection')
    return item


def _record_composition(item, record, workers, state):
    record['selection_id'] = item['id']
    if record['status'] != 'passed':
        return
    record['status'] = 'pending-review'
    record['next_action'] = 'Combined checks passed; one independent review of the entire selection remains required.'
    for worker in workers:
        claim = state['claims'][worker['claim_id']]
        if claim['owner'] not in item['implementers']:
            item['implementers'].append(claim['owner'])
        for task in claim['task_ids']:
            item['tested_tasks'][task] = {'revision': record['result_revision'], 'integration_id': record['id'], 'inputs': record['input_files']}


def _output(args, result):
    if getattr(args, 'output', None):
        write_json(args.output, result)
    return result


def _index_command(args):
    return _output(args, task_index(args.plan))


def _claim_command(args):
    return _output(args, create_claim(args.repo, read_json(args.spec)))


def _release_command(args):
    return release_claim(args.repo, args.claim, args.owner, args.reason)


def _worktree_command(args):
    if args.cleanup:
        return cleanup_worktree(args.repo, args.claim, args.owner)
    if not args.path or not args.branch:
        raise CoordinationError('Worktree creation requires --path and --branch')
    return create_worktree(args.repo, args.claim, args.path, args.branch, args.owner)


def _integrate_command(args):
    return integrate(args.repo, read_json(args.spec))


def _receipt_command(args):
    return capture_receipt(args.repo, read_json(args.spec))


def _evidence_command(args):
    return _output(args, validate_evidence(args.repo, read_json(args.requirements), read_json(args.evidence)))


def _selection_command(args):
    from .selection import selection
    return selection(args.repo, args.action, read_json(args.spec))


def _resume_command(args):
    return resume(args.repo, args.stale_seconds)


def register(subparsers):
    delivery = subparsers.add_parser('selection', help='Track one delivery selection, progress, repair limits and combined acceptance')
    delivery.add_argument('--repo', required=True)
    delivery.add_argument('--action', choices=('start', 'checkpoint', 'repair', 'accept', 'status', 'migrate'), required=True)
    delivery.add_argument('--spec', required=True)
    delivery.set_defaults(handler=_selection_command)
    index = subparsers.add_parser('task-index', help='Read plan/task sources, dependencies and ownership without dispatching work')
    index.add_argument('--plan', required=True)
    index.add_argument('--output')
    index.set_defaults(handler=_index_command)
    for name, handler in (('claim', _claim_command), ('integrate', _integrate_command), ('receipt', _receipt_command)):
        command = subparsers.add_parser(name)
        command.add_argument('--repo', required=True)
        command.add_argument('--spec', required=True, help='Structured JSON; never executable plan prose')
        command.set_defaults(handler=handler)
        if name == 'claim':
            command.add_argument('--output')
    release = subparsers.add_parser('release', help='Release only the recorded owner claim; retain its worktree')
    for field in ('repo', 'claim', 'owner', 'reason'):
        release.add_argument('--' + field, required=True)
    release.set_defaults(handler=_release_command)
    worktree = subparsers.add_parser('worktree', help='Create an isolated writing lane from the exact claim base')
    for field in ('repo', 'claim', 'owner'):
        worktree.add_argument('--' + field, required=True)
    for field in ('path', 'branch'):
        worktree.add_argument('--' + field)
    worktree.add_argument('--cleanup', action='store_true')
    worktree.set_defaults(handler=_worktree_command)
    resume_parser = subparsers.add_parser('resume', help='Inspect retained claims, revisions and correction state')
    resume_parser.add_argument('--repo', required=True)
    resume_parser.add_argument('--stale-seconds', type=int, default=3600)
    resume_parser.set_defaults(handler=_resume_command)
    evidence = subparsers.add_parser('evidence', help='Verify required cases, proof boundaries, hashes and recorded inspections')
    for field in ('repo', 'requirements', 'evidence'):
        evidence.add_argument('--' + field, required=True)
    evidence.add_argument('--output')
    evidence.set_defaults(handler=_evidence_command)
