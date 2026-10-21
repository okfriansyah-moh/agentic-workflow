from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from agent_workflow.host_probes import (blank_results, claude_metadata, copilot_metadata, delegation_graph_result, delegation_observation, json_events, native_edit_events, native_hook_events,
                                       native_skills, redact, role_observation, run_command, sha256_file,
                                       smoke_argv, smoke_prompt)
from agent_workflow.host_verification import (CLAUDE_CONFIG_DEFAULTS, check_verification_freshness, claude_user_config_digest, config_snapshot, create_fixture, cursor_runtime_inputs, fixture_snapshot, import_ui_evidence,
                                             json_hash, read_json, selected_bundle, summarize_host_verifications,
                                             runtime_support_inputs, support_identity, verification_status, verify_host, verify_one, write_json, _hook_verdict)


class ProbeParserTests(unittest.TestCase):
    def test_final_assistant_prose_cannot_establish_role(self):
        for host in ('codex', 'claude', 'copilot'):
            self.assertEqual(role_observation(host, [{'type': 'assistant', 'text': 'aw-review-verify passed'}], 'aw-review-verify')['status'], 'blocked')

    def test_codex_requires_native_child_role_identity(self):
        event = {'method': 'thread/started', 'params': {'thread': {'id': 'child', 'agentRole': 'aw-review-verify', 'parentThreadId': 'parent'}}}
        self.assertEqual(role_observation('codex', [event], 'aw-review-verify')['status'], 'passed')
        del event['params']['thread']['parentThreadId']
        self.assertEqual(role_observation('codex', [event], 'aw-review-verify')['status'], 'blocked')

    def test_claude_role_requires_tool_completion(self):
        start = {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'call1', 'name': 'Agent', 'input': {'subagent_type': 'aw-review-verify'}}]}}
        end = {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'call1', 'content': 'Actual native worker result'}]}}
        self.assertEqual(role_observation('claude', [start], 'aw-review-verify')['status'], 'blocked')
        self.assertEqual(role_observation('claude', [start, end], 'aw-review-verify')['status'], 'passed')
        end['message']['content'][0]['is_error'] = True
        self.assertEqual(role_observation('claude', [start, end], 'aw-review-verify')['status'], 'blocked')

    def test_copilot_discovery_requires_enabled_native_entries_and_scope(self):
        entries = [{'name': 'forge', 'enabled': True, 'path': '/tmp/fixture/.github/skills/forge', 'source': 'project'}]
        self.assertEqual(native_skills('copilot', entries, ['forge'], 'repo', '/tmp/fixture')['status'], 'passed')
        self.assertEqual(native_skills('copilot', entries, ['forge', 'missing'], 'repo', '/tmp/fixture')['status'], 'failed')
        self.assertEqual(native_skills('copilot', entries, ['forge'], 'repo', '/other/fixture')['status'], 'blocked')
        entries[0]['enabled'] = False
        self.assertEqual(native_skills('copilot', entries, ['forge'], 'global', '/tmp/fixture')['status'], 'failed')
        entries.append({'name': 'forge', 'enabled': True, 'path': '/home/.copilot/skills/forge'})
        self.assertEqual(native_skills('copilot', entries, ['forge'], 'repo', '/tmp/fixture')['status'], 'blocked')
        entries = [{'name': 'forge', 'enabled': True, 'path': '/tmp/fixture/../outside/forge'}]
        self.assertEqual(native_skills('copilot', entries, ['forge'], 'repo', '/tmp/fixture')['status'], 'blocked')

    def test_claude_metadata_uses_system_init_only(self):
        assistant = {'type': 'assistant', 'agents': ['aw-forge'], 'skills': ['forge']}
        self.assertEqual(claude_metadata([assistant], ['aw-forge'], ['forge']), {})
        event = {'type': 'system', 'subtype': 'init', 'agents': ['aw-forge'], 'skills': ['forge']}
        self.assertEqual(claude_metadata([event], ['aw-forge'], ['forge'])['skills']['status'], 'passed')
        scoped = claude_metadata([event], ['aw-forge'], ['forge'], 'repo', '/fixture')['skills']
        self.assertEqual(scoped['status'], 'blocked')
        self.assertEqual(scoped['availability'], 'passed')

    def test_edit_completion_requires_native_file_tool_for_fixture_path(self):
        event = {'type': 'item.completed', 'item': {'id': 'change1', 'type': 'file_change', 'status': 'completed', 'changes': [{'path': 'smoke.json'}]}}
        self.assertEqual(native_edit_events('codex', [event], '/tmp/fixture'), ['change1'])
        event['item']['changes'][0]['path'] = 'other.json'
        self.assertEqual(native_edit_events('codex', [event], '/tmp/fixture'), [])
        self.assertEqual(native_edit_events('codex', [{'type': 'assistant', 'text': 'I edited smoke.json'}], '/tmp/fixture'), [])

    def test_native_hook_event_parser_ignores_assistant_claims(self):
        self.assertEqual(native_hook_events('codex', [{'type': 'assistant', 'text': 'hook completed'}]), [])
        native = {'method': 'hook/completed', 'params': {'run': {'id': 'event1', 'eventName': 'postToolUse', 'status': 'completed', 'sourcePath': '/tmp/fixture/.codex/hooks.json'}}}
        self.assertEqual(native_hook_events('codex', [native])[0]['id'], 'event1')

    def test_no_bypass_or_model_override_in_bounded_native_commands(self):
        for host in ('codex', 'claude', 'copilot'):
            args = smoke_argv(host, '/runtime', '/fixture', 'Bounded prompt')
            self.assertFalse(any('bypass' in item or item in ('--model', '--allow-all', '--allow-all-tools', '--yolo') for item in args))
        with self.assertRaises(ValueError):
            smoke_argv('cursor', '/runtime', '/fixture', 'prompt')

    def test_unattended_native_permissions_require_explicit_flag(self):
        args = smoke_argv('copilot', '/runtime', '/fixture', 'prompt', unattended_authorized=True)
        self.assertIn('--allow-all', args)
        self.assertNotIn('--deny-tool', args)
        self.assertEqual(args[args.index('--max-ai-credits') + 1], '30')
        args = smoke_argv('claude', '/runtime', '/fixture', 'prompt', unattended_authorized=True)
        self.assertEqual(args[args.index('--permission-mode') + 1], 'bypassPermissions')
        self.assertNotIn('--disallowedTools', args)
        self.assertEqual(args[args.index('--max-budget-usd') + 1], '2.00')
        for host in ('claude', 'copilot'):
            args = smoke_argv(host, '/runtime', '/fixture', 'prompt')
            self.assertNotIn('--allow-all', args)
            self.assertNotIn('bypassPermissions', args)

    def test_native_limits_allow_persisted_delegation_with_supported_bounds(self):
        args = smoke_argv('codex', '/runtime', '/fixture', 'prompt')
        self.assertNotIn('--ephemeral', args)
        self.assertEqual(args[1], 'exec')
        args = smoke_argv('claude', '/runtime', '/fixture', 'prompt')
        self.assertEqual(args[args.index('--max-budget-usd') + 1], '2.00')
        args = smoke_argv('copilot', '/runtime', '/fixture', 'prompt')
        self.assertEqual(args[args.index('--max-ai-credits') + 1], '30')

    def test_permission_grants_cover_one_fixture_file_and_named_reviewer(self):
        args = smoke_argv('claude', '/runtime', '/fixture', 'prompt')
        grants = args[args.index('--allowedTools') + 1]
        self.assertIn('Read(//fixture/smoke.json)', grants)
        self.assertIn('Edit(//fixture/smoke.json) Agent(aw-backend) Agent(aw-review-verify)', grants)
        self.assertIn('Bash', args)
        self.assertEqual(args[args.index('--agent') + 1], 'aw-forge')
        self.assertIn('--forward-subagent-text', args)
        args = smoke_argv('copilot', '/runtime', '/fixture', 'prompt')
        self.assertIn('write(/fixture/smoke.json)', args)
        self.assertIn('read(/fixture/smoke.json)', args)
        self.assertIn('--deny-tool', args)
        self.assertNotIn('write', args)
        self.assertEqual(args[args.index('--agent') + 1], 'aw-forge')
        args = smoke_argv('claude', '/runtime', '/fixture', 'prompt', 'aw-backend')
        self.assertEqual(args[args.index('--agent') + 1], 'aw-backend')

    def test_smoke_brief_assigns_implementation_and_independent_review(self):
        for host in ('codex', 'claude', 'copilot'):
            prompt = smoke_prompt('fixture', 'pass', host)
            self.assertIn('aw-forge', prompt)
            self.assertNotIn('delegate implementation to aw-backend', prompt)
            self.assertIn('aw-review-verify', prompt)
            self.assertIn('implements directly', prompt)


