#!/usr/bin/env python3
"""Local Codex observation capture and update staging. No network or live installs."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import date, datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from zoneinfo import ZoneInfo
import yaml

DEFAULT_ROOT = Path(os.environ.get('AGENT_WORKFLOW_OBSERVATIONS', Path.home() / '.codex' / 'skill-workspace'))
NAME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
STATUSES = {'open', 'parked', 'actioned', 'declined', 'superseded'}

def today():
    return datetime.now(ZoneInfo('Asia/Jakarta')).date().isoformat()

def paths(root):
    if not root.is_absolute():
        raise ValueError('Workspace must be an absolute path')
    return root / 'skill-observations' / 'observation-log'

def require(root):
    log = paths(root)
    if not log.is_dir() or not (log / 'archive').is_dir() or not (root / 'skill-updates').is_dir():
        raise ValueError('Observer storage is missing; initialize it explicitly during setup')
    return log

def atomic_write(path, content):
    fd, temp = tempfile.mkstemp(prefix='.observer-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def init(root):
    log = paths(root)
    for p in (root, root/'skill-observations', log, log/'archive', root/'skill-updates'):
        p.mkdir(parents=True, exist_ok=True, mode=0o700)
    date = root/'skill-observations'/'last-review-date.txt'
    try:
        with date.open('x', encoding='utf-8') as f:
            f.write('never\n')
    except FileExistsError:
        pass
    return {'workspace': str(root), 'initialized': True}

@contextmanager
def lock(root):
    require(root)
    with (root/'skill-observations'/'.observer.lock').open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def records(root):
    log = require(root)
    entries = []
    seen = set()
    for p in sorted([*log.glob('*.md'), *(log/'archive').glob('*.md')]):
        text = p.read_text(encoding='utf-8')
        m = re.match(r'^---\n(.*?)\n---(?:\n|$)', text, re.S)
        if not m:
            raise ValueError(f'Missing observation header: {p}')
        data = yaml.safe_load(m[1])
        if not isinstance(data, dict) or type(data.get('id')) is not int or data['id'] <= 0:
            raise ValueError(f'Invalid observation id: {p}')
        if data['id'] in seen or not p.name.startswith(f"{data['id']:04d}-"):
            raise ValueError(f'Duplicate or mismatched observation id: {p}')
        if data.get('status') not in STATUSES or not isinstance(data.get('title'), str) or not data['title'].strip():
            raise ValueError(f'Invalid observation metadata: {p}')
        if not isinstance(data.get('skill'), list) or any(not isinstance(x, str) for x in data['skill']):
            raise ValueError(f'Invalid affected skills: {p}')
        if data.get('type') not in ('internal', 'open-source'):
            raise ValueError(f'Invalid observation classification: {p}')
        fingerprint = data.get('fingerprint')
        if not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
            raise ValueError(f'Invalid or missing observation fingerprint: {p}')
        try:
            date.fromisoformat(str(data['date']))
        except (KeyError, ValueError):
            raise ValueError(f'Invalid or missing observation date: {p}')
        strings(data, 'proposes_skill')
        body = text[m.end():]
        sections = re.findall(r'^## (Issue|Suggested improvement|Principle)\n+(.+?)(?=^## |\Z)', body, re.M | re.S)
        if [label for label, _ in sections] != ['Issue', 'Suggested improvement', 'Principle'] or any(not value.strip() for _, value in sections):
            raise ValueError(f'Missing or empty observation body sections: {p}')
        seen.add(data['id'])
        entries.append((p, data))
    return entries

def strings(data, key, required=True):
    value = data.get(key, [] if not required else None)
    if not isinstance(value, list) or any(not isinstance(s, str) or not s.strip() for s in value):
        raise ValueError(f'{key} must be a list of nonempty strings')
    return sorted(set(s.strip() for s in value))

def add(root, data):
    if not isinstance(data, dict):
        raise ValueError('Input must be a JSON object')
    for key in ('title', 'issue', 'suggested_improvement', 'principle'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f'{key} must be nonempty text')
    skills = strings(data, 'skill')
    proposals = strings(data, 'proposes_skill', False)
    kind = data.get('type', 'internal')
    if kind not in ('internal', 'open-source'):
        raise ValueError('type must be internal or open-source')
    normalized = [' '.join(data[k].split()).casefold() for k in ('title', 'issue', 'suggested_improvement', 'principle')]
    fingerprint = hashlib.sha256(json.dumps([skills, proposals, *normalized], sort_keys=True).encode()).hexdigest()
    with lock(root):
        existing = records(root)
        for p, m in existing:
            if m.get('fingerprint') == fingerprint:
                return {'created': False, 'duplicate': True, 'path': str(p), 'id': m['id'], 'status': m['status']}
        num = max((m['id'] for _, m in existing), default=0) + 1
        slug = re.sub(r'[^a-z0-9]+', '-', data['title'].lower()).strip('-')[:65].rstrip('-') or 'observation'
        path = require(root)/f'{num:04d}-{slug}.md'
        header = {'id': num, 'title': data['title'].strip(), 'status': 'open', 'type': kind,
                  'skill': skills, 'proposes_skill': proposals, 'date': today(),
                  'fingerprint': fingerprint, 'session_context': str(data.get('session_context','')),
                  'siblings_checked': str(data.get('siblings_checked','Not applicable or not yet assessed'))}
        body = '\n\n'.join('## '+label+'\n\n'+'\n'.join('> '+line for line in data[key].strip().splitlines()) for label,key in
                            [('Issue','issue'),('Suggested improvement','suggested_improvement'),('Principle','principle')])
        atomic_write(path, '---\n'+yaml.safe_dump(header, sort_keys=False, allow_unicode=True)+'---\n\n'+body+'\n')
        return {'created': True, 'duplicate': False, 'path': str(path), 'id': num}

def digest(path):
    result = {}
    for p in sorted(path.rglob('*')):
        if p.is_symlink():
            raise ValueError(f'Symlinks are not supported in staged bundles: {p}')
        if p.is_file():
            result[str(p.relative_to(path))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result

def stage(root, source):
    require(root)
    if not source.is_absolute() or not source.is_dir() or not NAME.fullmatch(source.name):
        raise ValueError('Skill source must be an absolute skill directory')
    text = (source/'SKILL.md').read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---', text, re.S)
    metadata = yaml.safe_load(m[1]) if m else None
    if not isinstance(metadata, dict) or metadata.get('name') != source.name:
        raise ValueError('Skill name must match its directory')
    before = digest(source)
    target = root/'skill-updates'/source.name
    with lock(root):
        target.mkdir(exist_ok=True, mode=0o700)
        run = Path(tempfile.mkdtemp(prefix=today()+'-', dir=target))
        try:
            shutil.copytree(source, run/'baseline')
            shutil.copytree(run/'baseline', run/'proposed')
            if digest(source) != before or digest(run/'baseline') != before:
                raise ValueError('Installed skill changed during staging; no proposal retained')
            manifest = {'skill': source.name, 'source': str(source), 'created': today(),
                        'status': 'staged', 'baseline_sha256': before, 'observations': [], 'changes': []}
            atomic_write(run/'manifest.json', json.dumps(manifest, indent=2)+'\n')
        except Exception:
            shutil.rmtree(run)
            raise
    return {'stage': str(run), 'installed': False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    sub.add_parser('list')
    p = sub.add_parser('add'); p.add_argument('--input', type=Path, required=True)
    p = sub.add_parser('stage'); p.add_argument('--skill-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        paths(args.workspace)
        if args.command == 'init':
            result = init(args.workspace)
        elif args.command == 'list':
            result = {'workspace': str(args.workspace), 'observations':
                      [{'path':str(p), **{k:m.get(k) for k in ('id','title','status','skill','proposes_skill')}}
                       for p,m in records(args.workspace) if m['status'] in ('open','parked')]}
        elif args.command == 'add':
            result = add(args.workspace, json.loads(args.input.read_text(encoding='utf-8')))
        else:
            result = stage(args.workspace, args.skill_dir)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f'Observer operation failed: {e}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
