"""Behavioral package checks through the actual command-line interface."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "evals"))
from fixture_helpers import package, metadata, second_task


class PackageChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.paths = package(Path(self.tmp.name))

    def run_check(self, *extra):
        result = subprocess.run([sys.executable, str(SKILL / "scripts/check_plan.py"), str(self.paths["entry"]), "--format", "json", *extra], capture_output=True, text=True)
        self.assertFalse(result.stderr, result.stderr)
        return result.returncode, json.loads(result.stdout)

    def finding(self, code, *extra, exit_code=1):
        status, report = self.run_check(*extra)
        self.assertEqual(status, exit_code, report)
        self.assertIn(code, [f["code"] for f in report["findings"]], report)

    def replace(self, key, before, after):
        path = self.paths[key]
        content = path.read_text()
        self.assertIn(before, content)
        path.write_text(content.replace(before, after))

    def test_complete_definition_can_await_execution(self):
        status, report = self.run_check("--strict")
        self.assertEqual(status, 0, report)
        self.assertEqual(report["tasks"], 1)
        self.assertEqual(report["counts"]["gap"], 0)

    def rename_group_folder(self, name):
        old = self.paths["group"].parent
        new = old.with_name(name)
        old.rename(new)
        self.paths["group"] = new / "group.md"
        self.paths["task"] = new / "tasks" / self.paths["task"].name
        self.paths["entry"].write_text(self.paths["entry"].read_text().replace(old.name, name))
        self.paths["group"].write_text(self.paths["group"].read_text().replace(old.name, name))

    def test_feature_folder_requires_number_prefix(self):
        self.rename_group_folder("count-validation")
        self.finding("group-layout")

    def test_feature_numbering_starts_at_one(self):
        self.rename_group_folder("00-count-validation")
        self.finding("group-order")

    def test_root_register_uses_consecutive_order(self):
        self.rename_group_folder("02-count-validation")
        self.finding("group-order")

    def test_group_title_matches_folder(self):
        self.replace("group", "# 01-count-validation", "# Count validation")
        self.finding("group-title")

    def sequential(self):
        metadata(self.paths["entry"], numbering="sequential")

    def test_sequential_complete_package(self):
        self.sequential()
        second_task(self.paths)
        self.assertEqual(self.run_check("--strict")[0], 0, self.run_check()[1])

    def test_sequential_group_matches_folder(self):
        self.sequential()
        self.replace("entry", "G01", "G02")
        self.replace("group", "G01", "G02")
        self.replace("task", "G01", "G02")
        self.finding("sequential-group")

    def test_legacy_group_id_can_differ(self):
        self.replace("entry", "G01", "G02")
        self.replace("group", "G01", "G02")
        self.replace("task", "G01", "G02")
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_unknown_numbering_mode(self):
        metadata(self.paths["entry"], numbering="anything")
        self.finding("numbering-mode")

    def test_sequential_task_gap(self):
        self.sequential()
        second = second_task(self.paths)
        for path in [self.paths["entry"], self.paths["group"], second]:
            path.write_text(path.read_text().replace("T002", "T003"))
        second.rename(second.with_name(second.name.replace("T002", "T003")))
        self.finding("sequential-tasks")

    def test_sequential_member_order(self):
        self.sequential()
        second_task(self.paths)
        metadata(self.paths["group"], tasks=["T002", "T001"])
        self.finding("sequential-tasks")

    def test_sequential_backward_dependency(self):
        self.sequential()
        second = second_task(self.paths)
        metadata(self.paths["task"], depends_on=["T002"])
        metadata(second, depends_on=[])
        self.finding("sequential-dependency")

    def test_legacy_backward_dependency_remains_valid(self):
        second = second_task(self.paths)
        metadata(self.paths["task"], depends_on=["T002"])
        metadata(second, depends_on=[])
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_sequential_duplicate_remains_rejected(self):
        self.sequential()
        other = self.paths["task"].with_name("T001-duplicate.md")
        other.write_text(self.paths["task"].read_text())
        self.finding("duplicate-task")

    def historical_mapping(self):
        import re
        metadata(self.paths["task"], status="In progress")
        self.replace("task", "| count-rule | Not run |", "| count-rule | Passed: historical detail |")
        self.replace("task", "| self-review | Not run |", "| self-review | Historical only |")
        base = self.paths["base"]
        for args in [["init"], ["add", "."], ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-m", "original plan"]]:
            subprocess.run(["git", "-C", str(base), *args], capture_output=True, check=True)
        revision = subprocess.run(["git", "-C", str(base), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        section = re.search(r"^## Evidence\n.*?(?=^## |\Z)", self.paths["task"].read_text(), re.M | re.S)[0]
        relative = str(self.paths["task"].relative_to(base))
        data = {"schema_version": 1, "target_numbering": "sequential", "source_revision": revision, "tasks": [{"old_id": "T001", "new_id": "T001", "old_group": "G01", "new_group": "G01", "old_path": relative, "new_path": relative, "status_before": "In progress", "depends_on_before": [], "depends_on_after": [], "evidence_sha256": hashlib.sha256(section.encode()).hexdigest()}]}
        path = base / "migration.json"
        path.write_text(json.dumps(data))
        return path

    def test_explicit_preserved_historical_evidence(self):
        mapping = self.historical_mapping()
        self.assertEqual(self.run_check("--historical-mapping", str(mapping))[0], 0)
        self.finding("evidence-result")

    def test_historical_evidence_changed_is_rejected(self):
        mapping = self.historical_mapping()
        self.replace("task", "Historical only", "Different historical record")
        self.finding("historical-mapping", "--historical-mapping", str(mapping))

    def test_historical_invalid_revision_is_rejected(self):
        mapping = self.historical_mapping()
        data = json.loads(mapping.read_text())
        data["source_revision"] = "f" * 40
        mapping.write_text(json.dumps(data))
        self.finding("historical-mapping", "--historical-mapping", str(mapping))

    def test_historical_mapping_must_cover_actual_new_ids(self):
        mapping = self.historical_mapping()
        data = json.loads(mapping.read_text())
        data["tasks"][0]["new_id"] = "T999"
        mapping.write_text(json.dumps(data))
        self.finding("historical-mapping", "--historical-mapping", str(mapping))

    def test_historical_missing_link_outside_evidence_still_fails(self):
        mapping = self.historical_mapping()
        self.replace("task", "../../../spec.md#invalid-input", "../../../missing.md#invalid-input")
        self.finding("link-missing", "--historical-mapping", str(mapping))

    def test_historical_missing_link_inside_evidence_is_warning(self):
        self.replace("task", "| count-rule | Not run | — |", "| count-rule | Not run | [History](missing-history.json) |")
        mapping = self.historical_mapping()
        status, report = self.run_check("--historical-mapping", str(mapping))
        self.assertEqual(status, 0, report)
        self.assertIn("warning", [row["severity"] for row in report["findings"] if row["code"] == "link-missing"])

    def test_check_is_read_only(self):
        def snapshot():
            return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.paths["base"].rglob("*") if p.is_file()}
        before = snapshot()
        self.run_check()
        self.assertEqual(before, snapshot())

    def test_output_text_and_json_are_available(self):
        out = subprocess.run([sys.executable, str(SKILL / "scripts/check_plan.py"), str(self.paths["entry"])], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        self.assertIn("0 errors; 0 gaps", out.stdout)

    def test_new_file_does_not_need_to_exist(self):
        self.assertFalse((self.paths["base"] / "tests/test_count.py").exists())
        self.assertEqual(self.run_check()[0], 0)

    def test_missing_modified_file_fails(self):
        self.paths["src"].unlink()
        self.finding("change-target-missing")

    def test_dependency_created_file_can_be_modified(self):
        second = second_task(self.paths)
        second.write_text(second.read_text().replace("| app | inspect | src/cli.py |", "| app | modify | tests/test_count.py |"))
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_unrelated_creator_cannot_satisfy_missing_modify(self):
        second = second_task(self.paths)
        metadata(second, depends_on=[])
        second.write_text(second.read_text().replace("| app | inspect | src/cli.py |", "| app | modify | tests/test_count.py |"))
        self.finding("change-target-missing")

    def test_cycle_across_two_tasks(self):
        second_task(self.paths)
        metadata(self.paths["task"], depends_on=["T002"])
        self.finding("dependency-cycle")

    def test_missing_dependency(self):
        metadata(self.paths["task"], depends_on=["T099"])
        self.finding("dependency-missing")

    def test_duplicate_task_id(self):
        other = self.paths["task"].with_name("T001-duplicate.md")
        other.write_text(self.paths["task"].read_text())
        self.finding("duplicate-task")

    def test_group_membership_must_match(self):
        metadata(self.paths["group"], tasks=["T001", "T002"])
        self.finding("membership")

    def test_unknown_integration_owner(self):
        metadata(self.paths["group"], integration_owner="T099")
        self.finding("integration-owner")

    def test_broken_document_link(self):
        self.replace("task", "../../../spec.md#invalid-input", "../../../absent.md#invalid-input")
        self.finding("link-missing")

    def test_missing_source_anchor(self):
        self.replace("task", "#invalid-input)", "#unknown)")
        self.finding("link-anchor")

    def test_reference_style_links(self):
        self.replace("task", "[invalid input](../../../spec.md#invalid-input)", "[invalid input][rule]")
        with self.paths["task"].open("a") as stream:
            stream.write("\n[rule]: ../../../spec.md#invalid-input\n")
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_fenced_example_links_are_not_checked(self):
        with self.paths["task"].open("a") as stream:
            stream.write("\n```markdown\n[Example](no-such-file.md)\n## Evidence\n```\n")
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_coverage_reference_link_uses_document_definition(self):
        self.replace("entry", "[Invalid input](spec.md#invalid-input)", "[Rule][rule]")
        with self.paths["entry"].open("a") as stream:
            stream.write("\n[rule]: spec.md#invalid-input\n")
        self.assertEqual(self.run_check("--strict")[0], 0, self.run_check()[1])

    def test_evidence_reference_link_uses_document_definition(self):
        self.passed_fixture()
        self.replace("task", "[Report](../evidence.md)", "[Report][proof]")
        with self.paths["task"].open("a") as stream:
            stream.write("\n[proof]: ../evidence.md\n")
        self.assertEqual(self.run_check("--strict")[0], 0, self.run_check()[1])

    def test_missing_reference_definition_fails(self):
        self.replace("entry", "[Invalid input](spec.md#invalid-input)", "[Rule][missing]")
        self.finding("coverage-locator")

    def test_source_hash_detects_drift(self):
        with self.paths["source"].open("a") as stream:
            stream.write("\nRule changed.\n")
        self.finding("source-stale")

    def test_draft_gap_is_reported_without_structural_failure(self):
        metadata(self.paths["entry"], readiness="Draft")
        metadata(self.paths["task"], readiness="Draft")
        self.finding("task-readiness", exit_code=0)
        self.finding("task-readiness", "--strict")

    def test_ready_root_cannot_contain_draft_task(self):
        metadata(self.paths["task"], readiness="Draft")
        self.finding("ready-with-gaps")

    def test_coverage_needs_verification_owner(self):
        self.replace("entry", "| T001 | T001 |", "| T001 | — |")
        self.finding("verification-owner")

    def test_reciprocal_ownership(self):
        self.replace("task", "| REQ-01 | both |", "| REQ-01 | implements |")
        self.finding("coverage-reciprocal")

    def test_independent_inventory_detects_omission(self):
        inventory = self.paths["base"] / "inventory.json"
        inventory.write_text(json.dumps({"obligations": [{"id": "REQ-01", "source": "SPEC", "disposition": "Covered", "reason": ""}, {"id": "REQ-02", "source": "SPEC", "disposition": "Covered", "reason": ""}]}))
        self.finding("inventory-missing", "--inventory", str(inventory))

    def test_matching_inventory_passes(self):
        inventory = self.paths["base"] / "inventory.json"
        inventory.write_text(json.dumps({"obligations": [{"id": "REQ-01", "source": "SPEC", "disposition": "Covered", "reason": ""}]}))
        status, report = self.run_check("--inventory", str(inventory))
        self.assertEqual(status, 0, report)
        self.assertEqual(report["counts"]["warning"], 0)

    def test_inactive_obligation_cannot_hide_active_owners(self):
        self.replace("entry", "| Covered |", "| Deferred |")
        self.finding("inactive-coverage")

    def test_done_requires_executed_evidence(self):
        metadata(self.paths["task"], status="Done")
        self.finding("done-evidence")

    def passed_fixture(self):
        artifact = self.paths["task"].parent / "evidence.md"
        # Keep fixture evidence outside tasks/*.md to avoid inventing another task.
        artifact = self.paths["group"].parent / "evidence.md"
        artifact.write_text("# Synthetic result\n\nThis tests evidence syntax, not software execution.\n")
        self.replace("task", "| count-rule | Not run | — | — | — | — |", "| count-rule | Passed | [Report](../evidence.md) | fixture-r1 | test-fixture | — |")
        self.replace("task", "| self-review | Not run | — | — | — | — |", "| self-review | Passed | [Report](../evidence.md) | fixture-r1 | test-fixture | implementer-A |")
        self.replace("task", "| independent-review | Not run | — | — | — | — |", "| independent-review | Passed | [Report](../evidence.md) | fixture-r1 | test-fixture | reviewer-B |")
        metadata(self.paths["task"], status="Done")

    def test_complete_evidence_structure(self):
        self.passed_fixture()
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_same_reviewer_is_not_independent(self):
        self.passed_fixture()
        self.replace("task", "reviewer-B", "implementer-A")
        self.finding("review-independence")

    def test_missing_evidence_artifact(self):
        self.passed_fixture()
        (self.paths["group"].parent / "evidence.md").unlink()
        self.finding("link-missing")

    def test_directory_is_not_evidence(self):
        self.passed_fixture()
        self.replace("task", "../evidence.md", "../")
        self.finding("evidence-artifact")

    def test_empty_report_is_not_evidence(self):
        self.passed_fixture()
        (self.paths["group"].parent / "evidence.md").write_text("")
        self.finding("evidence-artifact")

    def test_draft_root_does_not_hide_stale_done_task(self):
        self.passed_fixture()
        metadata(self.paths["entry"], readiness="Draft")
        self.paths["source"].write_text(self.paths["source"].read_text() + "\nChanged requirement.\n")
        self.finding("done-source-stale")

    def test_changed_revision_needs_reconciliation(self):
        self.passed_fixture()
        self.replace("task", "| fixture-r1 | test-fixture | reviewer-B |", "| fixture-r2 | test-fixture | reviewer-B |")
        self.finding("evidence-revision")

    def test_stale_evidence_cannot_pass_done(self):
        self.passed_fixture()
        self.replace("task", "| count-rule | Passed |", "| count-rule | Stale |")
        self.finding("done-evidence")

    def test_visual_task_requires_visual_check(self):
        metadata(self.paths["task"], visual_review="required")
        self.finding("required-review")

    def test_duplicate_yaml_keys_are_rejected(self):
        self.replace("task", "kind: task", "kind: task\nkind: task")
        self.finding("yaml")

    def test_invalid_metadata_type_is_reported(self):
        metadata(self.paths["task"], depends_on="T002")
        self.finding("metadata")

    def test_path_escape_is_rejected(self):
        self.replace("task", "src/cli.py", "../outside.py")
        self.finding("change-path")

    def test_multiple_repository_roots(self):
        sibling = self.paths["base"] / "service"
        sibling.mkdir()
        (sibling / "api.py").write_text("# Existing service fixture\n")
        metadata(self.paths["entry"], repositories={"app": "..", "service": "../service"})
        self.replace("task", "| app | modify | src/cli.py |", "| service | modify | api.py |")
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_dynamic_route_filename_is_a_literal_path(self):
        target = self.paths["base"] / "src/[id]/+page.svelte"
        target.parent.mkdir(parents=True)
        target.write_text("<!-- Existing component fixture -->\n")
        self.replace("task", "src/cli.py", "src/[id]/+page.svelte")
        self.assertEqual(self.run_check()[0], 0, self.run_check()[1])

    def test_boolean_schema_version_is_not_an_integer_version(self):
        metadata(self.paths["entry"], schema_version=True)
        self.finding("schema-version", exit_code=2)

    def test_integration_owner_needs_verification_coverage(self):
        second_task(self.paths)
        self.replace("task", "| REQ-01 | both |", "| REQ-01 | implements |")
        self.replace("entry", "| T001 | T001, T002 |", "| T001 | T002 |")
        metadata(self.paths["group"], integration_owner="T001")
        self.finding("integration-coverage")

    def test_shared_output_without_dependency_is_visible(self):
        second = second_task(self.paths)
        metadata(second, depends_on=[])
        self.finding("unordered-shared-write", exit_code=0)

    def test_retired_id_cannot_be_reused(self):
        with self.paths["entry"].open("a") as stream:
            stream.write("\n## Retired tasks\n\n| Task | Replaced by | Reason |\n|---|---|---|\n| T001 | — | Retired fixture task |\n")
        self.finding("retired-task")

    def test_duplicate_retired_id_is_rejected(self):
        with self.paths["entry"].open("a") as stream:
            stream.write("\n## Retired tasks\n\n| Task | Replaced by | Reason |\n|---|---|---|\n| T099 | T001 | Replaced fixture task |\n| T099 | T001 | Duplicate retirement |\n")
        self.finding("retired-task")

    def test_retired_id_must_have_task_syntax(self):
        with self.paths["entry"].open("a") as stream:
            stream.write("\n## Retired tasks\n\n| Task | Replaced by | Reason |\n|---|---|---|\n| free-text | T001 | Invalid retirement ID |\n")
        self.finding("retired-task")

    def test_legacy_layout_is_explicitly_unsupported(self):
        self.paths["entry"].write_text("# Existing plan\n\n## Task 1\nA legacy task.\n")
        self.finding("frontmatter", exit_code=2)

    def test_bad_inventory_does_not_produce_pass(self):
        inventory = self.paths["base"] / "inventory.json"
        inventory.write_text("[]")
        self.finding("input", "--inventory", str(inventory), exit_code=2)


if __name__ == "__main__":
    unittest.main()
