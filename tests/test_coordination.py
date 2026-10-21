from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import subprocess
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

from agent_workflow.coordination import integrate
from agent_workflow.coordination_evidence import capture_receipt, digest, requirements_digest, validate_evidence, validate_review, verify_receipt
from agent_workflow.coordination_plan import PlanError, frontmatter, task_index
from agent_workflow.coordination_state import (CoordinationError, cleanup_worktree, create_claim, create_worktree,
                                              git, input_snapshot, read_json, registry,
                                              release_claim, resume, revision, write_json)


def race_claim(repo, spec, queue):
    try:
        create_claim(repo, spec)
        queue.put('created')
    except CoordinationError:
        queue.put('blocked')


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        git(self.repo, 'init', '-b', 'main')
        git(self.repo, 'config', 'user.name', 'Fixture')
        git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/a.txt').write_text('original a\n')
        (self.repo / 'src/b.txt').write_text('original b\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-m', 'fixture baseline')
        self.base = revision(self.repo)

    def tearDown(self):
        self.temp.cleanup()

    def spec(self, task='T1', path='src/a.txt', owner='worker-a', **extra):
        return {'owner': owner, 'task_ids': [task], 'base_revision': self.base,
                'paths': [path] if path else [], 'resources': [], 'source_references': ['request:fixture'],
                'acceptance_ids': ['AC1'], 'required_checks': [{'id': 'check', 'kind': 'check', 'argv': [sys.executable, '-c', 'print("checked")']}], **extra}

    def lane(self, task='T1', path='src/a.txt', owner='worker-a', **extra):
        claim = create_claim(self.repo, self.spec(task, path, owner, **extra))['claim']
        lane = self.root / claim['id']
        create_worktree(self.repo, claim['id'], lane, claim['id'], owner)
        return claim, lane

    def ready(self, task='T1', path='src/a.txt', owner='worker-a'):
        claim, lane = self.lane(task, path, owner)
        (lane / path).write_text('changed by ' + owner + '\n')
        git(lane, 'add', path)
        git(lane, 'commit', '-m', 'worker change')
        result = capture_receipt(lane, {'claim_id': claim['id'], 'owner': owner,
                                      'commands': [{'id': 'check', 'kind': 'check', 'argv': [sys.executable, '-c', 'print("checked")']}],
                                      'selected_cases': ['AC1'], 'environment': 'fixture'})
        receipt = result['result']
        review = lane / '.ai/evidence/review.json'
        write_json(review, {'reviewer': 'reviewer', 'tested_revision': receipt['tested_revision'],
                            'input_fingerprint': receipt['input_fingerprint'], 'verdict': 'accepted', 'findings': []})
        return claim, lane, {'claim_id': claim['id'], 'commit': revision(lane),
                             'receipt': result['receipt'], 'review': str(review)}

    def integration(self, workers, commands=None):
        commands = commands or [{'id': 'combined', 'kind': 'check', 'argv': [sys.executable, '-c', 'print("combined check")']}]
        claim, lane = self.lane('integration:G1', None, 'integrator', role='integrator', required_checks=commands)
        spec = {'owner': 'integrator', 'integration_claim_id': claim['id'], 'expected_head': revision(lane),
                'group_id': 'G1', 'workers': workers,
                'commands': commands}
        return lane, spec


