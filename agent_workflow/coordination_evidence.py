"""Capture command results and verify evidence provenance and required boundaries."""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from .coordination_state import (CoordinationError, changed_files, check_contract, get_claim, input_snapshot,
                                 read_json, registry, repository, revision, safe_relative, write_json)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _artifact(repo, value):
    relative = safe_relative(repo, value)
    path = repository(repo) / relative
    if not path.is_file() or path.is_symlink():
        raise CoordinationError(f'Artifact must be a retained regular file: {value}')
    return path


def _test_result(repo, command, started, previous=None):
    report = command.get('test_report')
    if not isinstance(report, dict):
        return {'status': 'blocked', 'reason': 'Test command requires a machine-readable test_report'}
    path = _artifact(repo, report['path'])
    stat = path.stat()
    current = {'mtime_ns': stat.st_mtime_ns, 'size': stat.st_size, 'sha256': digest(path)}
    if stat.st_mtime < started - 1 or current == previous:
        return {'status': 'blocked', 'reason': 'Test report was not freshly produced by this command'}
    if report.get('format') == 'junit':
        root = ET.parse(path).getroot()
        cases = list(root.iter('testcase'))
        executed = len([case for case in cases if case.find('skipped') is None])
        failed = len([case for case in cases if case.find('failure') is not None or case.find('error') is not None])
        selected = len(cases)
    elif report.get('format') == 'vitest':
        data = read_json(path)
        selected = data['numTotalTests']
        executed = data['numPassedTests'] + data['numFailedTests']
        failed = data['numFailedTests']
    elif report.get('format') == 'workflow-test':
        data = read_json(path)
        selected, executed, failed = data['selected'], data['executed'], data['failed']
    else:
        return {'status': 'blocked', 'reason': 'Unsupported test report format'}
    valid = all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in (selected, executed, failed))
    passed = valid and selected > 0 and executed == selected and failed == 0
    return {'status': 'passed' if passed else 'blocked', 'selected': selected, 'executed': executed,
            'failed': failed, 'path': report['path'], 'sha256': digest(path)}


def _run(repo, command, output, index):
    command = check_contract(command)
    argv = command.get('argv')
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or '\0' in arg for arg in argv):
        raise CoordinationError('Every command needs a nonempty string argv array')
    if not command.get('id'):
        raise CoordinationError('Every command requires a check ID')
    cwd = repository(repo)
    if command.get('cwd') not in (None, '.'):
        cwd = cwd / safe_relative(repo, command['cwd'])
    previous = None
    if command['kind'] == 'test':
        report_path = repository(repo) / safe_relative(repo, command['test_report']['path'])
        if report_path.is_file():
            stat = report_path.stat()
            previous = {'mtime_ns': stat.st_mtime_ns, 'size': stat.st_size, 'sha256': digest(report_path)}
    started = time.time()
    result = {'id': command['id'], 'argv': argv, 'kind': command['kind'], 'contract': command, 'cwd': str(cwd), 'started_at': started}
    try:
        run = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=min(command.get('timeout', 300), 3600))
        stdout, stderr, exit_code = run.stdout, run.stderr, run.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        stdout = getattr(exc, 'stdout', None) or b''
        stderr = getattr(exc, 'stderr', None) or str(exc).encode('utf-8')
        exit_code = 124 if isinstance(exc, subprocess.TimeoutExpired) else 127
    logs = {}
    for name, data in (('stdout', stdout), ('stderr', stderr)):
        path = output / f'{index:02d}-{name}.log'
        path.write_bytes(data)
        logs[name] = {'path': str(path.relative_to(repository(repo))), 'sha256': digest(path)}
    result.update(exit_code=exit_code, finished_at=time.time(), logs=logs)
    if command.get('kind') == 'test':
        try:
            result['test_report_before'] = previous
            result['test_result'] = _test_result(repo, command, started, previous)
        except (ValueError, OSError, KeyError, ET.ParseError) as exc:
            result['test_result'] = {'status': 'blocked', 'reason': str(exc)}
    return result


