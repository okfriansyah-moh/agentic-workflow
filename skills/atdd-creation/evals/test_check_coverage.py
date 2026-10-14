#!/usr/bin/env python3
"""CLI-level regression checks for structural failures that can hide missing coverage."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / "scripts/check_coverage.py"


class CoverageChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "brief.md"
        self.source.write_text("AC-1: Invalid input preserves the original file.\nAC-2: Cloud sync is excluded.\n")
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.inventory = {"schema_version": 1, "sources": [
            {"id": "BRIEF", "path": "brief.md", "location": "brief.md", "sha256": self.digest}
        ], "obligations": [
            {"id": "AC-1", "source": "BRIEF", "locator": "AC-1", "statement": "Invalid input preserves the original file.", "scope": "Required", "reason": ""},
            {"id": "AC-2", "source": "BRIEF", "locator": "AC-2", "statement": "Cloud sync is excluded.", "scope": "Excluded", "reason": "Offline product; AC-2 explicitly excludes cloud sync."}
        ]}
        self.case = """### Case ATDD-001: Invalid input preserves the file

**Sources:** AC-1

**Priority:** P1

**Level:** Integration

**Platform:** Command and file

**Category:** Negative

**Automation:** Candidate

**Status:** Not Run

**Preconditions:** A fresh fixture directory contains saved.txt.

**Test data:** saved.txt contains alpha; supplied content is malformed.

**Scenario:**

```gherkin
Given saved.txt contains "alpha"
When malformed content is submitted
Then saved.txt still contains "alpha"
And the command reports invalid input
```

**Verification:** Read bytes from a fresh file handle and observe the real process exit.

**Cleanup:** Remove the fixture directory.

"""
        self.registers = f"""## Registers

| Source | Location | SHA-256 |
| --- | --- | --- |
| BRIEF | brief.md | {self.digest} |

