"""Reversible installations and host adapters, using only the standard library."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- agent-workflow:begin -->"
END = "<!-- agent-workflow:end -->"
HOSTS = ("codex", "claude", "cursor", "copilot")
BUNDLE_DIRS = ("agent_workflow", "scripts", "skills", "agents", "prompts", "profiles", "adapters", "resources", "schemas", "docs", "tests")


def load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".aw-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def tree_digest(path):
    result = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file() and not ignored(item.relative_to(path)):
            result.update(item.relative_to(path).as_posix().encode() + b"\0")
            result.update(hashlib.sha256(item.read_bytes()).digest() + b"\n")
    return result.hexdigest()


def ignored(path):
    return any(part in {"__pycache__", ".git", "node_modules", ".DS_Store"} for part in path.parts) or path.suffix == ".pyc"


def bundle_ignored(path):
    runtime_dirs = {"coverage", "build", "dist", ".gradle", ".svelte-kit", "test-results", "playwright-report"}
    return ignored(path) or (path.parts[0] == "tests" and bool(set(path.parts) & runtime_dirs))


def destination(args):
    if args.global_install:
        root = Path(args.home or Path.home()).expanduser().resolve()
        safe_path(root, ".local/share/agent-workflow/.install.lock")
        return root, root / ".local/share/agent-workflow", True
    root = Path(args.repo or ".").expanduser().resolve()
    safe_path(root, ".ai/.install.lock")
    return root, root / ".ai", False


def safe_path(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe managed path: {relative}")
    target = root / path
    for parent in target.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Refusing managed write through symlink: {parent}")
    return target


def snapshot(path):
    if path.is_symlink():
        return {"kind": "link", "target": os.readlink(path)}
    if path.exists():
        if not path.is_file():
            return {"kind": "directory"}
        return {"kind": "file", "sha256": digest(path.read_bytes())}
    return None


def bundle_files(source, prefix):
    result = {}
    candidates = [source / part for part in BUNDLE_DIRS]
    candidates += [source / name for name in ("manifest.json", "README.md", "LICENSE")]
    for item in candidates:
        paths = item.rglob("*") if item.is_dir() else [item]
        for path in paths:
            if path.is_file() and not bundle_ignored(path.relative_to(source)):
                if path.is_symlink():
                    raise ValueError(f"Source bundle contains a symlink: {path}")
                relative = (prefix / path.relative_to(source)).as_posix()
                result[relative] = {"kind": "file", "data": path.read_bytes(), "mode": path.stat().st_mode & 0o777}
    return result


def launcher(global_install):
    location = 'path.parent.parent / "share/agent-workflow"' if global_install else 'path.parent.parent'
    return f'''#!/usr/bin/env python3
import json
import pathlib
import sys
path = pathlib.Path(__file__).resolve()
state_root = {location}
config = json.loads((state_root / "config.json").read_text())
bundle = (state_root / config["bundle"]).resolve()
if not bundle.is_relative_to(state_root.resolve()):
    raise SystemExit("Bundle selection escapes installation root")
sys.path.insert(0, str(bundle))
from agent_workflow.cli import main
sys.exit(main())
'''.encode()


def instruction_body(source, version, global_install):
    body = (source / "adapters/AGENTS.md").read_text().replace("{version}", version)
    if global_install:
        body = "## Portable workflow\n\nUse a repository's `.ai/config.json` and root AGENTS.md when present. Its pinned bundle governs all workflow checks. Otherwise use the installed agent-workflow skill catalog under `~/.local/share/agent-workflow/bundles/" + version + "/docs/SKILLS.md`. Keep personal and repository instructions intact. Use native subagents only when delegated work is authorized; keep reviewers independent.\n"
    return START + "\n" + body.rstrip() + "\n" + END + "\n"


def roles(source):
    data = load(source / "agents/catalog.json", {})
    return data.get("roles", data.get("agents", []))


def role_text(role, host, prefix):
    instructions = role["instructions"]
    if isinstance(instructions, list):
        instructions = "\n".join(instructions)
    instructions += "\n\nRead the repository AGENTS.md and selected .ai/config.json first when present. "
    instructions += "Only Forge dispatches native subagents; workers return to their parent. Inherit the host model settings and never start a nested Forge. "
    instructions += "Role skill catalog (load only relevant entries): " + ", ".join(role.get("skills", [])) + ". "
    instructions += "Resolve .ai/config.json bundle relative to .ai, then read that bundle skills/<name>/SKILL.md directly. Do not resolve a pinned skill through a global name match. "
    instructions += f"Only when no project configuration exists, use skill files under {prefix}/skills.\n"
    name = "aw-" + role.get("id", role["name"])
    if host == "codex":
        fields = {"name": name, "description": role["description"], "developer_instructions": instructions}
        return "\n".join(key + " = " + json.dumps(value) for key, value in fields.items()) + "\n"
    if host == "cursor":
        description = " ".join(role["description"].split())
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,.;()/&'-]*", description):
            raise ValueError("Cursor role descriptions require plain single-line text without YAML delimiters")
        header = f"---\nname: {name}\ndescription: {description}\n"
    else:
        header = f"---\nname: {json.dumps(name)}\ndescription: {json.dumps(role['description'])}\n"
    if host == "copilot":
        header += "include-custom-instructions: true\n"
    return header + "---\n\n" + instructions


def host_command(global_install, host):
    if global_install:
        return 'python3 "$HOME/.local/bin/agent-workflow" host-hook --host ' + host + ' --scope global'
    code = "import pathlib,runpy,sys; p=pathlib.Path.cwd(); s=next((x/'.ai/bin/agent-workflow' for x in (p,*p.parents) if (x/'.ai/config.json').is_file()),None); sys.argv=[str(s),'host-hook','--host'," + repr(host) + ",'--scope','repo']; runpy.run_path(str(s),run_name='__main__') if s else None"
    return "python3 -c " + shlex.quote(code)


def hook_entry(global_install, host):
    command = host_command(global_install, host)
    if host in {"codex", "claude"}:
        return "PostToolUse", {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": command, "timeout": 60}]}
    if host == "cursor":
        return "postToolUse", {"command": command, "timeout": 60, "matcher": "Write|Delete"}
    return "postToolUse", {"type": "command", "bash": command, "timeoutSec": 60}


def adapter_files(source, root, bundle, global_install, version):
    files = {}
    for host in HOSTS:
        directory = ".copilot" if global_install and host == "copilot" else (".github" if host == "copilot" else "." + host)
        for role in roles(source):
            suffix = ".toml" if host == "codex" else (".agent.md" if host == "copilot" else ".md")
            name = "aw-" + role.get("id", role["name"]) + suffix
            prefix = "~/.local/share/agent-workflow/bundles/" + version if global_install else bundle.as_posix()
            text = role_text(role, host, prefix)
            files[f"{directory}/agents/{name}"] = {"kind": "file", "data": text.encode()}
        hook_path = f"{directory}/hooks.json"
        if host == "claude":
            hook_path = ".claude/settings.json"
        if host == "copilot":
            if global_install:
                continue  # Copilot's repository hook directory is the portable scope.
            hook_path = ".github/hooks/agent-workflow.json"
        event, entry = hook_entry(global_install, host)
        files[hook_path] = {"kind": "hooks", "event": event, "entry": entry, "versioned": host in {"cursor", "copilot"}}
    instructions = instruction_body(source, version, global_install)
    targets = (".codex/AGENTS.md", ".claude/CLAUDE.md") if global_install else ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md")
    for target in targets:
        files[target] = {"kind": "block", "text": instructions}
    if not global_install:
        files[".cursor/rules/agent-workflow.mdc"] = {"kind": "file", "data": b'---\ndescription: Portable implementation workflow\nalwaysApply: true\n---\nRead root AGENTS.md and the pinned .ai/config.json before implementation.\n'}
    return files


def skill_links(source, bundle, global_install):
    result = {}
    roots = (".codex/skills", ".claude/skills", ".cursor/skills", ".copilot/skills") if global_install else (".agents/skills", ".claude/skills", ".cursor/skills", ".github/skills")
    for skill in load(source / "manifest.json")["skills"]:
        name = skill["name"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            raise ValueError(f"Invalid skill name: {name}")
        for directory in roots:
            relative = Path(directory) / name
            target = os.path.relpath(bundle / "skills" / name, relative.parent)
            result[relative.as_posix()] = {"kind": "link", "target": target, "skill": name, "checksum": tree_digest(source / "skills" / name), "source_checksum": skill.get("source", {}).get("source_sha256")}
    return result


def file_state(spec):
    if spec["kind"] == "file":
        return {"kind": "file", "sha256": digest(spec["data"])}
    if spec["kind"] == "link":
        return {"kind": "link", "target": spec["target"]}
    return {key: value for key, value in spec.items() if key not in {"data", "checksum", "skill"}}


def block_in(text):
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError("Malformed managed instruction markers")
    if START not in text:
        return None
    return text[text.index(START):text.index(END) + len(END)] + "\n"


def render_block(path, spec, old):
    text = path.read_text() if path.exists() else ""
    current = block_in(text)
    if old and path.exists() and current is None:
        raise ValueError("Managed instruction block was removed or edited")
    if current and current != spec["text"] and (not old or current != old.get("text")):
        raise ValueError("Managed instruction block has local edits")
    if current:
        return text.replace(current.rstrip("\n"), spec["text"].rstrip("\n"), 1).encode()
    return (text + ("\n" if text and not text.endswith("\n\n") else "") + spec["text"]).encode()


def render_hooks(path, spec, old):
    data = load(path, {})
    hooks = data.setdefault("hooks", {})
    entries = hooks.setdefault(spec["event"], [])
    if old and path.exists() and old["entry"] not in entries:
        raise ValueError("Managed hook entry was removed or edited")
    if old and old["entry"] != spec["entry"]:
        if old["entry"] not in entries:
            raise ValueError("Managed hook entry has local edits")
        entries.remove(old["entry"])
    if spec["entry"] not in entries:
        entries.append(spec["entry"])
    if spec["versioned"]:
        if data.get("version", 1) != 1:
            raise ValueError("Unsupported existing hooks schema version")
        data["version"] = 1
    return encoded(data)


def prepare_reused_skill(path, spec, old):
    if not path.is_dir() or path.is_symlink():
        return None
    existing_hash = tree_digest(path)
    if old and old.get("kind") != "reused-skill":
        raise ValueError("Managed skill link was replaced by a directory")
    if old and existing_hash != old["checksum"]:
        raise ValueError("Reused skill has local edits; retained personal version")
    if existing_hash not in {spec["checksum"], spec.get("source_checksum")}:
        raise ValueError("Existing skill differs; retained personal version")
    return None, {"kind": "reused-skill", "checksum": existing_hash}, True


def validate_existing(current, old, update):
    if current is None:
        return
    if not old or current != {key: old.get(key) for key in current}:
        raise ValueError("Existing unmanaged or locally modified content")
    if not update:
        raise ValueError("Managed version changed; use explicit update")


def prepare_managed_text(path, current, spec, old):
    if current and current["kind"] != "file":
        raise ValueError("Instruction or settings path is not a regular file")
    data = render_block(path, spec, old) if spec["kind"] == "block" else render_hooks(path, spec, old)
    return data, file_state(spec), bool(current and path.read_bytes() == data)


def prepare_item(root, relative, spec, old, update):
    path = safe_path(root, relative)
    current = snapshot(path)
    if spec["kind"] in {"block", "hooks"}:
        return prepare_managed_text(path, current, spec, old)
    wanted = file_state(spec)
    if (old or {}).get("kind") == "reused-skill":
        if current and current["kind"] != "directory":
            raise ValueError("Reused skill directory was replaced; retained local content")
    if current == wanted:
        return None, old or dict(wanted, reused=True), True
    if spec["kind"] == "link":
        reused = prepare_reused_skill(path, spec, old)
        if reused is not None:
            return reused
    validate_existing(current, old, update)
    if (old or {}).get("restore"):
        wanted["restore"] = old["restore"]
    return spec.get("data"), wanted, False


def validate_source(source):
    manifest = load(source / "manifest.json")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("skills"), list):
        raise ValueError("Source requires a skill manifest")
    names = [item["name"] for item in manifest["skills"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate skill entries")
    for skill in manifest["skills"]:
        name = skill["name"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            raise ValueError(f"Invalid skill name: {name}")
        directory = source / "skills" / name
        if not (directory / "SKILL.md").is_file():
            raise ValueError(f"Missing skill entry: {name}")
        checksum = skill.get("checksum", {})
        if checksum and (checksum.get("algorithm") != "sha256-tree-v1" or checksum.get("value") != tree_digest(directory)):
            raise ValueError(f"Skill checksum does not match: {name}")
    for role in roles(source):
        missing = set(role.get("skills", [])) - set(names)
        if missing:
            raise ValueError(f"Role {role['name']} has missing skills: {sorted(missing)}")
    return manifest


def inventory(source, root, state_root, global_install, profile):
    manifest = validate_source(source)
    if not re.fullmatch(r"[a-z0-9-]+", profile):
        raise ValueError("Invalid profile name")
    version = manifest.get("version", manifest.get("bundle", {}).get("version"))
    if not version or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+.][A-Za-z0-9.-]+)?", version):
        raise ValueError("Bundle version must be a safe semantic version")
    prefix = state_root.relative_to(root)
    bundle = prefix / "bundles" / version
    files = bundle_files(source, bundle)
    files.update(adapter_files(source, root, bundle, global_install, version))
    files.update(skill_links(source, bundle, global_install))
    config = {"schema_version": 1, "bundle_version": version, "bundle": f"bundles/{version}", "profile": profile, "max_workers": 3, "max_correction_rounds": 2}
    files[(prefix / "config.json").as_posix()] = {"kind": "file", "data": encoded(config)}
    launcher_path = ".local/bin/agent-workflow" if global_install else ".ai/bin/agent-workflow"
    files[launcher_path] = {"kind": "file", "data": launcher(global_install), "mode": 0o755}
    if not global_install:
        files[".ai/.gitignore"] = {"kind": "file", "data": b"/state/\n/reports/\n/evidence/\n/install-backups/\n/.install.lock\n"}
    return version, files


def backup_item(root, backup, relative):
    path = safe_path(root, relative)
    before = snapshot(path)
    record = {"before": before, "mode": path.stat().st_mode & 0o777 if before and before["kind"] == "file" else None}
    if before and before["kind"] == "file":
        target = backup / relative
        atomic(target, path.read_bytes())
    return record


def restore_item(root, backup, relative, record):
    path = safe_path(root, relative)
    before = record["before"]
    if path.is_symlink() or path.is_file():
        path.unlink()
    if before and before["kind"] == "file":
        atomic(path, (backup / relative).read_bytes(), record["mode"])
    elif before and before["kind"] == "link":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(before["target"])


def apply_changes(root, state_root, changes, state):
    backup = state_root / "install-backups" / (time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
    records = {}
    try:
        for relative, spec, data in changes:
            records[relative] = backup_item(root, backup, relative)
            path = safe_path(root, relative)
            if spec["kind"] == "link":
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink() or path.is_file():
                    path.unlink()
                path.symlink_to(spec["target"])
            else:
                mode = spec.get("mode", path.stat().st_mode & 0o777 if path.exists() else 0o644)
                atomic(path, data, mode)
            records[relative]["after"] = snapshot(path)
        atomic(backup / "transaction.json", encoded({"files": records, "previous_state": load(state_root / "install-state.json", {})}))
        atomic(state_root / "install-state.json", encoded(state))
    except BaseException:
        for relative, record in reversed(list(records.items())):
            restore_item(root, backup, relative, record)
        raise
    return str(backup.relative_to(root))


def install(args):
    source = Path(args.source or ROOT).resolve()
    root, state_root, global_install = destination(args)
    root.mkdir(parents=True, exist_ok=True)
    state_root.mkdir(parents=True, exist_ok=True)
    with (state_root / ".install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return install_locked(args, source, root, state_root, global_install)


def install_locked(args, source, root, state_root, global_install):
    from .skill_resolution import unresolved_transactions
    pending = unresolved_transactions(state_root)
    if pending:
        return {"status": "blocked", "reason": "Recover interrupted skill resolution with rollback", "transactions": pending}
    previous = load(state_root / "install-state.json", {"files": {}})
    from .skill_resolution import restoration_conflicts
    restoration_errors = restoration_conflicts(root, previous["files"])
    if restoration_errors:
        return {"status": "blocked", "changed": 0, "conflicts": restoration_errors}
    profile = args.profile or load(state_root / "config.json", {}).get("profile", "general")
    version, files = inventory(source, root, state_root, global_install, profile)
    if previous.get("version") and previous["version"] != version and args.command != "update":
        return {"status": "blocked", "reason": "Installed version differs; invoke update explicitly"}
    managed, changes, conflicts, reused = dict(previous["files"]), [], [], 0
    for relative, spec in files.items():
        try:
            data, record, same = prepare_item(root, relative, spec, previous["files"].get(relative), args.command == "update")
            managed[relative] = record
            if same:
                reused += 1
            else:
                changes.append((relative, spec, data))
        except (ValueError, OSError) as error:
            conflicts.append({"path": relative, "reason": str(error)})
    critical = [item for item in conflicts if files[item["path"]]["kind"] != "link"]
    if critical:
        return {"status": "blocked", "conflicts": conflicts, "changed": 0}
    state = {"schema_version": 1, "version": version, "scope": "global" if global_install else "repository", "files": managed, "conflicts": conflicts}
    backup = apply_changes(root, state_root, changes, state) if changes else None
    if not changes and state != previous:
        atomic(state_root / "install-state.json", encoded(state))
    return {"status": "installed", "version": version, "scope": state["scope"], "changed": len(changes), "reused": reused, "conflicts": conflicts, "backup": backup, "host_loading": "not verified; see doctor and docs/HOSTS.md"}


def remove_managed(root, relative, record):
    path = safe_path(root, relative)
    if record.get("restore"):
        from .skill_resolution import restore_owned
        return restore_owned(root, relative, record)
    if record.get("reused") or record["kind"] == "reused-skill":
        return "preserved reused content"
    if record["kind"] == "block":
        text = path.read_text() if path.exists() else ""
        if block_in(text) != record["text"]:
            return "modified instruction block retained"
        updated = text.replace(record["text"].rstrip("\n"), "", 1)
        if updated.strip():
            atomic(path, updated.encode())
        else:
            path.unlink()
        return None
    if record["kind"] == "hooks":
        data = load(path, {})
        entries = data.get("hooks", {}).get(record["event"], [])
        if record["entry"] not in entries:
            return "modified hook retained"
        entries.remove(record["entry"])
        if not entries:
            data["hooks"].pop(record["event"], None)
        atomic(path, encoded(data))
        return None
    current = snapshot(path)
    if current is None:
        return None
    if current != record:
        return "modified content retained"
    path.unlink()
    return None


def uninstall(args):
    root, state_root, _ = destination(args)
    if not state_root.is_dir():
        return {"status": "not-installed", "removed": 0}
    retained, removed = [], 0
    with (state_root / ".install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        from .skill_resolution import unresolved_transactions
        pending_transactions = unresolved_transactions(state_root)
        if pending_transactions:
            return {"status": "blocked", "reason": "Recover interrupted skill resolution with rollback", "transactions": pending_transactions}
        state = load(state_root / "install-state.json", {})
        if not state:
            return {"status": "not-installed", "removed": 0}
        from .skill_resolution import restoration_conflicts
        conflicts = restoration_conflicts(root, state["files"], allow_restored=True)
        if conflicts:
            return {"status": "blocked", "removed": 0, "retained": conflicts}
        pending = {}
        ordered = sorted(state["files"].items(), key=lambda item: bool(item[1].get("restore")))
        for relative, record in reversed(ordered):
            reason = remove_managed(root, relative, record)
            if reason:
                retained.append({"path": relative, "reason": reason})
                pending[relative] = record
            else:
                removed += 1
        state["files"] = pending
        atomic(state_root / "install-state.json", encoded(state))
    return {"status": "uninstalled", "removed": removed, "retained": retained, "backups_retained": True}


def rollback(args):
    root, state_root, _ = destination(args)
    with (state_root / ".install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return rollback_locked(args, root, state_root)


def rollback_locked(args, root, state_root):
    backup = safe_path(root, args.backup)
    expected_root = state_root / "install-backups"
    if not backup.resolve().is_relative_to(expected_root.resolve()):
        raise ValueError("Backup must belong to this installation")
    transaction = load(backup / "transaction.json")
    if transaction.get("kind") == "skill-resolution":
        from .skill_resolution import rollback_resolution
        return rollback_resolution(root, state_root, backup, transaction)
    state = load(state_root / "install-state.json", {})
    conflicts = []
    for relative, record in transaction["files"].items():
        if snapshot(safe_path(root, relative)) != record.get("after"):
            conflicts.append(relative)
    if conflicts:
        return {"status": "blocked", "reason": "Local edits prevent rollback", "paths": conflicts}
    for relative, record in reversed(list(transaction["files"].items())):
        restore_item(root, backup, relative, record)
    atomic(state_root / "install-state.json", encoded(transaction["previous_state"]))
    return {"status": "rolled-back", "restored": len(transaction["files"])}


def check_owned(root, relative, record):
    path = safe_path(root, relative)
    if record["kind"] in {"file", "link"}:
        expected = {key: value for key, value in record.items() if key not in {"reused", "restore"}}
        if record.get("restore"):
            from .skill_resolution import restoration_conflicts
            return not restoration_conflicts(root, {relative: record})
        return snapshot(path) == expected
    if record["kind"] == "reused-skill":
        return path.is_dir() and not path.is_symlink() and tree_digest(path) == record["checksum"]
    if record["kind"] == "block":
        return path.is_file() and block_in(path.read_text()) == record["text"]
    if record["kind"] == "hooks":
        entries = load(path, {}).get("hooks", {}).get(record["event"], [])
        return record["entry"] in entries
    return True


def doctor(args):
    root, state_root, global_install = destination(args)
    state = load(state_root / "install-state.json", {})
    from .skill_resolution import unresolved_transactions
    findings = [{"path": f"install-backups/{name}", "status": "recovery-required"}
                for name in unresolved_transactions(state_root)]
    for relative, record in state.get("files", {}).items():
        try:
            valid = check_owned(root, relative, record)
        except (ValueError, OSError):
            valid = False
        if not valid:
            findings.append({"path": relative, "status": "modified-or-missing"})
    config = load(state_root / "config.json", {})
    bundle = state_root / config.get("bundle", "missing")
    manifest = load(bundle / "manifest.json", {})
    try:
        validate_source(bundle)
    except (ValueError, OSError) as error:
        findings.append({"path": str(bundle.relative_to(root)), "status": "invalid-bundle", "reason": str(error)})
    hosts = {}
    for host in HOSTS:
        binary = shutil.which("cursor-agent" if host == "cursor" else host)
        hosts[host] = {"executable": binary, "runtime_loading": "unverified", "trust": "host approval/reload may be required; never bypassed"}
    try:
        from .host_verification import summarize_host_verifications
    except ModuleNotFoundError as error:
        if error.name != "agent_workflow.host_verification":
            raise
        saved_hosts = {}
    else:
        saved_hosts = summarize_host_verifications(root, state_root, global_install)
    for host, verification in saved_hosts.items():
        hosts.setdefault(host, {})["saved_verification"] = verification
    return {"status": "healthy" if state and not findings else "blocked", "scope": "global" if global_install else "repository", "bundle": config, "skill_entries": len(manifest.get("skills", [])), "findings": findings, "preserved_conflicts": state.get("conflicts", []), "hosts": hosts, "python": sys.version.split()[0]}


def locate_repo(cwd):
    path = Path(cwd).resolve()
    return next((item for item in (path, *path.parents) if (item / ".ai/config.json").is_file()), None)


def local_call(root, arguments, payload=None, timeout=45):
    command = [sys.executable, str(root / ".ai/bin/agent-workflow"), *arguments]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, cwd=root, start_new_session=True)
    try:
        stdout, stderr = process.communicate(json.dumps(payload) if payload is not None else None, timeout=timeout)
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
        except ProcessLookupError:
            pass
        return subprocess.CompletedProcess(command, 124, "", "Pinned local hook timed out")


def hook_result(root, host, payload):
    completed = local_call(root, ["hook", "--repo", str(root), "--host", host, "--stage", "fast"], payload)
    try:
        result = json.loads(completed.stdout)
    except (ValueError, TypeError):
        result = {"status": "error"}
    if completed.returncode:
        result["status"] = "error"
    return result


def event_identity(payload):
    identity = next((payload[key] for key in ("tool_use_id", "toolUseId", "tool_call_id", "event_id") if payload.get(key)), None)
    session = payload.get("session_id", payload.get("sessionId"))
    if not identity and session and payload.get("timestamp"):
        identity = payload["timestamp"]
    if not identity:
        return None
    return digest(encoded({"session": session, "identity": identity, "payload": payload}))


def deduplicated_hook(root, host, payload):
    event = event_identity(payload)
    if event is None:
        return hook_result(root, host, payload)
    directory = safe_path(root, ".ai/state/hook-dedupe")
    safe_path(root, ".ai/state/hook-dedupe/lock")
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        probe = local_call(root, ["fingerprint", "--repo", str(root)], timeout=5)
        try:
            fingerprint = json.loads(probe.stdout)["sha256"] if probe.returncode == 0 else None
        except (ValueError, KeyError, TypeError):
            fingerprint = None
        if not fingerprint:
            return hook_result(root, host, payload)
        key = digest(encoded([host, event, fingerprint]))
        records = load(directory / "records.json", {})
        records = {k: v for k, v in records.items() if time.time() - v["created_at"] < 120}
        if key in records:
            return records[key]["result"]
        result = hook_result(root, host, payload)
        records[key] = {"created_at": time.time(), "result": result}
        records = dict(sorted(records.items(), key=lambda item: item[1]["created_at"])[-100:])
        atomic(directory / "records.json", encoded(records), 0o600)
        return result


def host_hook(args):
    payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    root = locate_repo(payload.get("cwd", os.getcwd()))
    if root is None:
        return {}
    result = deduplicated_hook(root, args.host, payload)
    if result.get("status") in {"failed", "blocked", "error"}:
        message = "Workflow fast checks need attention. Run .ai/bin/agent-workflow gate --repo . --stage fast for details."
        if args.host in {"codex", "claude"}:
            return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}
        if args.host == "copilot":
            return {"additionalContext": message}
        return {"additional_context": message}
    return {}


def register(subparsers):
    for name in ("install", "update", "uninstall", "doctor", "rollback"):
        parser = subparsers.add_parser(name)
        scope = parser.add_mutually_exclusive_group()
        scope.add_argument("--global", dest="global_install", action="store_true")
        scope.add_argument("--repo")
        parser.add_argument("--home", help="Global target home; intended for fixtures or explicit alternate users")
        parser.add_argument("--source", help="Source bundle for installation/update")
        parser.add_argument("--profile")
        if name == "rollback":
            parser.add_argument("--backup", required=True)
        parser.set_defaults(handler=install if name in {"install", "update"} else globals()[name])
    parser = subparsers.add_parser("host-hook")
    parser.add_argument("--host", choices=HOSTS, required=True)
    parser.add_argument("--scope", choices=("global", "repo"), required=True)
    parser.set_defaults(handler=host_hook)