def _receipt_selection(root, spec, claim):
    if not spec.get('selection_id'):
        return None
    from .selection import get_selection, require_checkpoint
    with registry(root) as state:
        selected = dict(get_selection(state, spec['selection_id'], spec['owner']))
        require_checkpoint(selected)
        if state['corrections'].get(selected['id'], 0) >= 2:
            raise CoordinationError('Two correction rounds failed; retain work and report the required blocker')
    if selected['status'] == 'accepted':
        raise CoordinationError('Selection already accepted; start a new requested selection for changed work')
    if claim.get('role') != 'integrator' and set(selected['task_ids']) - set(claim['task_ids']):
        raise CoordinationError('Final checks require ownership of the entire selection or its integration lane')
    return selected


def capture_receipt(repo, spec):
    root = repository(repo)
    with registry(root) as state:
        claim = dict(get_claim(state, spec['claim_id'], spec['owner']))
        if not claim.get('worktree') or root != Path(claim['worktree']).resolve():
            raise CoordinationError('Capture implementation checks in the assigned lane worktree')
    selected = _receipt_selection(root, spec, claim)
    commands = spec.get('commands', [])
    ids = [command.get('id') for command in commands]
    if not commands or len(ids) != len(set(ids)):
        raise CoordinationError('A receipt needs nonempty checks with distinct IDs')
    required = {check['id']: check for check in claim['required_checks']}
    if selected is not None:
        for check in selected['required_checks']:
            if check['id'] in required and required[check['id']] != check:
                raise CoordinationError('Selection and claim required check contracts disagree')
            required[check['id']] = check
    contracts = {command['id']: check_contract(command) for command in commands}
    if any(contracts.get(identity) != contract for identity, contract in required.items()):
        raise CoordinationError('Receipt commands do not match the exact required check contracts')
    receipt_id = 'run-' + uuid.uuid4().hex
    output = root / '.ai/evidence' / receipt_id
    output.mkdir(parents=True)
    before = input_snapshot(root)
    tested_revision = revision(root)
    results = [_run(root, command, output, n) for n, command in enumerate(commands)]
    after = input_snapshot(root)
    errors = _receipt_errors(results, before, after)
    receipt = {
        'schema_version': 1, 'id': receipt_id, 'status': 'passed' if not errors else 'blocked',
        'claim_id': claim['id'], 'implementer': claim['owner'],
        'task_ids': selected['task_ids'] if selected is not None else claim['task_ids'],
        'selection_id': selected['id'] if selected is not None else None,
        'tested_revision': tested_revision, 'base_revision': claim['base_revision'],
        'input_fingerprint': before['fingerprint'], 'input_files': before['files'],
        'actual_changed_files': changed_files(root, claim['base_revision']),
        'commands': results, 'selected_cases': spec.get('selected_cases', []),
        'environment': {'platform': platform.platform(), 'python': platform.python_version(),
                        'worktree': str(root), 'label': spec.get('environment', 'unspecified')},
        'created_at': time.time(), 'errors': errors,
    }
    path = output / 'receipt.json'
    write_json(path, receipt)
    with registry(root) as state:
        current = get_claim(state, claim['id'], claim['owner'])
        current.update(last_receipt=str(path), updated_at=time.time())
        state.setdefault('receipts', {})[receipt_id] = {'path': str(path.resolve()), 'sha256': digest(path)}
        if selected is not None:
            _record_final_check_failure(state, selected['id'], receipt, path, after)
    return {'status': 'ok' if not errors else 'blocked', 'receipt': str(path), 'result': receipt}


def _record_final_check_failure(state, identity, receipt, path, after):
    from .selection import get_selection, record_selection_failure
    item = get_selection(state, identity)
    if receipt['input_fingerprint'] != after['fingerprint'] or receipt['status'] != 'blocked':
        return
    required = {check['id'] for check in item['required_checks']}
    failed = [command for command in receipt['commands'] if command['id'] in required and _failed_product_check(command)]
    if failed:
        record_selection_failure(item, state, receipt, 'verification', digest(path), receipt['errors'])


def _failed_product_check(command):
    if command['kind'] != 'test':
        return command['exit_code'] not in (0, 124, 127)
    report = command.get('test_result', {})
    counts = [report.get(field) for field in ('selected', 'executed', 'failed')]
    if any(not isinstance(count, int) or isinstance(count, bool) for count in counts):
        return False
    selected, executed, failed = counts
    return selected >= executed >= failed > 0


