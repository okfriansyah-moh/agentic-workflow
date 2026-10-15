"""Recoverable explicit skill selection against isolated user directories."""
import argparse
import json
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_installer as fixture
from agent_workflow import installer as api
from agent_workflow import skill_resolution as resolution


class SkillResolutionTests(unittest.TestCase):
    setUp = fixture.InstallerTests.setUp
    manifest = fixture.InstallerTests.manifest
    args = fixture.InstallerTests.args

    def selected(self, hosts=None, skills=None):
        return argparse.Namespace(global_install=True, home=str(self.repo), repo=None,
                                  hosts=hosts or ["claude", "cursor"], skills=skills or ["sample"], use_bundle=True)

    def originals(self):
        snapshots = {}
        for host in ("claude", "cursor"):
            relative = f".{host}/skills/sample"
            path = self.repo / relative
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(f"Personal {host} skill.\n")
            (path / "scripts").mkdir(mode=0o751)
            executable = path / "scripts/run.sh"
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o751)
            (path / "alias").symlink_to("SKILL.md")
            (path / "empty").mkdir(mode=0o700)
            path.chmod(0o750)
            snapshots[relative] = resolution.directory_snapshot(path)
        api.install(self.args(global_install=True))
        return snapshots

    def state(self):
        return api.load(self.repo / ".local/share/agent-workflow/install-state.json")

    def assert_originals(self, snapshots):
        for relative, snapshot in snapshots.items():
            self.assertEqual(resolution.directory_snapshot(self.repo / relative), snapshot)

    def test_resolve_repeat_and_restore_directories_modes_links_and_hashes(self):
        snapshots = self.originals()
        result = resolution.resolve_skills(self.selected())
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["changed"], 2)
        self.assertIn(".local/share/agent-workflow/install-backups/", result["backup"])
        for relative, snapshot in snapshots.items():
            self.assertTrue((self.repo / relative).is_symlink())
            owned = self.state()["files"][relative]
            self.assertEqual(owned["restore"]["snapshot"], snapshot)
            self.assertEqual(resolution.directory_snapshot(self.repo / owned["restore"]["backup"]), snapshot)
        self.assertEqual(self.state()["conflicts"], [])
        repeated = resolution.resolve_skills(self.selected())
        self.assertEqual(repeated["changed"], 0)
        self.assertEqual(len(repeated["reused"]), 2)
        self.assertEqual(api.install(self.args(global_install=True))["conflicts"], [])
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "healthy")
        restored = api.rollback(self.args(global_install=True, backup=result["backup"]))
        self.assertEqual(restored["status"], "rolled-back")
        self.assert_originals(snapshots)

    def test_uninstall_restores_originals_and_retains_backups(self):
        snapshots = self.originals()
        result = resolution.resolve_skills(self.selected())
        removed = api.uninstall(self.args(global_install=True))
        self.assertEqual(removed["status"], "uninstalled")
        self.assert_originals(snapshots)
        self.assertTrue((self.repo / result["backup"] / "transaction.json").is_file())
        self.assertFalse((self.repo / ".local/bin/agent-workflow").exists())

    def test_changed_backup_blocks_rollback_uninstall_and_doctor(self):
        self.originals()
        result = resolution.resolve_skills(self.selected())
        owned = self.state()["files"][".claude/skills/sample"]
        original = self.repo / owned["restore"]["backup"] / "SKILL.md"
        original.write_text("Changed backup after installation.\n")
        self.assertEqual(api.rollback(self.args(global_install=True, backup=result["backup"]))["status"], "blocked")
        removed = api.uninstall(self.args(global_install=True))
        self.assertEqual(removed["status"], "blocked")
        self.assertEqual(removed["removed"], 0)
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "blocked")
        self.assertTrue((self.repo / ".local/bin/agent-workflow").exists())
        self.assertEqual(original.read_text(), "Changed backup after installation.\n")

    def test_modified_selected_link_blocks_re_resolution_and_preserves_original(self):
        self.originals()
        result = resolution.resolve_skills(self.selected())
        selected = self.repo / ".claude/skills/sample"
        selected.unlink()
        selected.mkdir()
        (selected / "SKILL.md").write_text("New personal directory.\n")
        with self.assertRaisesRegex(ValueError, "modified"):
            resolution.resolve_skills(self.selected())
        self.assertEqual(api.rollback(self.args(global_install=True, backup=result["backup"]))["status"], "blocked")
        self.assertEqual(api.uninstall(self.args(global_install=True))["status"], "blocked")
        self.assertEqual((selected / "SKILL.md").read_text(), "New personal directory.\n")

    def test_failure_after_first_replacement_restores_all_directories(self):
        snapshots = self.originals()
        previous = self.state()
        original = resolution.replace_directory
        def fail_second(root, relative, record):
            if relative.startswith(".cursor/"):
                raise OSError("Injected second replacement failure")
            return original(root, relative, record)
        with patch.object(resolution, "replace_directory", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "second replacement"):
                resolution.resolve_skills(self.selected())
        self.assert_originals(snapshots)
        self.assertEqual(self.state(), previous)
        self.assertEqual(resolution.unresolved_transactions(self.repo / ".local/share/agent-workflow"), [])

    def test_recovery_remains_available_when_directory_restore_fails(self):
        snapshots = self.originals()
        original_replace = resolution.replace_directory
        original_restore = resolution.restore_directory
        def fail_second(root, relative, record):
            if relative.startswith(".cursor/"):
                raise OSError("Injected replacement failure")
            return original_replace(root, relative, record)
        def fail_restore(root, relative, restore, expected):
            if relative.startswith(".claude/"):
                raise OSError("Injected restore failure")
            return original_restore(root, relative, restore, expected)
        with patch.object(resolution, "replace_directory", side_effect=fail_second), patch.object(resolution, "restore_directory", side_effect=fail_restore):
            result = resolution.resolve_skills(self.selected())
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(api.install(self.args(global_install=True))["status"], "blocked")
        self.assertEqual(api.uninstall(self.args(global_install=True))["status"], "blocked")
        self.assertEqual(resolution.resolve_skills(self.selected())["status"], "blocked")
        recovered = api.rollback(self.args(global_install=True, backup=result["backup"]))
        self.assertEqual(recovered["status"], "rolled-back")
        self.assert_originals(snapshots)

    def test_uninstall_can_resume_after_directory_restore_failure(self):
        snapshots = self.originals()
        resolution.resolve_skills(self.selected())
        original = resolution.restore_directory
        count = 0
        def fail_second_restore(root, relative, restore, expected):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("Injected uninstall restore failure")
            return original(root, relative, restore, expected)
        with patch.object(resolution, "restore_directory", side_effect=fail_second_restore):
            with self.assertRaisesRegex(OSError, "uninstall restore"):
                api.uninstall(self.args(global_install=True))
        self.assertTrue((self.repo / ".local/bin/agent-workflow").exists())
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "blocked")
        self.assertEqual(api.uninstall(self.args(global_install=True))["status"], "uninstalled")
        self.assert_originals(snapshots)

    def test_uninstall_retries_a_restore_interrupted_after_link_removal(self):
        snapshots = self.originals()
        resolution.resolve_skills(self.selected())
        original = os.replace
        failed = False
        def fail_restore_once(source, target):
            nonlocal failed
            if Path(source).name.startswith(".restore-") and not failed:
                failed = True
                raise OSError("Injected restore rename failure")
            return original(source, target)
        with patch.object(os, "replace", side_effect=fail_restore_once):
            with self.assertRaisesRegex(OSError, "restore rename"):
                api.uninstall(self.args(global_install=True))
        self.assertEqual(api.uninstall(self.args(global_install=True))["status"], "uninstalled")
        self.assert_originals(snapshots)

    def test_state_write_failure_restores_originals(self):
        snapshots = self.originals()
        original = api.atomic
        failed = False
        def fail_state_once(path, data, mode=0o644):
            nonlocal failed
            if path.name == "install-state.json" and not failed:
                failed = True
                raise OSError("Injected state write failure")
            return original(path, data, mode)
        with patch.object(api, "atomic", side_effect=fail_state_once):
            with self.assertRaisesRegex(OSError, "state write"):
                resolution.resolve_skills(self.selected())
        self.assert_originals(snapshots)

    def test_preflight_missing_skill_changes_no_directory(self):
        snapshots = self.originals()
        with self.assertRaisesRegex(ValueError, "absent"):
            resolution.resolve_skills(self.selected(skills=["sample", "missing"]))
        self.assert_originals(snapshots)

    def test_absolute_matching_link_is_reused_without_taking_ownership(self):
        api.install(self.args(global_install=True))
        path = self.repo / ".claude/skills/sample"
        target = path.resolve()
        path.unlink()
        path.symlink_to(target)
        result = resolution.resolve_skills(self.selected(hosts=["claude"]))
        self.assertEqual(result["changed"], 0)
        self.assertEqual(os.readlink(path), str(target))

    def test_rollback_after_later_update_refuses_to_reset_newer_state(self):
        self.originals()
        result = resolution.resolve_skills(self.selected())
        self.manifest("1.1.0")
        api.install(self.args(command="update", global_install=True))
        current = self.state()
        self.assertEqual(api.rollback(self.args(global_install=True, backup=result["backup"]))["status"], "blocked")
        self.assertEqual(self.state(), current)
        self.assertEqual(api.uninstall(self.args(global_install=True))["status"], "uninstalled")

    def test_directory_rename_error_preserves_every_original(self):
        snapshots = self.originals()
        original = os.replace
        def fail_skill_move(source, target):
            if Path(source).resolve() == (self.repo / ".claude/skills/sample").resolve():
                raise OSError("Injected cross-device rename failure")
            return original(source, target)
        with patch.object(os, "replace", side_effect=fail_skill_move):
            with self.assertRaisesRegex(OSError, "cross-device"):
                resolution.resolve_skills(self.selected())
        self.assert_originals(snapshots)

    def test_four_named_conflicts_are_cleared_without_touching_other_skills(self):
        entries = [{"name": "sample"}]
        for name in ("design-system", "ui-ux-pro-max"):
            shutil.copytree(self.source / "skills/sample", self.source / "skills" / name)
            entries.append({"name": name})
            for host in ("claude", "cursor"):
                original = self.repo / f".{host}/skills/{name}"
                original.mkdir(parents=True)
                (original / "SKILL.md").write_text(f"Personal {name} in {host}.\n")
        (self.source / "manifest.json").write_text(json.dumps({"version": "1.0.0", "skills": entries}))
        installed = api.install(self.args(global_install=True))
        self.assertEqual(len(installed["conflicts"]), 4)
        args = self.selected(skills=["design-system", "ui-ux-pro-max"])
        resolved = resolution.resolve_skills(args)
        self.assertEqual(resolved["changed"], 4)
        self.assertEqual(self.state()["conflicts"], [])
        self.assertEqual(resolution.resolve_skills(args)["changed"], 0)
        self.assertEqual(api.install(self.args(global_install=True))["conflicts"], [])
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "healthy")

    def test_backup_mode_edits_are_detected(self):
        self.originals()
        resolution.resolve_skills(self.selected())
        record = self.state()["files"][".claude/skills/sample"]
        backup = self.repo / record["restore"]["backup"] / "scripts/run.sh"
        backup.chmod(0o644)
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "blocked")
        self.assertEqual(api.uninstall(self.args(global_install=True))["status"], "blocked")

    def test_saved_transaction_recovers_an_interrupted_move_before_link_creation(self):
        snapshots = self.originals()
        state_root = self.repo / ".local/share/agent-workflow"
        backup = state_root / "install-backups/interrupted-fixture"
        records, _ = resolution.prepare_resolution(self.selected(), self.repo, state_root, self.state(), backup)
        transaction = {"kind": "skill-resolution", "phase": "prepared", "files": records,
                       "previous_state": self.state(), "next_state": resolution.resolution_state(self.state(), records)}
        resolution.save_transaction(backup, transaction)
        relative, record = next(iter(records.items()))
        original = self.repo / record["restore"]["backup"]
        original.parent.mkdir(parents=True)
        os.replace(self.repo / relative, original)
        self.assertEqual(api.install(self.args(global_install=True))["status"], "blocked")
        result = api.rollback(self.args(global_install=True, backup=backup.relative_to(self.repo).as_posix()))
        self.assertEqual(result["status"], "rolled-back")
        self.assert_originals(snapshots)

    def test_parser_requires_explicit_global_bundle_choice(self):
        parser = argparse.ArgumentParser()
        commands = parser.add_subparsers(dest="command")
        resolution.register(commands)
        args = parser.parse_args(["resolve-skills", "--global", "--hosts", "claude", "cursor", "--skills", "sample", "--use-bundle"])
        self.assertTrue(args.global_install)
        self.assertTrue(args.use_bundle)
        self.assertEqual(args.hosts, ["claude", "cursor"])


if __name__ == "__main__":
    unittest.main()