class ClaimsTests(GitFixture):
    def test_broad_directories_reserve_shared_mutations(self):
        create_claim(self.repo, self.spec(path='services/core'))
        with self.assertRaisesRegex(CoordinationError, 'shared:'):
            create_claim(self.repo, self.spec('T2', 'services/catalog', 'worker-b'))

    def test_config_and_host_capacity_reduce_three_worker_ceiling(self):
        write_json(self.repo / '.ai/config.json', {'max_workers': 1})
        create_claim(self.repo, self.spec())
        with self.assertRaisesRegex(CoordinationError, 'capacity 1'):
            create_claim(self.repo, self.spec('T2', 'src/b.txt', 'worker-b', host_capacity=2))

    def test_overlapping_directories_conflict_across_chats(self):
        create_claim(self.repo, self.spec(path='src'))
        with self.assertRaisesRegex(CoordinationError, 'conflicts'):
            create_claim(self.repo, self.spec('T2', 'src/b.txt', 'worker-b'))

    def test_resource_and_task_collisions(self):
        create_claim(self.repo, self.spec(resources=['port:4001']))
        with self.assertRaisesRegex(CoordinationError, 'resources'):
            create_claim(self.repo, self.spec('T2', 'src/b.txt', 'worker-b', resources=['port:4001']))

    def test_inferred_shared_resource_serializes_migrations(self):
        create_claim(self.repo, self.spec(path='service/db/migration/V1.sql'))
        with self.assertRaisesRegex(CoordinationError, 'migration-allocation'):
            create_claim(self.repo, self.spec('T2', 'service/db/migration/V2.sql', 'worker-b'))

    def test_concurrent_claim_is_atomic(self):
        context = multiprocessing.get_context('fork')
        queue = context.Queue()
        processes = [context.Process(target=race_claim, args=(str(self.repo), self.spec(owner=f'w{i}'), queue)) for i in range(2)]
        for process in processes:
            process.start()
        outcomes = [queue.get(timeout=10) for _ in processes]
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        self.assertCountEqual(outcomes, ['created', 'blocked'])

    def test_lock_timeout_does_not_remove_live_lock(self):
        with registry(self.repo):
            with self.assertRaisesRegex(CoordinationError, 'locked'):
                with registry(self.repo, timeout=0.05):
                    self.fail('second lock should fail')

    def test_wrong_base_rejected(self):
        (self.repo / 'src/a.txt').write_text('new head')
        git(self.repo, 'commit', '-am', 'new head')
        with self.assertRaisesRegex(CoordinationError, 'base'):
            create_claim(self.repo, self.spec())

    def test_worktree_exact_base_and_shared_registry(self):
        claim, lane = self.lane()
        self.assertEqual(revision(lane), self.base)
        with registry(lane) as state:
            self.assertIn(claim['id'], state['claims'])
        self.assertNotEqual(lane, self.repo)

    def test_stale_claim_requires_explicit_owner_release(self):
        claim, lane = self.lane()
        with registry(self.repo) as state:
            state['claims'][claim['id']]['updated_at'] = 0
        result = resume(self.repo)
        self.assertTrue(result['claims'][0]['stale_attention'])
        with self.assertRaises(CoordinationError):
            release_claim(self.repo, claim['id'], 'other-chat', 'looks old')
        release_claim(self.repo, claim['id'], claim['owner'], 'owner inspected retained branch')
        self.assertTrue(lane.is_dir())
        self.assertEqual(resume(self.repo)['claims'], [])

    def test_only_one_integrator(self):
        create_claim(self.repo, self.spec('integration:G1', None, 'integrator', role='integrator'))
        with self.assertRaisesRegex(CoordinationError, 'integrator'):
            create_claim(self.repo, self.spec('integration:G2', None, 'other-integrator', role='integrator'))

    def test_three_lane_limit_and_safe_path(self):
        for i in range(3):
            create_claim(self.repo, self.spec(f'T{i}', f'area{i}.txt', f'w{i}'))
        with self.assertRaisesRegex(CoordinationError, 'capacity'):
            create_claim(self.repo, self.spec('T4', 'area4.txt', 'w4'))
        with self.assertRaises(CoordinationError):
            create_claim(self.repo, self.spec('T5', '../outside', 'w5'))