| Obligation | Source | Locator | Disposition | Cases | Reason |
| --- | --- | --- | --- | --- | --- |
| AC-1 | BRIEF | AC-1 | Covered | ATDD-001 | Preserves saved bytes. |
| AC-2 | BRIEF | AC-2 | Excluded | — | Offline product; AC-2 explicitly excludes cloud sync. |
"""
        self.doc = "# Acceptance\n\n" + self.case + self.registers
        self.previous = None

    def run_check(self):
        inv = self.root / "inventory.json"
        inv.write_text(json.dumps(self.inventory))
        doc = self.root / "atdd.md"
        doc.write_text(self.doc)
        command = [sys.executable, str(HELPER), "--inventory", str(inv), "--document", str(doc)]
        if self.previous is not None:
            prev = self.root / "previous.md"
            prev.write_text(self.previous)
            command += ["--previous", str(prev)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def invalid(self, message):
        code, result = self.run_check()
        self.assertEqual(code, 1, result)
        self.assertTrue(any(message in e for e in result["errors"]), result)

    def passed(self):
        return self.doc.replace("**Status:** Not Run", "**Status:** Passed") .replace(
            "## Registers", "**Evidence:** [Run 41](evidence/run-41.txt)\n\n**Revision:** build-abc, expectation-v1\n\n**Environment:** isolated workstation\n\n**Executed at:** 2026-10-01T12:00:00Z\n\n## Registers")

    def test_output_wording_rejects_prose_and_code(self):
        for addition in ("\nCanonical acceptance.\n", "\n```json\n{\"emailCanonical\":\"example\"}\n```\n"):
            original = self.doc
            self.doc = original+addition
            self.invalid("Output wording:")
            self.doc = original

    def test_layout_separator_preserves_recorded_evidence(self):
        evidence = "**Evidence:** [Run 41](evidence/run-41.txt)\n\n**Revision:** build-abc, expectation-v1\n\n**Environment:** isolated workstation\n\n**Executed at:** 2026-10-01T12:00:00Z"
        self.previous = self.doc.replace("**Status:** Not Run", "**Status:** Passed\n\n" + evidence)
        self.doc = self.previous.replace("## Registers", "---\n\n## Registers")
        code, result = self.run_check()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["cases"], 1)

    def test_valid_with_justified_exclusion(self):
        code, result = self.run_check()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "structurally_valid")

    def test_wholly_omitted_requirement(self):
        self.inventory["obligations"].append({"id": "AC-3", "source": "BRIEF", "locator": "AC-3", "statement": "Uninventoried in output", "scope": "Required"})
        self.invalid("missing obligation register entry: AC-3")

    def test_orphan_case_source(self):
        self.doc = self.doc.replace("**Sources:** AC-1", "**Sources:** AC-1, ORPHAN")
        self.invalid("unknown obligation ORPHAN")

    def test_orphan_mapping(self):
        self.doc = self.doc.replace("| Covered | ATDD-001 |", "| Covered | ATDD-001, MISSING |")
        self.invalid("unknown case MISSING")

    def test_duplicate_case_id(self):
        self.doc = self.case + self.doc
        self.invalid("duplicate case ID")

    def test_duplicate_inventory_id(self):
        self.inventory["obligations"].append(self.inventory["obligations"][0])
        self.invalid("duplicate obligation ID")

    def test_duplicate_register(self):
        self.doc += self.registers
        self.invalid("expected one register")

    def test_duplicate_field(self):
        self.doc = self.doc.replace("**Cleanup:**", "**Priority:** P2\n\n**Cleanup:**")
        self.invalid("duplicate field Priority")

    def test_incomplete_case(self):
        self.doc = self.doc.replace("**Cleanup:** Remove the fixture directory.\n", "")
        self.invalid("missing field Cleanup")

    def test_missing_outcome(self):
        self.doc = self.doc.replace('Then saved.txt still contains "alpha"', 'And saved.txt still contains "alpha"')
        self.invalid("Given, When and Then")

    def test_changed_source_bytes(self):
        self.source.write_text("Changed rule")
        self.invalid("source fingerprint changed")

    def test_stale_register_fingerprint(self):
        self.doc = self.doc.replace(self.digest, "0" * 64)
        self.invalid("source register differs")

    def test_unjustified_exclusion(self):
        self.doc = self.doc.replace("| AC-1 | BRIEF | AC-1 | Covered | ATDD-001 | Preserves saved bytes. |", "| AC-1 | BRIEF | AC-1 | Excluded | — | Convenient. |")
        self.invalid("contradicts scope Required")

    def test_exclusion_reason_drift(self):
        self.doc = self.doc.replace("Offline product; AC-2 explicitly excludes cloud sync.", "No time.")
        self.invalid("exclusion/deferral reason differs")

    def test_gap_is_incomplete_not_invalid(self):
        self.doc = self.doc.replace("| Covered | ATDD-001 | Preserves saved bytes. |", "| Gap | ATDD-001 | Error presentation is undecided. |")
        code, result = self.run_check()
        self.assertEqual(code, 2, result)
        self.assertEqual(result["gaps"], ["AC-1"])

    def test_gap_requires_reason(self):
        self.doc = self.doc.replace("| Covered | ATDD-001 | Preserves saved bytes. |", "| Gap | ATDD-001 | |")
        self.invalid("Gap needs a reason")

    def test_no_cases_allowed_for_all_gaps(self):
        self.doc = "# Acceptance\n\n" + self.registers.replace("| Covered | ATDD-001 | Preserves saved bytes. |", "| Gap | — | Missing observable outcome. |")
        code, result = self.run_check()
        self.assertEqual(code, 2, result)

    def test_false_pass(self):
        self.doc = self.doc.replace("**Status:** Not Run", "**Status:** Passed")
        self.invalid("Passed requires substantive Evidence")

    def test_placeholder_evidence(self):
        self.doc = self.passed().replace("[Run 41](evidence/run-41.txt)", "Not executed")
        self.invalid("Passed requires substantive Evidence")

    def test_recorded_evidence_structurally_accepted(self):
        self.doc = self.passed()
        code, result = self.run_check()
        self.assertEqual(code, 0, result)
        self.assertIn("execution evidence require review", result["assurance"])

    def test_blocked_needs_reason(self):
        self.doc = self.doc.replace("**Status:** Not Run", "**Status:** Blocked")
        self.invalid("Blocked requires Blocker")

    def test_rename_requires_retirement(self):
        self.previous = self.doc
        self.doc = self.doc.replace("ATDD-001", "ATDD-010")
        self.invalid("removed without retirement")

    def test_retirement_preserves_history(self):
        self.previous = self.doc
        self.doc = self.doc.replace("ATDD-001", "ATDD-010") + "\n| Retired case | Reason | Replaced by |\n| --- | --- | --- |\n| ATDD-001 | Behavior split following source change. | ATDD-010 |\n"
        code, result = self.run_check()
        self.assertEqual(code, 0, result)

    def test_retired_id_cannot_reappear(self):
        self.previous = self.doc.replace("ATDD-001", "ATDD-010") + "\n| Retired case | Reason | Replaced by |\n| --- | --- | --- |\n| ATDD-001 | Split. | ATDD-010 |\n"
        self.invalid("retired history lost or ID reused")

    def test_changed_assertion_requires_stale(self):
        self.previous = self.passed()
        self.doc = self.previous.replace('Then saved.txt still contains "alpha"', 'Then saved.txt contains "gamma"')
        self.invalid("mark Stale")

    def test_stale_status_retains_historical_evidence(self):
        self.previous = self.passed()
        self.doc = self.previous.replace('Then saved.txt still contains "alpha"', 'Then saved.txt contains "gamma"').replace("**Status:** Passed", "**Status:** Stale")
        code, result = self.run_check()
        self.assertEqual(code, 0, result)

    def test_changed_source_requires_stale(self):
        self.previous = self.passed()
        self.source.write_text("AC-1 changed; AC-2 unchanged.")
        digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.inventory["sources"][0]["sha256"] = digest
        self.doc = self.previous.replace(self.digest, digest)
        self.invalid("mark Stale")

    def test_recorded_impact_review(self):
        self.previous = self.passed()
        self.doc = self.previous.replace("**Platform:** Command and file", "**Platform:** CLI and file").replace("## Registers", "**Impact review:** Only the platform label changed; run 41 still tests the same boundary and expectations.\n\n## Registers")
        code, result = self.run_check()
        self.assertEqual(code, 0, result)

    def test_reverse_mapping_missing(self):
        self.doc = self.doc.replace("**Sources:** AC-1", "**Sources:** AC-2")
        self.invalid("missing reverse case reference")

    def test_forward_mapping_missing(self):
        self.doc = self.doc.replace("| Covered | ATDD-001 | Preserves saved bytes. |", "| Gap | — | No mapped case yet. |")
        self.invalid("missing forward coverage reference")

    def test_empty_reference_tokens(self):
        self.doc = self.doc.replace("**Sources:** AC-1", "**Sources:** , —")
        self.invalid("at least one obligation ID")

    def test_exact_duplicate_different_ids(self):
        self.doc = self.case.replace("ATDD-001", "ATDD-002") + self.doc.replace("| Covered | ATDD-001 |", "| Covered | ATDD-001, ATDD-002 |")
        self.invalid("exact duplicate scenario")

    def test_examples_fences_do_not_create_cases(self):
        self.doc += "\n````markdown\n" + self.case + self.registers + "\n````\n"
        code, result = self.run_check()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["cases"], 1)

    def test_unclosed_fence(self):
        self.doc += "\n```text\ntruncated\n"
        self.invalid("unclosed Markdown")

    def test_outline_requires_example_rows(self):
        self.doc = self.doc.replace('Given saved.txt', 'Scenario Outline: Invalid rows\nGiven saved.txt')
        self.invalid("needs Examples rows")

    def test_outline_accepts_examples(self):
        self.doc = self.doc.replace('Given saved.txt', 'Scenario Outline: Invalid rows\nGiven saved.txt').replace('And the command reports invalid input\n', 'And the command reports invalid input\nExamples:\n| invalid |\n| truncated |\n')
        code, result = self.run_check()
        self.assertEqual(code, 0, result)

    def test_markdown_source_link(self):
        self.doc = self.doc.replace("| BRIEF | brief.md |", "| BRIEF | [Brief](brief.md) |")
        code, result = self.run_check()
        self.assertEqual(code, 0, result)

    def test_invalid_source_schema(self):
        self.inventory["sources"][0]["sha256"] = "missing"
        self.invalid("invalid SHA-256")

    def test_missing_source_file(self):
        self.source.unlink()
        self.invalid("No such file")

    def test_document_cannot_be_source(self):
        self.inventory["sources"][0]["path"] = "atdd.md"
        self.invalid("cannot serve as its own requirement source")


if __name__ == "__main__":
    unittest.main(verbosity=2)
