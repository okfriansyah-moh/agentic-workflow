"""Numbering changes preserve live ownership and immutable delivery history."""
from copy import deepcopy
import json

from agent_workflow.coordination_state import CoordinationError, git, registry, revision
from agent_workflow.numbering_migration import _translate_live
from agent_workflow.selection import selection
from tests import test_selection
from tests.test_coordination import GitFixture


class MigrationTests(GitFixture):
    plan = test_selection.SelectionTests.plan
    action = test_selection.SelectionTests.action
    def prepare(self):
        spec = self.plan()
        item = selection(self.repo, 'start', {**spec, 'group_ids': ['G1', 'G2']})['selection']
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-m', 'source plan')
        source = revision(self.repo)
        rows = []
        for number in (1, 2):
            old = self.repo / f'plan/0{number}'
            new = old.with_name(f'0{number}-stage')
            old.rename(new)
            task = new / f'tasks/T{number}.md'
            before = task.read_text()
            text = before.replace(f'id: T{number}\n', f'id: T{number:03d}\n').replace(f'group: G{number}\n', f'group: G{number:02d}\n').replace('[T1]', '[T001]')
            target = task.with_name(f'T{number:03d}-stage.md')
            target.write_text(text)
            task.unlink()
            group = new / 'group.md'
            group.write_text(group.read_text().replace(f'G{number}', f'G{number:02d}').replace(f'T{number}', f'T{number:03d}'))
            rows.append({'old_id': f'T{number}', 'new_id': f'T{number:03d}', 'old_group': f'G{number}', 'new_group': f'G{number:02d}', 'old_path': f'plan/0{number}/tasks/T{number}.md', 'new_path': f'plan/0{number}-stage/tasks/T{number:03d}-stage.md', 'status_before': 'Not started', 'depends_on_before': [] if number == 1 else ['T1'], 'depends_on_after': [] if number == 1 else ['T001']})
        plan = self.repo / 'PLAN.md'
        text = plan.read_text().replace('schema_version: 1', 'schema_version: 1\nnumbering: sequential')
        for number in (1, 2):
            text = text.replace(f'G{number}', f'G{number:02d}').replace(f'plan/0{number}/', f'plan/0{number}-stage/')
        plan.write_text(text)
        mapping = {'schema_version': 1, 'target_numbering': 'sequential', 'source_revision': source, 'tasks': rows, 'groups': [{'old_id': f'G{number}', 'old_path': f'plan/0{number}/group.md', 'new_ids': [f'G{number:02d}'], 'new_paths': [f'plan/0{number}-stage/group.md']} for number in (1, 2)]}
        (self.repo / 'map.json').write_text(json.dumps(mapping))
        with registry(self.repo) as state:
            saved = state['selections'][item['id']]
            saved['checkpoints'] = [{'receipt': 'historical-T1.json', 'task_ids': ['T1']}]
            saved['review_findings'] = {'finding': {'task_ids': ['T1'], 'status': 'unresolved'}}
        return item, mapping

    def migrate(self, item, **extra):
        return self.action(item, 'migrate', mapping='map.json', plan='PLAN.md', idle_acknowledged=True, **extra)

    def test_migration_preserves_history_budgets_and_is_idempotent(self):
        item, _ = self.prepare()
        with registry(self.repo) as state:
            before = deepcopy(state)
        result = self.migrate(item)
        migrated = result['selection']
        self.assertEqual(migrated['task_ids'], ['T001', 'T002'])
        self.assertEqual(migrated['dependencies'], {'T001': [], 'T002': ['T001']})
        self.assertEqual(migrated['group_ids'], ['G01', 'G02'])
        self.assertEqual(migrated['checkpoints'], before['selections'][item['id']]['checkpoints'])
        self.assertEqual(migrated['review_findings'], before['selections'][item['id']]['review_findings'])
        with registry(self.repo) as state:
            self.assertEqual(state.get('repair_budgets'), before.get('repair_budgets'))
            self.assertEqual(state['corrections'], before['corrections'])
        self.assertTrue(self.migrate(item)['idempotent'])

    def test_duplicate_mapping_rolls_back_transaction(self):
        item, data = self.prepare()
        data['tasks'][1]['new_id'] = data['tasks'][0]['new_id']
        (self.repo / 'map.json').write_text(json.dumps(data))
        with registry(self.repo) as state:
            before = deepcopy(state)
        with self.assertRaises(CoordinationError):
            self.migrate(item)
        with registry(self.repo) as state:
            self.assertEqual(state, before)

    def test_status_change_is_rejected(self):
        item, data = self.prepare()
        path = self.repo / data['tasks'][0]['new_path']
        path.write_text(path.read_text().replace('status: Not started', 'status: Done'))
        with self.assertRaises(CoordinationError):
            self.migrate(item)

    def test_wrong_owner_is_rejected(self):
        item, _ = self.prepare()
        with self.assertRaises(CoordinationError):
            selection(self.repo, 'migrate', {'selection_id': item['id'], 'owner': 'another'})

    def test_missing_idle_acknowledgment_is_rejected(self):
        item, _ = self.prepare()
        with self.assertRaises(CoordinationError):
            self.action(item, 'migrate', mapping='map.json', plan='PLAN.md')

    def test_dependency_edge_change_is_rejected(self):
        item, data = self.prepare()
        path = self.repo / data['tasks'][1]['new_path']
        path.write_text(path.read_text().replace('depends_on: [T001]', 'depends_on: []'))
        with self.assertRaises(CoordinationError):
            self.migrate(item)

    def test_evidence_is_preserved_and_verified(self):
        item, data = self.prepare()
        row = data['tasks'][0]
        row['evidence_sha256'] = 'a' * 64
        (self.repo / 'map.json').write_text(json.dumps(data))
        with self.assertRaises(CoordinationError):
            self.migrate(item)

    def test_active_claim_is_translated_without_receipt_edits(self):
        item, _ = self.prepare()
        with registry(self.repo) as state:
            state['claims']['claim'] = {'id': 'claim', 'status': 'active', 'owner': item['owner'], 'selection_id': item['id'], 'task_ids': ['T1', 'T2'], 'acceptance_ids': ['T1-A1'], 'last_receipt': 'proof/T1.json'}
        self.migrate(item)
        with registry(self.repo) as state:
            claim = state['claims']['claim']
            self.assertEqual(claim['task_ids'], ['T001', 'T002'])
            self.assertEqual(claim['acceptance_ids'], ['T001-A1'])
            self.assertEqual(claim['last_receipt'], 'proof/T1.json')

    def test_foreign_active_claim_blocks_without_mutation(self):
        item, _ = self.prepare()
        with registry(self.repo) as state:
            state['claims']['foreign'] = {'id': 'foreign', 'status': 'active', 'owner': 'another', 'task_ids': ['T1']}
        with self.assertRaises(CoordinationError):
            self.migrate(item)
        with registry(self.repo) as state:
            self.assertEqual(state['selections'][item['id']]['task_ids'], ['T1', 'T2'])

    def target_branch(self, item):
        with registry(self.repo) as state:
            state['claims']['owned'] = {'id': 'owned', 'status': 'active', 'owner': item['owner'], 'selection_id': item['id'], 'task_ids': ['T1'], 'branch': 'previous-claim', 'worktree': str(self.repo), 'repository': str(self.repo), 'base_revision': 'historical-base', 'last_receipt': 'historical-receipt'}
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-m', 'numbered plan')
        git(self.repo, 'checkout', '-b', 'codex/numbering-handoff')

    def test_absent_rebind_flag_preserves_selection_and_claim_branches(self):
        item, _ = self.prepare()
        self.target_branch(item)
        result = self.migrate(item)
        self.assertEqual(result['selection']['branch'], item['branch'])
        with registry(self.repo) as state:
            self.assertEqual(state['claims']['owned']['branch'], 'previous-claim')

    def test_rebind_uses_git_branch_and_retains_old_bindings(self):
        item, _ = self.prepare()
        self.target_branch(item)
        result = self.migrate(item, rebind_branch=True)
        saved = result['selection']
        self.assertEqual(saved['branch'], 'codex/numbering-handoff')
        audit = saved['numbering_migrations'][0]
        self.assertEqual(audit['target_revision'], revision(self.repo))
        self.assertEqual(audit['branch_bindings']['selection']['before'], item['branch'])
        self.assertEqual(audit['branch_bindings']['claims']['owned']['before'], 'previous-claim')
        with registry(self.repo) as state:
            claim = state['claims']['owned']
            self.assertEqual(claim['branch'], 'codex/numbering-handoff')
            self.assertEqual(claim['worktree'], str(self.repo))
            self.assertEqual(claim['repository'], str(self.repo))
            self.assertEqual(claim['base_revision'], 'historical-base')
            self.assertEqual(claim['last_receipt'], 'historical-receipt')

    def test_dirty_tracked_checkout_blocks_rebind_transaction(self):
        item, _ = self.prepare()
        self.target_branch(item)
        (self.repo / 'PLAN.md').write_text((self.repo / 'PLAN.md').read_text() + '\nChanged\n')
        with registry(self.repo) as state:
            before = deepcopy(state)
        with self.assertRaises(CoordinationError):
            self.migrate(item, rebind_branch=True)
        with registry(self.repo) as state:
            self.assertEqual(state, before)

    def test_untracked_file_blocks_rebind_transaction(self):
        item, _ = self.prepare()
        self.target_branch(item)
        (self.repo / 'untracked.txt').write_text('pending work')
        with registry(self.repo) as state:
            before = deepcopy(state)
        with self.assertRaises(CoordinationError):
            self.migrate(item, rebind_branch=True)
        with registry(self.repo) as state:
            self.assertEqual(state, before)

    def test_detached_checkout_blocks_rebind_transaction(self):
        item, _ = self.prepare()
        self.target_branch(item)
        git(self.repo, 'checkout', '--detach')
        with registry(self.repo) as state:
            before = deepcopy(state)
        with self.assertRaises(CoordinationError):
            self.migrate(item, rebind_branch=True)
        with registry(self.repo) as state:
            self.assertEqual(state, before)

    def test_translate_live_is_simultaneous_and_preserves_literals(self):
        item = {'task_ids': ['T006', 'T009'], 'acceptance_ids': ['T009-A1', 'REQ-009'], 'paths': ['old/task.md', 'src'], 'checkpoints': [{'task_ids': ['T009']}], 'required_checks': [{'argv': ['runner', '--task', 'T009', '--task=T006', '--label', 'T009']} ]}
        result = _translate_live(item, {'T006': 'T008', 'T009': 'T006'}, {'old/task.md': 'new/task.md'}, {})
        self.assertEqual(result['task_ids'], ['T008', 'T006'])
        self.assertEqual(result['acceptance_ids'], ['T006-A1', 'REQ-009'])
        self.assertEqual(result['required_checks'][0]['argv'], ['runner', '--task', 'T006', '--task=T008', '--label', 'T009'])
        self.assertEqual(result['checkpoints'], item['checkpoints'])
        self.assertEqual(item['task_ids'], ['T006', 'T009'])