class ReceiptTests(GitFixture):
    def test_receipt_captures_real_commands_and_detects_edits(self):
        claim, lane, worker = self.ready()
        receipt = read_json(worker['receipt'])
        self.assertEqual(receipt['commands'][0]['exit_code'], 0)
        self.assertEqual(verify_receipt(lane, receipt), [])
        (lane / 'src/a.txt').write_text('changed after checks')
        self.assertTrue(any('stale' in e for e in verify_receipt(lane, receipt)))

    def test_missing_tool_is_blocked(self):
        commands = [{'id': 'check', 'kind': 'check', 'argv': ['no-such-workflow-fixture-executable']}]
        claim, lane = self.lane(required_checks=commands)
        result = capture_receipt(lane, {'claim_id': claim['id'], 'owner': claim['owner'], 'commands': commands})
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['result']['commands'][0]['exit_code'], 127)

    def test_recent_but_unwritten_test_report_is_stale(self):
        report = '.ai/evidence/tests.json'
        commands = [{'id': 'check', 'kind': 'test', 'argv': [sys.executable, '-c', 'print("did not run tests")'],
                     'test_report': {'path': report, 'format': 'workflow-test'}}]
        claim, lane = self.lane(required_checks=commands)
        write_json(lane / report, {'selected': 1, 'executed': 1, 'failed': 0})
        result = capture_receipt(lane, {'claim_id': claim['id'], 'owner': claim['owner'], 'commands': commands})
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('freshly', result['result']['commands'][0]['test_result']['reason'])

    def test_empty_test_selection_is_blocked(self):
        report = '.ai/evidence/tests.json'
        data = json.dumps({'selected': 0, 'executed': 0, 'failed': 0})
        program = f'from pathlib import Path; Path({report!r}).write_text({data!r})'
        commands = [{'id': 'check', 'kind': 'test', 'argv': [sys.executable, '-c', program],
                     'test_report': {'path': report, 'format': 'workflow-test'}}]
        claim, lane = self.lane(required_checks=commands)
        result = capture_receipt(lane, {'claim_id': claim['id'], 'owner': claim['owner'], 'commands': commands})
        self.assertEqual(result['status'], 'blocked')

    def test_real_nonempty_machine_report_passes(self):
        report = '.ai/evidence/tests.xml'
        xml = '<testsuite><testcase name="behavior"/></testsuite>'
        program = f'from pathlib import Path; Path({report!r}).write_text({xml!r})'
        commands = [{'id': 'check', 'kind': 'test', 'argv': [sys.executable, '-c', program],
                     'test_report': {'path': report, 'format': 'junit'}}]
        claim, lane = self.lane(required_checks=commands)
        result = capture_receipt(lane, {'claim_id': claim['id'], 'owner': claim['owner'], 'commands': commands})
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['result']['commands'][0]['test_result']['executed'], 1)

    def test_required_command_cannot_be_downgraded(self):
        required = [{'id': 'check', 'kind': 'test', 'argv': ['test-runner'],
                     'test_report': {'path': '.ai/evidence/test.json', 'format': 'workflow-test'}}]
        claim, lane = self.lane(required_checks=required)
        with self.assertRaisesRegex(CoordinationError, 'contracts'):
            capture_receipt(lane, {'claim_id': claim['id'], 'owner': claim['owner'],
                                  'commands': [{'id': 'check', 'kind': 'check', 'argv': ['true']}]})

    def test_incomplete_command_capture_cannot_pass(self):
        _, lane, worker = self.ready()
        receipt = read_json(worker['receipt'])
        del receipt['commands'][0]['logs']['stdout']
        self.assertTrue(any('stdout' in e for e in verify_receipt(lane, receipt)))
        receipt['actual_changed_files'] = []
        self.assertTrue(any('inventory' in e for e in verify_receipt(lane, receipt)))

    def test_known_generated_outputs_do_not_invalidate_source(self):
        before = input_snapshot(self.repo)['fingerprint']
        for name in ('build/report.xml', 'test-results/run.json', '.ai/install-backups/backup.json', 'node_modules/package/index.js'):
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('generated output')
        self.assertEqual(input_snapshot(self.repo)['fingerprint'], before)
        code = self.repo / '.ai/bundles/1.0.0/agent_workflow/tool.py'
        code.parent.mkdir(parents=True)
        code.write_text('print("checked bundle code")')
        self.assertNotEqual(input_snapshot(self.repo)['fingerprint'], before)

    def test_bookkeeping_does_not_invalidate_requirements_do(self):
        path = self.repo / 'task.md'
        path.write_text('---\nkind: task\nstatus: Not started\n---\n## Acceptance\nExpected behavior.\n## Evidence\nNot run\n## Completion and handoff\nNext step.\n')
        before = input_snapshot(self.repo)['fingerprint']
        path.write_text(path.read_text().replace('Not started', 'In review').replace('Not run', 'Passed with linked evidence'))
        self.assertEqual(input_snapshot(self.repo)['fingerprint'], before)
        path.write_text(path.read_text().replace('Expected behavior.', 'Changed requirement.'))
        self.assertNotEqual(input_snapshot(self.repo)['fingerprint'], before)

    def test_review_cannot_be_self_review_or_stale(self):
        claim, lane, worker = self.ready()
        receipt = read_json(worker['receipt'])
        review = read_json(worker['review'])
        review['reviewer'] = receipt['implementer']
        self.assertTrue(validate_review(receipt, review))
        review['reviewer'] = 'another'
        review['input_fingerprint'] = 'old'
        self.assertTrue(validate_review(receipt, review))


