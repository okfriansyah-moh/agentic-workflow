"""Native-host verification with explicit proof boundaries and freshness checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time
import uuid

from .host_probes import (CATEGORIES, blank_results, claude_metadata, copilot_metadata, delegation_graph_result, delegation_observation, native_edit_events, native_hook_events,
                          native_skills, result, run_command,
                          sha256_file, smoke_argv, smoke_prompt, valid_implementation_edit)

HOSTS = ('codex', 'claude', 'copilot', 'cursor')
DESKTOP_CODEX = Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')


def read_json(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).is_file() else default


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp-' + uuid.uuid4().hex[:8])
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def selected_bundle(root, scope, home=None):
    home = Path(home or Path.home()).resolve()
    state = home / '.local/share/agent-workflow' if scope == 'global' else Path(root).resolve() / '.ai'
    config = read_json(state / 'config.json')
    if not config or not isinstance(config.get('bundle'), str):
        raise ValueError(f'No selected {scope} workflow bundle at {state}')
    bundle = (state / config['bundle']).resolve()
    if not bundle.is_relative_to(state.resolve()):
        raise ValueError('Selected bundle escapes its installation')
    manifest = read_json(bundle / 'manifest.json')
    if not manifest or not manifest.get('skills'):
        raise ValueError('Selected bundle has no skill manifest')
    return state, bundle, manifest


def runtime_path(host, override=None):
    if override:
        candidate = Path(override).expanduser().resolve()
    elif host == 'codex' and DESKTOP_CODEX.is_file():
        candidate = DESKTOP_CODEX
    elif host == 'cursor':
        candidate = Path('/Applications/Cursor.app/Contents/MacOS/Cursor')
    else:
        found = shutil.which(host)
        candidate = Path(found).resolve() if found else None
    if not candidate or not candidate.is_file():
        return None
    return candidate


def runtime_identity(host, runtime, artifact_dir, timeout, probe_version=True):
    if runtime is None:
        return {'path': None, 'version': None, 'sha256': None, 'surface': 'unavailable'}, None
    surface = 'desktop-engine' if host == 'codex' and runtime.resolve() == DESKTOP_CODEX.resolve() else 'cli'
    if host == 'cursor':
        surface = 'desktop-ui'
        info = runtime.parents[1] / 'Info.plist'
        version = None
        if info.is_file():
            with info.open('rb') as stream:
                version = plistlib.load(stream).get('CFBundleShortVersionString')
        support = cursor_runtime_inputs(runtime)
        return {'path': str(runtime), 'version': version, 'sha256': sha256_file(runtime), 'surface': surface,
                'support_files': support, 'support_sha256': json_hash(support)}, None
    if not probe_version:
        return {'path': str(runtime), 'version': None, 'sha256': sha256_file(runtime), 'surface': surface,
                **support_identity(host, runtime)}, None
    capture = run_command([str(runtime), '--version'], Path(artifact_dir).parent, artifact_dir, 'runtime-version', min(timeout, 15))
    data = capture['capture']
    return {'path': str(runtime), 'version': data['stdout'].strip() if data['exit_code'] == 0 else None,
            'sha256': sha256_file(runtime), 'surface': surface, **support_identity(host, runtime)}, capture['artifact']


def cursor_runtime_inputs(runtime):
    contents = Path(runtime).parents[1]
    paths = [contents / name for name in ('Info.plist', 'Resources/app/package.json', 'Resources/app/product.json')]
    return {str(path): sha256_file(path) if path.is_file() else None for path in paths}


def runtime_support_inputs(host, runtime):
    if host == 'cursor':
        return cursor_runtime_inputs(runtime)
    if host != 'copilot':
        return {}
    package = Path(runtime).resolve().parent
    paths = [package / 'package.json', package / 'index.js']
    for metadata in sorted(package.glob('node_modules/@github/copilot-*/package.json')):
        paths.extend(copilot_platform_inputs(metadata))
    return {str(path): sha256_file(path) if path.is_file() else None for path in paths}


def copilot_platform_inputs(metadata):
    data = read_json(metadata)
    export = data.get('exports') if isinstance(data, dict) else None
    if isinstance(export, dict) and set(export) == {'.'}:
        export = export['.']
    if not isinstance(export, str) or not export.startswith('./'):
        raise ValueError(f'Unsupported Copilot platform package export layout: {metadata}')
    target = (metadata.parent / export).resolve()
    if not target.is_relative_to(metadata.parent.resolve()):
        raise ValueError(f'Copilot platform export escapes its package: {metadata}')
    return [metadata, target]


def support_identity(host, runtime):
    if host not in ('cursor', 'copilot'):
        return {}
    inputs = runtime_support_inputs(host, runtime)
    return {'support_files': inputs, 'support_sha256': json_hash(inputs)}


CLAUDE_CONFIG_DEFAULTS = {
    'mcpServers': {}, 'mcpContextUris': [], 'allowedTools': [], 'disallowedTools': [],
    'permissions': {}, 'permissionMode': None, 'enableAllProjectMcpServers': False,
    'enabledMcpjsonServers': [], 'disabledMcpjsonServers': [], 'enabledMcpServers': [],
    'disabledMcpServers': [], 'hasTrustDialogAccepted': False, 'hasClaudeMdExternalIncludesApproved': False,
}


def claude_user_config_digest(path, project):
    data = read_json(path, {})
    if not isinstance(data, dict) or not isinstance(data.get('projects', {}), dict):
        raise ValueError('Claude user/project configuration must be JSON objects')
    project = Path(project).resolve()
    selected = [value for name, value in data.get('projects', {}).items() if Path(name).expanduser().resolve() == project]
    if any(not isinstance(value, dict) for value in selected):
        raise ValueError('Claude current-project configuration must be a JSON object')
    def settings(value):
        return {name: value.get(name, default) for name, default in CLAUDE_CONFIG_DEFAULTS.items()}
    variants = sorted({json_hash(settings(value)) for value in selected or [{}]})
    return json_hash({'user': settings(data), 'current_project_variants': variants})


def config_snapshot(host, root, scope, bundle, manifest, home=None):
    home, root = Path(home or Path.home()).resolve(), Path(root).resolve()
    roots = [('global', home)] + ([('repo', root)] if scope == 'repo' else [])
    files = {}
    for label, location in roots:
        directory = '.copilot' if host == 'copilot' and label == 'global' else '.github' if host == 'copilot' else '.' + host
        names = {'codex': ('config.toml', 'hooks.json', 'AGENTS.md'),
                 'claude': ('settings.json', 'settings.local.json', 'CLAUDE.md'),
                 'cursor': ('hooks.json', 'mcp.json', 'rules/agent-workflow.mdc', 'cli-config.json', 'permissions.json'),
                 'copilot': ('hooks/agent-workflow.json', 'copilot-instructions.md', 'settings.json', 'config.json', 'mcp-config.json', 'mcp.json')}[host]
        candidates = [location / directory / name for name in names]
        if host == 'claude' and label == 'global':
            candidates.append(location / '.claude.json')
        if host in ('claude', 'copilot') and label == 'repo':
            candidates.append(location / '.mcp.json')
        candidates.extend((location / directory / 'agents').glob('aw-*'))
        skills_dir = location / ('.agents/skills' if host == 'codex' and label == 'repo' else directory + '/skills')
        candidates.extend(skills_dir / skill['name'] / 'SKILL.md' for skill in manifest['skills'])
        for skill in manifest['skills']:
            candidates.extend(path for path in (skills_dir / skill['name']).rglob('*') if path.is_file() and '__pycache__' not in path.parts)
        if label == 'repo':
            candidates.extend(location / name for name in ('AGENTS.md', 'CLAUDE.md', '.ai/config.json', '.ai/gates.json', '.ai/bin/agent-workflow'))
        else:
            candidates.extend(location / name for name in ('.local/share/agent-workflow/config.json', '.local/bin/agent-workflow'))
        for path in candidates:
            key = label + ':' + str(path.relative_to(location))
            if host == 'claude' and path == home / '.claude.json':
                files[key] = claude_user_config_digest(path, root)
            else:
                files[key] = sha256_file(path) if path.is_file() else None
    from .autonomy import autonomy_diagnostics
    for candidate in autonomy_diagnostics(host, home, root if scope == 'repo' else None)['candidates']:
        path = Path(candidate['path'])
        files['autonomy:' + str(path)] = sha256_file(path) if path.is_file() else None
    files['bundle:manifest.json'] = sha256_file(Path(bundle) / 'manifest.json')
    for directory in ('agent_workflow', 'scripts', 'adapters', 'profiles', 'resources'):
        for path in sorted((Path(bundle) / directory).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                files['bundle:' + str(path.relative_to(bundle))] = sha256_file(path)
    return {'sha256': json_hash(files), 'files': files}


def create_fixture(bundle, destination, scope, host, nonce):
    """Install only into a fresh disposable directory, never the project under verification."""
    from .installer import install
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    installed = install(argparse.Namespace(global_install=False, repo=str(destination), home=None,
                                          source=str(bundle), profile='general', command='install'))
    if installed.get('status') != 'installed':
        raise ValueError(f'Fixture installation failed: {installed.get("status")}')
    if scope == 'global':
        for name in ('.codex', '.claude', '.cursor', '.github', '.agents'):
            target = destination / name
            if target.is_dir():
                shutil.rmtree(target)
        for name in ('AGENTS.md', 'CLAUDE.md'):
            (destination / name).unlink(missing_ok=True)
    write_json(destination / 'smoke.json', {'value': 'initial', 'nonce': nonce})
    program = "import json,pathlib,sys; d=json.loads(pathlib.Path('smoke.json').read_text()); print('host-smoke '+d['value']); sys.exit(0 if d['value']=='pass' else 1)"
    write_json(destination / '.ai/gates.json', {'schema_version': 1, 'supported_suffixes': [], 'source_exclude': ['**/*'],
              'checks': [{'id': 'native-host-smoke', 'stage': 'fast', 'required': True, 'kind': 'check',
                          'argv': [sys.executable, '-c', program]}]})
    subprocess.run(['git', 'init', '-q', str(destination)], check=True, capture_output=True)
    return destination


def _native_catalog(host, runtime, fixture, artifacts, expected, scope, timeout):
    observed = {}
    if host == 'codex':
        return {'discovery': result('blocked', 'The exec stream has no native role catalog; no desktop UI loading is inferred'),
                'skills': result('blocked', 'Native skills/list requires a supported app-server metadata connection; this probe does not start one against the real user home')}, []
    if host != 'copilot':
        return observed, []
    observed['discovery'] = result('blocked', 'Native custom-agent session metadata has not been captured; the interactive /agent picker is also available')
    captures = []
    for name in ('skill', 'instruction'):
        capture = run_command([str(runtime), '--no-auto-update', '-C', str(fixture), name, 'list', '--json'],
                              fixture, artifacts, name + '-catalog', min(timeout, 30))
        captures.append(capture['artifact'])
        if capture['capture']['exit_code']:
            observed['skills' if name == 'skill' else 'instruction_sources'] = result('blocked', f'Native {name} discovery failed', [capture['artifact']])
            continue
        try:
            payload = json.loads(capture['capture']['stdout'])
        except ValueError:
            continue
        if name == 'skill':
            observed['skills'] = native_skills(host, payload, expected, scope, fixture)
            observed['skills']['artifacts'] = [capture['artifact']]
        else:
            observed['instruction_sources'] = result('passed', 'Native instruction sources enumerated', [capture['artifact']], source_count=len(payload) if isinstance(payload, list) else 0)
    return observed, captures


def _gate_artifacts(fixture):
    artifacts = []
    for path in sorted((fixture / '.ai/reports').glob('*/result.json')):
        payload = read_json(path, {})
        if any(check.get('id') == 'native-host-smoke' for check in payload.get('results', [])):
            artifacts.append({'path': str(path), 'sha256': sha256_file(path), 'status': payload.get('status'),
                              'fingerprint': payload.get('input_fingerprint'), 'timestamp': payload.get('timestamp')})
    return artifacts


def _run_smoke(host, runtime, fixture, artifact_dir, expected_roles, expected_skills, timeout, nonce, scope, unattended_authorized=False):
    all_events, delegation_events, captures, phases = [], [], [], []
    delegation_completion = None
    for phase in ('pass', 'fail'):
        before = {item['path'] for item in _gate_artifacts(fixture)}
        prompt = smoke_prompt(nonce, phase, host)
        argv = smoke_argv(host, str(runtime), fixture, prompt, 'aw-forge' if phase == 'pass' else 'aw-backend', unattended_authorized)
        capture = run_command(argv, fixture, artifact_dir, phase + '-native-smoke', timeout)
        captures.append(capture['artifact'])
        events = capture['capture']['events']
        all_events.extend(events)
        if phase == 'pass':
            delegation_events = events
            delegation_completion = capture['capture']
        gates = [item for item in _gate_artifacts(fixture) if item['path'] not in before]
        phases.append({'phase': phase, 'exit_code': capture['capture']['exit_code'], 'timed_out': capture['capture']['timed_out'], 'hook_events': native_hook_events(host, events),
                       'gate_artifacts': gates, 'native_edit_ids': native_edit_events(host, events, fixture), 'actual_value': read_json(fixture / 'smoke.json', {}).get('value'),
                       'output_truncated': capture['capture']['truncated']})
        if capture['capture']['exit_code'] != 0 or phases[-1]['actual_value'] != phase:
            break  # Authentication, permission, trust and runtime errors never trigger hidden retries.
    found = claude_metadata(all_events, expected_roles, expected_skills, scope, fixture) if host == 'claude' else {}
    if host == 'copilot':
        found.update(copilot_metadata(all_events, expected_roles, expected_skills, scope, fixture))
    main_role = 'aw-forge' if host in ('claude', 'copilot') else None
    found['role_invocation'] = delegation_observation(host, delegation_events, fixture, main_role, delegation_completion)
    for value in found.values():
        value['artifacts'] = captures
    suffix = {'codex': '.codex/hooks.json', 'claude': '.claude/settings.json', 'copilot': '.github/hooks/agent-workflow.json'}[host]
    sources = [str((Path(fixture) / suffix).resolve())]
    if host != 'copilot':
        sources.append(str((Path.home() / suffix).resolve()))
    found['hooks'] = _hook_verdict(phases, captures, sources)
    found['trust'] = result('passed', 'Installed hooks executed through native host without trust override', captures) if found['hooks']['status'] == 'passed' else result('blocked', 'Native hook trust/execution has not been established; no trust record was changed', captures)
    return found, captures, phases


def _hook_verdict(phases, captures, expected_sources=()):
    if len(phases) != 2:
        return result('blocked', 'Both passing and failing native edits were not completed', captures, phases=phases)
    for phase in phases:
        expected = 'passed' if phase['phase'] == 'pass' else 'failed'
        if phase.get('exit_code') != 0 or phase.get('timed_out'):
            return result('blocked', 'Native phase failed or timed out; partial hook events cannot establish complete execution', captures, phases=phases)
        if phase['actual_value'] != phase['phase'] or phase['output_truncated'] or len(phase.get('native_edit_ids', [])) != 1:
            return result('blocked', 'Native edit or complete native event capture is missing', captures, phases=phases)
        matching = [event for event in phase['hook_events'] if event.get('source') in expected_sources
                    and event.get('tool_id') == phase['native_edit_ids'][0] and event.get('id')]
        if not matching:
            return result('blocked', 'Native hook source and edit correlation are unavailable; gate files alone cannot establish execution', captures, phases=phases)
        phase['matched_hook_events'] = matching
        if not all(event.get('status') in ('completed', 'success', 'succeeded') for event in matching):
            return result('blocked', 'Native hook execution did not complete successfully', captures, phases=phases)
        if len(phase['gate_artifacts']) != 1:
            return result('failed', 'Expected one gate run per edit after same-event deduplication', captures, phases=phases)
        if phase['gate_artifacts'][0]['status'] != expected:
            return result('failed', 'Native hook did not capture the expected passing/failing result', captures, phases=phases)
    fingerprints = [phase['gate_artifacts'][0].get('fingerprint') for phase in phases]
    if not all(fingerprints) or fingerprints[0] == fingerprints[1]:
        return result('blocked', 'Hook receipts do not distinguish the two edited input fingerprints', captures, phases=phases)
    outputs = phases[1]['matched_hook_events']
    if not any('Workflow fast checks need attention' in json.dumps(item.get('output')) for item in outputs):
        return result('blocked', 'Failure feedback from the native hook was not captured', captures, phases=phases)
    return result('passed', 'Native edits produced one passing and one failing gate with visible failure feedback', captures, phases=phases)


def import_ui_evidence(path, record, attested):
    evidence = read_json(path, {})
    if not attested:
        raise ValueError('UI import requires --attest-ui: the recorder must attest that linked captures came from the named native tool')
    runtime = record.get('runtime', {})
    if not runtime.get('path') or not runtime.get('sha256') or not Path(runtime['path']).is_file() or sha256_file(runtime['path']) != runtime['sha256']:
        raise ValueError('UI evidence requires a present verified native runtime executable')
    for field in ('host', 'scope', 'root', 'config_sha256'):
        expected = record['configuration']['sha256'] if field == 'config_sha256' else record[field]
        if evidence.get(field) != expected:
            raise ValueError(f'UI evidence does not match {field}')
    if evidence.get('runtime_sha256') != record['runtime']['sha256']:
        raise ValueError('UI evidence runtime is stale or belongs to another executable')
    if record['host'] in ('cursor', 'copilot') and evidence.get('runtime_support_sha256') != json_hash(runtime.get('support_files')):
        raise ValueError('UI evidence supporting runtime metadata is stale or missing')
    if evidence.get('provider') not in ('cua', 'native-host-ui') or not evidence.get('observer') or not evidence.get('tool_call_ids'):
        raise ValueError('UI evidence needs an identified native capture provider, observer and tool-call IDs')
    if not isinstance(evidence.get('captured_at'), (int, float)) or not -60 <= time.time() - evidence['captured_at'] <= 86400:
        raise ValueError('UI evidence capture is missing or older than 24 hours')
    for category, observation in evidence.get('observations', {}).items():
        if category not in CATEGORIES or observation.get('status') not in ('passed', 'failed', 'blocked'):
            raise ValueError('Unsupported UI observation category/status')
        if not observation.get('artifacts') or not observation.get('native_identifiers') or not observation.get('observed'):
            raise ValueError('Each UI observation needs captures, native identifiers and a concrete observation')
        if category == 'role_invocation' and observation['status'] == 'passed':
            graph = delegation_graph_result(observation.get('native_lifecycles', []))
            backend = next((node for node in graph['native_lifecycles'] if node['role'] == 'aw-backend'), {})
            if graph['status'] != 'passed' or not valid_implementation_edit(observation.get('implementation_edit', {}), backend):
                raise ValueError('UI delegation requires Forge, backend and reviewer lifecycles with parent/order and backend edit ownership')
        for artifact in observation['artifacts']:
            if not Path(artifact['path']).is_file() or sha256_file(artifact['path']) != artifact.get('sha256'):
                raise ValueError('UI capture is missing or changed')
        record['results'][category] = {**observation, 'proof_boundary': 'observer-attested-native-ui',
                                      'observer': evidence['observer'], 'tool_call_ids': evidence['tool_call_ids']}
    record['ui_attestation'] = {'path': str(Path(path).resolve()), 'sha256': sha256_file(path),
                              'note': 'Artifact integrity and observer provenance checked; JSON cannot cryptographically authenticate a computer-use provider.'}
    record['target'] = {'kind': 'observed-installation', 'path': record['root']}


def verification_status(results):
    statuses = [results[name]['status'] for name in CATEGORIES]
    return 'failed' if 'failed' in statuses else 'passed' if all(status == 'passed' for status in statuses) else 'blocked'


def _verify_fixture(args, scope, bundle, manifest, directory, record):
    fixture = create_fixture(bundle, directory / 'fixture', scope, args.host, record['id'])
    record['fixture'] = str(fixture)
    _, fixture_bundle, fixture_manifest = selected_bundle(fixture, 'repo', record['home'])
    record['fixture_bundle'] = str(fixture_bundle)
    record['fixture_configuration'] = config_snapshot(args.host, fixture, 'repo', fixture_bundle, fixture_manifest, record['home'])
    expected_skills = [item['name'] for item in manifest['skills']]
    catalog = read_json(bundle / 'agents/catalog.json', {})
    expected_roles = ['aw-' + role['id'] for role in catalog.get('roles', [])]
    if not expected_roles:
        raise ValueError('The selected bundle has no expected role catalog')
    runtime = Path(record['runtime']['path'])
    found, artifacts = _native_catalog(args.host, runtime, fixture, directory, expected_skills, scope, args.timeout)
    record['results'].update(found)
    record['artifacts'].extend(artifacts)
    smoke, artifacts, phases = _run_smoke(args.host, runtime, fixture, directory, expected_roles, expected_skills, args.timeout, record['id'], scope, getattr(args, 'unattended_authorized', False))
    record['results'].update(smoke)
    for value in record['results'].values():
        value['proof_boundary'] = 'native-disposable-fixture'
    record['artifacts'].extend(artifacts)
    record['fixture'], record['phases'] = str(fixture), phases
    record['target'] = {'kind': 'disposable-fixture', 'path': str(fixture), 'source_root': record['root']}
    record['installation_loading'] = 'unverified'
    if args.host == 'codex':
        record['runtime']['proof_note'] = 'Embedded engine process when selected; this does not prove desktop UI loading. No new app-server was started against the real user home.'


def fixture_snapshot(record):
    _, bundle, manifest = selected_bundle(record['fixture'], 'repo', record['home'])
    return config_snapshot(record['host'], record['fixture'], 'repo', bundle, manifest, record['home'])


def verify_one(args, scope):
    root, home = Path(args.repo or '.').resolve(), Path.home().resolve()
    if scope == 'global':
        root = home
    state, bundle, manifest = selected_bundle(root, scope, home)
    run_id = time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
    directory = state / 'state/host-verifications' / run_id
    if args.live:
        directory.mkdir(parents=True, exist_ok=False)
    runtime = runtime_path(args.host, args.runtime)
    identity, version_artifact = runtime_identity(args.host, runtime, directory, args.timeout, probe_version=args.live)
    snapshot = config_snapshot(args.host, root, scope, bundle, manifest, home)
    record = {'schema_version': 1, 'id': run_id, 'host': args.host, 'scope': scope, 'root': str(root),
              'home': str(home), 'bundle': str(bundle), 'runtime': identity, 'configuration': snapshot,
              'unattended_authorized': bool(getattr(args, 'unattended_authorized', False)),
              'approval_observation': {'status': 'unverified', 'reason': 'Inspect retained native events and actual UI prompts; configuration alone does not establish prompt-free execution.'},
              'created_at': time.time(), 'results': blank_results('Native verification has not run'),
              'artifacts': [version_artifact] if version_artifact else [], 'live_requested': bool(args.live)}
    if not args.live:
        record['status'] = 'blocked'
        record['reason'] = 'Add --live for authorized native probes; structure checks cannot establish native loading'
        return record
    if args.ui_evidence:
        import_ui_evidence(args.ui_evidence, record, args.attest_ui)
    elif runtime is None:
        record['results'] = blank_results('The selected native runtime is unavailable')
    elif args.host == 'cursor':
        record['results'] = blank_results('Use Cursor native UI captures with --ui-evidence and --attest-ui; no CLI fallback represents this GUI')
    else:
        _verify_fixture(args, scope, bundle, manifest, directory, record)
    after = config_snapshot(args.host, root, scope, bundle, manifest, home)
    if after['sha256'] != snapshot['sha256']:
        record['results'] = {name: result('blocked', 'Native configuration changed during verification; inspect changes and rerun') for name in CATEGORIES}
    if record.get('fixture'):
        after = fixture_snapshot(record)
        if after['sha256'] != record['fixture_configuration']['sha256']:
            record['results'] = blank_results('Native fixture configuration changed during verification')
    record['status'] = verification_status(record['results'])
    write_json(directory / 'verification.json', record)
    write_json(state / 'state/host-verifications' / f'latest-{args.host}-{scope}.json', record)
    return {**record, 'record_path': str(directory / 'verification.json')}


def _artifact_entries(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield value
        for child in value.values():
            yield from _artifact_entries(child)
    elif isinstance(value, list):
        for child in value:
            yield from _artifact_entries(child)


def check_verification_freshness(record):
    stale = []
    runtime = record.get('runtime', {})
    path = runtime.get('path')
    if not path or not Path(path).is_file() or sha256_file(path) != runtime.get('sha256'):
        stale.append('Runtime executable is missing or changed')
    try:
        if record.get('host') in ('cursor', 'copilot') and path and runtime_support_inputs(record['host'], path) != runtime.get('support_files'):
            stale.append(f'{record["host"].title()} application version or supporting runtime inputs changed')
    except (OSError, ValueError) as exc:
        stale.append(f'Supporting runtime inputs are unreadable or unsupported: {exc}')
    try:
        manifest = read_json(Path(record['bundle']) / 'manifest.json')
        current = config_snapshot(record['host'], record['root'], record['scope'], record['bundle'], manifest, record['home'])
        if current['sha256'] != record['configuration']['sha256']:
            stale.append('Native configuration, selected bundle, role or skill inputs changed')
    except (OSError, KeyError, TypeError, ValueError):
        stale.append('Configuration inputs are missing or unreadable')
    if record.get('fixture'):
        try:
            current = fixture_snapshot(record)
            if current['sha256'] != record.get('fixture_configuration', {}).get('sha256'):
                stale.append('Native fixture configuration changed')
        except (OSError, KeyError, TypeError, ValueError):
            stale.append('Native fixture inputs are missing or unreadable')
    evidence = [record.get('results', {}), record.get('artifacts', []), record.get('ui_attestation', {})]
    for artifact in _artifact_entries(evidence):
        if not Path(artifact['path']).is_file() or sha256_file(artifact['path']) != artifact['sha256']:
            stale.append('Native evidence artifact is missing or changed: ' + artifact['path'])
    return stale


def summarize_host_verifications(root, state_root, global_install):
    scope = 'global' if global_install else 'repo'
    summary = {}
    for host in HOSTS:
        path = Path(state_root) / 'state/host-verifications' / f'latest-{host}-{scope}.json'
        try:
            record = read_json(path)
        except (OSError, ValueError):
            summary[host] = {'status': 'blocked', 'reason': 'Saved verification record is unreadable'}
            continue
        if not record:
            summary[host] = {'status': 'unverified', 'reason': 'No saved native verification record'}
            continue
        expected_home = Path(root).resolve() if global_install else Path.home().resolve()
        binding = (record.get('host') == host and record.get('scope') == scope
                   and Path(record.get('root', '')).resolve() == Path(root).resolve()
                   and Path(record.get('home', '')).resolve() == expected_home)
        stale = check_verification_freshness(record) if binding else ['Saved record belongs to a different installation, scope or host']
        results = record.get('results', {})
        status = record.get('status', 'blocked')
        if record.get('target', {}).get('kind') == 'disposable-fixture':
            status = 'fixture-' + status
        summary[host] = {'status': 'stale' if stale else status, 'record': str(path),
                         'target': record.get('target'), 'installation_loading': record.get('installation_loading', 'unverified'),
                         'runtime': record.get('runtime'), 'stale_reasons': stale,
                         'results': {name: {'status': 'stale' if stale and value.get('status') == 'passed' else value.get('status'),
                                            'proof_boundary': value.get('proof_boundary'),
                                            'reason': value.get('reason', value.get('observed'))}
                                     for name, value in results.items()}}
    return summary


def verify_host(args):
    if not 1 <= args.timeout <= 300:
        raise ValueError('Native probe timeout must be between 1 and 300 seconds per bounded phase')
    scopes = ('global', 'repo') if args.scope == 'both' else (args.scope,)
    results = []
    for scope in scopes:
        try:
            results.append(verify_one(args, scope))
        except (OSError, ValueError) as exc:
            results.append({'host': args.host, 'scope': scope, 'status': 'blocked',
                            'results': blank_results(str(exc))})
    status = 'failed' if any(item['status'] == 'failed' for item in results) else 'passed' if all(item['status'] == 'passed' for item in results) else 'blocked'
    return {'status': status, 'host': args.host, 'verifications': results}


def register(subparsers):
    parser = subparsers.add_parser('verify-host', help='Capture native loading evidence separately from configuration syntax')
    parser.add_argument('--host', required=True, choices=HOSTS)
    parser.add_argument('--scope', required=True, choices=('global', 'repo', 'both'))
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--unattended-authorized', action='store_true',
                        help='Explicit user authorization for unattended disposable native checks; broadens only session permissions')
    parser.add_argument('--repo', default='.')
    parser.add_argument('--runtime', help='Exact CLI or application executable; never inferred from another installed version')
    parser.add_argument('--timeout', type=int, default=90)
    parser.add_argument('--ui-evidence', help='Observer-attested native UI evidence JSON with artifact, runtime and config hashes')
    parser.add_argument('--attest-ui', action='store_true', help='Attest that UI records were captured through the named native tool')
    parser.set_defaults(handler=verify_host)
