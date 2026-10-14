"""Behavior tests for the shared output check; rejected spellings are test input."""
from pathlib import Path
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(os.environ.get('PERSONAL_WORDING_CHECKER', Path(__file__).resolve().parents[1]/'scripts/check_output_wording.py'))
spec = importlib.util.spec_from_file_location('output_wording', HELPER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class WordingCheckTests(unittest.TestCase):
    def test_clean_meaning_specific_words(self):
        text = 'Seed data; source schema; shared contracts; normalized email; deterministic JSON.'
        result = subprocess.run([sys.executable, str(HELPER)], input=text, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_case_variants_identifiers_and_snippets(self):
        for text in ('Canonical seed', 'CANONICAL', 'canonicalization', 'canonically',
                     'emailCanonical', 'F-CANONICAL', '```json\n{"canonical":true}\n```'):
            with self.subTest(text=text):
                result = subprocess.run([sys.executable, str(HELPER), '-'], input=text, text=True, capture_output=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn('WORDING:', result.stderr)
                self.assertNotIn(text, result.stderr)

    def test_directory_checks_markup_names_and_hidden_authored_files(self):
        with tempfile.TemporaryDirectory(prefix='wording-') as directory:
            root = Path(directory)
            (root/'good.md').write_text('Shared source schema.')
            (root/'mockup').mkdir()
            (root/'mockup/index.html').write_text('<h1>Canonical design</h1>')
            (root/'.generated').mkdir()
            (root/'.generated/example.json').write_text('{"emailCanonical":"example"}')
            (root/'canonical.md').write_text('Clean text.')
            (root/'preview.png').write_bytes(b'\x89PNG\x00')
            (root/'.DS_Store').write_bytes(b'\xff')
            findings, errors = checker.scan_paths([root])
            self.assertFalse(errors)
            self.assertEqual(len(findings), 3)

    def test_missing_binary_and_invalid_utf8_fail_without_mutation(self):
        with tempfile.TemporaryDirectory(prefix='wording-') as directory:
            root = Path(directory)
            for filename, data in (('draft.pdf', b'%PDF-1.7'), ('bad.txt', b'\xff')):
                path = root/filename
                path.write_bytes(data)
                result = subprocess.run([sys.executable, str(HELPER), str(path)], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(path.read_bytes(), data)
            result = subprocess.run([sys.executable, str(HELPER), str(root/'missing.md')], capture_output=True)
            self.assertEqual(result.returncode, 2)

    def test_stdin_invalid_utf8(self):
        result = subprocess.run([sys.executable, str(HELPER)], input=b'\xff', capture_output=True)
        self.assertEqual(result.returncode, 2)

    def test_multiple_inputs_and_line_numbers(self):
        with tempfile.TemporaryDirectory(prefix='wording-') as directory:
            root = Path(directory)
            path = root/'text.md'
            path.write_text('Clean first line.\nCanonical second line.\n')
            result = subprocess.run([sys.executable, str(HELPER), str(path), '-'], input='canonicalization', text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(':2:', result.stderr)
            self.assertIn('<stdin>:1:', result.stderr)

    def test_symlink_and_unreadable_file_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix='wording-') as directory:
            root = Path(directory)
            target = root/'target.md'
            target.write_text('Shared contracts.')
            link = root/'link.md'
            link.symlink_to(target)
            self.assertTrue(checker.scan_paths([link])[1])
            target.chmod(0)
            try:
                if os.geteuid() != 0:
                    self.assertTrue(checker.scan_paths([target])[1])
            finally:
                target.chmod(0o600)


if __name__ == '__main__':
    unittest.main()