class IntegrationTests(GitFixture):
    def integration(self, workers, commands=None):
        from agent_workflow.selection import selection
        lane, spec = super().integration(workers, commands)
        with registry(lane) as state:
            tasks = sorted({task for worker in workers for task in state['claims'][worker['claim_id']]['task_ids']})
        item = selection(lane, 'start', {'owner': 'integrator', 'task_ids': tasks,
                         'outcome': 'Combined contribution', 'product_paths': ['src'],
                         'required_checks': spec['commands']})['selection']
        spec['selection_id'] = item['id']
        return lane, spec

    def test_integration_without_selection_rejects_before_mutation(self):
        _, _, worker = self.ready()
        lane, spec = super().integration([worker])
        head = revision(lane)
        with self.assertRaisesRegex(CoordinationError, 'requires selection_id'):
            integrate(lane, spec)
        self.assertEqual(revision(lane), head)

    def test_parallel_contributions_preserved_and_checked(self):
        _, _, a = self.ready()
        _, _, b = self.ready('T2', 'src/b.txt', 'worker-b')
        lane, spec = self.integration([b, a])
        b['depends_on'] = ['T1']
        result = integrate(lane, spec)
        self.assertEqual(result['status'], 'pending-review', result)
        self.assertEqual((lane / 'src/a.txt').read_text(), 'changed by worker-a\n')
        self.assertEqual((lane / 'src/b.txt').read_text(), 'changed by worker-b\n')
        self.assertEqual(result['result']['merged_claims'], [a['claim_id'], b['claim_id']])

    def test_wrong_integration_branch_is_rejected(self):
        _, _, worker = self.ready()
        lane, spec = self.integration([worker])
        git(lane, 'checkout', '--detach')
        with self.assertRaisesRegex(CoordinationError, 'claimed branch'):
            integrate(lane, spec)

    def test_worker_review_is_not_a_separate_acceptance_gate(self):
        _, _, worker = self.ready()
        Path(worker['review']).unlink()
        lane, spec = self.integration([worker])
        self.assertEqual(integrate(lane, spec)['status'], 'pending-review')

    def test_unclaimed_file_cannot_merge(self):
        claim, lane = self.lane()
        (lane / 'src/b.txt').write_text('outside assigned surface')
        git(lane, 'commit', '-am', 'outside claim')
        result = capture_receipt(lane, {'claim_id': claim['id'], 'owner': claim['owner'], 'commands': [
            {'id': 'check', 'kind': 'check', 'argv': [sys.executable, '-c', 'print("checked")']}]})
        receipt = result['result']
        review_path = lane / '.ai/evidence/review.json'
        write_json(review_path, {'reviewer': 'independent', 'tested_revision': receipt['tested_revision'],
                               'input_fingerprint': receipt['input_fingerprint'], 'verdict': 'accepted', 'findings': []})
        worker = {'claim_id': claim['id'], 'commit': revision(lane), 'receipt': result['receipt'], 'review': str(review_path)}
        integration_lane, spec = self.integration([worker])
        with self.assertRaisesRegex(CoordinationError, 'unclaimed'):
            integrate(integration_lane, spec)

    def test_conflicts_remain_for_semantic_resolution(self):
        _, _, worker = self.ready()
        lane, spec = self.integration([worker])
        (lane / 'src/a.txt').write_text('integrated prerequisite changed\n')
        git(lane, 'commit', '-am', 'new integrated behavior')
        spec['expected_head'] = revision(lane)
        result = integrate(lane, spec)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['result']['conflicted_files'], ['src/a.txt'])
        self.assertEqual(git(lane, 'rev-parse', '-q', '--verify', 'MERGE_HEAD', check=False).returncode, 0)
        self.assertTrue(resume(lane)['integrations'])

    def test_cleanup_preserves_evidence_and_unaccepted_work(self):
        claim, worker_lane, worker = self.ready()
        lane, spec = self.integration([worker])
        self.assertEqual(integrate(lane, spec)['status'], 'pending-review')
        with self.assertRaisesRegex(CoordinationError, 'release'):
            cleanup_worktree(self.repo, claim['id'], claim['owner'])
        release_claim(self.repo, claim['id'], claim['owner'], 'Retain pending review contribution')
        with self.assertRaisesRegex(CoordinationError, 'successful retained integration'):
            cleanup_worktree(self.repo, claim['id'], claim['owner'])
        self.assertTrue(worker_lane.exists())
        self.assertTrue((worker_lane / '.ai/evidence').exists())

    def test_two_failed_corrections_stop_without_deleting_work(self):
        _, _, worker = self.ready()
        lane, spec = self.integration([worker], [{'id': 'combined', 'kind': 'check', 'argv': [sys.executable, '-c', 'raise SystemExit(1)']}])
        for _ in range(2):
            self.assertEqual(integrate(lane, spec)['status'], 'blocked')
            spec['expected_head'] = revision(lane)
        with self.assertRaisesRegex(CoordinationError, 'Two correction'):
            integrate(lane, spec)
        self.assertTrue(lane.is_dir())
        self.assertEqual((lane / 'src/a.txt').read_text(), 'changed by worker-a\n')


