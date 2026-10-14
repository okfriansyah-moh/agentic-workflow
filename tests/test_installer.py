"""Installer behavior against isolated homes and relocatable repositories."""
import argparse
import json
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent_workflow import installer as api


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.repo = self.base / "project"
        self.source.mkdir()
        self.repo.mkdir()
        for name in ("agent_workflow", "adapters", "skills/sample", "agents", "profiles"):
            (self.source / name).mkdir(parents=True, exist_ok=True)
        for name in ("__init__.py", "cli.py", "installer.py"):
            shutil.copy2(api.ROOT / "agent_workflow" / name, self.source / "agent_workflow" / name)
        for name in ("coordination", "gates"):
            (self.source / "agent_workflow" / f"{name}.py").write_text("def register(parser):\n    pass\n")
        shutil.copy2(api.ROOT / "adapters/AGENTS.md", self.source / "adapters/AGENTS.md")
        (self.source / "skills/sample/SKILL.md").write_text("---\nname: sample\ndescription: Sample fixture skill\n---\nRead approved plans.\n")
        self.manifest("1.0.0")
        (self.source / "agents/catalog.json").write_text(json.dumps({"roles": [{"id": "forge", "name": "forge", "description": "Coordinate approved tasks", "instructions": "Keep independent review.", "skills": ["sample"]}]}))

    def manifest(self, version):
        (self.source / "manifest.json").write_text(json.dumps({"version": version, "skills": [{"name": "sample"}]}))

    def args(self, command="install", global_install=False, **extra):
        values = dict(command=command, repo=str(self.repo), global_install=global_install, home=str(self.repo) if global_install else None, source=str(self.source), profile=None)
        values.update(extra)
        return argparse.Namespace(**values)

    def test_clean_repeated_and_relocation(self):
        first = api.install(self.args())
        self.assertEqual(first["status"], "installed")
        self.assertGreater(first["changed"], 10)
        self.assertEqual(api.install(self.args())["changed"], 0)
        moved = self.base / "moved"
        self.repo.rename(moved)
        shutil.rmtree(self.source)
        completed = subprocess.run([sys.executable, str(moved / ".ai/bin/agent-workflow"), "doctor", "--repo", str(moved)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["skill_entries"], 1)
        self.assertTrue((moved / ".agents/skills/sample/SKILL.md").is_file())

    def test_local_edits_prevent_overwrite_and_uninstall_preserves_them(self):
        api.install(self.args())
        role = self.repo / ".codex/agents/aw-forge.toml"
        role.write_text("personal edit\n")
        result = api.install(self.args(command="update"))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["changed"], 0)
        result = api.uninstall(self.args())
        self.assertEqual(role.read_text(), "personal edit\n")
        self.assertTrue(any(item["path"] == ".codex/agents/aw-forge.toml" for item in result["retained"]))

    def test_personal_instructions_settings_and_permissions_survive(self):
        instructions = self.repo / "AGENTS.md"
        instructions.write_text("Personal policy.\n")
        settings = self.repo / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text(json.dumps({"permissions": {"deny": ["unsafe"]}, "hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": []}]}}))
        settings.chmod(0o600)
        api.install(self.args())
        self.assertEqual(settings.stat().st_mode & 0o777, 0o600)
        config = json.loads(settings.read_text())
        config["personal"] = True
        settings.write_text(json.dumps(config))
        api.uninstall(self.args())
        self.assertIn("Personal policy.", instructions.read_text())
        self.assertNotIn(api.START, instructions.read_text())
        remaining = json.loads(settings.read_text())
        self.assertTrue(remaining["personal"])
        self.assertEqual(remaining["permissions"]["deny"], ["unsafe"])
        self.assertEqual(len(remaining["hooks"]["PostToolUse"]), 1)

    def test_global_skill_conflict_retains_personal_and_bundle_is_available(self):
        existing = self.repo / ".codex/skills/sample"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("Personal skill\n")
        result = api.install(self.args(global_install=True))
        self.assertEqual(result["status"], "installed")
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertEqual((existing / "SKILL.md").read_text(), "Personal skill\n")
        self.assertTrue((self.repo / ".local/share/agent-workflow/bundles/1.0.0/skills/sample/SKILL.md").exists())
        api.uninstall(self.args(global_install=True))
        self.assertEqual((existing / "SKILL.md").read_text(), "Personal skill\n")

    def test_matching_preexisting_skill_is_reused_not_removed(self):
        existing = self.repo / ".codex/skills/sample"
        shutil.copytree(self.source / "skills/sample", existing)
        api.install(self.args(global_install=True))
        api.uninstall(self.args(global_install=True))
        self.assertTrue((existing / "SKILL.md").exists())

    def test_explicit_update_and_rollback(self):
        api.install(self.args(profile="movie-app"))
        self.manifest("1.1.0")
        self.assertEqual(api.install(self.args())["status"], "blocked")
        result = api.install(self.args(command="update"))
        self.assertEqual(result["status"], "installed")
        self.assertEqual(json.loads((self.repo / ".ai/config.json").read_text())["profile"], "movie-app")
        restored = api.rollback(self.args(backup=result["backup"]))
        self.assertEqual(restored["status"], "rolled-back")
        self.assertEqual(json.loads((self.repo / ".ai/config.json").read_text())["bundle_version"], "1.0.0")

    def test_rollback_preserves_settings_changed_after_update(self):
        api.install(self.args())
        self.manifest("1.1.0")
        result = api.install(self.args(command="update"))
        instructions = self.repo / "AGENTS.md"
        instructions.write_text(instructions.read_text() + "Added afterwards.\n")
        self.assertEqual(api.rollback(self.args(backup=result["backup"]))["status"], "blocked")
        self.assertIn("Added afterwards.", instructions.read_text())

    def test_symlink_parent_cannot_escape_target(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.repo / ".codex").symlink_to(outside)
        result = api.install(self.args())
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_state_root_is_rejected_before_lock_write(self):
        outside = self.base / "outside-state"
        outside.mkdir()
        (self.repo / ".ai").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            api.install(self.args())
        self.assertEqual(list(outside.iterdir()), [])

    def test_transaction_failure_restores_original_bytes(self):
        instructions = self.repo / "AGENTS.md"
        instructions.write_text("Keep me.\n")
        original = api.atomic
        calls = 0
        def fail_once(path, data, mode=0o644):
            nonlocal calls
            calls += 1
            if path.name == "config.json" and "install-backups" not in path.parts:
                raise OSError("Injected write failure")
            return original(path, data, mode)
        with patch.object(api, "atomic", side_effect=fail_once):
            with self.assertRaises(OSError):
                api.install(self.args())
        self.assertEqual(instructions.read_text(), "Keep me.\n")
        self.assertFalse((self.repo / ".ai/config.json").exists())

    def test_pinned_skill_edits_block_reinstall(self):
        api.install(self.args())
        skill = self.repo / ".ai/bundles/1.0.0/skills/sample/SKILL.md"
        skill.write_text("Locally changed pinned skill.\n")
        result = api.install(self.args(command="update"))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["changed"], 0)
        self.assertIn("Locally changed", skill.read_text())

    def test_doctor_detects_instruction_and_hook_edits(self):
        api.install(self.args())
        (self.repo / "AGENTS.md").write_text("Managed instructions removed.\n")
        settings = self.repo / ".claude/settings.json"
        settings.write_text('{"hooks": {}}')
        result = api.doctor(self.args())
        paths = {item["path"] for item in result["findings"]}
        self.assertEqual(result["status"], "blocked")
        self.assertIn("AGENTS.md", paths)
        self.assertIn(".claude/settings.json", paths)

    def test_host_hook_uses_pinned_runtime_and_global_does_not_assume_local_trust(self):
        gates = self.source / "agent_workflow/gates.py"
        gates.write_text("def register(parser):\n    command = parser.add_parser('hook')\n    command.add_argument('--repo')\n    command.add_argument('--host')\n    command.add_argument('--stage')\n    command.set_defaults(handler=lambda args: {'status': 'failed'})\n")
        api.install(self.args())
        payload = json.dumps({"cwd": str(self.repo)})
        with patch.object(sys, "stdin", io.StringIO(payload)):
            result = api.host_hook(argparse.Namespace(host="codex", scope="global"))
        self.assertIn("additionalContext", result["hookSpecificOutput"])
        with patch.object(sys, "stdin", io.StringIO(payload)):
            result = api.host_hook(argparse.Namespace(host="codex", scope="repo"))
        self.assertIn("additionalContext", result["hookSpecificOutput"])

    def test_hook_deduplication_requires_same_event_and_input(self):
        gates = self.source / "agent_workflow/gates.py"
        gates.write_text("import hashlib\nfrom pathlib import Path\ndef call(args):\n    path = Path(args.repo)/'.ai/state/count'\n    path.parent.mkdir(parents=True,exist_ok=True)\n    path.write_text(str(int(path.read_text())+1 if path.exists() else 1))\n    return {'status':'passed'}\ndef fingerprint(args):\n    source=Path(args.repo)/'input.txt'\n    return {'sha256':hashlib.sha256(source.read_bytes() if source.exists() else b'').hexdigest()}\ndef register(parser):\n    command=parser.add_parser('hook')\n    command.add_argument('--repo')\n    command.add_argument('--host')\n    command.add_argument('--stage')\n    command.set_defaults(handler=call)\n    command=parser.add_parser('fingerprint')\n    command.add_argument('--repo')\n    command.set_defaults(handler=fingerprint)\n")
        api.install(self.args())
        payload = {"cwd": str(self.repo), "session_id": "session", "tool_use_id": "edit-1"}
        def invoke(scope, context):
            with patch.object(sys, "stdin", io.StringIO(json.dumps(context))):
                api.host_hook(argparse.Namespace(host="codex", scope=scope))
        invoke("global", payload)
        invoke("repo", payload)
        count = self.repo / ".ai/state/count"
        self.assertEqual(count.read_text(), "1")
        (self.repo / "input.txt").write_text("Changed input")
        invoke("repo", payload)
        self.assertEqual(count.read_text(), "2")
        invoke("repo", dict(payload, tool_use_id="edit-2"))
        self.assertEqual(count.read_text(), "3")
        invoke("global", {"cwd": str(self.repo)})
        invoke("repo", {"cwd": str(self.repo)})
        self.assertEqual(count.read_text(), "5")

    def test_declared_skill_digest_is_verified_before_install(self):
        path = self.source / "manifest.json"
        data = json.loads(path.read_text())
        data["skills"][0]["checksum"] = {"algorithm": "sha256-tree-v1", "value": "0" * 64}
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "checksum"):
            api.install(self.args())
        self.assertFalse((self.repo / "AGENTS.md").exists())

    def test_modified_hook_is_not_added_twice_on_reinstall(self):
        api.install(self.args())
        path = self.repo / ".claude/settings.json"
        data = json.loads(path.read_text())
        data["hooks"]["PostToolUse"][0]["hooks"][0]["command"] = "personal-hook"
        path.write_text(json.dumps(data))
        result = api.install(self.args())
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(len(json.loads(path.read_text())["hooks"]["PostToolUse"]), 1)

    def test_uninstall_reads_state_after_lock_acquired(self):
        api.install(self.args())
        fresh = self.repo / "just-installed.txt"
        state_path = self.repo / ".ai/install-state.json"
        original = api.fcntl.flock
        def concurrent_update_then_lock(stream, operation):
            fresh.write_text("Managed by the preceding update.\n")
            state = json.loads(state_path.read_text())
            state["files"]["just-installed.txt"] = api.snapshot(fresh)
            state_path.write_text(json.dumps(state))
            return original(stream, operation)
        with patch.object(api.fcntl, "flock", side_effect=concurrent_update_then_lock):
            api.uninstall(self.args())
        self.assertFalse(fresh.exists())

    def test_codex_toml_and_copilot_instruction_opt_in(self):
        import tomllib
        api.install(self.args())
        role = tomllib.loads((self.repo / ".codex/agents/aw-forge.toml").read_text())
        self.assertEqual(role["name"], "aw-forge")
        self.assertNotIn("model", role)
        self.assertIn("include-custom-instructions: true", (self.repo / ".github/agents/aw-forge.agent.md").read_text())


if __name__ == "__main__":
    unittest.main()
