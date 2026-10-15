"""Autonomy diagnostics inspect safe defaults without changing a host or its policy."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_workflow.autonomy import autonomy_diagnostics


class AutonomyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve() / 'home'
        self.repo = self.home / 'project'
        self.repo.mkdir(parents=True)
        policy = patch('agent_workflow.autonomy.MANAGED_CLAUDE_SETTINGS', self.home / 'managed-settings.json')
        policy.start()
        self.addCleanup(policy.stop)

    def write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content))

    def diagnose(self, host, env=None):
        return autonomy_diagnostics(host, self.home, self.repo, environ=env or {})

    def test_codex_defaults_profiles_and_parent_project_sources_are_separate(self):
        user = self.home / '.codex/config.toml'
        self.write(user, 'approval_policy="never"\nsandbox_mode="danger-full-access"\n[profiles.review]\napproval_policy="on-request"\n')
        project = self.repo / '.codex/config.toml'
        self.write(project, 'approval_policy="untrusted"\n')
        before = user.read_bytes(), project.read_bytes()
        with patch('subprocess.Popen', side_effect=AssertionError('doctor cannot launch hosts')):
            result = self.diagnose('codex')
        self.assertEqual(result['configuration']['status'], 'unattended')
        self.assertEqual(result['configuration']['sources']['approval_policy'], str(user))
        self.assertTrue(any(item['layer'] == 'profile' and item['settings']['approval_policy'] == 'on-request' for item in result['candidates']))
        self.assertTrue(any(item['path'] == str(project) and item['settings']['approval_policy'] == 'untrusted' for item in result['candidates']))
        self.assertEqual(result['live_verification']['status'], 'unverified')
        self.assertEqual((user.read_bytes(), project.read_bytes()), before)

    def test_codex_home_override_reads_only_selected_user_file(self):
        alternative = self.home / 'alternative'
        self.write(alternative / 'config.toml', 'approval_policy="never"\nsandbox_mode="danger-full-access"\n')
        self.write(self.home / '.codex/config.toml', 'approval_policy="untrusted"\n')
        result = self.diagnose('codex', {'CODEX_HOME': str(alternative)})
        self.assertEqual(result['configuration']['status'], 'unattended')
        self.assertEqual(result['configuration']['sources']['approval_policy'], str(alternative / 'config.toml'))

    def test_claude_layers_and_private_rules(self):
        self.write(self.home / '.claude/settings.json', {'permissions': {'defaultMode': 'bypassPermissions'}})
        self.write(self.repo / '.claude/settings.json', {'permissions': {'defaultMode': 'plan'}})
        self.write(self.repo / '.claude/settings.local.json', {'permissions': {'defaultMode': 'acceptEdits', 'deny': ['private-rule-secret']}})
        result = self.diagnose('claude')
        self.assertEqual(result['configuration']['status'], 'restricted')
        self.assertEqual(result['configuration']['observed_defaults']['defaultMode'], 'acceptEdits')
        self.assertEqual(next(item for item in result['candidates'] if item['layer'] == 'project-local')['permission_rule_counts']['deny'], 1)
        self.assertNotIn('private-rule-secret', json.dumps(result))

    def test_claude_managed_default_overrides_project_local(self):
        self.write(self.home / '.claude/settings.json', {'permissions': {'defaultMode': 'bypassPermissions'}})
        self.write(self.home / 'managed-settings.json', {'permissions': {'defaultMode': 'plan'}})
        result = self.diagnose('claude')
        self.assertEqual(result['configuration']['status'], 'restricted')
        self.assertEqual(result['configuration']['observed_defaults']['defaultMode'], 'plan')
        self.assertEqual(result['configuration']['sources']['defaultMode'], str(self.home / 'managed-settings.json'))

    def test_claude_managed_bypass_restriction_is_not_unattended(self):
        self.write(self.home / '.claude/settings.json', {'permissions': {'defaultMode': 'bypassPermissions'}})
        self.write(self.home / 'managed-settings.json', {'permissions': {'disableBypassPermissionsMode': 'disable'}})
        self.assertEqual(self.diagnose('claude')['configuration']['status'], 'restricted')

    def test_copilot_uses_current_user_settings_and_home_override(self):
        directory = self.home / 'copilot-user'
        self.write(directory / 'config.json', '// internal JSONC is not user settings\n{"secret":"private-data"}')
        self.write(directory / 'settings.json', {'defaultPermissionMode': 'allow-all', 'defaultMode': 'autopilot', 'token': 'private-data'})
        result = self.diagnose('copilot', {'COPILOT_HOME': str(directory)})
        self.assertEqual(result['configuration']['status'], 'unattended')
        self.assertEqual(len(result['candidates']), 1)
        self.assertNotIn('private-data', json.dumps(result))

    def test_cursor_desktop_does_not_prove_cli_or_live_behavior(self):
        self.write(self.home / '.cursor/permissions.json', {'approvalMode': 'unrestricted'})
        self.write(self.home / '.cursor/cli-config.json', {'approvalMode': 'allowlist', 'sandbox': {'mode': 'disabled'}})
        result = self.diagnose('cursor')
        self.assertEqual(result['desktop_configuration']['status'], 'unattended')
        self.assertEqual(result['configuration']['status'], 'restricted')
        self.assertEqual(result['live_verification']['status'], 'unverified')
        self.write(self.home / '.cursor/cli-config.json', {'approvalMode': 'unrestricted'})
        self.assertEqual(self.diagnose('cursor')['configuration']['status'], 'unknown')

    def test_invalid_and_unrecognized_inputs_never_leak_contents(self):
        self.write(self.home / '.cursor/cli-config.json', '{"approvalMode":"private-secret", "sandbox":{"mode":"disabled"}}')
        self.write(self.home / '.cursor/permissions.json', '{invalid private-secret')
        result = self.diagnose('cursor')
        self.assertEqual(result['configuration']['status'], 'unknown')
        self.assertEqual(result['desktop_configuration']['status'], 'unknown')
        self.assertNotIn('private-secret', json.dumps(result))

    def test_missing_files_remain_unknown_for_all_hosts(self):
        for host in ('codex', 'claude', 'copilot', 'cursor'):
            with self.subTest(host=host):
                self.assertEqual(self.diagnose(host)['configuration']['status'], 'unknown')
