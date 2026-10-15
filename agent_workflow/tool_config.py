"""Field-owned hosted MCP configuration and secret-free connectivity checks."""
import json
import os
from pathlib import Path
import tomllib
import urllib.error
import urllib.request

from .tool_runtime import digest, read_lock, safe_path


HOST_PATHS = {
    'codex': ('.codex/config.toml', '.codex/config.toml'),
    'claude': ('.claude.json', '.mcp.json'),
    'cursor': ('.cursor/mcp.json', '.cursor/mcp.json'),
    'copilot': ('.copilot/mcp-config.json', '.github/mcp.json'),
}
START = '# BEGIN agent-workflow Context7\n'
END = '# END agent-workflow Context7\n'
MISSING = object()


def configs(home, repo=None, auth='oauth'):
    lock = read_lock()['context7']
    endpoint = lock['oauth_endpoint'] if auth == 'oauth' else lock['endpoint']
    root = Path(repo or home)
    result = []
    for host, names in HOST_PATHS.items():
        value = {'url': endpoint}
        if host in ('claude', 'copilot'):
            value['type'] = 'http'
        if host == 'copilot':
            value['tools'] = lock['tools']
        result.append({'host': host, 'path': str(safe_path(root, names[int(repo is not None)])),
                       'value': value, 'scope': 'repo' if repo else 'global', 'auth': auth})
    return result


def current_field(config):
    path = Path(config['path'])
    content = path.read_text() if path.exists() else ''
    if config['host'] == 'codex':
        parsed = tomllib.loads(content)
        servers = parsed.get('mcp_servers', {})
        if not isinstance(servers, dict):
            raise ValueError('MCP configuration must contain an object of servers')
        value = servers.get('context7', MISSING)
    else:
        parsed = json.loads(content or '{}')
        if not isinstance(parsed, dict) or not isinstance(parsed.get('mcpServers', {}), dict):
            raise ValueError('MCP configuration must contain an object of servers')
        value = parsed.get('mcpServers', {}).get('context7', MISSING)
    return content, parsed, value


def block(config):
    return START + '[mcp_servers.context7]\nurl = ' + json.dumps(config['value']['url']) + '\n' + END


def encoded_add(config, original, parsed):
    if config['host'] == 'codex':
        return original + ('\n' if original and not original.endswith('\n') else '') + '\n' + block(config)
    parsed.setdefault('mcpServers', {})['context7'] = config['value']
    return json.dumps(parsed, indent=2) + '\n'


def write_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError('MCP configuration cannot be a symbolic link')
    path.write_text(content)


def install_configs(home, repo=None, auth='oauth', existing=()):
    plans = []
    records = []
    prior = {record['path']: record for record in existing}
    for config in configs(home, repo, auth):
        original, parsed, value = current_field(config)
        if value is not MISSING and value != config['value']:
            raise ValueError(f"Existing Context7 configuration conflicts for {config['host']}; preserved")
        if value is not MISSING:
            records.append(prior.get(config['path'], {**config, 'owned': False}))
            continue
        plans.append((config, original, encoded_add(config, original, parsed)))
    originals = []
    try:
        for config, original, updated in plans:
            path = Path(config['path'])
            if (path.read_text() if path.exists() else '') != original:
                raise ValueError('MCP configuration changed during installation; retry after review')
            existed = path.exists()
            originals.append((config, original, updated, existed))
            write_text(path, updated)
            records.append({**config, 'owned': True, 'created_file': not existed,
                            'backup': {'field_existed': False},
                            'managed_sha256': digest(json.dumps(config['value'], sort_keys=True).encode())})
    except BaseException:
        for config, original, updated, existed in reversed(originals):
            rollback_config(config, original, updated, existed)
        raise
    return records



def rollback_config(config, original, updated, existed):
    path = Path(config['path'])
    actual = path.read_text() if path.exists() else ''
    if actual in (original, updated):
        if existed:
            path.write_text(original)
        else:
            path.unlink(missing_ok=True)
    elif path.exists():
        remove_config({**config, 'owned': True, 'created_file': not existed})


def inspect_config(record):
    _, _, value = current_field(record)
    if value is MISSING:
        return {'host': record['host'], 'status': 'missing'}
    status = 'configured' if value == record['value'] else 'modified'
    return {'host': record['host'], 'scope': record['scope'], 'status': status,
            'authentication': 'unverified' if record['auth'] == 'oauth' else 'anonymous-limited',
            'owned': record['owned']}


def remove_config(record):
    if not record['owned']:
        return 'preserved-unowned'
    original, parsed, value = current_field(record)
    if value is MISSING:
        return 'already-absent'
    if value != record['value']:
        return 'preserved-modified'
    path = Path(record['path'])
    if record['host'] == 'codex':
        owned = block(record)
        if original.count(owned) != 1:
            return 'preserved-modified'
        updated = original.replace(owned, '', 1)
        empty = not updated.strip()
    else:
        del parsed['mcpServers']['context7']
        if not parsed['mcpServers']:
            del parsed['mcpServers']
        updated = json.dumps(parsed, indent=2) + '\n'
        empty = not parsed
    if record.get('created_file') and empty:
        path.unlink()
    else:
        write_text(path, updated)
    return 'removed'


def parse_rpc(body):
    text = body.decode('utf-8')
    if text.lstrip().startswith('{'):
        return json.loads(text)
    for line in text.splitlines():
        if line.startswith('data:'):
            value = json.loads(line[5:].strip())
            if 'result' in value or 'error' in value:
                return value
    raise ValueError('MCP server did not return a JSON-RPC response')


def rpc_request(payload, session=None):
    lock = read_lock()['context7']
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
               'MCP-Protocol-Version': lock['protocol_version']}
    if session:
        headers['Mcp-Session-Id'] = session
    if os.environ.get('CONTEXT7_API_KEY'):
        headers['CONTEXT7_API_KEY'] = os.environ['CONTEXT7_API_KEY']
    request = urllib.request.Request(lock['endpoint'], json.dumps(payload).encode(), headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read(1024 * 1024)
        return (parse_rpc(body) if body else {}), response.headers.get('Mcp-Session-Id')


def probe_context7():
    authentication = 'api-key-provided' if os.environ.get('CONTEXT7_API_KEY') else 'anonymous'
    try:
        initialized, session = rpc_request({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
            'params': {'protocolVersion': read_lock()['context7']['protocol_version'],
                       'capabilities': {}, 'clientInfo': {'name': 'agent-workflow', 'version': '1.1.0'}}})
        if 'error' in initialized:
            return {'status': 'protocol-error', 'authentication': authentication}
        rpc_request({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, session)
        listing, _ = rpc_request({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'}, session)
        names = {tool.get('name') for tool in listing.get('result', {}).get('tools', [])}
        expected = set(read_lock()['context7']['tools'])
        available = sorted(names & expected)
        return {'status': 'reachable' if expected <= names else 'missing-tools',
                'authentication': authentication, 'tools': available, 'host_oauth_verified': False}
    except urllib.error.HTTPError as error:
        category = {401: 'authentication-required', 403: 'access-denied', 429: 'rate-limited'}.get(error.code, 'unavailable')
        return {'status': category, 'http_status': error.code, 'authentication': authentication}
    except (OSError, ValueError, urllib.error.URLError):
        return {'status': 'unavailable', 'authentication': authentication}