def _receipt_errors(results, before, after):
    errors = []
    for result in results:
        if result['exit_code'] != 0:
            errors.append(f"{result['id']}: command exited {result['exit_code']}")
        if result.get('test_result', {}).get('status') == 'blocked':
            errors.append(f"{result['id']}: test selection did not establish a complete nonempty pass")
    if before['fingerprint'] != after['fingerprint']:
        errors.append('Implementation inputs changed while commands ran; capture fresh checks')
    return errors


def validate_review(receipt, review):
    errors = []
    if not review.get('reviewer') or review['reviewer'] == receipt.get('implementer'):
        errors.append('Independent reviewer must differ from the implementer')
    for field in ('tested_revision', 'input_fingerprint'):
        if review.get(field) != receipt.get(field):
            errors.append(f'Review does not match receipt {field}')
    if review.get('verdict') != 'accepted':
        errors.append('Independent review did not accept this input')
    if not isinstance(review.get('findings'), list):
        errors.append('Review needs an explicit findings list')
    for finding in review.get('findings', []):
        if finding.get('required') and finding.get('status') != 'resolved':
            errors.append(f"Unresolved required finding: {finding.get('id', 'unnamed')}")
    return errors


def verify_receipt(repo, receipt):
    errors = []
    if receipt.get('schema_version') != 1 or receipt.get('status') != 'passed':
        errors.append('Receipt is not a successful supported command capture')
    snapshot = input_snapshot(repo)
    if receipt.get('input_fingerprint') != snapshot['fingerprint']:
        errors.append('Receipt implementation inputs are stale')
    if receipt.get('tested_revision') != revision(repo):
        errors.append('Receipt revision differs from the current lane revision')
    if not receipt.get('commands'):
        errors.append('Receipt has no captured commands')
    ids = [command.get('id') for command in receipt.get('commands', [])]
    if len(ids) != len(set(ids)):
        errors.append('Receipt has duplicate check IDs')
    if receipt.get('actual_changed_files') != changed_files(repo, receipt.get('base_revision', 'HEAD')):
        errors.append('Receipt changed-file inventory differs from the current worktree')
    for command in receipt.get('commands', []):
        if not all(field in command for field in ('id', 'argv', 'contract', 'kind', 'cwd', 'started_at', 'finished_at', 'exit_code')):
            errors.append('Receipt command capture structure is incomplete')
        contract = command.get('contract', {})
        if command.get('argv') != contract.get('argv') or command.get('kind') != contract.get('kind') or command.get('id') != contract.get('id'):
            errors.append('Captured command identity differs from its required contract')
        if set(command.get('logs', {})) != {'stdout', 'stderr'}:
            errors.append('Receipt requires hashed stdout and stderr logs')
        if command.get('kind') == 'test':
            try:
                reported = _test_result(repo, command['contract'], command['started_at'], command['test_report_before'])
                if reported != command.get('test_result') or reported.get('status') != 'passed':
                    errors.append('Test capture does not match a successful fresh machine-readable report')
            except (KeyError, ValueError, OSError, ET.ParseError):
                errors.append('Test capture has no complete machine-readable report')
        if command.get('exit_code') != 0:
            errors.append(f"Failed command: {command.get('id')}")
        for artifact in command.get('logs', {}).values():
            errors.extend(_verify_artifact(repo, artifact))
        if command.get('test_result', {}).get('status') == 'blocked':
            errors.append('Receipt contains an empty or failed test selection')
        if 'sha256' in command.get('test_result', {}):
            errors.extend(_verify_artifact(repo, command['test_result']))
    return errors


def _verify_artifact(repo, artifact):
    try:
        path = _artifact(repo, artifact['path'])
        if digest(path) != artifact.get('sha256'):
            return [f"Artifact hash mismatch: {artifact['path']}"]
        if path.stat().st_size == 0:
            return [f"Empty evidence artifact: {artifact['path']}"] if artifact.get('required_nonempty', False) else []
        return []
    except (KeyError, OSError, CoordinationError) as exc:
        return [f'Artifact unavailable: {exc}']


