import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_workflow import gates, gate_reports


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        from agent_workflow import resources
        from test_resources import healthy
        for target, name, options in [(resources, 'state_directory', {'return_value': self.repo / '.ai/state/machine'}),
                                      (resources.resource_system, 'snapshot', {'side_effect': lambda *a: healthy()}),
                                      (resources.resource_system, 'process_tree', {'return_value': {'known': True, 'rss_bytes': 1, 'descendants': 0, 'pids': []}}),
                                      (resources, 'INTERVAL', {'new': 0})]:
            mock = patch.object(target, name, **options)
            mock.start(); self.addCleanup(mock.stop)

        (self.repo / 'src').mkdir()
        (self.repo / 'src/app.ts').write_text('export const app = 1;\n')
        self.registry = self.repo / '.ai/gates.json'

    def run_gate(self, checks, stage='fast'):
        self.registry.parent.mkdir(exist_ok=True)
        self.registry.write_text(json.dumps({'schema_version': 1, 'supported_suffixes': ['.ts'], 'source_patterns': ['src/**'], 'checks': checks}))
        return gates.run_gates(self.repo, stage)

    def check(self, argv, **options):
        return dict(id='test', stage='fast', argv=argv, **options)

    def test_coverage_uses_project_threshold_without_changing_measurement(self):
        report = self.repo / 'coverage.xml'
        report.write_text('<report/>')
        coverage = {'component': 'app', 'roots': ['src'], 'reports': ['coverage.xml'], 'format': 'jacoco'}
        measurement = {'percent': 70, 'missing_files': [], 'executable': 10}
        with patch.object(gate_reports, 'changed_lines', return_value={'src/app.ts': {1}}), patch.object(gate_reports, 'coverage_lines', return_value={}), patch.object(gate_reports, 'measure_coverage', return_value=measurement):
            self.assertEqual(gates.coverage_result(self.repo, coverage, 'HEAD', [], 0, 65)['status'], 'passed')
            result = gates.coverage_result(self.repo, coverage, 'HEAD', [], 0, 80)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['threshold'], 80)

    def test_exit_code_is_captured(self):
        result = self.run_gate([self.check([sys.executable, '-c', 'raise SystemExit(7)'])])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['results'][0]['exit_code'], 7)

    def test_missing_tool_blocks(self):
        result = self.run_gate([self.check(['not-a-real-agent-workflow-test-binary'])])
        self.assertEqual(result['status'], 'blocked')

    def test_empty_tests_fail_despite_exit_zero(self):
        code = "from pathlib import Path; Path('.ai/tests.xml').write_text('<testsuite/>')"
        check = self.check([sys.executable, '-c', code], test_report={'format': 'junit', 'glob': '.ai/tests.xml'})
        # Reports must live in an excluded output directory, never source inputs.
        check['argv'][-1] = code.replace('.ai/tests.xml', '.ai/reports/tests.xml')
        check['test_report']['glob'] = '.ai/reports/tests.xml'
        (self.repo / '.ai/reports').mkdir(parents=True)
        result = self.run_gate([check])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['results'][0]['tests']['executed'], 0)

    def test_skipped_tests_do_not_establish_execution(self):
        path = self.repo / 'tests.xml'
        path.write_text('<testsuite><testcase><skipped/></testcase></testsuite>')
        self.assertEqual(gate_reports.test_summary([path], 'junit')['executed'], 0)

    def test_actual_test_selection_passes(self):
        output = self.repo / '.ai/reports'
        output.mkdir(parents=True)
        code = "from pathlib import Path; Path('.ai/reports/tests.xml').write_text('<testsuite><testcase name=\"behavior\"/></testsuite>')"
        check = self.check([sys.executable, '-c', code], test_report={'format': 'junit', 'glob': '.ai/reports/tests.xml'})
        self.assertEqual(self.run_gate([check])['status'], 'passed')

    def test_input_mutation_invalidates_run(self):
        code = "from pathlib import Path; Path('src/app.ts').write_text('changed')"
        result = self.run_gate([self.check([sys.executable, '-c', code])])
        self.assertEqual(result['results'][-1]['id'], 'input-stability')
        self.assertEqual(result['status'], 'failed')

    def test_bookkeeping_does_not_change_fingerprint(self):
        before = gates.fingerprint(self.repo)
        output = self.repo / '.ai/evidence/result.json'
        output.parent.mkdir(parents=True)
        output.write_text('{}')
        self.assertEqual(before, gates.fingerprint(self.repo))
        (self.repo / 'src/app.ts').write_text('changed')
        self.assertNotEqual(before, gates.fingerprint(self.repo))

    def test_stage_and_applicability(self):
        check = self.check(['missing-command'], when=['server/**/*.kt'])
        self.assertEqual(self.run_gate([check])['results'][0]['status'], 'not-applicable')
        check['when'] = ['src/**/*.ts']
        self.assertEqual(self.run_gate([check])['status'], 'blocked')

    def test_argument_array_is_not_shell(self):
        result = self.run_gate([self.check([sys.executable, '-c', 'import sys; print(sys.argv[1])', '$(touch SHOULD_NOT_EXIST)'])])
        self.assertEqual(result['status'], 'passed')
        self.assertFalse((self.repo / 'SHOULD_NOT_EXIST').exists())

    def test_coverage_per_component_and_missing_inventory(self):
        changes = {'src/app.ts': {1, 2, 3, 4, 5}}
        report = {'src/app.ts': {1: True, 2: True, 3: True, 4: True, 5: False}}
        result = gate_reports.measure_coverage(self.repo, changes, report)
        self.assertEqual(result['percent'], 80)
        report['src/app.ts'][4] = False
        self.assertEqual(gate_reports.measure_coverage(self.repo, changes, report)['percent'], 60)
        self.assertEqual(gate_reports.measure_coverage(self.repo, changes, {})['missing_files'], ['src/app.ts'])

    def test_no_executable_lines(self):
        result = gate_reports.measure_coverage(self.repo, {'src/app.ts': {9}}, {'src/app.ts': {1: True}})
        self.assertEqual(result['executable'], 0)
        self.assertEqual(result['missing_files'], [])

    def test_changed_lines_includes_untracked(self):
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'baseline'], check=True)
        (self.repo / 'src/new.ts').write_text('const created = true;\n')
        (self.repo / 'src/app.ts').write_text('export const app = 2;\n')
        changes = gate_reports.changed_lines(self.repo, 'HEAD', ['src'])
        self.assertEqual(changes, {'src/new.ts': {1}, 'src/app.ts': {1}})

    def test_report_rejects_path_escape(self):
        path = self.repo / 'lcov.info'
        path.write_text('SF:../../outside.ts\nDA:1,1\n')
        with self.assertRaises(ValueError):
            gate_reports.coverage_lines([path], 'lcov')

    def test_optional_failed_sonar_does_not_pass_analysis(self):
        check = self.check([sys.executable, '-c', 'print("analysis unavailable")'], sonar={'report': '.ai/reports/sonar.json'}, required=False)
        result = self.run_gate([check])
        self.assertEqual(result['results'][0]['status'], 'blocked')
        self.assertEqual(result['status'], 'passed')

    def test_unconfigured_source_directory_blocks(self):
        (self.repo / 'stray.ts').write_text('export const unmanaged = 1;')
        result = self.run_gate([])
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['results'][0]['paths'], ['stray.ts'])

    def test_unknown_component_rejected(self):
        self.run_gate([])
        with self.assertRaises(ValueError):
            gates.run_gates(self.repo, component='typo')

    def test_task_bookkeeping_and_installer_backup_excluded(self):
        task = self.repo / 'task.md'
        task.write_text('---\nkind: task\nstatus: Not started\n---\n## Scope\nBuild.\n## Evidence\nNot run\n')
        before = gates.fingerprint(self.repo)
        task.write_text(task.read_text().replace('Not started', 'In progress').replace('Not run', 'Passed'))
        backup = self.repo / '.ai/install-backups/first/script.py'
        backup.parent.mkdir(parents=True)
        backup.write_text('old executable')
        self.assertEqual(before, gates.fingerprint(self.repo))

    def test_jacoco_default_package(self):
        report = self.repo / 'coverage.xml'
        report.write_text('<report><package name=""><sourcefile name="Foo.kt"><line nr="1" ci="1"/></sourcefile></package></report>')
        self.assertEqual(gate_reports.coverage_lines([report], 'jacoco', 'src'), {'src/Foo.kt': {1: True}})

    def test_browser_reports_are_output_not_source(self):
        code = "from pathlib import Path; p=Path('test-results'); p.mkdir(); (p/'junit.xml').write_text('<testsuite><testcase name=\"browser\"/></testsuite>')"
        check = self.check([sys.executable, '-c', code], test_report={'format': 'junit', 'glob': 'test-results/junit.xml'})
        self.assertEqual(self.run_gate([check])['status'], 'passed')

    def test_required_sonar_needs_proof_command(self):
        self.run_gate([])
        data = json.loads(self.registry.read_text())
        data['sonar'] = {'required': True}
        self.registry.write_text(json.dumps(data))
        self.assertEqual(gates.run_gates(self.repo, 'integration')['status'], 'blocked')

    def test_sonar_null_revision_cannot_pass(self):
        (self.repo / '.ai/reports').mkdir(parents=True)
        code = "from pathlib import Path; Path('.ai/reports/sonar.json').write_text('{\"revision\": null, \"status\": \"OK\"}')"
        check = self.check([sys.executable, '-c', code], sonar={'report': '.ai/reports/sonar.json'})
        self.assertEqual(self.run_gate([check])['status'], 'failed')

    def test_required_sonar_cannot_be_skipped_by_component_filter(self):
        checks = [dict(id='frontend-lint', component='frontend', stage='fast', argv=[sys.executable, '-c', 'pass']),
                  dict(id='backend-sonar', component='backend', stage='integration', argv=['missing-sonar'], sonar={'report': '.ai/reports/sonar.json'})]
        self.run_gate(checks)
        data = json.loads(self.registry.read_text())
        data['sonar'] = {'required': True}
        self.registry.write_text(json.dumps(data))
        self.assertEqual(gates.run_gates(self.repo, 'integration', component='frontend')['status'], 'blocked')

    def test_empty_or_unresolved_security_inventory_blocks(self):
        self.assertEqual(gates.scanner_summary(b'{"results":[]}', 'osv-json')['status'], 'blocked')
        incomplete = b'{"results":[{"packages":[{"package":{"name":"unknown"}}]}]}'
        self.assertEqual(gates.scanner_summary(incomplete, 'osv-json')['status'], 'blocked')
        self.assertEqual(gates.scanner_summary(b'{"results":[],"errors":[],"paths":{"scanned":[]}}', 'semgrep-json')['status'], 'blocked')
        self.assertEqual(gates.scanner_summary(b'not-json', 'semgrep-json')['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
