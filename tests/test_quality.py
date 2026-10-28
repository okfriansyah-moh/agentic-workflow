import copy
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from agent_workflow import gate_selection, quality


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.started = datetime.now(timezone.utc).isoformat()
        (self.repo / 'src').mkdir()
        (self.repo / 'src/app.ts').write_text('export const n = 1;\n')
        (self.repo / 'tests.ts').write_text('test behavior\n')
        (self.repo / 'docker.lock').write_text('image@sha256:' + 'a' * 64)
        (self.repo / 'unit.lcov').write_text('SF:src/app.ts\nDA:1,1\nend_of_record\n')
        (self.repo / 'tests.xml').write_text('<testsuite><testcase name="behavior"/></testsuite>')
        self.analyzer = {'status': 'SUCCESS', 'gate': 'OK', 'analysis_id': 'analysis-1',
                         'lines': {'covered': 8, 'total': 10}, 'conditions': {'covered': 8, 'total': 10},
                         'security_issues': 0, 'reliability_issues': 0, 'duplicated_lines': 0,
                         'duplicated_blocks': 0, 'classifications': [], 'classified_issue_ids': []}
        (self.repo / 'analyzer.json').write_text(json.dumps(self.analyzer))
        self.contract = {'id': 'app', 'production': ['src/*.ts'], 'inputs': ['src/*.ts', 'tests.ts'],
                         'toolchain_files': ['docker.lock'], 'commands': [['docker', 'compose', 'run', 'unit']],
                         'roots': ['src'], 'unit_report': {'format': 'lcov', 'reports': ['unit.lcov']},
                         'test_report': {'format': 'junit', 'glob': 'tests.xml'}}
        self.proof = {'measured_at': self.started, 'revision': 'measured-commit',
                      'contract_sha256': gate_selection.digest(self.contract),
                      'execution': {'runtime': 'docker', 'images': ['image@sha256:' + 'a' * 64],
                                    'memory_bytes': 1024, 'workers': 1, 'tests_separate_from_analysis': True},
                      'inputs': quality.snapshot(self.repo, self.contract['inputs']),
                      'toolchain_files': quality.snapshot(self.repo, ['docker.lock']),
                      'commands': self.contract['commands'], 'production_files': ['src/app.ts'],
                      'reports': quality.snapshot(self.repo, ['unit.lcov', 'tests.xml', 'analyzer.json']),
                      'unit': {'kind': 'unit', 'lines': {'covered': 1, 'total': 1},
                               'tests': {'executed': 1, 'failures': 0, 'skipped': 0}},
                      'changed': {'base': 'base', 'covered': 1, 'total': 1, 'missing_files': []},
                      'analyzer_report': 'analyzer.json', 'producer_report': 'producer.json', 'analyzer': self.analyzer}
        self.refresh_reports()
        self.changes = patch.object(quality.gate_reports, 'changed_lines', return_value={'src/app.ts': {1}})
        self.changes.start()
        self.addCleanup(self.changes.stop)

    def validate(self):
        return quality.validate_component(self.repo, self.contract, self.proof, 'base')

    def refresh_reports(self):
        receipt = {key: self.proof[key] for key in ('inputs', 'toolchain_files', 'commands', 'contract_sha256', 'revision', 'measured_at')}
        receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
        receipt['unit_reports'] = quality.snapshot(self.repo, ['unit.lcov', 'tests.xml'])
        (self.repo / 'producer.json').write_text(json.dumps(receipt))
        self.analyzer['input_sha256'] = gate_selection.digest(self.proof['inputs'])
        self.analyzer['producer_sha256'] = hashlib.sha256((self.repo / 'producer.json').read_bytes()).hexdigest()
        (self.repo / 'analyzer.json').write_text(json.dumps(self.analyzer))
        self.proof['reports'] = quality.snapshot(self.repo, ['unit.lcov', 'tests.xml', 'analyzer.json', 'producer.json'])

    def test_valid_retained_measurement_reuses_after_metadata_changes(self):
        self.validate()
        (self.repo / 'README.md').write_text('New documentation')
        self.validate()

    def test_source_tests_toolchain_and_command_changes_invalidate(self):
        for path in ('src/app.ts', 'tests.ts', 'docker.lock'):
            original = (self.repo / path).read_text()
            (self.repo / path).write_text(original + 'changed')
            with self.assertRaises(ValueError):
                self.validate()
            (self.repo / path).write_text(original)
        self.proof['commands'] = [['true']]
        with self.assertRaises(ValueError):
            self.validate()

    def test_rounded_duplication_does_not_hide_a_single_line(self):
        self.analyzer['duplicated_lines'] = 1
        self.refresh_reports()
        with self.assertRaisesRegex(ValueError, 'exactly zero'):
            self.validate()

    def test_analyzer_incomplete_failed_or_low_combined_blocks(self):
        for key, value in [('status', 'PENDING'), ('gate', 'ERROR'), ('conditions', {'covered': 0, 'total': 100})]:
            old = self.analyzer[key]
            self.analyzer[key] = value
            self.refresh_reports()
            with self.assertRaises(ValueError):
                self.validate()
            self.analyzer[key] = old

    def test_boolean_normalized_native_counters_block(self):
        for value, key in [(self.proof['unit']['lines'], 'covered'),
                           (self.proof['unit']['tests'], 'executed'),
                           (self.proof['changed'], 'covered')]:
            old = value[key]
            value[key] = True
            with self.assertRaises(ValueError):
                self.validate()
            value[key] = old

    def test_invalid_counters(self):
        for covered in (True, -1, 1.5, 11):
            self.analyzer['lines']['covered'] = covered
            self.refresh_reports()
            with self.assertRaises(ValueError):
                self.validate()

    def test_failed_and_empty_suites(self):
        for xml in ('<testsuite/>', '<testsuite><testcase><failure/></testcase></testsuite>'):
            (self.repo / 'tests.xml').write_text(xml)
            self.refresh_reports()
            with self.assertRaises(ValueError):
                self.validate()

    def test_missing_untested_production_file_blocks(self):
        (self.repo / 'src/new.ts').write_text('export const untested = 1;')
        self.proof['inputs'] = quality.snapshot(self.repo, self.contract['inputs'])
        self.proof['production_files'].append('src/new.ts')
        self.refresh_reports()
        with self.assertRaisesRegex(ValueError, 'instrumentation'):
            self.validate()

    def test_native_unit_below_80_blocks(self):
        (self.repo / 'unit.lcov').write_text('SF:src/app.ts\nDA:1,0\nend_of_record\n')
        self.proof['unit']['lines']['covered'] = 0
        self.refresh_reports()
        with self.assertRaisesRegex(ValueError, 'below 80'):
            self.validate()

    def test_raw_analyzer_mismatch_and_missing_artifact(self):
        self.proof['analyzer'] = dict(self.analyzer, security_issues=1)
        with self.assertRaisesRegex(ValueError, 'retained report'):
            self.validate()
        (self.repo / 'analyzer.json').unlink()
        with self.assertRaises(ValueError):
            self.validate()

    def test_invalid_false_positive_review(self):
        self.analyzer['classifications'] = [{'status': 'FALSE_POSITIVE'}]
        self.refresh_reports()
        with self.assertRaisesRegex(ValueError, 'review evidence'):
            self.validate()

    def test_omitted_component_and_weak_component_cannot_average(self):
        registry = {'runtime_components': ['app', 'other'], 'quality': {'schema_version': 1, 'required': True,
                    'proof': 'proof.json', 'components': [self.contract]}}
        self.assertEqual(quality.results(self.repo, registry, 'base')[0]['status'], 'blocked')
        self.assertEqual(quality.results(self.repo, registry, 'base', set()), [])

    def test_changed_base_and_stale_measurement(self):
        self.proof['changed']['base'] = 'different'
        with self.assertRaises(ValueError):
            self.validate()
        self.proof['measured_at'] = '2000-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.validate()

    def test_rewrapping_older_reports_with_new_inputs_is_rejected(self):
        receipt = json.loads((self.repo / 'producer.json').read_text())
        receipt['inputs'] = {'src/app.ts': 'invented'}
        (self.repo / 'producer.json').write_text(json.dumps(receipt))
        self.proof['reports'] = quality.snapshot(self.repo, ['unit.lcov', 'tests.xml', 'analyzer.json', 'producer.json'])
        with self.assertRaisesRegex(ValueError, 'Producer provenance'):
            self.validate()

    def test_analyzer_must_reference_same_unit_measurement(self):
        self.analyzer['producer_sha256'] = 'different-measurement'
        (self.repo / 'analyzer.json').write_text(json.dumps(self.analyzer))
        self.proof['reports'] = quality.snapshot(self.repo, ['unit.lcov', 'tests.xml', 'analyzer.json', 'producer.json'])
        with self.assertRaisesRegex(ValueError, 'unit receipt'):
            self.validate()

    def test_invalid_raw_coverage_counters(self):
        for entry in ('DA:1,-1', 'DA:0,1'):
            (self.repo / 'unit.lcov').write_text(f'SF:src/app.ts\n{entry}\nend_of_record\n')
            self.refresh_reports()
            with self.assertRaises(ValueError):
                self.validate()

    def test_invalid_raw_test_counters(self):
        (self.repo / 'vitest.json').write_text(json.dumps({'numPassedTests': -1, 'numFailedTests': 0}))
        with self.assertRaises(ValueError):
            quality.gate_reports.test_summary([self.repo / 'vitest.json'], 'vitest')

    def test_changed_coverage_measures_every_supported_runtime_suffix(self):
        for suffix in quality.gate_reports.SOURCE_SUFFIXES:
            name = 'src/runtime' + suffix
            measured = quality.gate_reports.measure_coverage(self.repo, {name: {1}}, {name: {1: False}})
            self.assertEqual(measured['executable'], 1, suffix)
            self.assertEqual(measured['covered'], 0, suffix)
            with self.assertRaisesRegex(ValueError, 'below 80'):
                quality.ratio({'covered': measured['covered'], 'total': measured['executable']}, 'Changed')

    def test_uninstrumented_python_change_is_missing(self):
        measured = quality.gate_reports.measure_coverage(self.repo, {'src/runtime.py': {1}}, {})
        self.assertEqual(measured['missing_files'], ['src/runtime.py'])

    def test_missing_or_unreviewed_analyzer_dispositions_block(self):
        del self.analyzer['classified_issue_ids']
        self.refresh_reports()
        with self.assertRaises(KeyError):
            self.validate()
        self.analyzer['classified_issue_ids'] = ['unreviewed-issue']
        self.refresh_reports()
        with self.assertRaisesRegex(ValueError, 'disposition inventory'):
            self.validate()

    def test_changed_coverage_measures_any_instrumented_runtime_language(self):
        measured = quality.gate_reports.measure_coverage(self.repo, {'src/app.php': {1}}, {'src/app.php': {1: False}})
        self.assertEqual(measured['executable'], 1)
        self.assertEqual(measured['covered'], 0)
        with self.assertRaisesRegex(ValueError, 'below 80'):
            quality.ratio({'covered': measured['covered'], 'total': measured['executable']}, 'Changed')