class DelegationProofTests(unittest.TestCase):
    def claude_events(self):
        events = [{'type': 'system', 'subtype': 'init', 'agent_type': 'aw-forge', 'session_id': 'forge1'}]
        for role, identity in (('aw-backend', 'backend1'), ('aw-review-verify', 'review1')):
            events.append({'type': 'assistant', 'session_id': 'forge1', 'message': {'content': [
                {'type': 'tool_use', 'id': identity, 'name': 'Agent', 'input': {'subagent_type': role}}]}})
            if role == 'aw-backend':
                events.extend([{'type': 'assistant', 'parent_tool_use_id': identity, 'message': {'content': [
                    {'type': 'tool_use', 'id': 'edit1', 'name': 'Write', 'input': {'file_path': '/fixture/smoke.json'}}]}},
                    {'type': 'user', 'parent_tool_use_id': identity, 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'edit1'}]}}])
            events.append({'type': 'user', 'session_id': 'forge1', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': identity}]}})
        events.append({'type': 'result', 'session_id': 'forge1', 'is_error': False})
        return events

    def test_claude_requires_three_completed_connected_roles_and_backend_edit(self):
        events = self.claude_events()
        self.assertEqual(delegation_observation('claude', events, '/fixture')['status'], 'passed')
        events[2]['parent_tool_use_id'] = 'forge1'
        self.assertEqual(delegation_observation('claude', events, '/fixture')['status'], 'blocked')

    def test_reviewer_only_and_requested_main_role_cannot_pass(self):
        events = self.claude_events()
        reviewer_only = [event for event in events if 'backend1' not in json.dumps(event) and 'aw-backend' not in json.dumps(event)]
        self.assertEqual(delegation_observation('claude', reviewer_only)['status'], 'passed')
        self.assertEqual(delegation_observation('claude', reviewer_only, '/fixture')['status'], 'blocked')
        del events[0]['agent_type']
        self.assertEqual(delegation_observation('claude', events)['status'], 'blocked')

    def test_wrong_parent_and_review_before_implementation_complete_block(self):
        events = self.claude_events()
        events[5]['session_id'] = 'different-forge'
        self.assertEqual(delegation_observation('claude', events)['status'], 'blocked')

    def test_backend_edit_after_completed_review_cannot_pass(self):
        events = self.claude_events()
        late_edit = events[:2] + events[4:-1] + events[2:4] + events[-1:]
        self.assertEqual(delegation_observation('claude', late_edit, '/fixture')['status'], 'blocked')

    def test_direct_coordinator_edit_precedes_independent_review(self):
        events = [
            {'type': 'system', 'subtype': 'init', 'agent_type': 'aw-forge', 'session_id': 'main'},
            {'type': 'assistant', 'session_id': 'main', 'message': {'content': [{'type': 'tool_use', 'id': 'edit', 'name': 'Write', 'input': {'file_path': '/fixture/smoke.json'}}]}},
            {'type': 'user', 'session_id': 'main', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'edit'}]}},
            {'type': 'assistant', 'session_id': 'main', 'message': {'content': [{'type': 'tool_use', 'id': 'review', 'name': 'Agent', 'input': {'subagent_type': 'aw-review-verify'}}]}},
            {'type': 'user', 'session_id': 'main', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'review'}]}},
            {'type': 'result', 'session_id': 'main', 'is_error': False}]
        self.assertEqual(delegation_observation('claude', events, '/fixture')['status'], 'passed')
        events[1]['session_id'] = 'unrelated'
        self.assertEqual(delegation_observation('claude', events, '/fixture')['status'], 'blocked')

    def test_codex_direct_native_stream_edit_and_reviewer_lifecycle(self):
        events = [
            {'type': 'thread.started', 'thread_id': 'main'},
            {'type': 'item.completed', 'item': {'id': 'edit', 'type': 'file_change', 'status': 'completed', 'changes': [{'path': 'smoke.json'}]}},
            {'type': 'item.completed', 'item': {'type': 'collab_agent_tool_call', 'tool': 'spawn_agent', 'agent_type': 'aw-review-verify', 'sender_thread_id': 'main', 'receiver_thread_ids': ['review']}},
            {'type': 'item.completed', 'item': {'type': 'collab_agent_tool_call', 'tool': 'wait', 'agents_states': {'review': {'status': 'completed'}}}},
            {'type': 'turn.completed'}]
        self.assertEqual(delegation_observation('codex', events, '/fixture')['status'], 'passed')
        events[1]['thread_id'] = 'unrelated'
        self.assertEqual(delegation_observation('codex', events, '/fixture')['status'], 'blocked')

    def test_malformed_or_negative_ui_lifecycle_order_cannot_pass(self):
        graph = [{'id': 'forge', 'role': 'aw-forge', 'started': 0, 'completed': 10, 'parent_id': None},
                 {'id': 'backend', 'role': 'aw-backend', 'started': 1, 'completed': 2, 'parent_id': 'forge'},
                 {'id': 'reviewer', 'role': 'aw-review-verify', 'started': 3, 'completed': -1, 'parent_id': 'forge'}]
        self.assertEqual(delegation_graph_result(graph)['status'], 'blocked')
        graph[-1]['completed'] = '9'
        self.assertEqual(delegation_graph_result(graph)['status'], 'blocked')
        graph[-1]['completed'] = None
        self.assertEqual(delegation_graph_result(graph)['status'], 'blocked')
        events = self.claude_events()
        events[4], events[5] = events[5], events[4]
        self.assertEqual(delegation_observation('claude', events)['status'], 'blocked')

    def test_codex_native_child_tree_requires_completed_wait_states(self):
        events = []
        for role, identity, parent in (('aw-forge', 'forge1', 'launcher'), ('aw-backend', 'backend1', 'forge1'), ('aw-review-verify', 'review1', 'forge1')):
            events.append({'method': 'thread/started', 'params': {'thread': {'id': identity, 'agentRole': role, 'parentThreadId': parent}}})
            if role != 'aw-forge':
                events.append({'type': 'item.completed', 'item': {'type': 'collab_agent_tool_call', 'tool': 'wait', 'agents_states': {identity: {'status': 'completed'}}}})
        events.append({'type': 'item.completed', 'item': {'type': 'collab_agent_tool_call', 'tool': 'wait', 'agents_states': {'forge1': {'status': 'completed'}}}})
        self.assertEqual(delegation_observation('codex', events)['status'], 'passed')
        self.assertEqual(delegation_observation('codex', events[:-1])['status'], 'blocked')
        events.insert(-1, {'type': 'item.completed', 'item': {'type': 'collab_agent_tool_call', 'tool': 'wait', 'agents_states': {'backend1': {'status': 'completed'}}}})
        self.assertEqual(delegation_observation('codex', events)['status'], 'passed')

    def test_copilot_requires_main_identity_and_distinct_completed_children(self):
        events = [{'type': 'session.start', 'data': {'sessionId': 'forge1', 'agentName': 'aw-forge'}}]
        for role, identity in (('aw-backend', 'backend1'), ('aw-review-verify', 'review1')):
            events.extend([{'type': 'subagent.started', 'data': {'agentName': role, 'toolCallId': identity, 'parentSessionId': 'forge1'}},
                           {'type': 'subagent.completed', 'data': {'toolCallId': identity, 'success': True}}])
        events.append({'type': 'session.end', 'data': {'sessionId': 'forge1'}})
        self.assertEqual(delegation_observation('copilot', events)['status'], 'passed')
        events[3]['data']['toolCallId'] = 'backend1'
        self.assertEqual(delegation_observation('copilot', events)['status'], 'blocked')

    def test_json_parser_does_not_execute_prose_or_non_object_output(self):
        self.assertEqual(json_events('not json\n[1,2]\n{"type":"native"}\n'), [{'type': 'native'}])

    def test_secret_fields_and_known_token_patterns_redacted(self):
        self.assertEqual(redact({'authorization': 'Bearer hidden', 'message': 'sk-abcdefghijklmnop'})['authorization'], '[redacted]')
        self.assertNotIn('abcdefghijklmnop', redact('sk-abcdefghijklmnop'))

    def test_gate_files_without_host_events_never_pass(self):
        phases = [{'phase': name, 'actual_value': name, 'exit_code': 0, 'timed_out': False, 'output_truncated': False, 'hook_events': [],
                   'native_edit_ids': ['edit-' + name], 'gate_artifacts': []} for name, expected in (('pass', 'passed'), ('fail', 'failed'))]
        self.assertEqual(_hook_verdict(phases, [])['status'], 'blocked')
        for phase in phases:
            phase['hook_events'] = [{'id': 'native-' + phase['phase'], 'source': '/fixture/.claude/settings.json',
                                     'status': 'completed', 'tool_id': 'edit-' + phase['phase'], 'output': 'Workflow edit observed'}]
        sources = ['/fixture/.claude/settings.json']
        self.assertEqual(_hook_verdict(phases, [], sources)['status'], 'passed')
        phases[1]['exit_code'], phases[1]['timed_out'] = 124, True
        self.assertEqual(_hook_verdict(phases, [], sources)['status'], 'blocked')
        phases[1]['exit_code'], phases[1]['timed_out'] = 0, False
        self.assertEqual(_hook_verdict(phases, [], ['/unrelated/personal-hook'])['status'], 'blocked')
        phases[0]['hook_events'][0]['tool_id'] = 'different-edit'
        self.assertEqual(_hook_verdict(phases, [], sources)['status'], 'blocked')
        phases[0]['hook_events'][0]['tool_id'] = 'edit-pass'
        phases[0]['gate_artifacts'].append({'status': 'passed'})
        self.assertEqual(_hook_verdict(phases, [], sources)['status'], 'failed')


