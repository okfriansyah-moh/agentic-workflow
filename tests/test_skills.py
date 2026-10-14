"""Exercise portable skill discovery, resources and shared policy behavior."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def tree_hash(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix == '.pyc':
            continue
        if any(part in {'.git', '__pycache__', '.DS_Store', 'node_modules', '.pytest_cache'} for part in path.parts):
            continue
        digest.update(path.relative_to(root).as_posix().encode() + b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest() + b'\n')
    return digest.hexdigest()


class SkillPackageTests(unittest.TestCase):
    def test_discovery_and_graph_resolve_all_entries(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text())
        entries = {item['name']: item for item in manifest['skills']}
        self.assertEqual(71, len(entries))
        self.assertEqual(set(entries), {p.name for p in (ROOT / 'skills').iterdir() if p.is_dir()})
        categories = {}
        for name, item in entries.items():
            categories[item['source']['kind']] = categories.get(item['source']['kind'], 0) + 1
            body = (ROOT / 'skills' / name / 'SKILL.md').read_text()
            self.assertTrue(body.startswith('---\n'))
            self.assertRegex(body, r'(?m)^name: ' + re.escape(name) + r'$')
            self.assertRegex(body, r'(?m)^description: .+')
            self.assertEqual(tree_hash(ROOT / 'skills' / name), item['checksum']['value'])
            self.assertTrue(set(item['dependencies']).issubset(entries))
            self.assertTrue(set(item['conditional_dependencies']).issubset(entries))
        self.assertEqual({'reuse': 47, 'new': 11, 'adapt': 7, 'upstream-adapt': 6}, categories)
        def visit(name, trail):
            self.assertNotIn(name, trail, 'Hard skill dependency cycle')
            for dep in entries[name]['dependencies']:
                visit(dep, trail + [name])
        for name in entries:
            visit(name, [])
        catalog = json.loads((ROOT / 'agents/catalog.json').read_text())
        self.assertEqual(8, len(catalog['roles']))
        for role in catalog['roles']:
            self.assertTrue(set(role['skills']).issubset(entries))

    def test_active_skill_links_are_available(self):
        paths = list((ROOT / 'skills').glob('*/SKILL.md'))
        paths += list((ROOT / 'skills').glob('*/references/routing.md'))
        for path in paths:
            body = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
            for match in re.finditer(r'\[[^\]\n]+\]\(([^\s)]+)\)', body):
                target = match.group(1).split('#')[0]
                if not target or ':' in target or target.startswith('#'):
                    continue
                self.assertTrue((path.parent / target).exists(), f'{path}: {target}')

    def test_helpers_relocate_without_original_home(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)
            for name in ['design-system', 'atdd-creation', 'humanizer']:
                shutil.copytree(ROOT / 'skills' / name, dest / 'skills' / name)
            shutil.copytree(ROOT / 'resources/wording', dest / 'resources/wording')
            for relative in ['skills/design-system/scripts/check_artifacts.py', 'skills/atdd-creation/scripts/check_coverage.py']:
                code = (dest / relative).read_text()
                self.assertNotIn('/Users/', code)
                result = subprocess.run([sys.executable, str(dest / relative), '--help'], cwd=dest, capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
            helper = dest / 'resources/wording/check_output_wording.py'
            clean = subprocess.run([sys.executable, str(helper)], input='Specific verified behavior.', text=True, capture_output=True)
            self.assertEqual(0, clean.returncode)
            spec = importlib.util.spec_from_file_location('wording_policy', helper)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            rejected = subprocess.run([sys.executable, str(helper)], input=module.FORBIDDEN.pattern, text=True, capture_output=True)
            self.assertEqual(1, rejected.returncode)

    def test_contrast_math_supporting_resource(self):
        helper = ROOT / 'skills/antislop-human/contrast-check.py'
        result = subprocess.run([sys.executable, str(helper), '--selftest'], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
