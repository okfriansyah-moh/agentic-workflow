"""Explicit replacement of selected skill directories with recoverable ownership."""
import copy
import fcntl
import os
from pathlib import Path
import re
import shutil
import stat
import time
import uuid

from . import installer as api

HOST_ROOTS = {"codex": ".codex/skills", "claude": ".claude/skills",
              "cursor": ".cursor/skills", "copilot": ".copilot/skills"}


def directory_snapshot(path):
    if path.is_symlink() or not path.is_dir():
        return None
    entries = {}
    for item in [path, *sorted(path.rglob("*"))]:
        info = item.lstat()
        entry = {"mode": stat.S_IMODE(info.st_mode)}
        if stat.S_ISLNK(info.st_mode):
            entry.update(kind="link", target=os.readlink(item))
        elif stat.S_ISDIR(info.st_mode):
            entry["kind"] = "directory"
        elif stat.S_ISREG(info.st_mode):
            entry.update(kind="file", sha256=api.digest(item.read_bytes()))
        else:
            raise ValueError(f"Unsupported special file in skill: {item.name}")
        entries[item.relative_to(path).as_posix()] = entry
    return {"kind": "directory", "sha256": api.digest(api.encoded(entries)), "entries": entries}


def backup_directory(root, restore):
    relative = restore["backup"]
    expected = ".local/share/agent-workflow/install-backups/"
    if not relative.startswith(expected) or "/originals/" not in relative:
        raise ValueError("Skill backup must be inside this global installation")
    path = api.safe_path(root, relative)
    if path.is_symlink():
        raise ValueError("Skill backup must be a directory, not a symlink")
    return path


def restoration_conflicts(root, files, allow_restored=False):
    conflicts = []
    for relative, record in files.items():
        if not record.get("restore"):
            continue
        try:
            path = api.safe_path(root, relative)
            if allow_restored and directory_snapshot(path) == record["restore"]["snapshot"]:
                continue
            current = api.snapshot(path)
            if current != {"kind": "link", "target": record["target"]} and not (allow_restored and current is None):
                raise ValueError("Selected skill link was modified; retained")
            original = backup_directory(root, record["restore"])
            if directory_snapshot(original) != record["restore"]["snapshot"]:
                raise ValueError("Original skill backup was modified or removed; retained")
        except (OSError, ValueError) as error:
            conflicts.append({"path": relative, "reason": str(error)})
    return conflicts


def restore_directory(root, relative, restore, expected):
    path = api.safe_path(root, relative)
    original = backup_directory(root, restore)
    if directory_snapshot(path) == restore["snapshot"]:
        return
    if directory_snapshot(original) != restore["snapshot"]:
        raise ValueError("Original skill backup was modified or removed")
    current = api.snapshot(path)
    if current is not None and current != expected:
        raise ValueError("Local edits prevent restoring the original skill")
    staged = original.parent / (".restore-" + uuid.uuid4().hex)
    try:
        shutil.copytree(original, staged, symlinks=True)
        if directory_snapshot(staged) != restore["snapshot"]:
            raise ValueError("Restored skill does not match the saved hashes and modes")
        if path.is_symlink():
            path.unlink()
        os.replace(staged, path)
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def restore_owned(root, relative, record):
    conflicts = restoration_conflicts(root, {relative: record}, allow_restored=True)
    if conflicts:
        return conflicts[0]["reason"]
    restore_directory(root, relative, record["restore"], {"kind": "link", "target": record["target"]})
    return None


def unresolved_transactions(state_root):
    pending = []
    for path in sorted((state_root / "install-backups").glob("*/transaction.json")):
        data = api.load(path, {})
        if data.get("kind") == "skill-resolution" and data.get("phase") not in {"completed", "rolled-back"}:
            pending.append(path.parent.name)
    return pending


def selected_bundle(root, state_root):
    config = api.load(state_root / "config.json", {})
    relative = config.get("bundle")
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Install a global bundle before resolving skills")
    bundle = api.safe_path(root, (state_root.relative_to(root) / relative / "manifest.json").as_posix()).parent
    manifest = api.validate_source(bundle)
    return bundle, {item["name"] for item in manifest["skills"]}


def prepare_resolution(args, root, state_root, state, backup):
    bundle, available = selected_bundle(root, state_root)
    files, reused = {}, []
    for host in dict.fromkeys(args.hosts):
        for skill in dict.fromkeys(args.skills):
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", skill) or skill not in available:
                raise ValueError(f"Skill is absent from the selected bundle: {skill}")
            relative = f"{HOST_ROOTS[host]}/{skill}"
            path = api.safe_path(root, relative)
            expected = {"kind": "link", "target": os.path.relpath(bundle / "skills" / skill, path.parent)}
            owned = state["files"].get(relative, {})
            conflicts = restoration_conflicts(root, {relative: owned})
            if conflicts:
                raise ValueError(conflicts[0]["reason"])
            if path.is_symlink() and path.resolve() == (bundle / "skills" / skill).resolve():
                reused.append(relative)
                continue
            original = directory_snapshot(path)
            if original is None:
                raise ValueError(f"Expected an existing skill directory: {relative}")
            restore = {"backup": (backup / "originals" / relative).relative_to(root).as_posix(), "snapshot": original}
            files[relative] = {"before": original, "after": expected, "restore": restore}
    return files, reused


