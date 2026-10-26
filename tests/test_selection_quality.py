import hashlib
import json
from unittest.mock import patch

from agent_workflow import gates, selection_quality
from agent_workflow.coordination_state import CoordinationError, git, revision
from tests.test_coordination import GitFixture


class SelectionQualityTests(GitFixture):
    def setUp(self):
        super().setUp()
        self.item = {'initial_revision': self.base}
        self.registry = {'schema_version': 1, 'checks': [{'id': 'lint', 'argv': ['true'], 'stage': 'fast'}]}

    def modify(self, name):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('changed\n')
        git(self.repo, 'add', name)
        git(self.repo, 'commit', '-m', 'change selected input')

    def test_arbitrary_required_check_cannot_accept_runtime_feature(self):
        self.modify('app.py')
        with patch.object(gates, 'load_registry', return_value=self.registry):
            with self.assertRaisesRegex(CoordinationError, 'full delivery'):
                selection_quality.validate_acceptance(self.repo, self.item, {}, {})

    def test_document_only_acceptance_does_not_execute_checks(self):
        self.modify('README.md')
        with patch.object(gates, 'load_registry', return_value=self.registry), patch.object(gates, 'run_gates') as run:
            selection_quality.validate_acceptance(self.repo, self.item, {}, {})
            run.assert_not_called()

    def test_maintenance_requires_reviewed_approved_exact_scope(self):
        self.modify('agent_workflow/helper.py')
        scope = {'kind': 'workflow-maintenance', 'approval_reference': 'user:approved',
                 'reason': 'Harness upgrade', 'paths': ['agent_workflow']}
        self.item['quality_scope'] = scope
        with patch.object(gates, 'load_registry', return_value=self.registry):
            with self.assertRaisesRegex(CoordinationError, 'independent review'):
                selection_quality.validate_acceptance(self.repo, self.item, {}, {})
            selection_quality.validate_acceptance(self.repo, self.item, {'quality_scope': scope}, {})

    def test_wildcard_scope_cannot_exempt_product_runtime(self):
        self.modify('frontend/src/app.ts')
        scope = {'kind': 'workflow-maintenance', 'approval_reference': 'user:approved',
                 'reason': 'Attempt bypass', 'paths': ['**']}
        self.item['quality_scope'] = scope
        with patch.object(gates, 'load_registry', return_value=self.registry):
            with self.assertRaisesRegex(CoordinationError, 'product paths'):
                selection_quality.validate_acceptance(self.repo, self.item, {'quality_scope': scope}, {})

    def test_maintenance_cannot_exempt_declared_product_in_harness_named_path(self):
        self.modify('agent_workflow/app.py')
        scope = {'kind': 'workflow-maintenance', 'approval_reference': 'user:approved',
                 'reason': 'Upgrade', 'paths': ['agent_workflow']}
        self.item['quality_scope'] = scope
        self.registry['quality'] = {'components': [{'production': ['agent_workflow/*.py']}]}
        with patch.object(gates, 'load_registry', return_value=self.registry):
            with self.assertRaisesRegex(CoordinationError, 'product runtime'):
                selection_quality.validate_acceptance(self.repo, self.item, {'quality_scope': scope}, {})

    def gate_record(self):
        log = self.repo / '.ai/reports/lint.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text('verified command')
        return {'status': 'passed', 'stage': 'delivery', 'full_acceptance': True, 'base': self.base,
                'input_fingerprint': gates.fingerprint(self.repo)['sha256'],
                'registry_sha256': hashlib.sha256(json.dumps(self.registry, sort_keys=True).encode()).hexdigest(),
                'results': [{'id': 'lint', 'status': 'passed', 'argv': ['true'], 'log': '.ai/reports/lint.log',
                             'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest(),
                             'outputs': {'.ai/reports/lint.log': hashlib.sha256(log.read_bytes()).hexdigest()}},
                            {'id': 'component-quality', 'status': 'passed', 'components': [{'component': 'app'}]}]}

    def test_fast_gate_and_stale_gate_cannot_accept(self):
        for mutation in ({'stage': 'fast'}, {'input_fingerprint': 'old'}, {'registry_sha256': 'old'}, {'results': []}):
            with self.assertRaises(CoordinationError):
                selection_quality.check_gate_record(self.repo, self.registry, self.gate_record() | mutation)

    def test_retained_gate_requires_current_read_only_component_validation(self):
        record = self.gate_record()
        with patch.object(selection_quality.quality, 'results', return_value=[{'status': 'blocked'}]):
            with self.assertRaisesRegex(CoordinationError, 'component quality'):
                selection_quality.check_gate_record(self.repo, self.registry, record)
        proof = [{'status': 'passed', 'components': [{'component': 'app'}]}]
        with patch.object(selection_quality.quality, 'results', return_value=proof):
            selection_quality.check_gate_record(self.repo, self.registry, record)

    def test_forged_passing_gate_is_not_registered(self):
        self.modify('app.py')
        path = self.repo / '.ai/reports/forged/result.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(self.gate_record()))
        proof = [{'status': 'passed', 'components': [{'component': 'app'}]}]
        with patch.object(gates, 'load_registry', return_value=self.registry), patch.object(selection_quality.quality, 'results', return_value=proof):
            with self.assertRaisesRegex(CoordinationError, 'full delivery'):
                selection_quality.validate_acceptance(self.repo, self.item, {}, {'gate_report': str(path)})

    def test_modified_registered_gate_is_rejected(self):
        self.modify('app.py')
        path = self.repo / '.ai/reports/captured/result.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(self.gate_record()))
        gates.register_gate_record(self.repo, path)
        path.write_text(path.read_text() + ' ')
        with patch.object(gates, 'load_registry', return_value=self.registry):
            with self.assertRaisesRegex(CoordinationError, 'full delivery'):
                selection_quality.validate_acceptance(self.repo, self.item, {}, {'gate_report': str(path)})

    def test_actual_registered_delivery_gate_can_be_accepted_read_only(self):
        self.modify('app.py')
        self.registry.update(supported_suffixes=['.py'], source_patterns=['*.py'],
                             component_inputs={}, component_dependencies={})
        proof = [{'id': 'component-quality', 'required': True, 'status': 'passed', 'components': [{'component': 'app'}]}]
        checks = self.gate_record()['results'][:1]
        with patch.object(gates, 'load_registry', return_value=self.registry), patch.object(gates, 'check_results', return_value=checks), patch.object(selection_quality.quality, 'results', return_value=proof):
            record = gates.run_gates(self.repo, stage='delivery', base=self.base)
            self.assertEqual(record['status'], 'passed')
            selection_quality.validate_acceptance(self.repo, self.item, {}, {'gate_report': record['report']})

    def test_retained_integration_reports_must_remain_unchanged(self):
        check = {'id': 'integration', 'argv': ['true'], 'stage': 'integration',
                 'test_report': {'format': 'junit', 'glob': '.ai/reports/integration.xml'}}
        path = self.repo / '.ai/reports/integration.xml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<testsuite><testcase name="database behavior"/></testsuite>')
        result = self.gate_record()['results'][0]
        result['outputs'][str(path.relative_to(self.repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
        result['tests'] = {'executed': 1, 'failures': 0, 'skipped': 0}
        selection_quality.retained_check(self.repo, check, result)
        path.write_text('<testsuite/>')
        with self.assertRaisesRegex(CoordinationError, 'artifacts'):
            selection_quality.retained_check(self.repo, check, result)
        path.unlink()
        with self.assertRaisesRegex(CoordinationError, 'artifacts'):
            selection_quality.retained_check(self.repo, check, result)

    def test_nested_gate_registration_is_blocked_without_waiting(self):
        from agent_workflow.coordination_state import registry
        path = self.repo / '.ai/reports/result.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}')
        with registry(self.repo):
            with self.assertRaisesRegex(CoordinationError, 'locked'):
                gates.register_gate_record(self.repo, path)
