#!/usr/bin/env python3
"""Execute optional pinned web/JVM tools against isolated positive and negative examples."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(argv, cwd, expected, results, label, env=None, marker=None):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, env=env, timeout=180)
    passed = (result.returncode == 0) == (expected == 'pass')
    if marker:
        passed = passed and marker in result.stdout + result.stderr
    results.append({'case': label, 'argv': argv, 'exit_code': result.returncode,
                    'expected': expected, 'expected_finding': marker, 'passed': passed,
                    'output': (result.stdout + result.stderr)[-4000:]})


def web_cases(results):
    web = ROOT / 'tests/fixtures/web'
    bins = web / 'node_modules/.bin'
    if not bins.exists():
        results.append({'case': 'web-tools', 'status': 'blocked', 'reason': 'Run npm ci in tests/fixtures/web'})
        return
    for name, args in [('eslint', ['src']), ('svelte-check', ['--tsconfig', 'tsconfig.json']),
                       ('depcruise', ['src', '--config', '../../../profiles/web/dependency-cruiser.cjs', '--output-type', 'err']),
                       ('vitest', ['run', '--coverage', '--reporter=json', '--outputFile=coverage/test-results.json'])]:
        run([str(bins / name), *args], web, 'pass', results, 'web-' + name)
    bad = web / 'src/bad.ts'
    try:
        bad.write_text('export function tooLong() {\n' + '\n'.join(f'  const v{i} = {i};' for i in range(51)) + '\n}\n')
        run([str(bins / 'eslint'), str(bad)], web, 'fail', results, 'web-function-limit', marker='max-lines-per-function')
        bad.write_text('export const incorrect: number = "text";\n')
        run([str(bins / 'svelte-check'), '--tsconfig', 'tsconfig.json'], web, 'fail', results, 'web-type-error', marker='not assignable')
    finally:
        bad.unlink(missing_ok=True)
    first, second = web / 'src/cycle-a.ts', web / 'src/cycle-b.ts'
    try:
        first.write_text('import { b } from "./cycle-b"; export function a() { return b(); }\n')
        second.write_text('import { a } from "./cycle-a"; export function b() { return a(); }\n')
        run([str(bins / 'depcruise'), 'src', '--config', '../../../profiles/web/dependency-cruiser.cjs', '--output-type', 'err'], web, 'fail', results, 'web-cycle', marker='no-cycles')
    finally:
        first.unlink(missing_ok=True)
        second.unlink(missing_ok=True)


def jvm_cases(tools, results):
    fixture = ROOT / 'tests/fixtures/jvm'
    if not tools or not (tools / 'detekt.jar').exists():
        results.append({'case': 'jvm-tools', 'status': 'blocked', 'reason': 'Supply --jvm-tools containing pinned jars'})
        return
    for name, expected in [('Good.kt', 'pass'), ('Bad.kt', 'fail')]:
        run(['java', '-jar', str(tools / 'detekt.jar'), '--input', str(fixture / name),
             '--config', str(ROOT / 'profiles/kotlin/detekt.yml')], ROOT, expected, results, 'detekt-' + name, marker='NestedBlockDepth' if expected == 'fail' else None)
    with tempfile.TemporaryDirectory() as temporary:
        classes = Path(temporary) / 'classes'
        classes.mkdir()
        deps = os.pathsep.join(str(tools / name) for name in ['archunit.jar', 'slf4j-api.jar'])
        sources = [str(p) for p in (fixture / 'src').rglob('*.java')]
        run(['javac', '-cp', deps, '-d', str(classes), *sources], ROOT, 'pass', results, 'jvm-compile')
        for package, rule, expected in [('fixture.good', 'injection', 'pass'), ('fixture.bad', 'injection', 'fail'), ('fixture.bad', 'cycles', 'fail')]:
            run(['java', '-cp', str(classes) + os.pathsep + deps, 'BoundaryCheck', package, rule], ROOT, expected, results, 'architecture-' + package + '-' + rule, marker='Architecture Violation' if expected == 'fail' else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jvm-tools', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = []
    web_cases(results)
    jvm_cases(args.jvm_tools, results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + '\n')
    failures = [r for r in results if not r.get('passed', False)]
    print(json.dumps({'cases': len(results), 'passed': len(results) - len(failures), 'failed_or_blocked': len(failures)}))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
