import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from agent_workflow import gates, gate_selection


class GateSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        for component in ['api', 'web', 'other']:
            root = self.repo / component
            root.mkdir()
            (root / 'app.ts').write_text('const app = 1;\n')
            (root / 'test.ts').write_text('const test = 1;\n')
        self.registry = {'schema_version': 1, 'supported_suffixes': ['.ts'],
                         'component_inputs': {c: [f'{c}/**'] for c in ['api', 'web', 'other']},
                         'component_dependencies': {'api': [], 'web': ['api'], 'other': []},
                         'shared_input_patterns': ['config/**'],
                         'checks': [self.check(c) for c in ['api', 'web', 'other']]}
        self.save()
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'baseline')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)

    def check(self, component, **options):
        return dict(id=component, component=component, stage='fast', when=[f'{component}/**'],
                    argv=[sys.executable, '-c', f'print("{component}")'], **options)

    def save(self):
        path = self.repo / '.ai/gates.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(self.registry))

    def run_gate(self, **options):
        self.save()
        return gates.run_gates(self.repo, **options)

    def enable_reuse(self, index=0):
        self.registry['checks'][index]['reuse'] = {'max_age_seconds': 600}

    def result(self, **options):
        return self.run_gate(reuse=True, **options)['results'][0]

    def test_affected_producer_includes_downstream_but_not_unrelated(self):
        (self.repo / 'api/app.ts').write_text('changed')
        result = self.run_gate(affected=True, base='HEAD')
        self.assertEqual([r['id'] for r in result['results']], ['api', 'web'])

    def test_affected_consumer_does_not_select_producer(self):
        (self.repo / 'web/test.ts').write_text('changed')
        result = self.run_gate(affected=True, base='HEAD')
        self.assertEqual([r['id'] for r in result['results']], ['web'])

    def test_root_build_config_broadens_selection(self):
        (self.repo / 'package-lock.json').write_text('{}')
        self.assertEqual(len(self.run_gate(affected=True, base='HEAD')['results']), 3)

    def test_shared_or_unclassified_nested_input_broadens(self):
        (self.repo / 'config').mkdir()
        (self.repo / 'config/build.json').write_text('{}')
        self.assertIsNone(self.run_gate(affected=True, base='HEAD')['selection']['components'])

    def test_missing_invalid_base_and_incomplete_cycle_graph_broaden(self):
        for base in [None, 'missing-revision']:
            self.assertEqual(len(self.run_gate(affected=True, base=base)['results']), 3)
        self.registry['component_dependencies']['api'] = ['web']
        self.assertIsNone(self.run_gate(affected=True, base='HEAD')['selection']['components'])
        del self.registry['component_dependencies']['web']
        self.assertIsNone(self.run_gate(affected=True, base='HEAD')['selection']['components'])

    def test_unchanged_selection_still_checks_source_support(self):
        result = self.run_gate(affected=True, base='HEAD')
        self.assertEqual(result['selection']['components'], [])
        (self.repo / 'unmanaged.ts').write_text('source')
        result = self.run_gate(affected=True, base='HEAD')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['results'][-1]['id'], 'stack-support')

    def test_report_outputs_do_not_broaden_next_selection(self):
        self.run_gate()
        (self.repo / 'web/app.ts').write_text('changed')
        self.assertEqual(self.run_gate(affected=True, base='HEAD')['selection']['components'], ['web'])

    def test_full_and_component_modes_remain(self):
        self.assertEqual(len(self.run_gate()['results']), 3)
        self.assertEqual([r['id'] for r in self.run_gate(component='web')['results']], ['web'])

    def test_reuse_requires_explicit_policy_and_flag(self):
        self.result()
        self.assertNotIn('reused_from', self.result())
        self.enable_reuse()
        self.result()
        self.assertIn('reused_from', self.result())
        self.assertNotIn('reused_from', self.run_gate()['results'][0])

    def test_source_and_test_changes_invalidate_reuse(self):
        self.enable_reuse()
        for name in ['api/app.ts', 'api/test.ts']:
            self.result()
            (self.repo / name).write_text(f'changed {name}')
            self.assertNotIn('reused_from', self.result())

    def test_unrelated_input_does_not_invalidate_component_result(self):
        self.enable_reuse()
        self.result()
        (self.repo / 'other/app.ts').write_text('unrelated')
        self.assertIn('reused_from', self.result())

    def test_unclassified_helper_change_invalidates_reuse(self):
        self.enable_reuse()
        self.result()
        (self.repo / 'scripts').mkdir()
        (self.repo / 'scripts/helper.txt').write_text('shared helper')
        self.assertNotIn('reused_from', self.result())

    def test_declared_output_artifact_must_exist_and_match(self):
        self.enable_reuse()
        check = self.registry['checks'][0]
        check['reuse']['artifacts'] = ['.ai/reports/generated.txt']
        self.result()
        self.assertNotIn('reused_from', self.result())
        check['argv'][-1] = "from pathlib import Path; p=Path('.ai/reports'); p.mkdir(parents=True, exist_ok=True); (p/'generated.txt').write_text('valid')"
        self.result()
        self.assertIn('reused_from', self.result())
        (self.repo / '.ai/reports/generated.txt').write_text('modified')
        self.assertNotIn('reused_from', self.result())

    def test_upstream_input_invalidates_consumer_result(self):
        self.enable_reuse(1)
        self.run_gate(reuse=True)
        (self.repo / 'api/app.ts').write_text('upstream change')
        self.assertNotIn('reused_from', self.run_gate(reuse=True)['results'][1])

    def test_environment_runtime_and_command_changes_invalidate(self):
        self.enable_reuse()
        self.result()
        with patch.dict(os.environ, {'WORKFLOW_TEST_ENV': 'changed'}):
            self.assertNotIn('reused_from', self.result())
        with patch('agent_workflow.gate_selection.platform.platform', return_value='different-runtime'):
            self.assertNotIn('reused_from', self.result())
        self.registry['checks'][0]['argv'][-1] = 'print("changed command")'
        self.assertNotIn('reused_from', self.result())

    def test_toolchain_and_configuration_changes_invalidate(self):
        installed = self.repo / '.ai/reports/toolchain.txt'
        installed.parent.mkdir(parents=True)
        installed.write_text('installation v1')
        self.enable_reuse()
        self.registry['checks'][0]['reuse']['toolchain_files'] = ['.ai/reports/toolchain.txt']
        self.result()
        installed.write_text('installation v2')
        self.assertNotIn('reused_from', self.result())
        self.registry['checks'][0]['timeout_seconds'] = 20
        self.assertNotIn('reused_from', self.result())
        installed.unlink()
        self.assertNotIn('reused_from', self.result())

    def test_missing_modified_expired_and_failed_proofs_do_not_reuse(self):
        self.enable_reuse()
        first = self.result()
        (self.repo / first['log']).unlink()
        self.assertNotIn('reused_from', self.result())
        latest = self.result()
        (self.repo / latest['log']).write_text('tampered')
        self.assertNotIn('reused_from', self.result())
        with patch('agent_workflow.gate_selection.time.time', return_value=time.time() + 700):
            self.assertNotIn('reused_from', self.result())

    def test_failed_command_is_not_reused(self):
        self.enable_reuse()
        self.registry['checks'][0]['argv'][-1] = 'raise SystemExit(1)'
        self.assertEqual(self.result()['status'], 'failed')
        self.assertNotIn('reused_from', self.result())

    def test_scanner_and_sonar_never_reuse(self):
        self.enable_reuse()
        files = gates.fingerprint(self.repo)['files']
        for field in [{'result_format': 'osv-json'}, {'sonar': {'report': '.ai/reports/sonar.json'}},
                      {'argv': ['gitleaks', 'dir', '.']}]:
            check = self.registry['checks'][0] | field
            self.assertIsNone(gate_selection.reuse_identity(self.repo, self.registry, check, files))

    def test_concrete_security_findings_remain_blocking(self):
        osv = {'results': [{'packages': [{'package': {'name': 'unsafe', 'version': '1', 'ecosystem': 'npm'},
                                         'vulnerabilities': [{'id': 'fixture'}]}]}]}
        self.assertEqual(gates.scanner_summary(json.dumps(osv).encode(), 'osv-json')['status'], 'failed')
        sast = {'results': [{'check_id': 'fixture'}], 'errors': [], 'paths': {'scanned': ['api/app.ts']}}
        self.assertEqual(gates.scanner_summary(json.dumps(sast).encode(), 'semgrep-json')['status'], 'failed')

    def test_semantic_commands_deduplicate_but_report_contracts_do_not(self):
        first = self.registry['checks'][0]
        self.registry['checks'].append(dict(first, id='duplicate-api', required=False))
        result = self.run_gate()
        self.assertEqual(result['results'][-1]['deduplicated_from'], 'api')
        self.assertFalse(result['results'][-1]['required'])
        self.registry['checks'][-1]['test_report'] = {'format': 'junit', 'glob': '.ai/reports/missing.xml'}
        self.assertEqual(self.run_gate()['results'][-1]['status'], 'failed')

    def test_test_artifact_and_nonempty_test_selection_are_required(self):
        self.enable_reuse()
        check = self.registry['checks'][0]
        check['test_report'] = {'format': 'junit', 'glob': '.ai/reports/tests.xml'}
        check['argv'][-1] = "from pathlib import Path; p=Path('.ai/reports'); p.mkdir(parents=True, exist_ok=True); (p/'tests.xml').write_text('<testsuite><testcase/></testsuite>')"
        self.assertEqual(self.result()['tests']['executed'], 1)
        self.assertIn('reused_from', self.result())
        (self.repo / '.ai/reports/tests.xml').write_text('<testsuite/>')
        self.assertNotIn('reused_from', self.result())
        check['argv'][-1] = check['argv'][-1].replace('<testsuite><testcase/></testsuite>', '<testsuite/>')
        self.assertEqual(self.result()['status'], 'failed')

    def test_coverage_stays_eighty_and_reused_artifact_integrity_is_checked(self):
        report = self.repo / '.ai/reports/coverage.info'
        report.parent.mkdir(parents=True)
        report.write_text('SF:api/app.ts\nDA:1,0\nend_of_record\n')
        config = {'component': 'api', 'roots': ['api'], 'reports': ['.ai/reports/coverage.info'], 'format': 'lcov'}
        proof = {'reused_from': 'prior', 'artifacts': gate_selection.hash_paths(self.repo, ['.ai/reports/coverage.info'])}
        with patch('agent_workflow.gate_reports.changed_lines', return_value={'api/app.ts': {1}}):
            result = gates.coverage_result(self.repo, config, 'HEAD', [proof], time.time() + 1)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['threshold'], 80)
            report.write_text('SF:api/app.ts\nDA:1,1\nend_of_record\n')
            self.assertEqual(gates.coverage_result(self.repo, config, 'HEAD', [proof], time.time() + 1)['status'], 'blocked')

    def test_profile_limits_are_preserved(self):
        profile = json.loads((gates.BUNDLE / 'profiles/movie-app.json').read_text())
        self.assertEqual(profile['limits'], {'function_lines': 50, 'cyclomatic': 10, 'nesting': 3, 'changed_coverage_percent': 80})


if __name__ == '__main__':
    unittest.main()
