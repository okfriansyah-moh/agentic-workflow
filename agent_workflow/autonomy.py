"""Read-only permission diagnostics; configuration is never live execution proof."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
import tomllib


CLAUDE_ROOT_LOCAL_SUPPORTED = os.name != 'nt'
MANAGED_CLAUDE_SETTINGS = (Path('/Library/Application Support/ClaudeCode/managed-settings.json')
                           if os.sys.platform == 'darwin' else Path('/etc/claude-code/managed-settings.json'))

VALUES = {
    'approval_policy': {'never', 'on-request', 'on-failure', 'untrusted'},
    'sandbox_mode': {'danger-full-access', 'workspace-write', 'read-only'},
    'defaultMode': {'default', 'acceptEdits', 'plan', 'dontAsk', 'bypassPermissions', 'autopilot', 'interactive'},
    'defaultPermissionMode': {'default', 'allow-all', 'deny-all'},
    'approvalMode': {'manual', 'unrestricted', 'allowlist'},
    'mode': {'disabled', 'enabled'},
}


def _safe_values(data, fields):
    return {key: value if isinstance(value, str) and value in VALUES[key] else '<unrecognized>'
            for key in fields if (value := data.get(key)) is not None}


def _read(path, layer, fields, nested=None):
    record = {'path': str(path), 'layer': layer, 'status': 'missing', 'settings': {}}
    try:
        content = path.read_text()
        data = tomllib.loads(content) if path.suffix == '.toml' else json.loads(content)
        if not isinstance(data, dict):
            raise ValueError('Expected object')
        selected = data
        for key in nested or ():
            selected = selected.get(key, {})
            if not isinstance(selected, dict):
                raise ValueError('Expected settings object')
        record.update(status='read', settings=_safe_values(selected, fields))
        # Only counts are retained: tool rules can contain private paths or commands.
        record['bypass_disabled'] = selected.get('disableBypassPermissionsMode') == 'disable'
        record['permission_rule_counts'] = {key: len(selected[key]) for key in ('allow', 'deny', 'ask')
                                            if isinstance(selected.get(key), list)}
        return record, data
    except FileNotFoundError:
        return record, {}
    except (OSError, ValueError):
        record['status'] = 'unreadable-or-invalid'
        return record, {}


def _summary(records, expected):
    settings, sources = {}, {}
    for record in records:
        for key, value in record['settings'].items():
            settings[key], sources[key] = value, record['path']
    invalid = any(record['status'] == 'unreadable-or-invalid' for record in records)
    status = ('unknown' if invalid or any(key not in settings or settings[key] == '<unrecognized>' for key in expected)
              else 'unattended' if all(settings[key] == value for key, value in expected.items())
              and not any(item.get('bypass_disabled') for item in records) else 'restricted')
    return {'status': status, 'observed_defaults': settings, 'sources': sources}


def _claude_local_sources(repo, home):
    """Resolve the current CLI's root-local file, retaining the older cwd-local file."""
    starting = repo / '.claude/settings.local.json'
    paths = [(starting, 'project-local')]
    root = next((path for path in (repo, *repo.parents) if (path / '.git').exists()), None)
    if root is None or not CLAUDE_ROOT_LOCAL_SUPPORTED or root == home.resolve():
        return paths, True
    try:
        # Claude keeps local settings beside shared settings for repositories it does not own.
        entries = (root, root / '.git', root / '.claude')
        if any(path.exists() and path.stat().st_uid != os.getuid() for path in entries):
            return paths, True
        observed = subprocess.run(['git', '-C', str(repo), 'worktree', 'list', '--porcelain', '-z'],
                                  stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, timeout=5, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
        first = observed.stdout.split('\0', 1)[0]
        if observed.returncode or not first.startswith('worktree '):
            return paths, False
        main = Path(first.removeprefix('worktree '))
        if not main.is_absolute() or not main.is_dir():
            return paths, False
        main = main.resolve()
        if main == home.resolve() or any(path.exists() and path.stat().st_uid != os.getuid()
                                         for path in (main, main / '.git', main / '.claude')):
            return paths, True
        local = main / '.claude/settings.local.json'
        if local != starting:
            paths.append((local, 'repository-local'))
        return paths, True
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return paths, False


def autonomy_diagnostics(host, home, repo=None, environ=None):
    """Report whitelisted file defaults and override candidates without launching a host."""
    home, repo = Path(home), Path(repo).resolve() if repo else None
    environ = os.environ if environ is None else environ
    records, caveats = [], ['Active session, CLI flags, organization policy and OS controls are unobserved.']
    local_sources_resolved = True

    def read(path, layer, fields, nested=None):
        record, data = _read(path, layer, fields, nested)
        records.append(record)
        return data

    if host == 'codex':
        directory = Path(environ.get('CODEX_HOME') or home / '.codex').expanduser()
        fields = ('approval_policy', 'sandbox_mode')
        paths = [(directory / 'config.toml', 'user')]
        if repo:
            paths += [(parent / '.codex/config.toml', 'project-trust-dependent')
                      for parent in reversed((repo, *repo.parents)) if parent != home]
        for path, layer in paths:
            data = read(path, layer, fields)
            profiles = data.get('profiles', {})
            if isinstance(profiles, dict):
                for index, (name, profile) in enumerate(profiles.items()):
                    if isinstance(profile, dict) and any(key in profile for key in fields):
                        records.append({'path': str(path), 'layer': 'profile', 'profile_index': index,
                                        'selected_in_file': data.get('profile') == name, 'status': 'read',
                                        'settings': _safe_values(profile, fields)})
        # Profiles and project files are candidates, not a claim about runtime selection/trust.
        defaults = [item for item in records if item['layer'] == 'user']
        expected = {'approval_policy': 'never', 'sandbox_mode': 'danger-full-access'}
        caveats.append('Project trust and CLI-selected profiles determine which candidates the host loads.')
    elif host == 'claude':
        fields = ('defaultMode',)
        directory = Path(environ.get('CLAUDE_CONFIG_DIR') or home / '.claude').expanduser()
        paths = [(directory / 'settings.json', 'user')]
        if repo:
            local_paths, local_sources_resolved = _claude_local_sources(repo, home)
            paths += [(repo / '.claude/settings.json', 'project'), *local_paths]
        # Platform policy locations are fixed; no command or remote policy query is performed.
        paths += [(MANAGED_CLAUDE_SETTINGS, 'managed')]
        for path, layer in paths:
            read(path, layer, fields, ('permissions',))
        defaults, expected = records, {'defaultMode': 'bypassPermissions'}
        caveats.append('Deny/ask rules and managed permission restrictions may still block actions; rule contents are omitted.')
        caveats.append('Current CLI repository-local settings use the main checkout on supported owned repositories; older cwd-local settings are also read. SDK and older runtime selection remain unobserved.')
    elif host == 'copilot':
        directory = Path(environ.get('COPILOT_HOME') or home / '.copilot').expanduser()
        read(directory / 'settings.json', 'user', ('defaultPermissionMode', 'defaultMode'))
        defaults, expected = records, {'defaultPermissionMode': 'allow-all', 'defaultMode': 'autopilot'}
        caveats.append('Only user-editable settings.json is read; internal config.json is not a settings source.')
    elif host == 'cursor':
        data = read(home / '.cursor/cli-config.json', 'cli-user', ('approvalMode',))
        sandbox = data.get('sandbox', {})
        if isinstance(sandbox, dict):
            records[0]['settings'].update(_safe_values(sandbox, ('mode',)))
        read(home / '.cursor/permissions.json', 'desktop-user', ('approvalMode',))
        defaults, expected = records[:1], {'approvalMode': 'unrestricted', 'mode': 'disabled'}
        caveats.append('CLI and desktop are separate surfaces; desktop permission-file support depends on the installed runtime.')
    else:
        raise ValueError('Unknown host')
    result = {'configuration': _summary(defaults, expected), 'candidates': records,
              'live_verification': {'status': 'unverified', 'reason': 'No native session was observed by this read-only diagnostic.'},
              'limitations': caveats}
    if host == 'claude':
        result['local_settings_resolution'] = 'resolved' if local_sources_resolved else 'unknown'
        if not local_sources_resolved:
            result['configuration']['status'] = 'unknown'
            result['limitations'].append('Git repository-local settings could not be resolved; no unattended configuration is inferred.')
    if host == 'cursor':
        result['desktop_configuration'] = _summary(records[1:], {'approvalMode': 'unrestricted'})
    return result
