#!/usr/bin/env python3
"""Read-only check of generated text, artifact names, and completion text."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

# The exact spelling belongs in checker configuration, not generated material.
FORBIDDEN = re.compile('canonical', re.IGNORECASE)
DEPENDENCY_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
FILESYSTEM_METADATA = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
NON_TEXT_ASSETS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.ico',
                   '.woff', '.woff2', '.ttf', '.otf', '.mp3', '.wav', '.ogg',
                   '.mp4', '.webm', '.mov', '.flac', '.m4a'}
EXTRACT_FIRST = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.odt', '.odp'}


def scan_text(text: str, label: str = '<stdin>') -> list[str]:
    """Inspect complete text, including markup, code, and embedded identifiers."""
    return [f'{label}:{number}: rephrase prohibited wording'
            for number, line in enumerate(text.splitlines(), 1)
            if FORBIDDEN.search(line)]


def scan_paths(paths) -> tuple[list[str], list[str]]:
    """Return wording findings and input errors; never rewrite input files."""
    findings, errors, seen = [], [], set()

    def inspect(path: Path):
        key = str(path.absolute())
        if key in seen:
            return
        seen.add(key)
        if FORBIDDEN.search(path.name):
            findings.append(f'{path}: rename generated artifact')
        try:
            if path.is_symlink():
                errors.append(f'{path}: supply the actual output path instead of a symlink')
            elif path.suffix.lower() in NON_TEXT_ASSETS:
                if not path.is_file():
                    errors.append(f'{path}: missing output asset')
                else:
                    with path.open('rb') as handle:
                        handle.read(1)
            elif path.suffix.lower() in EXTRACT_FIRST:
                errors.append(f'{path}: extract document text and check that text before delivery')
            else:
                findings.extend(scan_text(path.read_text(encoding='utf-8'), str(path)))
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f'{path}: cannot inspect input ({type(error).__name__})')

    for supplied in paths:
        path = Path(supplied)
        if not path.is_dir() or path.is_symlink():
            inspect(path)
            continue
        if FORBIDDEN.search(path.name):
            findings.append(f'{path}: rename generated artifact directory')
        def walk_error(error):
            errors.append(f'{error.filename}: cannot inspect directory ({type(error).__name__})')
        for directory, subdirs, filenames in os.walk(path, onerror=walk_error, followlinks=False):
            for name in list(subdirs):
                child = Path(directory)/name
                if name in DEPENDENCY_DIRS:
                    subdirs.remove(name)
                elif child.is_symlink():
                    errors.append(f'{child}: supply the actual output directory instead of a symlink')
                    subdirs.remove(name)
                elif FORBIDDEN.search(name):
                    findings.append(f'{child}: rename generated artifact directory')
            for name in sorted(filenames):
                if name not in FILESYSTEM_METADATA:
                    inspect(Path(directory)/name)
    return sorted(set(findings)), sorted(set(errors))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='Files/directories to check; - reads stdin. No paths also reads stdin.')
    args = parser.parse_args(argv)
    inputs = args.paths or ['-']
    findings, errors = scan_paths([path for path in inputs if path != '-'])
    if '-' in inputs:
        if sys.stdin.isatty():
            errors.append('Provide output paths or pipe completion text through stdin.')
        else:
            try:
                findings.extend(scan_text(sys.stdin.buffer.read().decode('utf-8')))
            except (OSError, UnicodeError) as error:
                errors.append(f'<stdin>: cannot inspect input ({type(error).__name__})')
    for message in sorted(set(findings)):
        print('WORDING:', message, file=sys.stderr)
    for message in sorted(set(errors)):
        print('INPUT:', message, file=sys.stderr)
    if errors:
        return 2
    if findings:
        return 1
    print('PASS: output wording check.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
