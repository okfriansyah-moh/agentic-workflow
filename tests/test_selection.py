from __future__ import annotations

import contextlib
import io
import json
import sys
from unittest.mock import patch

from agent_workflow.cli import main
from agent_workflow.coordination import integrate
from agent_workflow.coordination_evidence import capture_receipt
from agent_workflow.coordination_state import (CoordinationError, create_claim, git, read_json,
                                               registry, resume, revision, write_json)
from agent_workflow.selection import selection
from tests.test_coordination import GitFixture


class SelectionTests(GitFixture):
    def start(self, tasks=None, **extra):
        spec = {'owner': 'worker-a', 'task_ids': tasks or ['T1', 'T2'], 'outcome': 'Both requested behaviors work',
                'product_paths': ['src'], 'required_checks': self.spec()['required_checks'],
                'dependencies': {'T2': ['T1']}, **extra}
        return selection(self.repo, 'start', spec)['selection']

    def action(self, item, action, **extra):
        return selection(self.repo, action, {'selection_id': item['id'], 'owner': item['owner'], **extra})

    def checked_selection(self):
        item = self.start()
        claim = create_claim(self.repo, self.spec(task_ids=['T1', 'T2'], reuse_worktree=True))['claim']
        (self.repo / 'src/a.txt').write_text('first behavior\n')
        (self.repo / 'src/b.txt').write_text('second behavior\n')
        git(self.repo, 'commit', '-am', 'implement requested selection')
        result = capture_receipt(self.repo, {'claim_id': claim['id'], 'owner': claim['owner'],
                                           'selection_id': item['id'], 'commands': self.spec()['required_checks']})
        receipt = result['result']
        review = self.repo / '.ai/evidence/combined-review.json'
        write_json(review, {'reviewer': 'independent', 'task_ids': item['task_ids'],
                            'tested_revision': receipt['tested_revision'], 'input_fingerprint': receipt['input_fingerprint'],
                            'verdict': 'accepted', 'findings': []})
        return item, result['receipt'], review

    def plan(self):
        (self.repo / 'plan/01/tasks').mkdir(parents=True)
        (self.repo / 'plan/02/tasks').mkdir(parents=True)
        (self.repo / 'PLAN.md').write_text('---\nkind: plan\nschema_version: 1\nreadiness: Ready\nplan_root: plan\ngroups:\n- id: G1\n  path: plan/01/group.md\n- id: G2\n  path: plan/02/group.md\n---\n# Selection plan\n')
        for number in (1, 2):
            folder = self.repo / f'plan/0{number}'
            (folder / 'group.md').write_text(f'---\nkind: group\nid: G{number}\ntasks: [T{number}]\nintegration_owner: T{number}\n---\n# Group\n')
            dependencies = '[]' if number == 1 else '[T1]'
            (folder / f'tasks/T{number}.md').write_text(f'---\nkind: task\nid: T{number}\ngroup: G{number}\ndepends_on: {dependencies}\nreadiness: Ready\nstatus: Not started\ntest_strategy: checks-only\nvisual_review: not-applicable\n---\n## Acceptance\nT{number}-A1: observable result\n')
        return {'owner': 'worker-a', 'plan': 'PLAN.md', 'outcome': 'Requested groups work',
                'product_paths': ['src'], 'required_checks': self.spec()['required_checks']}

    def test_group_and_two_group_selection_have_one_review_unit(self):
        spec = self.plan()
        item = selection(self.repo, 'start', {**spec, 'group_ids': ['G1', 'G2']})['selection']
        self.assertEqual(item['task_ids'], ['T1', 'T2'])
        self.assertEqual(item['group_ids'], ['G1', 'G2'])
        self.assertEqual(len(resume(self.repo)['selections']), 1)
        self.assertEqual(self.action(item, 'status')['development_ready'], ['T1'])

    def test_single_group_maps_only_its_tasks(self):
        spec = self.plan()
        item = selection(self.repo, 'start', {**spec, 'group_ids': ['G1']})['selection']
        self.assertEqual(item['task_ids'], ['T1'])

    def test_cli_repair_exhaustion_is_nonzero(self):
        item = self.start()
        for _ in range(2):
            self.action(item, 'repair', phase='begin', reason='Optional recorder')
            self.action(item, 'repair', phase='end', outcome='Stopped')
        spec = self.repo / '.ai/state/repair.json'
        write_json(spec, {'selection_id': item['id'], 'owner': item['owner'], 'phase': 'begin', 'reason': 'Another attempt'})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(['selection', '--repo', str(self.repo), '--action', 'repair', '--spec', str(spec)])
        self.assertEqual(code, 1)
        self.assertIn('exhausted', json.loads(output.getvalue())['error'])

    def test_accepted_status_rejects_subsequent_source_changes(self):
        item, receipt, review = self.checked_selection()
        self.action(item, 'accept', receipt=receipt, review=str(review))
        self.assertTrue(self.action(item, 'status')['acceptance_current'])
        (self.repo / 'src/a.txt').write_text('changed after review\n')
        status = self.action(item, 'status')
        self.assertEqual(status['status'], 'blocked')
        self.assertFalse(status['acceptance_current'])

    def test_selection_acceptance_requires_functional_observations(self):
        requirements = {'cases': [{'id': 'AC1', 'boundary': 'browser', 'speech_required': True}]}
        item = self.start(requirements=requirements)
        claim = create_claim(self.repo, self.spec(task_ids=['T1', 'T2'], reuse_worktree=True))['claim']
        result = capture_receipt(self.repo, {'claim_id': claim['id'], 'owner': claim['owner'],
                                           'selection_id': item['id'], 'commands': self.spec()['required_checks']})
        receipt = result['result']
        review = self.repo / '.ai/evidence/review.json'
        write_json(review, {'reviewer': 'independent', 'task_ids': item['task_ids'], 'tested_revision': receipt['tested_revision'],
                            'input_fingerprint': receipt['input_fingerprint'], 'verdict': 'accepted', 'findings': []})
        with self.assertRaisesRegex(CoordinationError, 'functional acceptance evidence'):
            self.action(item, 'accept', receipt=result['receipt'], review=str(review))
        evidence = self.repo / '.ai/evidence/browser.json'
        from agent_workflow.coordination_evidence import requirements_digest
        write_json(evidence, {'requirements_sha256': requirements_digest(requirements), 'input_fingerprint': receipt['input_fingerprint'],
                              'implementer': 'worker-a', 'reviewer': 'independent', 'cases': [
                                  {'id': 'AC1', 'boundary': 'browser', 'result': 'passed', 'assertions': ['DOM status exists'],
                                   'direct_observation': {'observer': 'independent', 'method': 'DOM inspection', 'observations': 'Status text present'}}]})
        with self.assertRaisesRegex(CoordinationError, 'assistive-technology'):
            self.action(item, 'accept', receipt=result['receipt'], review=str(review), evidence=str(evidence))

    def test_selection_correction_limit_cannot_reset_by_group_rename(self):
        _, _, worker = self.ready()
        commands = [{'id': 'combined', 'kind': 'check', 'argv': [sys.executable, '-c', 'raise SystemExit(1)']}]
        lane, spec = self.integration([worker], commands)
        item = selection(lane, 'start', {'owner': 'integrator', 'task_ids': ['T1'], 'outcome': 'Working contribution',
                                        'product_paths': ['src'], 'required_checks': commands})['selection']
        spec['selection_id'] = item['id']
        for number in range(2):
            spec['group_id'] = f'renamed-{number}'
            self.assertEqual(integrate(lane, spec)['status'], 'blocked')
            spec['expected_head'] = revision(lane)
        spec['group_id'] = 'new-phase'
        with self.assertRaisesRegex(CoordinationError, 'Two correction'):
            integrate(lane, spec)
        with self.assertRaisesRegex(CoordinationError, 'Two correction'):
            selection(lane, 'accept', {'selection_id': item['id'], 'owner': 'integrator'})

    def test_one_combined_review_accepts_all_tasks_and_rejects_second(self):
        item, receipt, review = self.checked_selection()
        result = self.action(item, 'accept', receipt=receipt, review=str(review))
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['selection']['status'], 'accepted')
        with self.assertRaisesRegex(CoordinationError, 'already'):
            self.action(item, 'accept', receipt=receipt, review=str(review))

    def test_partial_review_or_same_implementer_cannot_accept(self):
        item, receipt, review = self.checked_selection()
        document = read_json(review)
        document['task_ids'] = ['T1']
        write_json(review, document)
        with self.assertRaisesRegex(CoordinationError, 'entire selection'):
            self.action(item, 'accept', receipt=receipt, review=str(review))
        document.update(task_ids=['T1', 'T2'], reviewer='worker-a')
        write_json(review, document)
        with self.assertRaisesRegex(CoordinationError, 'reviewer'):
            self.action(item, 'accept', receipt=receipt, review=str(review))

    def test_changed_source_and_forged_check_cannot_accept(self):
        item, receipt, review = self.checked_selection()
        (self.repo / 'src/a.txt').write_text('changed after checks\n')
        git(self.repo, 'commit', '-am', 'invalidate checks')
        with self.assertRaisesRegex(CoordinationError, 'stale|revision'):
            self.action(item, 'accept', receipt=receipt, review=str(review))
        document = read_json(receipt)
        document['tested_revision'] = revision(self.repo)
        write_json(receipt, document)
        with self.assertRaisesRegex(CoordinationError, 'unchanged receipt'):
            self.action(item, 'accept', receipt=receipt, review=str(review))

    def test_missing_checks_stale_review_and_required_findings_block(self):
        item, receipt, review = self.checked_selection()
        document = read_json(review)
        document['input_fingerprint'] = 'old'
        write_json(review, document)
        with self.assertRaisesRegex(CoordinationError, 'fingerprint'):
            self.action(item, 'accept', receipt=receipt, review=str(review))
        document['input_fingerprint'] = read_json(receipt)['input_fingerprint']
        document['findings'] = [{'id': 'missing success announcement', 'required': True, 'status': 'open'}]
        write_json(review, document)
        with self.assertRaisesRegex(CoordinationError, 'Unresolved'):
            self.action(item, 'accept', receipt=receipt, review=str(review))
        fake = self.repo / '.ai/evidence/fake.json'
        write_json(fake, {'id': 'invented', 'status': 'passed'})
        with self.assertRaisesRegex(CoordinationError, 'captured'):
            self.action(item, 'accept', receipt=str(fake), review=str(review))

    def test_checkpoint_separates_product_commit_from_pr_metadata(self):
        item = self.start(pr_head=self.base)
        result = self.action(item, 'checkpoint', next_action='Implement first behavior', pr_metadata_changed=True)
        self.assertEqual(result['status'], 'attention')
        self.assertFalse(result['checkpoint']['product_progress'])
        self.assertFalse(result['checkpoint']['published_source_changed'])
        (self.repo / 'src/a.txt').write_text('working behavior\n')
        git(self.repo, 'commit', '-am', 'implement behavior locally')
        result = self.action(item, 'checkpoint', next_action='Implement second behavior')
        self.assertTrue(result['checkpoint']['product_progress'])
        self.assertEqual(result['checkpoint']['product_commits'], [revision(self.repo)])
        self.assertEqual(result['checkpoint']['pr_head'], self.base)
        self.assertFalse(result['checkpoint']['published_source_changed'])

    def test_45_minute_checkpoint_is_durable_and_blocks_support_work(self):
        with patch('agent_workflow.selection.time.time', return_value=1000):
            item = self.start()
        with patch('agent_workflow.selection.time.time', return_value=3701):
            self.assertTrue(self.action(item, 'status')['checkpoint_due'])
            with self.assertRaisesRegex(CoordinationError, '45-minute'):
                self.action(item, 'repair', phase='begin', reason='Optional trace recorder')
            result = self.action(item, 'checkpoint', next_action='Resolve actual feature failure')
            self.assertTrue(result['checkpoint']['overdue'])
            self.assertEqual(result['status'], 'attention')
        self.assertEqual(resume(self.repo)['selections'][0]['id'], item['id'])

    def test_repair_attempts_cannot_reset_by_phase_or_overlapping_selection(self):
        item = self.start()
        for phase in ('capture-one', 'renamed-phase-two'):
            self.action(item, 'repair', phase='begin', reason=phase)
            result = self.action(item, 'repair', phase='end', outcome='Recorder remains unavailable')
        self.assertEqual(result['status'], 'blocked')
        with self.assertRaisesRegex(CoordinationError, 'exhausted'):
            self.action(item, 'repair', phase='begin', reason='third phase')
        with self.assertRaisesRegex(CoordinationError, 'resume'):
            self.start(task_ids=['T1'], dependencies={})
        self.assertEqual(resume(self.repo)['selections'][0]['repair_budget_id'], item['repair_budget_id'])

    def test_active_repair_counts_downtime_and_other_worktrees(self):
        with patch('agent_workflow.selection.time.time', return_value=1000):
            item = self.start()
            self.action(item, 'repair', phase='begin', reason='Optional recording fixture')
        lane = self.root / 'resume-checkout'
        git(self.repo, 'worktree', 'add', '-b', 'resume', str(lane))
        with patch('agent_workflow.selection.time.time', return_value=2201):
            result = selection(lane, 'status', {'selection_id': item['id']})
            self.assertTrue(result['repair_budget']['exhausted'])
            self.assertGreaterEqual(result['repair_budget']['elapsed_seconds'], 1200)
            with self.assertRaisesRegex(CoordinationError, 'exhausted'):
                selection(lane, 'repair', {'selection_id': item['id'], 'owner': item['owner'], 'phase': 'begin', 'reason': 'Rename'})
            self.assertEqual(selection(lane, 'repair', {'selection_id': item['id'], 'owner': item['owner'], 'phase': 'end', 'outcome': 'Stopped optional tooling'})['status'], 'blocked')

    def test_tested_predecessor_unblocks_development_before_acceptance(self):
        item = self.start()
        self.assertEqual(self.action(item, 'status')['development_ready'], ['T1'])
        claim = create_claim(self.repo, self.spec(reuse_worktree=True))['claim']
        (self.repo / 'src/a.txt').write_text('tested predecessor\n')
        git(self.repo, 'commit', '-am', 'predecessor')
        result = capture_receipt(self.repo, {'claim_id': claim['id'], 'owner': claim['owner'], 'commands': self.spec()['required_checks']})
        self.action(item, 'checkpoint', receipts=[result['receipt']], next_action='Implement dependent behavior')
        status = self.action(item, 'status')
        self.assertEqual(status['development_ready'], ['T1', 'T2'])
        self.assertEqual(status['selection']['status'], 'implementing')
        with self.assertRaisesRegex(CoordinationError, 'review is missing'):
            self.action(item, 'accept', receipt=result['receipt'], review=str(self.repo / '.ai/evidence/no-review.json'))

    def test_selection_repair_budget_survives_accepted_reselection(self):
        item, receipt, review = self.checked_selection()
        for _ in range(2):
            self.action(item, 'repair', phase='begin', reason='Optional screenshot capture')
            self.action(item, 'repair', phase='end', outcome='Use browser assertions')
        self.action(item, 'accept', receipt=receipt, review=str(review))
        replacement = self.start(dependencies={})
        with self.assertRaisesRegex(CoordinationError, 'exhausted'):
            self.action(replacement, 'repair', phase='begin', reason='Rebranded media phase')

    def test_unreviewed_workers_compose_but_cannot_be_accepted_individually(self):
        _, _, worker = self.ready()
        from pathlib import Path
        Path(worker['review']).unlink()
        lane, spec = self.integration([worker])
        item = selection(lane, 'start', {'owner': 'integrator', 'task_ids': ['T1'], 'outcome': 'Working contribution',
                                        'product_paths': ['src'], 'required_checks': spec['commands']})['selection']
        spec['selection_id'] = item['id']
        result = integrate(lane, spec)
        self.assertEqual(result['status'], 'pending-review')
        with registry(lane) as state:
            self.assertEqual(state['selections'][item['id']]['status'], 'implementing')
            self.assertIn('T1', state['selections'][item['id']]['tested_tasks'])


if __name__ == '__main__':
    import unittest
    unittest.main()