def resolution_state(state, records):
    updated = copy.deepcopy(state)
    for relative, record in records.items():
        updated["files"][relative] = dict(record["after"], restore=record["restore"])
    updated["conflicts"] = [item for item in updated.get("conflicts", []) if item["path"] not in records]
    return updated


def save_transaction(backup, transaction):
    api.atomic(backup / "transaction.json", api.encoded(transaction), 0o600)


def replace_directory(root, relative, record):
    path = api.safe_path(root, relative)
    if directory_snapshot(path) != record["before"]:
        raise ValueError("Skill changed during resolution; no replacement was made")
    saved = backup_directory(root, record["restore"])
    saved.parent.mkdir(parents=True, exist_ok=True)
    os.replace(path, saved)
    if directory_snapshot(saved) != record["before"]:
        raise ValueError("Moved skill backup does not match its original snapshot")
    path.symlink_to(record["after"]["target"])


def rollback_resolution(root, state_root, backup, transaction):
    conflicts = []
    current_state = api.load(state_root / "install-state.json", {})
    if current_state not in (transaction["previous_state"], transaction["next_state"]):
        conflicts.append("install-state.json changed after skill resolution")
    for relative, record in transaction["files"].items():
        path = api.safe_path(root, relative)
        if directory_snapshot(path) == record["before"]:
            continue
        original = backup_directory(root, record["restore"])
        if api.snapshot(path) not in (None, record["after"]) or directory_snapshot(original) != record["before"]:
            conflicts.append(relative)
    if conflicts:
        return {"status": "blocked", "reason": "Local edits or damaged backups prevent rollback", "paths": conflicts}
    for relative, record in reversed(list(transaction["files"].items())):
        restore_directory(root, relative, record["restore"], record["after"])
    api.atomic(state_root / "install-state.json", api.encoded(transaction["previous_state"]))
    transaction["phase"] = "rolled-back"
    save_transaction(backup, transaction)
    return {"status": "rolled-back", "restored": len(transaction["files"])}


def apply_resolution(root, state_root, backup, records, state):
    transaction = {"schema_version": 1, "kind": "skill-resolution", "phase": "prepared",
                   "files": records, "previous_state": state, "next_state": resolution_state(state, records)}
    backup.mkdir(parents=True, mode=0o700)
    save_transaction(backup, transaction)
    try:
        for relative, record in records.items():
            replace_directory(root, relative, record)
        api.atomic(state_root / "install-state.json", api.encoded(transaction["next_state"]))
        transaction["phase"] = "completed"
        save_transaction(backup, transaction)
    except BaseException as error:
        transaction["phase"] = "recovery-required"
        try:
            recovered = rollback_resolution(root, state_root, backup, transaction)
        except (OSError, ValueError) as restore_error:
            recovered = {"status": "blocked", "reason": str(restore_error)}
        if recovered["status"] != "rolled-back":
            save_transaction(backup, transaction)
            return {"status": "blocked", "reason": str(error), "recovery": recovered,
                    "backup": backup.relative_to(root).as_posix()}
        raise
    return {"status": "resolved", "changed": len(records), "backup": backup.relative_to(root).as_posix()}


def resolve_skills(args):
    if not args.global_install or not args.use_bundle:
        raise ValueError("Skill resolution requires --global and --use-bundle")
    root, state_root, _ = api.destination(args)
    if not state_root.is_dir():
        raise ValueError("Install a global bundle before resolving skills")
    with (state_root / ".install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pending = unresolved_transactions(state_root)
        if pending:
            return {"status": "blocked", "reason": "Recover interrupted skill resolution with rollback", "transactions": pending}
        state = api.load(state_root / "install-state.json", {})
        if not state.get("files"):
            raise ValueError("No managed global installation was found")
        name = time.strftime("%Y%m%d-%H%M%S") + "-skills-" + uuid.uuid4().hex[:8]
        backup = api.safe_path(root, (state_root.relative_to(root) / "install-backups" / name / "transaction.json").as_posix()).parent
        records, reused = prepare_resolution(args, root, state_root, state, backup)
        if not records:
            return {"status": "resolved", "changed": 0, "reused": reused, "backup": None}
        result = apply_resolution(root, state_root, backup, records, state)
        result["reused"] = reused
        return result


def register(subparsers):
    parser = subparsers.add_parser("resolve-skills", help="Replace selected global skill directories with the pinned bundle")
    parser.add_argument("--global", dest="global_install", action="store_true", required=True)
    parser.add_argument("--home", help="Alternate installation home for fixtures")
    parser.add_argument("--hosts", choices=tuple(HOST_ROOTS), nargs="+", required=True)
    parser.add_argument("--skills", nargs="+", required=True)
    parser.add_argument("--use-bundle", action="store_true", required=True)
    parser.set_defaults(handler=resolve_skills, repo=None)
