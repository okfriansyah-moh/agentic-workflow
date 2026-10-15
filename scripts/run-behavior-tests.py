#!/usr/bin/env python3
"""Run selected unittest cases and retain machine-readable execution counts."""
import argparse
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pattern', default='test_*.py')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=args.pattern)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'selected': result.testsRun, 'executed': result.testsRun - len(result.skipped),
              'failed': len(result.failures) + len(result.errors), 'skipped': len(result.skipped)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    return not result.wasSuccessful() or not result.testsRun or bool(result.skipped)


if __name__ == '__main__':
    raise SystemExit(main())