class MeasuredStreamTests(unittest.TestCase):
    """Minimal vendor event shapes, with invented IDs and fixture paths."""
    def copilot_events(self):
        events = [{'type': 'tool.execution_start', 'data': {'toolName': 'task', 'toolCallId': 'call-forge',
                   'arguments': {'agent_type': 'aw-forge'}}},
                  {'type': 'subagent.started', 'agentId': 'native-forge', 'parentId': 'previous-event',
                   'data': {'agentName': 'aw-forge', 'toolCallId': 'call-forge'}}]
        for role, name in (('aw-backend', 'backend'), ('aw-review-verify', 'review')):
            events.extend([{'type': 'tool.execution_start', 'agentId': 'native-forge', 'data': {
                'toolName': 'task', 'toolCallId': 'call-' + name, 'parentToolCallId': 'call-forge', 'arguments': {'agent_type': role}}},
                {'type': 'subagent.started', 'agentId': 'native-' + name, 'parentId': 'previous-event',
                 'data': {'agentName': role, 'toolCallId': 'call-' + name, 'parentId': 'native-forge'}}])
            if name == 'backend':
                events.extend([{'type': 'tool.execution_start', 'agentId': 'native-backend', 'data': {
                    'toolName': 'edit', 'toolCallId': 'edit1', 'parentToolCallId': 'call-backend', 'arguments': {'path': '/fixture/smoke.json'}}},
                    {'type': 'tool.execution_complete', 'agentId': 'native-backend', 'data': {
                        'toolCallId': 'edit1', 'parentToolCallId': 'call-backend', 'success': True}}])
            events.extend([{'type': 'subagent.completed', 'agentId': 'native-' + name, 'data': {
                'agentName': role, 'toolCallId': 'call-' + name}},
                {'type': 'tool.execution_complete', 'agentId': 'native-forge', 'data': {
                    'toolCallId': 'call-' + name, 'parentToolCallId': 'call-forge', 'success': True}}])
        events.extend([{'type': 'tool.execution_complete', 'data': {'toolCallId': 'call-forge', 'success': True}},
                       {'type': 'subagent.completed', 'agentId': 'native-forge', 'data': {'agentName': 'aw-forge', 'toolCallId': 'call-forge'}}])
        return events

    def test_codex_measured_alias_preserves_missing_spawn_and_identity_block(self):
        wait = {'type': 'item.completed', 'item': {'type': 'collab_tool_call', 'tool': 'wait',
                'sender_thread_id': 'launcher', 'receiver_thread_ids': [], 'agents_states': {}, 'status': 'completed'}}
        self.assertEqual(delegation_observation('codex', [wait])['status'], 'blocked')
        spawn = {'type': 'item.completed', 'item': {'type': 'collab_tool_call', 'tool': 'spawn_agent',
                 'receiver_thread_ids': ['child'], 'status': 'completed'}}
        self.assertEqual(role_observation('codex', [spawn], 'aw-review-verify')['status'], 'blocked')
        spawn['item']['agent_type'] = 'aw-review-verify'
        self.assertEqual(role_observation('codex', [spawn], 'aw-review-verify')['status'], 'passed')

    def test_copilot_native_catalog_preserves_user_and_project_scope(self):
        roles = ['aw-forge', 'aw-backend', 'aw-review-verify']
        events = [{'type': 'session.custom_agents_updated', 'data': {'agents': [
            {'name': name, 'source': 'user'} for name in roles], 'errors': [], 'warnings': []}},
                  {'type': 'session.skills_loaded', 'data': {'skills': [
                      {'name': 'forge', 'enabled': True, 'path': '/fixture/.github/skills/forge/SKILL.md', 'source': 'project'}]}}]
        global_result = copilot_metadata(events, roles, ['forge'], 'global', '/fixture')
        self.assertEqual(global_result['discovery']['status'], 'passed')
        scoped = copilot_metadata(events, roles, ['forge'], 'repo', '/fixture')
        self.assertEqual(scoped['discovery']['status'], 'blocked')
        self.assertEqual(scoped['discovery']['availability'], 'passed')
        self.assertEqual(scoped['skills']['status'], 'passed')
        events[0]['data']['agents'].append(dict(events[0]['data']['agents'][0]))
        self.assertEqual(copilot_metadata(events, roles, ['forge'], 'global', '/fixture')['discovery']['status'], 'blocked')
        events[0]['data']['agents'].pop()
        events[0]['data']['agents'].pop()
        self.assertEqual(copilot_metadata(events, roles, ['forge'], 'global', '/fixture')['discovery']['status'], 'failed')

    def test_copilot_correlates_task_success_and_parent_native_agent_ids(self):
        observed = delegation_observation('copilot', self.copilot_events(), '/fixture')
        self.assertEqual(observed['status'], 'passed')
        self.assertEqual(observed['native_lifecycles'][1]['parent_id'], 'call-forge')
        self.assertEqual(observed['native_implementation_edits'][0]['owner'], 'call-backend')

    def test_copilot_completion_without_matching_task_success_does_not_pass(self):
        for missing in (False, True):
            events = self.copilot_events()
            completion = next(event for event in events if event['type'] == 'tool.execution_complete' and event['data']['toolCallId'] == 'call-backend')
            if missing:
                events.remove(completion)
            else:
                completion['data']['success'] = False
            self.assertEqual(delegation_observation('copilot', events, '/fixture')['status'], 'blocked')

    def test_copilot_unknown_parent_or_cancelled_worker_does_not_pass(self):
        for change in ('parent', 'cancelled'):
            events = self.copilot_events()
            for event in events:
                if event['data'].get('toolCallId') == 'call-backend':
                    if change == 'parent' and event['type'] == 'subagent.started':
                        event['data']['parentId'] = 'unknown-native-agent'
                    if change == 'cancelled' and event['type'] == 'subagent.completed':
                        event['data']['cancelled'] = True
            self.assertEqual(delegation_observation('copilot', events, '/fixture')['status'], 'blocked')

    def test_requested_main_forge_and_observed_child_remain_unproven(self):
        observed = delegation_observation('copilot', self.copilot_events(), '/fixture', main_role='aw-forge')
        self.assertEqual(observed['status'], 'blocked')
        self.assertIn('Requested main Forge profile conflicts', observed['reason'])

    def test_native_main_forge_with_completed_child_forge_fails_contract(self):
        events = [{'type': 'system', 'subtype': 'init', 'agent_type': 'aw-forge', 'session_id': 'main-forge'},
                  {'type': 'assistant', 'session_id': 'main-forge', 'message': {'content': [
                      {'type': 'tool_use', 'id': 'child-forge', 'name': 'Agent', 'input': {'subagent_type': 'aw-forge'}}]}},
                  {'type': 'user', 'session_id': 'main-forge', 'message': {'content': [
                      {'type': 'tool_result', 'tool_use_id': 'child-forge', 'is_error': False}]}},
                  {'type': 'result', 'session_id': 'main-forge', 'is_error': False}]
        observed = delegation_observation('claude', events, main_role='aw-forge')
        self.assertEqual(observed['status'], 'failed')
        self.assertIn('Native metadata connects', observed['reason'])

    def test_timeout_cannot_pass_complete_native_lifecycles(self):
        observed = delegation_observation('copilot', self.copilot_events(), '/fixture', completion={'exit_code': 124, 'timed_out': True})
        self.assertEqual(observed['status'], 'blocked')

    def test_claude_measured_init_missing_main_identity_retains_worker_proof(self):
        events = DelegationProofTests().claude_events()
        events[0].pop('agent_type')
        events[0]['agents'] = ['aw-forge', 'aw-backend', 'aw-review-verify']
        observed = delegation_observation('claude', events, '/fixture', main_role='aw-forge', completion={'exit_code': 0, 'timed_out': False})
        self.assertEqual(observed['status'], 'blocked')
        self.assertIn('omits the selected main Forge identity', observed['reason'])
        self.assertEqual(len(observed['native_lifecycles']), 2)
        self.assertEqual(len(observed['native_implementation_edits']), 1)


