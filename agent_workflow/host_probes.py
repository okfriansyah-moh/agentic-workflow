"""Bounded native-host probes and strict parsing of native metadata/events."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

CATEGORIES = ('discovery', 'role_invocation', 'skills', 'hooks', 'trust')
SMOKE_ROLES = ('aw-forge', 'aw-backend', 'aw-review-verify')
CODEX_COLLAB_TYPES = ('collab_agent_tool_call', 'collab_tool_call')
SECRET_KEYS = re.compile(r'(?i)(token|password|secret|credential|authorization|cookie|api.?key)')


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def redact(value):
    if isinstance(value, dict):
        return {key: '[redacted]' if SECRET_KEYS.search(key) else redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        text = re.sub(r'\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{16,})\b', '[redacted]', value)
        text = re.sub(r'(?i)(bearer\s+)[^\s"\']+', r'\1[redacted]', text)
        text = re.sub(r'''(?i)((?:["']?)(?:api.?key|token|password|secret|authorization|credential)(?:["']?)\s*[:=]\s*)(["'])(.*?)\2''',
                      r'\1\2[redacted]\2', text)
        for key, secret in os.environ.items():
            if SECRET_KEYS.search(key) and len(secret) >= 8:
                text = text.replace(secret, '[redacted]')
        return text
    return value


def json_events(text):
    events = []
    for line in text.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def sanitized_output(text):
    lines = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
            lines.append(json.dumps(redact(value)))
        except ValueError:
            lines.append(redact(line))
    return '\n'.join(lines)


def run_command(argv, cwd, artifact_dir, label, timeout=90):
    """Retain bounded, sanitized output; terminate the whole process group on timeout."""
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    try:
        process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            code, timed_out = process.returncode, False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            code, timed_out = 124, True
    except OSError as exc:
        stdout, stderr, code, timed_out = b'', str(exc).encode(), 127, False
    decoded = stdout.decode('utf-8', errors='replace')
    events = json_events(decoded)
    retained = {'argv': redact(argv), 'cwd': str(cwd), 'exit_code': code, 'timed_out': timed_out,
                'started_at': started, 'finished_at': time.time(),
                'stdout_sha256': hashlib.sha256(stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(stderr).hexdigest(),
                'events': redact(events), 'stdout': sanitized_output(decoded)[:1000000],
                'stderr': sanitized_output(stderr.decode('utf-8', errors='replace'))[:200000],
                'truncated': len(stdout) > 1000000 or len(stderr) > 200000}
    path = artifact_dir / f'{label}.json'
    path.write_text(json.dumps(retained, indent=2) + '\n')
    return {'capture': retained, 'artifact': {'path': str(path), 'sha256': sha256_file(path)}}


def result(status, reason, artifacts=(), **details):
    return {'status': status, 'reason': reason, 'artifacts': list(artifacts), **details}


def blank_results(reason):
    return {category: result('blocked', reason) for category in CATEGORIES}


def native_skills(host, payload, expected, scope, fixture):
    if host == 'copilot' and isinstance(payload, list):
        entries = payload
    elif host == 'codex' and isinstance(payload, dict) and isinstance(payload.get('data'), list):
        entries = [skill for group in payload['data'] for skill in group.get('skills', [])]
    else:
        return result('blocked', 'No supported native skill catalog was captured')
    enabled = {entry.get('name') for entry in entries if entry.get('enabled') is True}
    missing = sorted(set(expected) - enabled)
    if missing:
        return result('failed', 'Native catalog omits required enabled skills', missing=missing)
    if scope == 'repo':
        project = {entry.get('name') for entry in entries if entry.get('enabled') is True and _within(entry.get('path', ''), fixture)}
        missing_project = sorted(set(expected) - project)
        if missing_project:
            return result('blocked', 'Skills are visible globally but project-native discovery is incomplete', missing=missing_project)
    return result('passed', 'Required enabled skills were returned by native discovery', observed_count=len(enabled))


def _within(path, root):
    try:
        return bool(path) and Path(path).resolve().is_relative_to(Path(root).resolve())
    except (ValueError, TypeError):
        return False


def claude_metadata(events, expected_roles, expected_skills, scope='global', fixture=None):
    initial = next((item for item in events if item.get('type') == 'system' and item.get('subtype') == 'init'), None)
    if initial is None:
        return {}
    results = {}
    for category, field, expected in (('discovery', 'agents', expected_roles), ('skills', 'skills', expected_skills)):
        values = initial.get(field)
        if isinstance(values, list) and all(isinstance(value, str) for value in values):
            missing = sorted(set(expected) - set(values))
            results[category] = result('failed' if missing else 'passed', 'Native session initialization catalog', missing=missing)
            if category == 'skills' and scope == 'repo' and not missing:
                results[category] = result('blocked', 'Native skill names establish availability but omit selected project source paths',
                                           availability='passed', observed_count=len(values), expected_scope=str(fixture))
    return results


def copilot_metadata(events, expected_roles, expected_skills, scope, fixture):
    results = {}
    for event in events:
        data = event.get('data', {})
        if not isinstance(data, dict):
            continue
        if event.get('type') == 'session.custom_agents_updated':
            results['discovery'] = copilot_role_catalog(data, expected_roles, scope, fixture)
        elif event.get('type') == 'session.skills_loaded' and isinstance(data.get('skills'), list):
            results['skills'] = native_skills('copilot', data['skills'], expected_skills, scope, fixture)
    return results


def copilot_role_catalog(data, expected, scope, fixture):
    entries = data.get('agents')
    if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
        return result('blocked', 'Native custom-agent catalog is malformed')
    selected = {item.get('name'): item for item in entries if isinstance(item.get('name'), str)}
    if any(sum(item.get('name') == name for item in entries) > 1 for name in expected):
        return result('blocked', 'Native custom-agent catalog contains conflicting required role identities')
    missing = sorted(set(expected) - set(selected))
    details = {'missing': missing, 'role_sources': {name: {'source': selected[name].get('source'),
                'path': selected[name].get('path')} for name in expected if name in selected}}
    if data.get('errors') or missing:
        return result('failed', 'Native custom-agent catalog reports errors or missing required roles', **details)
    required_source = 'user' if scope == 'global' else 'project'
    scoped = all(selected[name].get('source') == required_source and
                 (scope == 'global' or _within(selected[name].get('path'), fixture)) for name in expected)
    if not scoped:
        return result('blocked', 'Native roles are available but their sources do not establish the requested installation scope',
                      availability='passed', **details)
    return result('passed', 'Required roles were returned by the native custom-agent catalog', **details)


def role_observation(host, events, role):
    """Single-role diagnostic only; delegation_observation owns workflow acceptance."""
    if host == 'codex':
        for event in events:
            thread = event.get('params', {}).get('thread', {})
            if event.get('method') == 'thread/started' and thread.get('agentRole') == role and thread.get('parentThreadId'):
                return result('passed', 'Native child thread records the requested role', native_id=thread['id'])
            item = event.get('item', {})
            if item.get('type') in CODEX_COLLAB_TYPES and item.get('tool') == 'spawn_agent':
                if item.get('agent_type', item.get('agent_role')) == role and item.get('status') == 'completed' and item.get('receiver_thread_ids'):
                    return result('passed', 'Native spawn event completed for the requested role', native_id=item.get('id'))
    if host == 'claude':
        calls = set()
        for event in events:
            content = event.get('message', {}).get('content', [])
            if not isinstance(content, list):
                continue
            for block in content:
                if block.get('type') == 'tool_use' and block.get('name') in ('Agent', 'Task') and block.get('input', {}).get('subagent_type') == role:
                    calls.add(block.get('id'))
                if block.get('type') == 'tool_result' and block.get('tool_use_id') in calls and block.get('is_error', False) is False:
                    return result('passed', 'Native Agent/Task invocation returned a successful tool result', native_id=block['tool_use_id'])
    if host == 'copilot':
        for event in events:
            data = event.get('data', {})
            if event.get('type') == 'subagent.started' and data.get('agentName') == role and data.get('toolCallId'):
                completed = any(item.get('type') == 'subagent.completed' and item.get('data', {}).get('toolCallId') == data['toolCallId'] for item in events)
                if completed:
                    return result('passed', 'Native subagent lifecycle completed for the requested role', native_id=data['toolCallId'])
    return result('blocked', 'No successful native role lifecycle was captured; assistant prose is not role evidence')


def _codex_delegation(events):
    nodes = {}
    for index, event in enumerate(events):
        if event.get('type') == 'thread.started' and event.get('thread_id'):
            identity = event['thread_id']
            nodes[identity] = {'id': identity, 'role': 'aw-forge', 'parent_id': None, 'started': index, 'origin': 'session', 'role_source': 'current-session coordinator; named profile unverified'}
        if event.get('type') == 'turn.completed':
            for node in nodes.values():
                if node.get('origin') == 'session':
                    node['completed'] = index
        thread = event.get('params', {}).get('thread', {})
        if event.get('method') == 'thread/started' and thread.get('agentRole') in SMOKE_ROLES and thread.get('id'):
            nodes[thread['id']] = {'id': thread['id'], 'role': thread['agentRole'], 'parent_id': thread.get('parentThreadId'), 'started': index}
        item = event.get('item', {})
        if item.get('type') not in CODEX_COLLAB_TYPES:
            continue
        role = item.get('agent_type', item.get('agent_role'))
        if item.get('tool') == 'spawn_agent' and role in SMOKE_ROLES:
            for identity in item.get('receiver_thread_ids', []):
                nodes.setdefault(identity, {'id': identity, 'role': role, 'parent_id': item.get('sender_thread_id'), 'started': index})
        states = item.get('agents_states', {})
        for identity, state in states.items() if isinstance(states, dict) else []:
            if identity in nodes and state.get('status') == 'completed':
                nodes[identity].setdefault('completed', index)
    return list(nodes.values())


def _claude_delegation(events):
    nodes = {}
    for index, event in enumerate(events):
        role = event.get('agent_type', event.get('agent'))
        session = event.get('session_id')
        if event.get('type') == 'system' and event.get('subtype') == 'init' and role in SMOKE_ROLES and session:
            nodes[session] = {'id': session, 'role': role, 'parent_id': None, 'started': index, 'origin': 'session'}
        content = event.get('message', {}).get('content', [])
        for block in content if isinstance(content, list) else []:
            role = block.get('input', {}).get('subagent_type')
            if block.get('type') == 'tool_use' and block.get('name') in ('Agent', 'Task') and role in SMOKE_ROLES and block.get('id'):
                identity = block['id']
                nodes[identity] = {'id': identity, 'role': role, 'parent_id': event.get('parent_tool_use_id') or session,
                                   'started': index, 'origin': 'subagent'}
            identity = block.get('tool_use_id')
            if block.get('type') == 'tool_result' and identity in nodes and not block.get('is_error', False):
                nodes[identity]['completed'] = index
        if event.get('type') == 'result' and session in nodes and not event.get('is_error', False):
            nodes[session]['completed'] = index
    return list(nodes.values())


def _copilot_delegation(events):
    nodes, completions = {}, {}
    for index, event in enumerate(events):
        data = event.get('data', {})
        session = data.get('sessionId', event.get('sessionId'))
        if event.get('type') == 'session.start' and data.get('agentName') in SMOKE_ROLES and session:
            nodes[session] = {'id': session, 'role': data['agentName'], 'parent_id': None, 'started': index, 'origin': 'session'}
        identity = data.get('toolCallId')
        if event.get('type') == 'subagent.started' and data.get('agentName') in SMOKE_ROLES and isinstance(identity, str) and identity:
            nodes[identity] = {'id': identity, 'role': data['agentName'], 'started': index,
                               'parent_id': data.get('parentToolCallId', data.get('parentSessionId', session)),
                               'native_agent_id': event.get('agentId'), 'parent_native_agent_id': data.get('parentId'), 'origin': 'subagent'}
        if event.get('type') == 'subagent.completed' and isinstance(identity, str) and identity in nodes:
            completions.setdefault(identity, (index, data, event.get('agentId')))
        if event.get('type') in ('session.end', 'session.idle') and session in nodes:
            nodes[session]['completed'] = index
    _bind_copilot_workers(nodes, completions, _copilot_task_calls(events))
    return list(nodes.values())


def _copilot_task_calls(events):
    calls = {}
    for index, event in enumerate(events):
        data = event.get('data', {})
        identity = data.get('toolCallId')
        if not isinstance(identity, str) or not identity:
            continue
        if event.get('type') == 'tool.execution_start' and data.get('toolName') == 'task':
            arguments = data.get('arguments', {})
            if isinstance(arguments, dict):
                calls[identity] = {'role': arguments.get('agent_type'), 'parent_id': data.get('parentToolCallId'), 'started': index}
        if event.get('type') == 'tool.execution_complete' and identity in calls:
            calls[identity].setdefault('completed', index)
            calls[identity]['success'] = calls[identity].get('success', True) and data.get('success') is True
    return calls


def _bind_copilot_workers(nodes, completions, calls):
    agent_ids = {node['native_agent_id']: identity for identity, node in nodes.items() if isinstance(node.get('native_agent_id'), str)}
    for identity, node in nodes.items():
        native_parent = node.get('parent_native_agent_id')
        if native_parent is not None:
            node['parent_id'] = agent_ids.get(native_parent) if isinstance(native_parent, str) else None
        if identity not in completions:
            continue
        index, data, native_id = completions[identity]
        if data.get('cancelled') or data.get('success') is False:
            continue
        if node.get('native_agent_id') is None and data.get('success') is True:
            node['completed'] = index
            continue
        call = calls.get(identity, {})
        matches = (native_id == node.get('native_agent_id') and native_id is not None
                   and call.get('role') == node['role'] and call.get('parent_id') == node.get('parent_id')
                   and call.get('success') is True and call.get('started', index) < node['started']
                   and call.get('completed', -1) > node['started'])
        if matches:
            node['completed'] = max(index, call['completed'])


def delegation_graph_result(nodes):
    if not isinstance(nodes, list) or any(not valid_lifecycle(node) for node in nodes):
        return result('blocked', 'Native lifecycle records are malformed', native_lifecycles=[])
    roles = {role: [node for node in nodes if node['role'] == role] for role in SMOKE_ROLES}
    details = {'required_roles': ['aw-forge', 'aw-review-verify'], 'native_lifecycles': nodes}
    required = ['aw-forge', 'aw-review-verify']
    if any(len(roles[role]) != 1 for role in required) or len(roles['aw-backend']) > 1:
        return result('blocked', 'One coordinator and one independent reviewer are required', **details)
    if any(type(node.get('completed')) is not int for node in nodes):
        return result('blocked', 'Native implementation and review must complete', **details)
    forge, reviewer = [roles[role][0] for role in required]
    implementer = roles['aw-backend'][0] if roles['aw-backend'] else forge
    if len({node['id'] for node in nodes}) != len(nodes):
        return result('blocked', 'Implementation and review must use distinct native identities', **details)
    native_ids = [node.get('native_agent_id') for node in nodes]
    if all(native_ids) and len(set(native_ids)) != len(nodes):
        return result('blocked', 'Implementation and review reused a native agent identity', **details)
    if reviewer.get('parent_id') != forge['id']:
        return result('blocked', 'Reviewer must belong to the current coordinator', **details)
    if implementer is not forge and (implementer.get('parent_id') != forge['id'] or implementer['started'] <= forge['started']):
        return result('blocked', 'Contributor must belong to the current coordinator', **details)
    if reviewer['started'] <= implementer['started'] or reviewer['completed'] >= forge['completed']:
        return result('blocked', 'Native lifecycle order does not establish independent review', **details)
    if implementer is not forge and reviewer['started'] <= implementer['completed']:
        return result('blocked', 'Contributor implementation must complete before review', **details)
    return result('passed', 'Native coordinator and independent reviewer completed the single workflow', **details)


def valid_lifecycle(node):
    if not isinstance(node, dict) or not isinstance(node.get('id'), str) or not node['id'] or node.get('role') not in SMOKE_ROLES:
        return False
    if node.get('native_agent_id') is not None and (not isinstance(node['native_agent_id'], str) or not node['native_agent_id']):
        return False
    start, end = node.get('started'), node.get('completed')
    return type(start) is int and start >= 0 and (end is None or type(end) is int and end > start)


def valid_implementation_edit(edit, backend):
    if not isinstance(edit, dict):
        return False
    start, end = edit.get('started'), edit.get('completed')
    return (edit.get('owner') == backend['id'] and type(start) is int and type(end) is int
            and backend['started'] < start <= end < backend['completed'])


def delegation_observation(host, events, fixture=None, main_role=None, completion=None):
    parsers = {'codex': _codex_delegation, 'claude': _claude_delegation, 'copilot': _copilot_delegation}
    nodes = parsers[host](events) if host in parsers else []
    observed = delegation_graph_result(nodes)
    if host == 'codex' and any(node.get('role_source') for node in nodes):
        observed['coordinator_profile_loading'] = 'unverified'
    if main_role == 'aw-forge':
        observed['requested_main_role'] = main_role
        mains = [node for node in nodes if node['role'] == main_role and node.get('origin') == 'session']
        children = [node for node in nodes if node['role'] == main_role and node.get('origin') == 'subagent']
        nested = any(child.get('parent_id') == parent['id'] and type(child.get('completed')) is int
                     and child['started'] > parent['started'] for child in children for parent in mains)
        if nested:
            observed.update(status='failed', reason='Native metadata connects a completed second Forge to the active main Forge; the single-orchestrator contract failed')
        elif children:
            observed.update(status='blocked', reason='Requested main Forge profile conflicts with an observed Forge child; native metadata does not establish an authorized single-Forge topology')
        elif not mains:
            observed.update(status='blocked', reason='Native metadata omits the selected main Forge identity; captured worker lifecycles remain partial evidence')
    if fixture is not None:
        edits = native_edit_observations(host, events, fixture)
        observed['native_implementation_edits'] = edits
        backend = next((node for node in nodes if node['role'] == 'aw-backend'), next((node for node in nodes if node['role'] == 'aw-forge'), None))
        if observed['status'] == 'passed' and (len(edits) != 1 or not valid_implementation_edit(edits[0], backend) or edits[0].get('completed', len(events)) >= next(node['started'] for node in nodes if node['role'] == 'aw-review-verify')):
            observed.update(status='blocked', reason='The implementation edit lacks owner provenance before independent review')
    if completion is not None and (completion.get('exit_code') != 0 or completion.get('timed_out')):
        observed.update(status='blocked', reason='Native delegation phase failed or timed out; partial lifecycle evidence cannot pass')
    return observed


def native_edit_observations(host, events, fixture):
    identities = set(native_edit_events(host, events, fixture))
    edits = {}
    main_id = next((event.get('thread_id') for event in events if event.get('type') == 'thread.started'), None)
    for index, event in enumerate(events):
        item = event.get('item', {})
        if host == 'codex' and item.get('id') in identities:
            identity = item['id']
            edit = edits.setdefault(identity, {'id': identity, 'owner': event.get('thread_id', event.get('threadId', main_id)), 'started': index})
            if event.get('type') == 'item.completed':
                edit['completed'] = index
        if host == 'claude':
            content = event.get('message', {}).get('content', [])
            for block in content if isinstance(content, list) else []:
                if block.get('type') == 'tool_use' and block.get('id') in identities:
                    edits[block['id']] = {'id': block['id'], 'owner': event.get('parent_tool_use_id') or event.get('session_id'), 'started': index}
                if block.get('type') == 'tool_result' and block.get('tool_use_id') in edits and not block.get('is_error', False):
                    edits[block['tool_use_id']]['completed'] = index
        data = event.get('data', {})
        if host == 'copilot' and event.get('type') == 'tool.execution_start' and data.get('toolCallId') in identities:
            edits[data['toolCallId']] = {'id': data['toolCallId'], 'owner': data.get('parentToolCallId') or data.get('sessionId', event.get('sessionId')), 'started': index}
        if host == 'copilot' and event.get('type') == 'tool.execution_complete' and data.get('toolCallId') in edits and data.get('success') is True:
            edits[data['toolCallId']]['completed'] = index
    return list(edits.values())


def native_edit_events(host, events, fixture):
    edits, pending = [], {}
    expected = (Path(fixture) / 'smoke.json').resolve()
    for event in events:
        item = event.get('item', {})
        if host == 'codex' and event.get('type') == 'item.completed' and item.get('type') in ('file_change', 'fileChange'):
            changes = item.get('changes', [])
            if item.get('status') == 'completed' and any(_edit_path(change.get('path'), fixture) == expected for change in changes):
                edits.append(item.get('id'))
        if host == 'claude':
            content = event.get('message', {}).get('content', [])
            for block in content if isinstance(content, list) else []:
                if block.get('type') == 'tool_use' and block.get('name') in ('Write', 'Edit'):
                    if _edit_path(block.get('input', {}).get('file_path'), fixture) == expected:
                        pending[block.get('id')] = True
                if block.get('type') == 'tool_result' and block.get('tool_use_id') in pending and not block.get('is_error', False):
                    edits.append(block['tool_use_id'])
        if host == 'copilot':
            data = event.get('data', {})
            if event.get('type') == 'tool.execution_start' and data.get('toolName') in ('write', 'edit', 'create'):
                arguments = data.get('arguments', {})
                if isinstance(arguments, dict) and _edit_path(arguments.get('path'), fixture) == expected:
                    pending[data.get('toolCallId')] = True
            if event.get('type') == 'tool.execution_complete' and data.get('toolCallId') in pending and data.get('success') is True:
                edits.append(data['toolCallId'])
    return [identity for identity in edits if identity]


def _edit_path(value, fixture):
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    return (path if path.is_absolute() else Path(fixture) / path).resolve()


def native_hook_events(host, events):
    hooks = []
    for event in events:
        if host == 'codex' and event.get('method') == 'hook/completed':
            run = event.get('params', {}).get('run', {})
            if run.get('eventName') == 'postToolUse' and run.get('id'):
                hooks.append({'id': run['id'], 'status': run.get('status'), 'source': run.get('sourcePath'),
                              'tool_id': run.get('toolUseId', run.get('tool_use_id')), 'output': run.get('entries', [])})
        elif host == 'claude' and event.get('type') == 'system' and event.get('subtype') == 'hook_response':
            if event.get('hook_event') == 'PostToolUse' and event.get('hook_id'):
                hooks.append({'id': event['hook_id'], 'status': 'completed' if event.get('exit_code') == 0 else 'failed',
                              'source': event.get('source_path', event.get('hook_name')), 'tool_id': event.get('tool_use_id'),
                              'output': event.get('stdout', '')})
        elif host == 'copilot' and event.get('type') == 'hook.end':
            data = event.get('data', {})
            if data.get('hookType') == 'postToolUse' and data.get('hookId'):
                hooks.append({'id': data['hookId'], 'status': data.get('status'), 'source': data.get('source'),
                              'tool_id': data.get('toolCallId'), 'output': data.get('output')})
    return hooks


def fixture_read_paths(fixture):
    root = Path(fixture).resolve()
    paths = [root / name for name in ('smoke.json', 'AGENTS.md', '.ai/config.json')]
    config = root / '.ai/config.json'
    if config.is_file():
        bundle = (root / '.ai' / json.loads(config.read_text())['bundle']).resolve()
        if not bundle.is_relative_to(root / '.ai'):
            raise ValueError('Fixture read grants must remain inside its selected bundle')
        paths.extend(bundle / 'skills' / name / 'SKILL.md' for name in ('forge', 'task-implement', 'code-review'))
        paths.extend(bundle / 'docs' / name for name in ('COORDINATION.md', 'DELIVERY.md'))
    return paths


def smoke_argv(host, runtime, fixture, prompt, main_role='aw-forge', unattended_authorized=False):
    if host == 'codex':
        return [runtime, 'exec', '--json', '--cd', str(fixture), prompt]
    if host == 'claude':
        target = '/' + str((Path(fixture) / 'smoke.json').resolve())
        reads = ' '.join(f'Read(/{path})' for path in fixture_read_paths(fixture))
        grants = f'{reads} Edit({target}) Agent(aw-backend) Agent(aw-review-verify)'
        return [runtime, '--agent', main_role, '--print', '--verbose', '--output-format', 'stream-json',
                '--include-hook-events', '--forward-subagent-text',
                '--permission-prompts', 'none',
                *(['--permission-mode', 'bypassPermissions'] if unattended_authorized else
                  ['--allowedTools', grants, '--disallowedTools', 'Bash']),
                '--max-budget-usd', '2.00', prompt]
    if host == 'copilot':
        target = str((Path(fixture) / 'smoke.json').resolve())
        reads = [value for path in fixture_read_paths(fixture) for value in ('--allow-tool', f'read({path})')]
        return [runtime, '--agent', main_role, '--no-auto-update', '-C', str(fixture), '--output-format', 'json',
                *(['--allow-all'] if unattended_authorized else
                  ['--allow-tool', f'write({target})', *reads, '--deny-tool', 'shell']),
                '--max-ai-credits', '30', '--max-autopilot-continues', '0', '--prompt', prompt]
    raise ValueError('Cursor UI requires native UI evidence; no substitute CLI is assumed')


def smoke_prompt(nonce, phase, host):
    role = 'aw-forge' if phase == 'pass' else 'aw-backend'
    review = ('After the edit completes, use one native aw-review-verify agent for read-only inspection and wait for its result. '
              'The reviewer must be independent; do not delegate implementation or start another coordinator. ') if phase == 'pass' else ''
    return (f'Authorized bounded agent-workflow host smoke {nonce}. Work only inside this disposable fixture. '
            f'The current {role} session implements directly: use the native file-edit tool once to replace '
            f'smoke.json with {{"value":"{phase}"}}. {review}'
            'This task assigns only the fixture edit, independent review when requested, and observation of installed hooks. '
            'Do not run tests, Git commands, gates, application tasks, configuration changes, trust approval, or credential reads. '
            'Let edit notification hooks return feedback without executing checks. '
            'Report unavailable native roles, denied operations, trust prompts, or authentication failure and stop without retry.')