class EvidenceTests(GitFixture):
    def evidence(self, requirements=None):
        requirements = requirements or {'cases': [{'id': 'AC1', 'boundary': 'database', 'independent_state': True}]}
        path = self.repo / '.ai/evidence/result.json'
        write_json(path, {'actual': 'expected'})
        return {'requirements_sha256': requirements_digest(requirements), 'input_fingerprint': input_snapshot(self.repo)['fingerprint'], 'implementer': 'worker', 'reviewer': 'reviewer',
                'cases': [{'id': 'AC1', 'boundary': 'database', 'result': 'passed', 'assertions': ['Fresh reader observed committed row'],
                           'artifacts': [{'path': '.ai/evidence/result.json', 'sha256': digest(path)}],
                           'state_observation': {'method': 'Separate connection read committed row', 'artifact': {'path': '.ai/evidence/result.json', 'sha256': digest(path)}}}]}

    def test_required_mapping_boundary_and_staleness(self):
        requirements = {'cases': [{'id': 'AC1', 'boundary': 'database', 'independent_state': True}]}
        evidence = self.evidence()
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'passed')
        evidence['cases'][0]['boundary'] = 'unit'
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'blocked')
        evidence['cases'] = []
        self.assertTrue(any('Missing' in error for error in validate_evidence(self.repo, requirements, evidence)['errors']))
        with self.assertRaises(CoordinationError):
            validate_evidence(self.repo, {'cases': []}, evidence)

    def test_browser_assertions_pass_without_optional_recording(self):
        requirements = {'cases': [{'id': 'AC1', 'boundary': 'browser'}]}
        evidence = self.evidence(requirements)
        case = evidence['cases'][0]
        case['boundary'] = 'browser'
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'passed')
        case['artifacts'] = []
        case['direct_observation'] = {'observer': 'reviewer', 'method': 'Actual browser interaction',
                                      'observations': 'Submitted form persisted and displayed its saved value'}
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'passed')
        case['assertions'] = []
        self.assertTrue(any('assertions' in error for error in validate_evidence(self.repo, requirements, evidence)['errors']))

    def test_speech_obligation_cannot_be_replaced_by_dom_assertions(self):
        requirements = {'cases': [{'id': 'AC1', 'boundary': 'browser', 'assistive_technology': 'VoiceOver', 'speech_required': True}]}
        evidence = self.evidence(requirements)
        case = evidence['cases'][0]
        case['boundary'] = 'browser'
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'blocked')
        case['assistive_observation'] = {'observer': 'reviewer', 'tool': 'VoiceOver', 'result': 'passed',
                                          'observations': 'Success announcement was spoken after saving',
                                          'artifact': case['artifacts'][0], 'speech_observed': True}
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'passed')
        case['assistive_observation']['speech_observed'] = False
        self.assertTrue(any('speech' in error for error in validate_evidence(self.repo, requirements, evidence)['errors']))

    def test_missing_frames_or_unreadable_recording_blocks(self):
        evidence = self.evidence()
        case = evidence['cases'][0]
        case['boundary'] = 'browser'
        requirements = {'cases': [{'id': 'AC1', 'boundary': 'browser', 'recording_required': True}]}
        evidence['requirements_sha256'] = requirements_digest(requirements)
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'blocked')
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            self.skipTest('ffmpeg/ffprobe unavailable for real recording fixture')
        video = self.repo / '.ai/evidence/journey.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=320x240:d=3', '-y', str(video)], check=True)
        frame = self.repo / '.ai/evidence/frame.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-ss', '1', '-i', str(video), '-frames:v', '1', '-y', str(frame)], check=True)
        case['recording'] = {'path': '.ai/evidence/journey.mp4', 'sha256': digest(video), 'timestamps': [0, 3], 'redaction_checked': True, 'inspected_frames': [
            {'path': '.ai/evidence/frame.png', 'sha256': digest(frame), 'timestamp': 1, 'recording_sha256': digest(video),
             'inspector': 'reviewer', 'readable': False, 'observations': 'Caption is cropped'}]}
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'blocked')
        case['recording']['inspected_frames'][0]['readable'] = True
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'passed')
        self.assertIn('reviewer must inspect', validate_evidence(self.repo, requirements, evidence)['scope'])
        frame.write_text('text disguised as an image')
        case['recording']['inspected_frames'][0]['sha256'] = digest(frame)
        self.assertTrue(any('decodable' in error for error in validate_evidence(self.repo, requirements, evidence)['errors']))

    def test_requirements_changes_in_excluded_state_invalidate_evidence(self):
        requirements = {'cases': [{'id': 'AC1', 'boundary': 'database', 'independent_state': True}]}
        evidence = self.evidence(requirements)
        requirements['cases'][0]['independent_state'] = False
        self.assertTrue(any('requirements JSON' in e for e in validate_evidence(self.repo, requirements, evidence)['errors']))

    def test_artifact_hash_change_and_feature_owner_block(self):
        evidence = self.evidence()
        requirements = {'cases': [{'id': 'AC1', 'boundary': 'database'}], 'feature_completion': True, 'integration_owner': 'T9'}
        evidence['requirements_sha256'] = requirements_digest(requirements)
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'blocked')
        evidence['integration_owner'] = 'T9'
        (self.repo / '.ai/evidence/result.json').write_text('replacement artifact')
        self.assertEqual(validate_evidence(self.repo, requirements, evidence)['status'], 'blocked')


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'plan/01/tasks').mkdir(parents=True)
        (self.root / 'source.md').write_text('# Source\n')
        digest_value = hashlib.sha256((self.root / 'source.md').read_bytes()).hexdigest()
        (self.root / 'PLAN.md').write_text(f'---\nkind: plan\nschema_version: 1\nreadiness: Ready\nplan_root: plan\nsources:\n- id: SOURCE\n  path: source.md\n  sha256: {digest_value}\ngroups:\n- id: G1\n  path: plan/01/group.md\n---\n# Plan\n')
        (self.root / 'plan/01/group.md').write_text('---\nkind: group\nid: G1\ntasks:\n- T1\n- T2\nintegration_owner: T2\n---\n# Group\n')
        for number in (1, 2):
            dependency = '[]' if number == 1 else '[T1]'
            (self.root / f'plan/01/tasks/T{number}.md').write_text(f'---\nkind: task\nid: T{number}\ngroup: G1\ndepends_on: {dependency}\nreadiness: Ready\nstatus: Not started\ntest_strategy: checks-only\nvisual_review: not-applicable\n---\n## Acceptance\n- T{number}-A1: observable result\n')

    def tearDown(self):
        self.temp.cleanup()

    def test_actual_supported_shape_and_eligibility_without_mutation(self):
        path = self.root / 'PLAN.md'
        before = {str(p): p.read_bytes() for p in self.root.rglob('*.md')}
        result = task_index(path)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['dependency_order'], ['T1', 'T2'])
        self.assertTrue(result['tasks']['T1']['execution_eligible'])
        self.assertFalse(result['tasks']['T2']['execution_eligible'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*.md')})

    def test_cycles_source_drift_and_group_owner(self):
        task = self.root / 'plan/01/tasks/T1.md'
        task.write_text(task.read_text().replace('depends_on: []', 'depends_on: [T2]'))
        with self.assertRaisesRegex(PlanError, 'cycle'):
            task_index(self.root / 'PLAN.md')
        task.write_text(task.read_text().replace('depends_on: [T2]', 'depends_on: []'))
        (self.root / 'source.md').write_text('Changed source')
        self.assertEqual(task_index(self.root / 'PLAN.md')['status'], 'blocked')
        group = self.root / 'plan/01/group.md'
        group.write_text(group.read_text().replace('integration_owner: T2', 'integration_owner: T3'))
        with self.assertRaisesRegex(PlanError, 'owner'):
            task_index(self.root / 'PLAN.md')

    def test_unsupported_yaml_never_executes(self):
        path = self.root / 'unsafe.md'
        path.write_text('---\nkind: !dangerous object\n---\n')
        with self.assertRaises(PlanError):
            frontmatter(path)
        path.write_text('---\nkind: plan\nkind: task\n---\n')
        with self.assertRaisesRegex(PlanError, 'Duplicate'):
            frontmatter(path)


if __name__ == '__main__':
    unittest.main()