class NativeCaptureFixtureTests(unittest.TestCase):
    def test_fresh_global_and_project_fixtures_use_selected_local_bundle(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            for scope in ('global', 'repo'):
                fixture = create_fixture(source, Path(temp) / scope, scope, 'claude', 'controlled-fixture')
                self.assertEqual((fixture / '.claude').is_dir(), scope == 'repo')
                self.assertEqual((fixture / '.agents').is_dir(), scope == 'repo')
                _, bundle, manifest = selected_bundle(fixture, 'repo')
                self.assertTrue(bundle.is_relative_to(fixture.resolve()))
                self.assertEqual(read_json(fixture / '.ai/gates.json')['checks'][0]['id'], 'native-host-smoke')
                self.assertTrue(manifest['skills'])

    def test_fake_executable_capture_is_parser_fixture_not_live_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / 'controlled-native'
            executable.write_text('#!/usr/bin/env python3\nprint(\'{"type":"system","subtype":"init","agents":["aw-forge"]}\')\n')
            executable.chmod(0o755)
            captured = run_command([str(executable)], root, root / 'artifacts', 'controlled-fixture', 3)
            self.assertEqual(captured['capture']['exit_code'], 0)
            self.assertEqual(sha256_file(captured['artifact']['path']), captured['artifact']['sha256'])
            self.assertNotIn('live_verified', captured)

    def test_timeout_is_bounded_and_retained(self):
        import sys
        with tempfile.TemporaryDirectory() as temp:
            captured = run_command([sys.executable, '-c', 'import time; time.sleep(5)'], temp, Path(temp) / 'artifacts', 'timeout', 0.05)
            self.assertEqual(captured['capture']['exit_code'], 124)
            self.assertTrue(captured['capture']['timed_out'])

    def test_json_secret_fields_are_removed_from_retained_stdout_and_events(self):
        import sys
        with tempfile.TemporaryDirectory() as temp:
            captured = run_command([sys.executable, '-c', 'print(\'{"api_key":"private-value"}\')'], temp, Path(temp) / 'artifacts', 'secret-fixture', 3)
            self.assertNotIn('private-value', Path(captured['artifact']['path']).read_text())
            self.assertEqual(captured['capture']['events'][0]['api_key'], '[redacted]')
            nested = {'message': {'content': [{'text': '{"api_key":"fixture-private-value"}'}]}}
            self.assertNotIn('fixture-private-value', json.dumps(redact(nested)))

    def test_missing_runtime_is_captured_as_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            captured = run_command(['/no-such-native-host-runtime'], temp, Path(temp) / 'artifacts', 'missing', 1)
            self.assertEqual(captured['capture']['exit_code'], 127)


class VerificationRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home, self.repo = self.root / 'home', self.root / 'repo'
        self.home.mkdir()
        self.repo.mkdir()
        self.bundle = self.repo / '.ai/bundles/1.1.0'
        self.bundle.mkdir(parents=True)
        self.manifest = {'version': '1.1.0', 'skills': [{'name': 'forge'}]}
        write_json(self.bundle / 'manifest.json', self.manifest)
        write_json(self.repo / '.ai/config.json', {'bundle': 'bundles/1.1.0'})
        self.runtime = self.root / 'cursor-runtime'
        self.runtime.write_bytes(b'fixture runtime binary')
        self.artifact = self.root / 'native-ax.txt'
        self.artifact.write_text('Actual native fixture observation for parser validation only')
        self.record = {'schema_version': 1, 'host': 'cursor', 'scope': 'repo', 'root': str(self.repo), 'home': str(self.home),
                       'bundle': str(self.bundle), 'runtime': {'path': str(self.runtime), 'sha256': sha256_file(self.runtime), 'support_files': cursor_runtime_inputs(self.runtime)},
                       'configuration': config_snapshot('cursor', self.repo, 'repo', self.bundle, self.manifest, self.home),
                       'results': blank_results('Not observed'), 'status': 'blocked'}

    def tearDown(self):
        self.temp.cleanup()

    def ui(self):
        return {'host': 'cursor', 'scope': 'repo', 'root': str(self.repo), 'runtime_sha256': self.record['runtime']['sha256'],
                'runtime_support_sha256': json_hash(self.record['runtime']['support_files']),
                'config_sha256': self.record['configuration']['sha256'], 'provider': 'cua', 'observer': 'fixture-recorder',
                'captured_at': time.time(), 'tool_call_ids': ['fixture-native-call'], 'observations': {'discovery': {
                    'status': 'passed', 'observed': 'Role names shown by native settings view', 'native_identifiers': ['aw-forge'],
                    'artifacts': [{'path': str(self.artifact), 'sha256': sha256_file(self.artifact)}]}}}

    def test_ui_import_requires_explicit_observer_attestation(self):
        path = self.root / 'ui.json'
        write_json(path, self.ui())
        with self.assertRaisesRegex(ValueError, 'attest'):
            import_ui_evidence(path, self.record, False)
        import_ui_evidence(path, self.record, True)
        self.assertEqual(self.record['results']['discovery']['status'], 'passed')
        self.assertEqual(self.record['results']['skills']['status'], 'blocked')
        self.assertEqual(self.record['results']['discovery']['proof_boundary'], 'observer-attested-native-ui')

    def test_ui_missing_changed_artifact_rejected(self):
        path = self.root / 'ui.json'
        write_json(path, self.ui())
        self.artifact.write_text('changed capture')
        with self.assertRaisesRegex(ValueError, 'capture'):
            import_ui_evidence(path, self.record, True)

    def test_ui_runtime_configuration_and_capture_time_bound(self):
        path = self.root / 'ui.json'
        ui = self.ui()
        ui['captured_at'] = 1
        write_json(path, ui)
        with self.assertRaisesRegex(ValueError, 'older'):
            import_ui_evidence(path, self.record, True)
        ui = self.ui()
        ui['config_sha256'] = 'stale'
        write_json(path, ui)
        with self.assertRaisesRegex(ValueError, 'config'):
            import_ui_evidence(path, self.record, True)

    def test_doctor_summary_is_read_only_and_marks_changed_configuration_stale(self):
        path = self.root / 'ui.json'
        write_json(path, self.ui())
        import_ui_evidence(path, self.record, True)
        destination = self.repo / '.ai/state/host-verifications/latest-cursor-repo.json'
        write_json(destination, self.record)
        before = destination.read_bytes()
        with patch('agent_workflow.host_verification.Path.home', return_value=self.home):
            summary = summarize_host_verifications(self.repo, self.repo / '.ai', False)
        self.assertEqual(summary['cursor']['status'], 'blocked')
        write_json(self.repo / '.cursor/hooks.json', {'version': 1, 'hooks': {}})
        with patch('agent_workflow.host_verification.Path.home', return_value=self.home):
            summary = summarize_host_verifications(self.repo, self.repo / '.ai', False)
        self.assertEqual(summary['cursor']['status'], 'stale')
        self.assertEqual(summary['cursor']['results']['discovery']['status'], 'stale')
        self.assertEqual(destination.read_bytes(), before)

    def test_saved_record_from_another_repository_cannot_pass_doctor(self):
        other = self.root / 'other'
        write_json(other / '.ai/state/host-verifications/latest-cursor-repo.json', self.record)
        with patch('agent_workflow.host_verification.Path.home', return_value=self.home):
            summary = summarize_host_verifications(other, other / '.ai', False)
        self.assertEqual(summary['cursor']['status'], 'stale')
        self.assertIn('different installation', summary['cursor']['stale_reasons'][0])

    def test_ui_evidence_cannot_pass_without_a_native_runtime(self):
        evidence = self.ui()
        evidence['runtime_sha256'] = None
        self.record['runtime'] = {'path': None, 'sha256': None}
        path = self.root / 'ui.json'
        write_json(path, evidence)
        with self.assertRaisesRegex(ValueError, 'runtime'):
            import_ui_evidence(path, self.record, True)

    def test_fixture_success_is_not_reported_as_installation_loading(self):
        for value in self.record['results'].values():
            value['status'] = 'passed'
            value['proof_boundary'] = 'native-disposable-fixture'
        self.record['status'] = 'passed'
        self.record['target'] = {'kind': 'disposable-fixture', 'path': '/temporary-fixture'}
        write_json(self.repo / '.ai/state/host-verifications/latest-cursor-repo.json', self.record)
        with patch('agent_workflow.host_verification.Path.home', return_value=self.home):
            summary = summarize_host_verifications(self.repo, self.repo / '.ai', False)
        self.assertEqual(summary['cursor']['status'], 'fixture-passed')
        self.assertEqual(summary['cursor']['installation_loading'], 'unverified')

    def test_runtime_or_artifact_changes_invalidate_proof(self):
        path = self.root / 'ui.json'
        write_json(path, self.ui())
        import_ui_evidence(path, self.record, True)
        self.assertEqual(check_verification_freshness(self.record), [])
        self.runtime.write_bytes(b'new runtime')
        self.assertTrue(any('Runtime' in reason for reason in check_verification_freshness(self.record)))
        self.artifact.unlink()
        self.assertTrue(any('artifact' in reason for reason in check_verification_freshness(self.record)))

    def test_ui_attestation_file_change_invalidates_proof(self):
        path = self.root / 'ui.json'
        write_json(path, self.ui())
        import_ui_evidence(path, self.record, True)
        path.write_text('{}')
        self.assertTrue(any('artifact' in reason for reason in check_verification_freshness(self.record)))

    def test_launcher_helpers_and_skill_resources_are_freshness_inputs(self):
        for relative in ('.ai/bin/agent-workflow', '.cursor/skills/forge/scripts/helper.py', '.ai/gates.json', '.ai/bundles/1.1.0/agent_workflow/gates.py', '.ai/bundles/1.1.0/resources/policy.txt'):
            with self.subTest(relative=relative):
                path = self.repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('first')
                self.record['configuration'] = config_snapshot('cursor', self.repo, 'repo', self.bundle, self.manifest, self.home)
                path.write_text('changed')
                self.assertTrue(any('configuration' in reason for reason in check_verification_freshness(self.record)))

    def test_native_mcp_configuration_changes_invalidate_proof(self):
        for host, relative in (('cursor', '.cursor/mcp.json'), ('claude', '.mcp.json'), ('copilot', '.github/mcp.json')):
            with self.subTest(host=host):
                self.record['host'] = host
                path = self.repo / relative
                write_json(path, {'mcpServers': {}})
                self.record['configuration'] = config_snapshot(host, self.repo, 'repo', self.bundle, self.manifest, self.home)
                write_json(path, {'mcpServers': {'fixture': {}}})
                self.assertTrue(any('configuration' in reason for reason in check_verification_freshness(self.record)))

    def test_claude_usage_and_unrelated_project_cache_do_not_invalidate_config(self):
        path = self.home / '.claude.json'
        data = {'mcpServers': {'fixture': {'type': 'http', 'url': 'https://example.invalid/mcp'}},
                'projects': {str(self.repo.resolve()): {'allowedTools': ['Read(./fixture.txt)']}}}
        write_json(path, data)
        before = config_snapshot('claude', self.repo, 'repo', self.bundle, self.manifest, self.home)
        data.update(numStartups=3, skillUsage={'forge': 1}, cachedExperimentData={'fixture': True})
        data['projects'][str(self.repo.resolve())].update(lastCost=0.4, lastSessionId='new-session', exampleFiles=['smoke.json'])
        data['projects'][str(self.root / 'unrelated')] = {'mcpServers': {'other': {'command': 'other'}}}
        write_json(path, data)
        self.assertEqual(before, config_snapshot('claude', self.repo, 'repo', self.bundle, self.manifest, self.home))

    def test_claude_new_default_project_record_is_semantically_unchanged(self):
        path = self.home / '.claude.json'
        before = claude_user_config_digest(path, self.repo)
        write_json(path, {'numStartups': 1, 'projects': {str(self.repo.resolve()): {
            'allowedTools': [], 'mcpServers': {}, 'hasTrustDialogAccepted': False, 'lastCost': 0.1}}})
        self.assertEqual(before, claude_user_config_digest(path, self.repo))

    def test_claude_supported_user_and_current_project_settings_remain_bound(self):
        path = self.home / '.claude.json'
        before = claude_user_config_digest(path, self.repo)
        for scope in ('user', 'project'):
            for key, default in CLAUDE_CONFIG_DEFAULTS.items():
                with self.subTest(scope=scope, setting=key):
                    changed = {'fixture': 'changed'} if isinstance(default, dict) else ['changed'] if isinstance(default, list) else True if default is False else 'plan'
                    data = {key: changed} if scope == 'user' else {'projects': {str(self.repo.resolve()): {key: changed}}}
                    write_json(path, data)
                    self.assertNotEqual(before, claude_user_config_digest(path, self.repo))

    def test_claude_malformed_current_project_config_is_rejected(self):
        path = self.home / '.claude.json'
        write_json(path, {'projects': {str(self.repo.resolve()): []}})
        with self.assertRaisesRegex(ValueError, 'current-project'):
            claude_user_config_digest(path, self.repo)

    def test_copilot_native_binary_and_fallback_changes_invalidate_loader_proof(self):
        runtime = self.root / 'copilot/npm-loader.js'
        runtime.parent.mkdir()
        runtime.write_text('unchanged vendor loader')
        write_json(runtime.parent / 'package.json', {'version': '1'})
        fallback = runtime.parent / 'index.js'
        fallback.write_text('fallback v1')
        binary = runtime.parent / 'node_modules/@github/copilot-darwin-arm64/copilot'
        binary.parent.mkdir(parents=True)
        write_json(binary.parent / 'package.json', {'exports': './copilot'})
        binary.write_bytes(b'native v1')
        self.record['host'] = 'copilot'
        self.record['configuration'] = config_snapshot('copilot', self.repo, 'repo', self.bundle, self.manifest, self.home)
        self.record['runtime'] = {'path': str(runtime), 'sha256': sha256_file(runtime), **support_identity('copilot', runtime)}
        self.assertIn(str(binary.resolve()), runtime_support_inputs('copilot', runtime))
        self.assertEqual(check_verification_freshness(self.record), [])
        binary.write_bytes(b'native v2')
        self.assertIn('Copilot application version or supporting runtime inputs changed', check_verification_freshness(self.record))
        self.record['runtime'].update(support_identity('copilot', runtime))
        fallback.write_text('fallback v2')
        self.assertIn('Copilot application version or supporting runtime inputs changed', check_verification_freshness(self.record))

    def test_copilot_changed_platform_export_and_selected_target_invalidate_runtime(self):
        runtime = self.root / 'copilot/npm-loader.js'
        runtime.parent.mkdir()
        runtime.write_text('unchanged vendor loader')
        metadata = runtime.parent / 'node_modules/@github/copilot-darwin-arm64/package.json'
        write_json(metadata, {'exports': './copilot'})
        (metadata.parent / 'copilot').write_bytes(b'original')
        self.record['host'] = 'copilot'
        self.record['configuration'] = config_snapshot('copilot', self.repo, 'repo', self.bundle, self.manifest, self.home)
        self.record['runtime'] = {'path': str(runtime), 'sha256': sha256_file(runtime), **support_identity('copilot', runtime)}
        write_json(metadata, {'exports': {'.': './alternate'}})
        alternate = metadata.parent / 'alternate'
        alternate.write_bytes(b'alternate v1')
        self.assertIn('Copilot application version or supporting runtime inputs changed', check_verification_freshness(self.record))
        self.record['runtime'].update(support_identity('copilot', runtime))
        self.assertIn(str(alternate.resolve()), self.record['runtime']['support_files'])
        self.assertEqual(check_verification_freshness(self.record), [])
        alternate.write_bytes(b'alternate v2')
        self.assertIn('Copilot application version or supporting runtime inputs changed', check_verification_freshness(self.record))

    def test_copilot_unsupported_platform_exports_block_runtime_proof(self):
        runtime = self.root / 'copilot/npm-loader.js'
        runtime.parent.mkdir()
        runtime.write_text('unchanged vendor loader')
        metadata = runtime.parent / 'node_modules/@github/copilot-darwin-arm64/package.json'
        write_json(metadata, {'exports': {'import': './alternate', 'default': './copilot'}})
        self.record['host'] = 'copilot'
        self.record['runtime'] = {'path': str(runtime), 'sha256': sha256_file(runtime), 'support_files': {}}
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            runtime_support_inputs('copilot', runtime)
        self.assertTrue(any('unsupported' in reason for reason in check_verification_freshness(self.record)))

    def test_cursor_supporting_runtime_change_invalidates_unchanged_launcher(self):
        runtime = self.root / 'Cursor.app/Contents/MacOS/Cursor'
        runtime.parent.mkdir(parents=True)
        runtime.write_bytes(b'unchanged launcher')
        info = runtime.parents[1] / 'Resources/app/package.json'
        write_json(info, {'version': '1'})
        self.record['runtime'] = {'path': str(runtime), 'sha256': sha256_file(runtime), 'support_files': cursor_runtime_inputs(runtime)}
        self.assertEqual(check_verification_freshness(self.record), [])
        write_json(info, {'version': '2'})
        self.assertIn('Cursor application version or supporting runtime inputs changed', check_verification_freshness(self.record))

    def test_cursor_ui_from_before_package_update_cannot_bind_to_new_record(self):
        runtime = self.root / 'Cursor.app/Contents/MacOS/Cursor'
        runtime.parent.mkdir(parents=True)
        runtime.write_bytes(b'unchanged launcher')
        package = runtime.parents[1] / 'Resources/app/package.json'
        write_json(package, {'version': '1'})
        self.record['runtime'] = {'path': str(runtime), 'sha256': sha256_file(runtime), 'support_files': cursor_runtime_inputs(runtime)}
        old = self.ui()
        write_json(package, {'version': '2'})
        self.record['runtime']['support_files'] = cursor_runtime_inputs(runtime)
        path = self.root / 'old-ui.json'
        write_json(path, old)
        with self.assertRaisesRegex(ValueError, 'metadata'):
            import_ui_evidence(path, self.record, True)

    def test_copied_fixture_helper_changes_invalidate_fixture_proof(self):
        fixture = self.root / 'fixture'
        write_json(fixture / '.ai/config.json', {'bundle': 'bundles/1.1.0'})
        write_json(fixture / '.ai/bundles/1.1.0/manifest.json', self.manifest)
        helper = fixture / '.ai/bundles/1.1.0/agent_workflow/gates.py'
        helper.parent.mkdir()
        helper.write_text('first')
        self.record['fixture'] = str(fixture)
        self.record['fixture_configuration'] = fixture_snapshot(self.record)
        self.assertEqual(check_verification_freshness(self.record), [])
        helper.write_text('changed')
        self.assertIn('Native fixture configuration changed', check_verification_freshness(self.record))

    def test_preview_runs_no_command_and_creates_no_state(self):
        args = argparse.Namespace(host='claude', repo=str(self.repo), runtime=str(self.runtime), timeout=5, live=False)
        with patch('agent_workflow.host_verification.Path.home', return_value=self.home), patch('agent_workflow.host_verification.run_command') as command:
            record = verify_one(args, 'repo')
        command.assert_not_called()
        self.assertEqual(record['runtime']['sha256'], sha256_file(self.runtime))
        self.assertFalse((self.repo / '.ai/state').exists())

    def test_missing_scope_does_not_prevent_other_scope_verification(self):
        args = argparse.Namespace(host='claude', repo=str(self.repo), scope='both', timeout=5)
        with patch('agent_workflow.host_verification.verify_one', side_effect=[ValueError('global missing'), {'status': 'passed', 'scope': 'repo'}]):
            records = verify_host(args)['verifications']
        self.assertEqual([record['status'] for record in records], ['blocked', 'passed'])

    def test_bundle_selection_cannot_escape_installation(self):
        state, bundle, manifest = selected_bundle(self.repo, 'repo', self.home)
        self.assertEqual(bundle, self.bundle.resolve())
        write_json(self.repo / '.ai/config.json', {'bundle': '../../outside'})
        with self.assertRaisesRegex(ValueError, 'escapes'):
            selected_bundle(self.repo, 'repo', self.home)

    def test_partial_observations_cannot_pass_entire_host(self):
        self.assertEqual(verification_status(self.record['results']), 'blocked')
        self.record['results']['discovery']['status'] = 'passed'
        self.assertEqual(verification_status(self.record['results']), 'blocked')
        self.record['results']['hooks']['status'] = 'failed'
        self.assertEqual(verification_status(self.record['results']), 'failed')


if __name__ == '__main__':
    unittest.main()
