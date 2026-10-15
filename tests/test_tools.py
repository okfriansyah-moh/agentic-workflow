"""Behavioral lifecycle tests use temporary homes and never launch a scan."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from agent_workflow import tools, tool_config, tool_runtime as runtime


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.parser = argparse.ArgumentParser()
        tools.register(self.parser.add_subparsers(required=True))

    def command(self, *values):
        args = self.parser.parse_args(['tools', *values, '--home', str(self.home)])
        return args.handler(args)

    def fake_provision(self, name, home, node=None, python=None):
        target = runtime.safe_path(home, '.local/share/agent-workflow/tools/runtimes/' + name)
        target.mkdir(parents=True)
        script = target / 'fixture.py'
        script.write_text('print("fixture tool")\n')
        return {'name': name, 'version': runtime.read_lock()[name]['version'], 'path': str(target),
                'tree_sha256': runtime.tree_digest(target), 'argv': [sys.executable, str(script)],
                'environment': {}, 'capability': 'fixture-executable'}

    def install_fake(self, name='playwright-cli'):
        with patch.object(runtime, 'provision', side_effect=self.fake_provision):
            return self.command('install', name)

    def test_runtime_install_reuse_execute_and_remove(self):
        first = self.install_fake()
        self.assertEqual(first['status'], 'ok')
        binary = self.home / '.local/bin/playwright-cli'
        self.assertEqual(subprocess.check_output([str(binary)], text=True).strip(), 'fixture tool')
        with patch.object(runtime, 'provision', side_effect=AssertionError('Unexpected download')):
            self.assertTrue(self.command('install', 'playwright-cli')['tools'][0]['reused'])
        self.assertEqual(self.command('status', 'playwright-cli')['status'], 'ok')
        self.assertEqual(self.command('remove', 'playwright-cli')['status'], 'ok')
        self.assertFalse(binary.exists())
        self.assertEqual(self.command('remove', 'playwright-cli')['tools'][0]['status'], 'already-absent')

    def test_unowned_binary_preserved(self):
        binary = self.home / '.local/bin/strix'
        binary.parent.mkdir(parents=True)
        binary.write_text('personal launcher')
        with patch.object(runtime, 'provision') as download, self.assertRaises(ValueError):
            self.command('install', 'strix')
        download.assert_not_called()
        self.assertEqual(binary.read_text(), 'personal launcher')

    def test_modified_runtime_blocks_status_and_removal(self):
        self.install_fake()
        record = tools.read_state(self.home)['tools']['playwright-cli']
        (Path(record['path']) / 'fixture.py').write_text('personal edit')
        self.assertEqual(self.command('status', 'playwright-cli')['status'], 'blocked')
        self.assertEqual(self.command('remove', 'playwright-cli')['status'], 'blocked')
        self.assertTrue(Path(record['path']).is_dir())

    def test_modified_launcher_is_preserved(self):
        self.install_fake('strix')
        binary = self.home / '.local/bin/strix'
        binary.write_text('personal launcher update')
        self.assertEqual(self.command('remove', 'strix')['status'], 'blocked')
        self.assertEqual(binary.read_text(), 'personal launcher update')

    def test_publication_failure_rolls_back_runtime_and_launcher(self):
        with patch.object(runtime, 'provision', side_effect=self.fake_provision), \
             patch.object(runtime, 'write_json', side_effect=OSError('fixture disk full')):
            with self.assertRaises(OSError):
                self.command('install', 'playwright-cli')
        self.assertFalse((self.home / '.local/bin/playwright-cli').exists())
        self.assertFalse((self.home / '.local/share/agent-workflow/tools/runtimes/playwright-cli').exists())

    def test_provision_failure_removes_only_new_runtime(self):
        existing = self.home / '.local/share/agent-workflow/tools/runtimes/unrelated'
        existing.mkdir(parents=True)
        with patch.object(runtime, 'install_strix', side_effect=RuntimeError('fixture installer failure')):
            with self.assertRaises(RuntimeError):
                runtime.provision('strix', self.home)
        self.assertEqual(list(existing.parent.iterdir()), [existing])

    def test_symlink_destination_rejected(self):
        outside = self.home / 'personal'
        outside.mkdir()
        (self.home / '.local').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.command('install', 'context7')
        self.assertEqual(list(outside.iterdir()), [])

    def test_unrelated_mcp_fields_survive_install_repeat_and_remove(self):
        path = self.home / '.claude.json'
        original = {'personal_setting': 'fixture-secret', 'mcpServers': {'personal': {'command': 'custom'}}}
        path.write_text(json.dumps(original))
        self.command('install', 'context7')
        first = tools.read_state(self.home)
        self.assertEqual(len(first['context7']), 4)
        self.assertNotIn('fixture-secret', json.dumps(first))
        self.command('install', 'context7')
        self.assertEqual(first, tools.read_state(self.home))
        added = json.loads(path.read_text())
        added['later_setting'] = True
        path.write_text(json.dumps(added))
        self.command('remove', 'context7')
        self.assertEqual(json.loads(path.read_text()), {**original, 'later_setting': True})

    def test_toml_unrelated_text_preserved(self):
        path = self.home / '.codex/config.toml'
        path.parent.mkdir()
        initial = '# personal\nmodel = "inherited"\n[mcp_servers.personal]\ncommand = "test"\n'
        path.write_text(initial)
        self.command('install', 'context7')
        path.write_text(path.read_text() + '\n# later personal note\n')
        self.command('remove', 'context7')
        self.assertTrue(path.read_text().startswith(initial))
        self.assertIn('# later personal note', path.read_text())
        self.assertNotIn('mcp_servers.context7', path.read_text())

    def test_existing_different_context7_aborts_without_changes(self):
        path = self.home / '.cursor/mcp.json'
        path.parent.mkdir()
        path.write_text('{"mcpServers":{"context7":{"url":"https://existing.test"}}}')
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            self.command('install', 'context7')
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.home / '.codex/config.toml').exists())

    def test_existing_matching_context7_is_unowned_and_preserved(self):
        config = tool_config.configs(self.home)[1]
        path = Path(config['path'])
        path.write_text(json.dumps({'mcpServers': {'context7': config['value']}}))
        self.command('install', 'context7')
        self.command('remove', 'context7')
        self.assertEqual(json.loads(path.read_text())['mcpServers']['context7'], config['value'])

    def test_context_config_transaction_rolls_back_partial_write(self):
        original_write = tool_config.write_text
        count = 0
        def failing_write(path, text):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('fixture write failure')
            return original_write(path, text)
        with patch.object(tool_config, 'write_text', side_effect=failing_write), self.assertRaises(OSError):
            self.command('install', 'context7')
        self.assertFalse((self.home / '.codex/config.toml').exists())
        self.assertFalse((self.home / '.claude.json').exists())
        self.assertEqual(tools.read_state(self.home)['context7'], [])

    def test_context_state_failure_restores_owned_fields_only(self):
        original = {'personal': True}
        path = self.home / '.claude.json'
        path.write_text(json.dumps(original))
        with patch.object(runtime, 'write_json', side_effect=OSError('fixture disk full')), self.assertRaises(OSError):
            self.command('install', 'context7')
        self.assertEqual(json.loads(path.read_text()), original)
        self.assertFalse((self.home / '.codex/config.toml').exists())

    def test_modified_context_field_preserved(self):
        self.command('install', 'context7')
        path = self.home / '.cursor/mcp.json'
        data = json.loads(path.read_text())
        data['mcpServers']['context7']['url'] = 'https://personal.test'
        path.write_text(json.dumps(data))
        self.assertEqual(self.command('remove', 'context7')['status'], 'blocked')
        self.assertEqual(json.loads(path.read_text()), data)

    def test_global_and_repo_scope_are_independent(self):
        repo = self.home / 'repository'
        repo.mkdir()
        self.command('install', 'context7')
        self.command('install', 'context7', '--repo', str(repo))
        self.assertEqual(len(tools.read_state(self.home)['context7']), 8)
        self.assertTrue((repo / '.github/mcp.json').is_file())
        self.assertTrue((repo / '.mcp.json').is_file())
        self.command('remove', 'context7', '--repo', str(repo))
        self.assertEqual(self.command('status', 'context7')['status'], 'ok')
        self.assertFalse((repo / '.mcp.json').exists())

    def test_http_auth_and_rate_limits_are_not_passes(self):
        for code, expected in [(401, 'authentication-required'), (403, 'access-denied'), (429, 'rate-limited')]:
            error = urllib.error.HTTPError('https://fixture.test', code, 'fixture', {}, None)
            with patch.object(tool_config, 'rpc_request', side_effect=error):
                result = tool_config.probe_context7()
            self.assertEqual(result['status'], expected)
            self.assertEqual(result['http_status'], code)

    def test_anonymous_probe_never_claims_oauth_success(self):
        responses = [({'result': {}}, None), ({}, None),
                     ({'result': {'tools': [{'name': 'resolve-library-id'}, {'name': 'query-docs'}, {'name': 'untrusted-name'}]}}, None)]
        with patch.dict(os.environ, {}, clear=True), patch.object(tool_config, 'rpc_request', side_effect=responses):
            result = tool_config.probe_context7()
        self.assertEqual(result['status'], 'reachable')
        self.assertEqual(result['authentication'], 'anonymous')
        self.assertFalse(result['host_oauth_verified'])
        self.assertNotIn('untrusted-name', json.dumps(result))

    def test_strix_preflight_only_reads_docker_and_environment(self):
        self.install_fake('strix')
        with patch.dict(os.environ, {}, clear=True), patch('shutil.which', return_value='/fake/docker'), \
             patch.object(runtime, 'run', return_value='29.8.2') as executed:
            result = self.command('strix-preflight')
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['scan_executed'])
        self.assertFalse(result['provider_key_in_environment'])
        self.assertEqual(executed.call_args.args[0], ['/fake/docker', 'info', '--format', '{{.ServerVersion}}'])

    def report_fixture(self, status='completed', target='https://authorized.test'):
        path = self.home / 'vulnerabilities.json'
        path.write_text(json.dumps([{'id': 'vuln-0001', 'severity': 'high', 'evidence': 'fixture-private-detail'}]))
        path.with_name('run.json').write_text(json.dumps({'status': status, 'end_time': '2026-10-15T01:00:00Z',
                                                       'targets_info': [{'original': target}]}))
        return path

    def test_strix_report_ingestion_never_executes_or_claims_acceptance(self):
        path = self.report_fixture()
        args = self.parser.parse_args(['tools', 'strix-report', '--report', str(path), '--target', 'https://authorized.test'])
        with patch.object(runtime, 'run', side_effect=AssertionError('No execution allowed')):
            result = args.handler(args)
        self.assertEqual(result['findings'], 1)
        self.assertEqual(result['severity_counts']['high'], 1)
        self.assertFalse(result['scan_executed'])
        self.assertFalse(result['acceptance_pass'])
        self.assertNotIn('fixture-private-detail', json.dumps(result))

    def test_strix_report_requires_complete_matching_scope(self):
        for status, target in [('failed', 'https://authorized.test'), ('completed', 'https://other.test')]:
            path = self.report_fixture(status, target)
            args = argparse.Namespace(report=str(path), target='https://authorized.test')
            with self.assertRaises(ValueError):
                tools.strix_report(args)

    def test_missing_tools_are_blocked_and_no_scan_command_exists(self):
        self.assertEqual(self.command('status')['status'], 'blocked')
        operations = next(action for action in self.parser._actions if isinstance(action, argparse._SubParsersAction))
        tool_parser = operations.choices['tools']
        sub = next(action for action in tool_parser._actions if isinstance(action, argparse._SubParsersAction))
        self.assertNotIn('scan', sub.choices)

    def test_lock_contains_exact_versions_and_valid_digest(self):
        lock = runtime.read_lock()
        self.assertEqual(runtime.digest(lock['strix']['requirements'].encode()), lock['strix']['requirements_sha256'])
        for name, package in lock['playwright-cli']['package_lock']['packages'].items():
            if name:
                self.assertTrue(package['integrity'].startswith('sha512-'))
                self.assertTrue(package['resolved'].startswith('https://registry.npmjs.org/'))
                self.assertFalse(any(char in package['version'] for char in ('^', '~', '*')))
        self.assertFalse(json.loads((runtime.ROOT / 'profiles/tools.json').read_text())['tools']['strix']['default_scan_enabled'])

    def test_run_hides_failed_command_output(self):
        result = subprocess.CompletedProcess(['fixture'], 2, stdout='fixture-secret', stderr='fixture-secret')
        with patch('subprocess.run', return_value=result):
            with self.assertRaises(RuntimeError) as failure:
                runtime.run(['fixture'])
        self.assertNotIn('fixture-secret', str(failure.exception))


if __name__ == '__main__':
    unittest.main()
