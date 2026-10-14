#!/usr/bin/env python3
"""Verify scanner results using clean, intentionally unsafe and malformed fixtures."""
import argparse
import json
import os
from pathlib import Path
import ssl
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def execute(argv, expected, label, results, env=None):
    run = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
    try:
        document = json.loads(run.stdout)
    except ValueError:
        document = None
    valid = run.returncode == expected if isinstance(expected, int) else run.returncode not in (0, 1)
    results.append({'case': label, 'argv': argv, 'exit_code': run.returncode, 'passed': valid,
                    'expected_exit': expected, 'stderr_tail': run.stderr[-1000:]})
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--semgrep', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory() as state:
        env = dict(os.environ, SEMGREP_SETTINGS_FILE=state + '/settings.yml',
                   SEMGREP_LOG_FILE=state + '/semgrep.log', SEMGREP_ENABLE_VERSION_CHECK='0')
        cert = ssl.get_default_verify_paths().cafile
        if cert:
            env['SSL_CERT_FILE'] = cert
        for mode, expected in [('good', 0), ('bad', 1)]:
            folder = 'tests/fixtures/security/' + mode
            data = execute([str(args.semgrep), 'scan', '--config', 'profiles/security/semgrep.yml', '--metrics', 'off', '--error', '--strict', '--json', folder], expected, 'semgrep-' + mode, results, env)
            if data is not None:
                results[-1]['findings'] = len(data['results'])
                results[-1]['parsed_files'] = len(data.get('paths', {}).get('scanned', []))
                results[-1]['passed'] &= bool(results[-1]['parsed_files']) and not data.get('errors') and (mode != 'bad' or len(data['results']) == 2)
            else:
                results[-1]['passed'] = False
            execute([str(args.tools / 'gitleaks'), 'dir', '--redact', '--no-banner', '--exit-code', '1', '--config', 'profiles/security/gitleaks.toml', folder], expected, 'gitleaks-' + mode, results)
            data = execute([str(args.tools / 'osv-scanner'), 'scan', 'source', '--recursive', '--format', 'json', '--all-packages', folder], expected, 'osv-' + mode, results)
            if data is not None:
                packages = [p for source in data['results'] for p in source['packages']]
                findings = [v for p in packages for v in p.get('vulnerabilities', [])]
                results[-1]['packages'] = len(packages)
                results[-1]['vulnerabilities'] = len(findings)
                results[-1]['passed'] &= bool(packages) and (mode != 'bad' or bool(findings))
            else:
                results[-1]['passed'] = False
        execute([str(args.semgrep), 'scan', '--config', 'tests/fixtures/security/invalid/package-lock.json', '--metrics', 'off', '--strict', 'tests/fixtures/security/good'], 'error', 'semgrep-invalid-config', results, env)
        execute([str(args.tools / 'osv-scanner'), 'scan', 'source', '--recursive', 'tests/fixtures/security/invalid'], 'error', 'osv-invalid-inventory', results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + '\n')
    failed = sum(not item['passed'] for item in results)
    print(json.dumps({'cases': len(results), 'passed': len(results) - failed, 'failed': failed}))
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