def _case_errors(repo, requirement, case):
    errors = []
    if case.get('boundary') != requirement['boundary']:
        errors.append(f"{requirement['id']}: required boundary is {requirement['boundary']}")
    if case.get('result') != 'passed' or not case.get('assertions'):
        errors.append(f"{requirement['id']}: successful observable assertions are missing")
    observation = case.get('direct_observation', {})
    observed = (isinstance(observation, dict) and observation.get('observer')
                and observation.get('method') and observation.get('observations'))
    if not case.get('artifacts') and not observed:
        errors.append(f"{requirement['id']}: retained evidence or direct observation is missing")
    for artifact in case.get('artifacts', []):
        errors += _verify_artifact(repo, {**artifact, 'required_nonempty': True})
    if requirement.get('recording_required') or case.get('recording'):
        errors += _visual_errors(repo, requirement['id'], case)
    if requirement.get('assistive_technology') or requirement.get('speech_required'):
        errors += _assistive_errors(repo, requirement, case)
    if requirement.get('independent_state'):
        observation = case.get('state_observation', {})
        if not isinstance(observation, dict) or not observation.get('method') or not observation.get('artifact'):
            errors.append(f"{requirement['id']}: independent state observation and artifact are missing")
        else:
            errors += _verify_artifact(repo, {**observation['artifact'], 'required_nonempty': True})
    return errors


def _assistive_errors(repo, requirement, case):
    observation = case.get('assistive_observation', {})
    expected = requirement.get('assistive_technology')
    if not isinstance(observation, dict):
        observation = {}
    if (not observation.get('observer') or not observation.get('tool')
            or not observation.get('observations') or observation.get('result') != 'passed'
            or not observation.get('artifact')):
        return [f"{requirement['id']}: actual assistive-technology observation is missing"]
    errors = _verify_artifact(repo, {**observation['artifact'], 'required_nonempty': True})
    if expected and observation['tool'] != expected:
        errors.append(f"{requirement['id']}: required assistive technology was not observed")
    if requirement.get('speech_required') and observation.get('speech_observed') is not True:
        errors.append(f"{requirement['id']}: actual speech observation is missing")
    return errors


def _video_duration(repo, recording):
    errors = _verify_artifact(repo, {**recording, 'required_nonempty': True})
    if errors:
        return None, errors
    executable = shutil.which('ffprobe')
    if not executable:
        return None, ['ffprobe is unavailable; recording stream/duration verification is blocked']
    path = _artifact(repo, recording['path'])
    probe = subprocess.run([executable, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)],
                           capture_output=True, timeout=30)
    if probe.returncode:
        return None, ['Recording is not readable video media']
    try:
        metadata = json.loads(probe.stdout)
        video = [stream for stream in metadata['streams'] if stream.get('codec_type') == 'video']
        duration = float(metadata['format']['duration'])
        if not video or duration <= 0 or any(not 0 < stream.get('width', 0) * stream.get('height', 0) <= 16000000 for stream in video):
            raise ValueError('Missing usable video stream')
        return duration, []
    except (ValueError, KeyError, TypeError):
        return None, ['Recording metadata does not establish a video stream and positive duration']


def _frame_errors(repo, recording, frame):
    errors = _verify_artifact(repo, {**frame, 'required_nonempty': True})
    if errors:
        return errors
    probe, decoder = shutil.which('ffprobe'), shutil.which('ffmpeg')
    if not probe or not decoder:
        return ['ffprobe/ffmpeg unavailable; decoded-frame provenance is blocked']
    image = _artifact(repo, frame['path'])
    video = _artifact(repo, recording['path'])
    inspected = subprocess.run([probe, '-v', 'error', '-show_streams', '-of', 'json', str(image)], capture_output=True, timeout=30)
    try:
        streams = json.loads(inspected.stdout)['streams']
        valid = [stream for stream in streams if stream.get('codec_name') in ('png', 'mjpeg', 'webp', 'bmp', 'tiff')]
        if inspected.returncode or not valid or any(not 0 < stream.get('width', 0) * stream.get('height', 0) <= 16000000 for stream in valid):
            return ['Inspected frame is not a decodable bounded image']
    except (ValueError, KeyError, TypeError):
        return ['Inspected frame is not a decodable image']
    timestamp = frame.get('timestamp')
    if not isinstance(timestamp, (int, float)) or timestamp < 0:
        return ['Inspected frame has no valid extraction timestamp']
    common = ['-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1']
    image_pixels = subprocess.run([decoder, '-v', 'error', '-i', str(image), *common], capture_output=True, timeout=30)
    video_pixels = subprocess.run([decoder, '-v', 'error', '-ss', str(timestamp), '-i', str(video), *common], capture_output=True, timeout=30)
    if image_pixels.returncode or video_pixels.returncode or not image_pixels.stdout or image_pixels.stdout != video_pixels.stdout:
        return ['Inspected frame pixels do not match the recording at the declared timestamp']
    return []


