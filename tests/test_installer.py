"""Installer behavior against isolated homes and relocatable repositories."""
import argparse
from concurrent.futures import ThreadPoolExecutor
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
        for module in (api.ROOT / "agent_workflow").glob("*.py"):
            shutil.copy2(module, self.source / "agent_workflow" / module.name)
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
        repeated = api.install(self.args(global_install=True))
        self.assertEqual(repeated["conflicts"], [])
        self.assertEqual(repeated["changed"], 0)
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "healthy")
        api.uninstall(self.args(global_install=True))
        self.assertTrue((existing / "SKILL.md").exists())

    def test_reused_original_hashes_repeat_for_47_skills_and_detect_later_edits(self):
        entries = []
        for index in range(47):
            name = f"fixture-{index:02d}"
            original = self.repo / ".codex/skills" / name
            original.mkdir(parents=True)
            (original / "SKILL.md").write_text(f"Original skill {index}.\n")
            portable = self.source / "skills" / name
            shutil.copytree(original, portable)
            (portable / "SKILL.md").write_text(f"Portable skill {index}.\n")
            entries.append({"name": name, "source": {"source_sha256": api.tree_digest(original)}})
        entries.append({"name": "sample"})
        (self.source / "manifest.json").write_text(json.dumps({"version": "1.0.0", "skills": entries}))
        first = api.install(self.args(global_install=True))
        self.assertEqual(first["conflicts"], [])
        state_path = self.repo / ".local/share/agent-workflow/install-state.json"
        state = json.loads(state_path.read_text())
        state["conflicts"] = [{"path": f".codex/skills/fixture-{i:02d}", "reason": "Old false conflict"} for i in range(47)]
        state_path.write_text(json.dumps(state))
        repeated = api.install(self.args(global_install=True))
        self.assertEqual(repeated["conflicts"], [])
        self.assertEqual(repeated["changed"], 0)
        self.assertEqual(json.loads(state_path.read_text())["conflicts"], [])
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "healthy")
        changed = self.repo / ".codex/skills/fixture-03/SKILL.md"
        changed.write_text("Personal change after reuse.\n")
        diagnostic = api.doctor(self.args(global_install=True))
        self.assertEqual(diagnostic["status"], "blocked")
        self.assertIn(".codex/skills/fixture-03", {item["path"] for item in diagnostic["findings"]})
        repeated = api.install(self.args(global_install=True))
        self.assertEqual(len(repeated["conflicts"]), 1)
        self.assertEqual(changed.read_text(), "Personal change after reuse.\n")

    def test_doctor_reused_skill_replacement_or_deletion_is_detected(self):
        original = self.repo / ".codex/skills/sample"
        shutil.copytree(self.source / "skills/sample", original)
        api.install(self.args(global_install=True))
        shutil.rmtree(original)
        original.symlink_to(self.source / "skills/sample")
        result = api.doctor(self.args(global_install=True))
        self.assertEqual(result["status"], "blocked")
        reinstall = api.install(self.args(global_install=True))
        self.assertTrue(any(item["path"] == ".codex/skills/sample" for item in reinstall["conflicts"]))
        original.unlink()
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "blocked")

    def test_unattended_defaults_survive_repeat_update_and_rollback(self):
        for global_install in (False, True):
            with self.subTest(global_install=global_install):
                target = self.base / ('global-home' if global_install else 'autonomy-project')
                target.mkdir()
                settings = {
                    '.codex/config.toml': 'approval_policy="never"\nsandbox_mode="danger-full-access"\nmodel="personal"\n',
                    '.claude/settings.json': json.dumps({'permissions': {'defaultMode': 'bypassPermissions', 'deny': ['private-rule']}, 'personal': True}),
                    '.copilot/settings.json': json.dumps({'defaultPermissionMode': 'allow-all', 'defaultMode': 'autopilot', 'personal': True}),
                    '.cursor/cli-config.json': json.dumps({'approvalMode': 'unrestricted', 'sandbox': {'mode': 'disabled'}, 'personal': True}),
                    '.cursor/permissions.json': json.dumps({'approvalMode': 'unrestricted', 'personal': True}),
                }
                for relative, text in settings.items():
                    path = target / relative
                    path.parent.mkdir(exist_ok=True)
                    path.write_text(text)
                args = self.args(global_install=global_install, repo=str(target), home=str(target))
                self.manifest('1.0.0')
                self.assertEqual(api.install(args)['status'], 'installed')
                self.assertEqual(api.install(args)['changed'], 0)
                self.manifest('1.1.1')
                args.command = 'update'
                updated = api.install(args)
                self.assertEqual(updated['status'], 'installed')
                self.assertEqual(api.install(args)['changed'], 0)
                diagnostic = api.doctor(args)
                self.assertIn('autonomy', diagnostic['hosts']['cursor'])
                args.backup = updated['backup']
                self.assertEqual(api.rollback(args)['status'], 'rolled-back')
                for relative, text in settings.items():
                    value = (target / relative).read_text()
                    if relative == '.claude/settings.json':
                        self.assertEqual(json.loads(value)['permissions'], json.loads(text)['permissions'])
                        self.assertTrue(json.loads(value)['personal'])
                    elif relative == '.codex/config.toml':
                        import tomllib
                        parsed = tomllib.loads(value)
                        self.assertEqual(parsed['approval_policy'], 'never')
                        self.assertEqual(parsed['sandbox_mode'], 'danger-full-access')
                        self.assertEqual(parsed['model'], 'personal')
                    else:
                        self.assertEqual(value, text)

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

    def enable_edit_checks(self):
        path = self.repo / ".ai/config.json"
        config = json.loads(path.read_text())
        config["hook_mode"] = "fast"
        path.write_text(json.dumps(config))

    def test_feedback_hooks_do_not_repeat_gates_after_edits(self):
        api.install(self.args())
        self.assertEqual(json.loads((self.repo / ".ai/config.json").read_text())["hook_mode"], "feedback")
        for host in ("codex", "claude", "cursor", "copilot"):
            payload = {"cwd": str(self.repo), "workspace_roots": [str(self.repo)],
                       "session_id": "selection", "tool_use_id": "edit-1"}
            with self.subTest(host=host), patch.object(api, "local_call") as execute:
                with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
                    self.assertEqual(api.host_hook(argparse.Namespace(host=host, scope="repo")), {})
                execute.assert_not_called()

    def test_host_hook_uses_pinned_runtime_and_global_does_not_assume_local_trust(self):
        gates = self.source / "agent_workflow/gates.py"
        gates.write_text("def register(parser):\n    command = parser.add_parser('hook')\n    command.add_argument('--repo')\n    command.add_argument('--host')\n    command.add_argument('--stage')\n    command.set_defaults(handler=lambda args: {'status': 'failed'})\n")
        api.install(self.args())
        self.enable_edit_checks()
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
        self.enable_edit_checks()
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

    def workflow_root(self, name):
        root = self.base / name
        (root / ".ai").mkdir(parents=True, exist_ok=True)
        (root / ".ai/config.json").write_text("{}")
        return root.resolve()

    def test_cursor_hook_selects_native_workspace_when_user_hook_cwd_is_elsewhere(self):
        root = self.workflow_root("workspace")
        payload = {"workspace_roots": [str(root)], "tool_input": {"file_path": "smoke.json"}}
        with patch.object(api.os, "getcwd", return_value=str(self.base / "home/.cursor")):
            self.assertEqual(api.hook_repository(payload, "cursor", "global"), root)
            self.assertEqual(api.hook_repository(dict(payload, cwd=str(self.base)), "cursor", "global"), root)
            self.assertIsNone(api.hook_repository({}, "cursor", "global"))
            self.assertIsNone(api.hook_repository(dict(payload, workspace_roots=[]), "cursor", "global"))

    def test_cursor_multiroot_uses_file_or_working_directory_without_guessing(self):
        first, second = self.workflow_root("first"), self.workflow_root("second")
        payload = {"workspace_roots": [str(first), str(second)]}
        target = dict(payload, tool_input={"file_path": str(second / "smoke.json")})
        self.assertEqual(api.hook_repository(target, "cursor", "global"), second)
        self.assertEqual(api.hook_repository(dict(payload, cwd=str(first)), "cursor", "global"), first)
        for extra in ({}, {"tool_input": {"file_path": "smoke.json"}},
                      {"tool_input": {"file_path": str(first / "a"), "path": str(second / "b")}}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                api.hook_repository(dict(payload, **extra), "cursor", "global")
        (second / ".ai/config.json").unlink()
        with self.assertRaises(ValueError):
            api.hook_repository(payload, "cursor", "global")
        self.assertIsNone(api.hook_repository(target, "cursor", "global"))

    def test_cursor_hook_rejects_workspace_escape_and_invalid_context(self):
        root, other = self.workflow_root("workspace"), self.workflow_root("outside")
        (root / "escape").symlink_to(other, target_is_directory=True)
        for value in (str(other / "smoke.json"), "../outside/smoke.json", "escape/smoke.json"):
            payload = {"workspace_roots": [str(root)], "tool_input": {"file_path": value}}
            with self.subTest(value=value), self.assertRaises(ValueError):
                api.hook_repository(payload, "cursor", "global")
        for roots in (str(root), ["relative"], [str(root / "missing")], [None]):
            with self.subTest(roots=roots), self.assertRaises(ValueError):
                api.hook_repository({"workspace_roots": roots}, "cursor", "global")
        child = root / "child"
        child.mkdir()
        self.assertEqual(api.hook_repository({"workspace_roots": [str(root), str(child)]}, "cursor", "global"), root)
        self.assertEqual(api.hook_repository({"cwd": str(root), "tool_input": "*** Begin Patch"}, "codex", "global"), root)

    def real_hook_fixture(self):
        shutil.copy2(api.ROOT / "agent_workflow/gates.py", self.source / "agent_workflow/gates.py")
        api.install(self.args())
        self.enable_edit_checks()
        program = ("import json; from pathlib import Path; "
                   "count=Path('.ai/state/gate-count'); count.parent.mkdir(parents=True,exist_ok=True); "
                   "count.write_text(str(int(count.read_text())+1 if count.exists() else 1)); "
                   "good=json.loads(Path('smoke.json').read_text())['passing']; "
                   "print('fixture gate passed' if good else 'fixture gate failed'); raise SystemExit(0 if good else 1)")
        registry = {"schema_version": 1, "supported_suffixes": [], "checks": [
            {"id": "fixture", "stage": "fast", "required": True, "argv": [sys.executable, "-c", program]}]}
        (self.repo / ".ai/gates.json").write_text(json.dumps(registry))
        (self.repo / "smoke.json").write_text('{"passing": true}')
        return {"workspace_roots": [str(self.repo)], "conversation_id": "conversation", "generation_id": "generation",
                "session_id": "conversation", "tool_use_id": "edit-1", "hook_event_name": "postToolUse",
                "tool_name": "Write", "tool_input": {"file_path": str(self.repo / "smoke.json"), "content": "private-input"},
                "tool_output": {"api_key": "private-output"}}

    def call_host_hook(self, host, scope, payload):
        with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), patch.object(api.os, "getcwd", return_value=str(self.base / "home/.cursor")):
            return api.host_hook(argparse.Namespace(host=host, scope=scope))

    def test_real_cursor_gate_and_claude_compatibility_wrappers_share_results(self):
        payload = self.real_hook_fixture()
        count = self.repo / ".ai/state/gate-count"
        for passing, number in ((True, 1), (False, 2)):
            (self.repo / "smoke.json").write_text(json.dumps({"passing": passing}))
            payload["tool_use_id"] = f"edit-{number}"
            for host, scope in (("cursor", "global"), ("claude", "global"), ("cursor", "repo"), ("claude", "repo")):
                context = dict(payload)
                if host == "claude":
                    context.update(tool_name="Edit", hook_event_name="PostToolUse", cwd=str(self.repo))
                result = self.call_host_hook(host, scope, context)
                self.assertEqual(bool(result), not passing, (host, scope, result))
                if not passing:
                    self.assertIn("additional_context", result)
                self.assertEqual(count.read_text(), str(number))
        records = (self.repo / ".ai/state/hook-dedupe/records.json").read_text()
        self.assertNotIn("private-input", records)
        self.assertNotIn("private-output", records)
        self.assertNotIn("conversation", records)
        self.assertEqual({record["result"]["status"] for record in json.loads(records).values()}, {"passed", "error"})

    def test_real_hook_rechecks_changed_input_distinct_events_and_missing_identity(self):
        payload = self.real_hook_fixture()
        self.assertEqual(self.call_host_hook("cursor", "global", payload), {})
        (self.repo / "smoke.json").write_text('{"passing": false}')
        self.assertIn("additional_context", self.call_host_hook("claude", "global", payload))
        self.call_host_hook("cursor", "repo", dict(payload, tool_use_id="edit-2"))
        self.call_host_hook("cursor", "repo", dict(payload, tool_name="Read"))
        for host in ("cursor", "claude"):
            self.call_host_hook(host, "global", dict(payload, tool_use_id=None))
        native_claude = {key: value for key, value in payload.items() if key not in {"workspace_roots", "conversation_id", "generation_id"}}
        native_claude["cwd"] = str(self.repo)
        self.assertIn("hookSpecificOutput", self.call_host_hook("claude", "global", native_claude))
        self.assertEqual((self.repo / ".ai/state/gate-count").read_text(), "7")

    def test_ambiguous_cursor_payload_returns_feedback_without_running_gate(self):
        payload = self.real_hook_fixture()
        other = self.workflow_root("other")
        payload.update(workspace_roots=[str(self.repo), str(other)], tool_input={})
        for host in ("cursor", "claude"):
            result = self.call_host_hook(host, "global", payload)
            self.assertIn("one safe repository", result["additional_context"])
        self.assertFalse((self.repo / ".ai/state/gate-count").exists())

    def test_generated_global_and_project_wrappers_share_one_gate_execution(self):
        payload = self.real_hook_fixture()
        home = self.base / "home"
        home.mkdir()
        api.install(self.args(global_install=True, home=str(home)))
        environment = dict(os.environ, HOME=str(home))
        calls = []
        for host, scope in (("cursor", "global"), ("claude", "global"), ("cursor", "repo"), ("claude", "repo")):
            root = home if scope == "global" else self.repo
            path = root / (".cursor/hooks.json" if host == "cursor" else ".claude/settings.json")
            event = "postToolUse" if host == "cursor" else "PostToolUse"
            entry = json.loads(path.read_text())["hooks"][event][0]
            command = entry["command"] if host == "cursor" else entry["hooks"][0]["command"]
            cwd = root / ("." + host) if scope == "global" else root
            calls.append((command, cwd))
        def invoke(item):
            return subprocess.run(["/bin/sh", "-c", item[0]], cwd=item[1], env=environment,
                                  input=json.dumps(payload), capture_output=True, text=True, timeout=30)
        for passing, number in ((True, 1), (False, 2)):
            (self.repo / "smoke.json").write_text(json.dumps({"passing": passing}))
            payload["tool_use_id"] = f"edit-{number}"
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(invoke, calls))
            for completed in results:
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertEqual(bool(json.loads(completed.stdout)), not passing)
            self.assertEqual((self.repo / ".ai/state/gate-count").read_text(), str(number))

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

    def test_doctor_includes_saved_host_verification_without_probing(self):
        import types
        module = types.ModuleType("agent_workflow.host_verification")
        module.summarize_host_verifications = lambda root, state_root, global_install: {"codex": {"status": "stale", "reason": "Native configuration changed"}}
        api.install(self.args())
        with patch.dict(sys.modules, {"agent_workflow.host_verification": module}):
            result = api.doctor(self.args())
        self.assertEqual(result["hosts"]["codex"]["saved_verification"]["status"], "stale")
        self.assertEqual(result["hosts"]["codex"]["runtime_loading"], "unverified")

    def test_claude_cursor_compatibility_has_eight_matching_plain_role_ids(self):
        roles = api.roles(api.ROOT)
        self.assertEqual(len(roles), 8)
        names = set()
        for role in roles:
            headers = []
            for host in ("claude", "cursor"):
                text = api.role_text(role, host, "bundle")
                header = text.split("---\n", 2)[1]
                headers.append(header)
                self.assertIn(f"name: aw-{role['id']}\n", header)
                self.assertIn(f"description: {role['description']}\n", header)
                self.assertNotIn('name: "', header)
                names.add(header.splitlines()[0])
            self.assertEqual(*headers)
        self.assertEqual(len(names), 8)

    def test_plain_role_frontmatter_rejects_ambiguous_yaml(self):
        role = {"name": "unsafe", "description": "Review approved changes", "instructions": "Read"}
        for host in ("claude", "cursor"):
            for description in ("Description: YAML mapping", "Description # comment", "true", "null"):
                with self.subTest(host=host, description=description), self.assertRaisesRegex(ValueError, "plain single-line"):
                    api.role_text({**role, "description": description}, host, "bundle")
            with self.assertRaisesRegex(ValueError, "role name"):
                api.role_text({**role, "id": "worker\nextra: value"}, host, "bundle")
        copilot = api.role_text({**role, "description": "Description: YAML mapping"}, "copilot", "bundle")
        self.assertIn('name: "aw-unsafe"\n', copilot)
        self.assertIn('description: "Description: YAML mapping"\n', copilot)
        self.assertIn("include-custom-instructions: true\n", copilot)

    def personal_global_profiles(self):
        personal = {}
        for host in ("claude", "cursor"):
            directory = self.repo / f".{host}"
            (directory / "agents").mkdir(parents=True)
            for name in ("backend", "forge", "frontend", "review", "operations"):
                path = directory / "agents" / f"{name}.md"
                path.write_text(f"---\nname: {name}\n---\nPersonal {name}.\n")
                path.chmod(0o600)
                personal[path] = (path.read_bytes(), path.stat().st_mode & 0o777)
        settings = self.repo / ".claude/settings.json"
        settings.write_text(json.dumps({"permissions": {"deny": ["Bash(private-command)"]}, "personal": True}))
        settings.chmod(0o600)
        instructions = self.repo / ".claude/CLAUDE.md"
        instructions.write_text("Personal workflow instructions.\n")
        return personal, settings, instructions

    def test_quoted_claude_global_upgrade_preserves_personal_roles_and_settings(self):
        catalog = [{**role, "skills": ["sample"]} for role in api.roles(api.ROOT)]
        (self.source / "agents/catalog.json").write_text(json.dumps({"roles": catalog}))
        personal, settings, instructions = self.personal_global_profiles()
        render = api.role_text
        def legacy(role, host, prefix):
            text = render(role, host, prefix)
            if host == "claude":
                text = text.replace(f"name: aw-{role['id']}\n", f"name: {json.dumps('aw-' + role['id'])}\n", 1)
                text = text.replace(f"description: {role['description']}\n", f"description: {json.dumps(role['description'])}\n", 1)
            return text
        with patch.object(api, "role_text", side_effect=legacy):
            self.assertEqual(api.install(self.args(global_install=True))["status"], "installed")
        original_roles = {path: path.read_bytes() for path in (self.repo / ".claude/agents").glob("aw-*.md")}
        before_settings = settings.read_bytes()
        self.assertEqual(api.install(self.args(global_install=True))["status"], "blocked")
        updated = api.install(self.args(command="update", global_install=True))
        self.assertEqual(updated["status"], "installed")
        self.assertEqual(updated["conflicts"], [])
        self.assertEqual(updated["changed"], 8)
        for role in catalog:
            headers = [(self.repo / f".{host}/agents/aw-{role['id']}.md").read_text().split("---\n", 2)[1]
                       for host in ("claude", "cursor")]
            self.assertEqual(*headers)
        self.assertEqual(api.install(self.args(global_install=True))["changed"], 0)
        self.assertEqual(api.doctor(self.args(global_install=True))["status"], "healthy")
        self.assertEqual(settings.read_bytes(), before_settings)
        self.assertEqual(settings.stat().st_mode & 0o777, 0o600)
        self.assertIn("Personal workflow instructions.", instructions.read_text())
        for path, (content, mode) in personal.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mode & 0o777), (content, mode))
        self.assertEqual(api.rollback(self.args(global_install=True, backup=updated["backup"]))["status"], "rolled-back")
        for path, content in original_roles.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(settings.read_bytes(), before_settings)

    def test_edited_global_claude_profile_blocks_update(self):
        api.install(self.args(global_install=True))
        profile = self.repo / ".claude/agents/aw-forge.md"
        changed = profile.read_text() + "Personal role adjustment.\n"
        profile.write_text(changed)
        result = api.install(self.args(command="update", global_install=True))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["changed"], 0)
        self.assertEqual(profile.read_text(), changed)

    def test_codex_toml_and_copilot_instruction_opt_in(self):
        import tomllib
        api.install(self.args())
        role = tomllib.loads((self.repo / ".codex/agents/aw-forge.toml").read_text())
        self.assertEqual(role["name"], "aw-forge")
        self.assertNotIn("model", role)
        self.assertIn("include-custom-instructions: true", (self.repo / ".github/agents/aw-forge.agent.md").read_text())


if __name__ == "__main__":
    unittest.main()