def _visual_errors(repo, case_id, case):
    errors = []
    recording = case.get('recording', {})
    duration, media_errors = _video_duration(repo, recording)
    errors += [f'{case_id}: {error}' for error in media_errors]
    interval = recording.get('timestamps', [])
    if len(interval) != 2 or not all(isinstance(n, (int, float)) for n in interval) or not 0 <= interval[0] < interval[1]:
        errors.append(f'{case_id}: invalid recording timestamps')
    elif duration is not None and interval[1] > duration + 0.1:
        errors.append(f'{case_id}: case interval exceeds recording duration')
    frames = recording.get('inspected_frames', [])
    if not frames:
        errors.append(f'{case_id}: no inspected frames')
    for frame in frames:
        if not media_errors:
            errors += _frame_errors(repo, recording, frame)
        else:
            errors += _verify_artifact(repo, {**frame, 'required_nonempty': True})
        if frame.get('recording_sha256') != recording.get('sha256'):
            errors.append(f'{case_id}: inspected frame does not identify its recording hash')
        if not frame.get('inspector') or frame.get('readable') is not True or not frame.get('observations'):
            errors.append(f'{case_id}: frame inspection lacks readability or visible-result observations')
        if len(interval) == 2 and isinstance(frame.get('timestamp'), (float, int)):
            if not interval[0] <= frame['timestamp'] <= interval[1]:
                errors.append(f'{case_id}: inspected frame is outside its case interval')
        else:
            errors.append(f'{case_id}: inspected frame timestamp missing')
    if recording.get('redaction_checked') is not True:
        errors.append(f'{case_id}: recording redaction review missing')
    return errors


def requirements_digest(requirements):
    data = json.dumps(requirements, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def validate_evidence(repo, requirements, evidence):
    cases = requirements.get('cases', [])
    if not cases:
        raise CoordinationError('Acceptance verification requires a nonempty case selection')
    ids = [case['id'] for case in cases]
    mapped = evidence.get('cases', [])
    mapped_ids = [case.get('id') for case in mapped]
    if len(ids) != len(set(ids)) or len(mapped_ids) != len(set(mapped_ids)):
        raise CoordinationError('Case IDs must be unique in requirements and evidence')
    errors = []
    if evidence.get('requirements_sha256') != requirements_digest(requirements):
        errors.append('Acceptance evidence does not match the supplied requirements JSON')
    if evidence.get('input_fingerprint') != input_snapshot(repo)['fingerprint']:
        errors.append('Acceptance evidence has stale implementation or requirement inputs')
    if not evidence.get('implementer') or not evidence.get('reviewer') or evidence['reviewer'] == evidence['implementer']:
        errors.append('Evidence requires distinct implementer and independent reviewer identities')
    results = {case['id']: case for case in mapped}
    for case in cases:
        if case['id'] not in results:
            errors.append(f"Missing acceptance mapping: {case['id']}")
        else:
            errors += _case_errors(repo, case, results[case['id']])
    if requirements.get('feature_completion'):
        if evidence.get('integration_owner') != requirements.get('integration_owner'):
            errors.append('Feature evidence is not attributed to its named integration owner')
    return {'status': 'passed' if not errors else 'blocked', 'errors': errors,
            'case_count': len(cases), 'requirements_sha256': requirements_digest(requirements),
            'verified_fingerprint': evidence.get('input_fingerprint'),
            'scope': 'Provenance and declared review completeness; a reviewer must inspect assertions and visible content.'}
