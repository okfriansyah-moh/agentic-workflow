#!/usr/bin/env python3
"""Read-only validation for the plan-creation package format. Never runs task commands."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    yaml = None

READINESS = {"Draft", "Ready", "Needs update"}
STATUSES = {"Not started", "In progress", "In review", "Blocked", "Done"}
EMPTY = {"", "—", "-"}
TASK_ID = re.compile(r"T\d{3,}\Z")
GROUP_ID = re.compile(r"G\d{2,}\Z")
FEATURE = re.compile(r"[0-9]{2,}-[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
ROOT_SECTIONS = ["Goal and scope", "Shared execution rules", "Feature groups", "Obligation coverage", "Release verification"]
GROUP_SECTIONS = ["Outcome and scope", "Shared context", "Task list", "Dependencies", "Integrated acceptance"]
TASK_SECTIONS = ["Purpose and scope", "Traceability", "Prerequisites", "Change surface", "Knowledge", "Implementation", "Development guidance", "Acceptance", "Tests", "Validation", "Review and evidence", "Evidence", "Completion and handoff"]
COVERAGE = ["Obligation", "Source", "Locator", "Disposition", "Implementing tasks", "Verification tasks", "Reason"]
SURFACE = ["Repository", "Action", "Path", "Responsibility"]
VALIDATION = ["Check", "Method or command", "Working directory", "Expected result", "Required"]
EVIDENCE = ["Check", "Result", "Artifact", "Revision", "Environment", "Reviewer"]
INLINE_LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+["\'][^\n]*?["\'])?\s*\)')
REF_DEF = re.compile(r'^\s*\[([^\]]+)\]:\s*(<[^>]+>|\S+)', re.M)
REF_USE = re.compile(r'!?\[([^\]\n]+)\]\[([^\]\n]*)\]')


def unfence(text):
    """Remove fenced examples so their headings, tables, and links are not interpreted."""
    out, marker, length = [], None, 0
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if match:
            run = match.group(1)
            if marker is None:
                marker, length = run[0], len(run)
            elif run[0] == marker and len(run) >= length and not line[match.end():].strip():
                marker = None
            continue
        if marker is None:
            out.append(line)
    return "\n".join(out)


def clean(value):
    return str(value).strip().strip("`").strip()


def ids(value):
    value = clean(value)
    return [] if value in EMPTY else [clean(item) for item in value.split(",") if clean(item)]


def link_targets(text, document=None):
    definitions = {m.group(1).casefold(): m.group(2).strip("<>") for m in REF_DEF.finditer(unfence(document if document is not None else text))}
    links = [m.group(1).strip("<>") for m in INLINE_LINK.finditer(text)]
    for m in REF_USE.finditer(text):
        key = (m.group(2) or m.group(1)).casefold()
        links.append(definitions.get(key, "MISSING-REFERENCE:" + key))
    return links


def anchors(text):
    text = unfence(text)
    found = set(re.findall(r'\b(?:id|name)=["\']([^"\']+)["\']', text))
    counts = {}
    for match in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M):
        title = re.sub(r"<[^>]+>", "", match.group(1)).lower()
        title = re.sub(r"[^\w\-\s]", "", title)
        slug = re.sub(r"\s", "-", title)
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug + (f"-{count}" if count else ""))
    return found


def local_link(origin, target):
    target = target.strip("<>")
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return None
    return (origin.parent / unquote(parts.path)).resolve() if parts.path else origin, unquote(parts.fragment)


@dataclass
class Document:
    path: Path
    meta: dict
    body: str
    sections: dict


class Checker:
    def __init__(self, entry, inventory=None):
        self.entry = Path(entry).resolve()
        self.inventory = inventory
        self.findings = []
        self.docs = {}
        self.tasks = {}
        self.groups = {}
        self.repos = {}
        self.sources = {}
        self.unfresh_sources = set()
        self.coverage = {}
        self.root = None
        self.unsupported = False

    def add(self, code, path, message, severity="error"):
        self.findings.append({"severity": severity, "code": code, "path": str(path), "message": message})

    def gap(self, code, path, message):
        self.add(code, path, message, "gap")

    def load(self, path, kind, required):
        path = Path(path).resolve()
        if path in self.docs:
            doc = self.docs[path]
            if doc.meta.get("kind") != kind:
                self.add("kind", path, f"Expected kind {kind}.")
            return doc
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self.add("read", path, str(exc))
            return None
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", raw, re.S)
        if not match:
            self.add("frontmatter", path, "Missing package YAML header; legacy layouts need manual review.")
            if path == self.entry:
                self.unsupported = True
            return None
        try:
            meta = yaml.load(match.group(1), Loader=UniqueLoader)
        except (yaml.YAMLError, ValueError, TypeError) as exc:
            self.add("yaml", path, str(exc))
            return None
        if not isinstance(meta, dict):
            self.add("yaml", path, "Metadata must be a mapping.")
            return None
        if meta.get("kind") != kind:
            self.add("kind", path, f"Expected kind {kind}.")
        body = raw[match.end():]
        visible = unfence(body)
        parts = re.split(r"^## (.+?)\s*$", visible, flags=re.M)
        sections = {}
        for i in range(1, len(parts), 2):
            heading = parts[i]
            if heading in sections:
                self.add("duplicate-section", path, f"Repeated section: {heading}.")
            sections[heading] = parts[i + 1]
        for heading in required:
            if not sections.get(heading, "").strip():
                self.add("section", path, f"Missing or empty section: {heading}.")
        if re.search(r"\{\{[^}]+\}\}", raw):
            self.gap("placeholder", path, "Unfilled template slots remain.")
        doc = Document(path, meta, body, sections)
        self.docs[path] = doc
        return doc

    def table(self, doc, heading, columns, required=True):
        text = doc.sections.get(heading, "")
        lines = text.splitlines()
        rows, collecting, found = [], False, False
        for line in lines:
            if not line.strip().startswith("|"):
                collecting = False
                continue
            cells = [clean(c.replace(r"\|", "|")) for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if cells == columns:
                if found:
                    self.add("duplicate-table", doc.path, f"Repeated {heading} table.")
                collecting, found = True, True
                continue
            if not collecting or all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if len(cells) != len(columns):
                self.add("table-row", doc.path, f"{heading}: expected {len(columns)} cells, got {len(cells)}.")
            else:
                rows.append(dict(zip(columns, cells)))
        if required and (not found or not rows):
            self.add("table", doc.path, f"Missing/empty {heading} table with columns: {', '.join(columns)}.")
        return rows

    def enum(self, doc, key, allowed):
        value = doc.meta.get(key)
        if not isinstance(value, str) or value not in allowed:
            self.add("metadata", doc.path, f"{key} must be one of: {', '.join(sorted(allowed))}.")

    def list_strings(self, doc, key):
        value = doc.meta.get(key)
        if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
            self.add("metadata", doc.path, f"{key} must be a list of nonempty strings.")
            return []
        if len(value) != len(set(value)):
            self.add("metadata", doc.path, f"{key} contains duplicate IDs.")
        return value

    def validate_sources(self):
        raw = self.root.meta.get("sources")
        if not isinstance(raw, list) or not raw:
            self.add("sources", self.entry, "sources must be a nonempty list.")
            return
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                self.add("source", self.entry, "Each source needs a string id.")
                continue
            sid = item["id"]
            if sid in self.sources:
                self.add("duplicate-source", self.entry, f"Repeated source ID {sid}.")
            self.sources[sid] = item
            if isinstance(item.get("path"), str) and item["path"]:
                path = (self.entry.parent / item["path"]).resolve()
                item["resolved"] = path
                try:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError as exc:
                    self.unfresh_sources.add(sid)
                    self.gap("source-access", self.entry, f"{sid}: {exc}")
                    continue
                if not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]):
                    self.unfresh_sources.add(sid)
                    self.gap("source-hash", self.entry, f"{sid}: record the source SHA-256.")
                elif digest != item["sha256"]:
                    self.unfresh_sources.add(sid)
                    self.gap("source-stale", self.entry, f"{sid}: source bytes changed; inspect impact before refreshing the digest.")
            elif isinstance(item.get("url"), str) and urlsplit(item["url"]).scheme in {"http", "https"}:
                if not isinstance(item.get("revision"), str) or not item["revision"]:
                    self.unfresh_sources.add(sid)
                    self.gap("source-revision", self.entry, f"{sid}: remote source needs consulted revision/date.")
                self.add("remote-source", self.entry, f"{sid}: remote freshness/locators require manual review.", "warning")
            else:
                self.add("source", self.entry, f"{sid}: supply a local path or HTTP(S) URL.")

    def validate_repositories(self):
        raw = self.root.meta.get("repositories")
        if not isinstance(raw, dict) or not raw:
            self.add("repositories", self.entry, "repositories must be a nonempty mapping.")
            return
        for name, value in raw.items():
            planned = isinstance(value, dict) and value.get("planned") is True
            path = value.get("path") if isinstance(value, dict) else value
            if not isinstance(name, str) or not isinstance(path, str) or not path:
                self.add("repository", self.entry, "Repository aliases and paths must be nonempty strings.")
                continue
            target = (self.entry.parent / path).resolve()
            self.repos[name] = target
            if not target.is_dir() and not planned:
                self.gap("repository-missing", self.entry, f"{name}: root does not exist; declare planned only for a proposed repository.")

    def collect_groups(self):
        folder = self.root.meta.get("plan_root")
        if not isinstance(folder, str) or not folder:
            self.add("plan-root", self.entry, "plan_root must name the package folder.")
            return
        package = (self.entry.parent / folder).resolve()
        items = self.root.meta.get("groups")
        if not isinstance(items, list) or not items:
            self.add("groups", self.entry, "groups must be a nonempty list.")
            return
        prefix_width = max(2, len(str(len(items))))
        for order, item in enumerate(items, 1):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("path"), str):
                self.add("group", self.entry, "Each group requires string id and path.")
                continue
            gid = item["id"]
            path = (self.entry.parent / item["path"]).resolve()
            if not GROUP_ID.fullmatch(gid) or gid in self.groups:
                self.add("group-id", path, f"Invalid or duplicate group ID {gid}.")
                continue
            if path.name != "group.md" or path.parent.parent != package or not FEATURE.fullmatch(path.parent.name):
                self.add("group-layout", path, "Use plan_root/<01-feature-name>/group.md with a numerical order prefix.")
            expected_prefix = f"{order:0{prefix_width}d}-"
            if not path.parent.name.startswith(expected_prefix):
                self.add("group-order", path, f"Root group order requires consecutive folder prefix {expected_prefix}.")
            group = self.load(path, "group", GROUP_SECTIONS)
            if not group:
                continue
            self.groups[gid] = group
            heading = re.search(r"^#\s+(.+?)\s*$", unfence(group.body), re.M)
            if heading is None or heading.group(1) != path.parent.name:
                self.add("group-title", path, "Group H1 must exactly match its complete numbered folder name.")
            if group.meta.get("id") != gid:
                self.add("group-id", path, "Root and group IDs disagree.")
            members = self.list_strings(group, "tasks")
            if not members:
                self.add("group-empty", path, "A group needs at least one task.")
            if group.meta.get("integration_owner") not in members:
                self.add("integration-owner", path, "integration_owner must identify a member task.")
            for task_path in sorted((path.parent / "tasks").glob("*.md")):
                task = self.load(task_path, "task", TASK_SECTIONS)
                if not task:
                    continue
                tid = task.meta.get("id")
                if not isinstance(tid, str) or not TASK_ID.fullmatch(tid):
                    self.add("task-id", task_path, "Task ID must be T followed by at least three digits.")
                    continue
                if tid in self.tasks:
                    self.add("duplicate-task", task_path, f"Duplicate task ID {tid}.")
                    continue
                self.tasks[tid] = task
                if not re.fullmatch(re.escape(tid) + r"-[a-z0-9]+(?:-[a-z0-9]+)*\.md", task_path.name):
                    self.add("task-filename", task_path, "Filename must be ID plus a descriptive lowercase slug.")
                if task.meta.get("group") != gid or tid not in members:
                    self.add("membership", task_path, "Task metadata, group folder and member list must agree.")
            actual = {tid for tid, task in self.tasks.items() if task.path.parent.parent == path.parent}
            if set(members) != actual:
                self.add("membership", path, f"Listed tasks differ from files: {sorted(set(members) ^ actual)}.")
        registered = {group.path for group in self.groups.values()}
        for path in sorted(package.rglob("group.md")):
            if path.resolve() not in registered:
                self.add("orphan-group", path, "Group is absent from the root index.")
        registered_tasks = {task.path for task in self.tasks.values()}
        for path in sorted(package.glob("*/tasks/*.md")):
            if path.resolve() not in registered_tasks:
                self.add("orphan-task", path, "Task is not reachable through a registered group.")

    def validate_dependencies(self):
        graph = {}
        for tid, task in self.tasks.items():
            deps = self.list_strings(task, "depends_on")
            graph[tid] = deps
            for dep in deps:
                if dep not in self.tasks:
                    self.add("dependency-missing", task.path, f"Unknown dependency {dep}.")
        visiting, visited = set(), set()

        def visit(tid, chain):
            if tid in visiting:
                self.add("dependency-cycle", self.tasks[tid].path, " → ".join(chain + [tid]))
                return
            if tid in visited or tid not in graph:
                return
            visiting.add(tid)
            for dep in graph[tid]:
                visit(dep, chain + [tid])
            visiting.remove(tid)
            visited.add(tid)

        for tid in graph:
            visit(tid, [])
        for tid, task in self.tasks.items():
            if task.meta.get("status") == "Done":
                for dep in graph[tid]:
                    if dep in self.tasks and self.tasks[dep].meta.get("status") != "Done":
                        self.add("unfinished-dependency", task.path, f"Done task depends on unfinished {dep}.")
        return graph

    def validate_coverage(self):
        for row in self.table(self.root, "Obligation coverage", COVERAGE):
            oid = row["Obligation"]
            if oid in EMPTY or oid in self.coverage:
                self.add("duplicate-obligation", self.entry, f"Empty or duplicate obligation {oid}.")
                continue
            self.coverage[oid] = row
            source = self.sources.get(row["Source"])
            if source is None:
                self.add("coverage-source", self.entry, f"{oid}: unknown source {row['Source']}.")
            locators = link_targets(row["Locator"], self.root.body)
            if not locators:
                self.add("coverage-locator", self.entry, f"{oid}: supply a source Markdown link.")
            elif source:
                for target in locators:
                    local = local_link(self.entry, target)
                    if "resolved" in source and (not local or local[0] != source["resolved"]):
                        self.add("coverage-locator", self.entry, f"{oid}: locator must point into source {row['Source']}.")
                    if "url" in source and target.split("#")[0] != source["url"].split("#")[0]:
                        self.add("coverage-locator", self.entry, f"{oid}: locator does not match its remote source.")
            disposition = row["Disposition"]
            impl, proof = ids(row["Implementing tasks"]), ids(row["Verification tasks"])
            if disposition not in {"Covered", "Gap", "Deferred", "Excluded"}:
                self.add("coverage-disposition", self.entry, f"{oid}: invalid disposition.")
            if disposition == "Covered" and not proof:
                self.add("verification-owner", self.entry, f"{oid}: Covered needs a verification owner.")
            if disposition == "Gap":
                self.gap("coverage-gap", self.entry, f"{oid}: {row['Reason']}")
            if disposition in {"Gap", "Deferred", "Excluded"} and row["Reason"] in EMPTY:
                self.add("coverage-reason", self.entry, f"{oid}: disposition needs a precise reason.")
            if disposition in {"Deferred", "Excluded"} and (impl or proof):
                self.add("inactive-coverage", self.entry, f"{oid}: inactive obligation has active owners.")
            for tid in impl + proof:
                if tid not in self.tasks:
                    self.add("coverage-task", self.entry, f"{oid}: unknown owner {tid}.")
        actual = {}
        for tid, task in self.tasks.items():
            seen = set()
            for row in self.table(task, "Traceability", ["Obligation", "Role"]):
                oid, role = row["Obligation"], row["Role"]
                if oid in seen:
                    self.add("traceability-duplicate", task.path, f"Repeated obligation {oid}.")
                seen.add(oid)
                if oid not in self.coverage or role not in {"implements", "verifies", "both"}:
                    self.add("traceability", task.path, f"Unknown obligation or invalid role: {oid}, {role}.")
                    continue
                for name in (["implements", "verifies"] if role == "both" else [role]):
                    actual.setdefault((oid, name), set()).add(tid)
        for oid, row in self.coverage.items():
            for role, column in [("implements", "Implementing tasks"), ("verifies", "Verification tasks")]:
                if set(ids(row[column])) != actual.get((oid, role), set()):
                    self.add("coverage-reciprocal", self.entry, f"{oid}: {role} owners disagree with task traceability.")
            if row["Source"] in self.unfresh_sources:
                for tid in set(ids(row["Implementing tasks"]) + ids(row["Verification tasks"])):
                    if tid in self.tasks and self.tasks[tid].meta.get("status") == "Done":
                        self.add("done-source-stale", self.tasks[tid].path, f"{oid}: inspect source impact before retaining Done.")
        for group in self.groups.values():
            owner = group.meta.get("integration_owner")
            if isinstance(owner, str) and not any(owner in ids(row["Verification tasks"]) for row in self.coverage.values()):
                self.add("integration-coverage", group.path, "The integration owner has no assigned verification obligation.")

    def validate_surfaces(self, graph):
        changes, creates = [], {}
        for tid, task in self.tasks.items():
            for row in self.table(task, "Change surface", SURFACE):
                repo = self.repos.get(row["Repository"])
                action = row["Action"]
                if repo is None or action not in {"create", "modify", "delete", "inspect"}:
                    self.add("change-surface", task.path, "Unknown repository or action.")
                    continue
                if row["Path"] in EMPTY or any(c in row["Path"] for c in "*?"):
                    self.add("change-path", task.path, "Use concrete change paths, not empty values or globs.")
                    continue
                path = (repo / row["Path"]).resolve()
                if not path.is_relative_to(repo):
                    self.add("change-path", task.path, "Change path escapes its declared repository.")
                    continue
                if row["Responsibility"] in EMPTY:
                    self.add("change-owner", task.path, "Describe responsibility for each change target.")
                changes.append((tid, action, path))
                if action == "create":
                    creates.setdefault(path, set()).add(tid)

        def predecessors(tid):
            seen, todo = set(), list(graph.get(tid, []))
            while todo:
                node = todo.pop()
                if node not in seen:
                    seen.add(node)
                    todo.extend(graph.get(node, []))
            return seen

        for tid, action, path in changes:
            if action == "create" or path.exists():
                continue
            if not (creates.get(path, set()) & predecessors(tid)):
                # A completed deletion deliberately leaves no file; its evidence is checked separately.
                if action == "delete" and self.tasks[tid].meta.get("status") == "Done":
                    continue
                self.add("change-target-missing", self.tasks[tid].path, f"{action} target absent and no dependency creates it: {path}")
        writers = {}
        for tid, action, path in changes:
            if action != "inspect":
                writers.setdefault(path, set()).add(tid)
        for path, owners in writers.items():
            ordered = sorted(owners)
            for i, left in enumerate(ordered):
                for right in ordered[i + 1:]:
                    if left not in predecessors(right) and right not in predecessors(left):
                        self.add("unordered-shared-write", self.tasks[right].path, f"{left} and {right} both write {path}; establish ordering or reconcile ownership before parallel work.", "warning")

    def validate_evidence(self, task):
        checks = {}
        for row in self.table(task, "Validation", VALIDATION):
            cid = row["Check"]
            if cid in checks or cid in EMPTY:
                self.add("check-id", task.path, f"Empty or duplicate check ID {cid}.")
            checks[cid] = row
            if row["Required"] not in {"yes", "no"} or any(row[key] in EMPTY for key in VALIDATION[1:4]):
                self.add("validation", task.path, f"{cid}: provide method, workdir, expectation and yes/no Required.")
        required_reviews = ["self-review", "independent-review"]
        if task.meta.get("visual_review") == "required":
            required_reviews.append("visual-review")
        for cid in required_reviews:
            if checks.get(cid, {}).get("Required") != "yes":
                self.add("required-review", task.path, f"Missing required {cid} check.")
        evidence = {}
        for row in self.table(task, "Evidence", EVIDENCE):
            cid, result = row["Check"], row["Result"]
            if cid in evidence or cid not in checks:
                self.add("evidence-check", task.path, f"Duplicate or unknown evidence check {cid}.")
            evidence[cid] = row
            if result not in {"Not run", "Passed", "Failed", "Blocked", "Stale"}:
                self.add("evidence-result", task.path, f"{cid}: invalid result {result}.")
            if result == "Passed":
                links = link_targets(row["Artifact"], task.body)
                local_artifacts = [local[0] for link in links if (local := local_link(task.path, link))]
                if not any(path.is_file() and path.stat().st_size > 0 for path in local_artifacts):
                    self.add("evidence-artifact", task.path, f"{cid}: Passed requires a nonempty local evidence file.")
                if row["Revision"] in EMPTY or row["Environment"] in EMPTY:
                    self.add("evidence-context", task.path, f"{cid}: Passed needs revision and environment.")
                if cid in {"self-review", "independent-review"} and row["Reviewer"] in EMPTY:
                    self.add("reviewer", task.path, f"{cid}: identify the reviewer.")
        if set(checks) != set(evidence):
            self.add("evidence-coverage", task.path, "Every validation check needs one current evidence row.")
        first, second = evidence.get("self-review", {}), evidence.get("independent-review", {})
        if first.get("Result") == second.get("Result") == "Passed" and first.get("Reviewer") == second.get("Reviewer"):
            self.add("review-independence", task.path, "Self and independent review identify the same reviewer.")
        if task.meta.get("status") == "Done":
            if task.meta.get("readiness") != "Ready":
                self.add("done-readiness", task.path, "Done requires Ready instructions.")
            for cid, row in checks.items():
                if row["Required"] == "yes" and evidence.get(cid, {}).get("Result") != "Passed":
                    self.add("done-evidence", task.path, f"Required check {cid} has not passed.")
            revisions = {row["Revision"] for cid, row in evidence.items() if checks.get(cid, {}).get("Required") == "yes" and row["Result"] == "Passed"}
            if len(revisions) > 1:
                self.add("evidence-revision", task.path, "Required Done evidence must identify the same assessed revision/fingerprint set.")

    def validate_links(self):
        for doc in self.docs.values():
            for target in link_targets(unfence(doc.body)):
                if target.startswith("MISSING-REFERENCE:"):
                    self.add("link-definition", doc.path, target)
                    continue
                try:
                    local = local_link(doc.path, target)
                except ValueError as exc:
                    self.add("link", doc.path, str(exc))
                    continue
                if local is None:
                    continue
                path, fragment = local
                if not path.exists():
                    self.add("link-missing", doc.path, f"Missing target: {target}")
                elif fragment and path.suffix.lower() in {".md", ".html", ".htm"}:
                    try:
                        if fragment not in anchors(path.read_text(encoding="utf-8")):
                            self.add("link-anchor", doc.path, f"Unknown anchor: {target}")
                    except (OSError, UnicodeError) as exc:
                        self.add("link-read", doc.path, str(exc))
        # Metadata indexes must also be navigable through document links.
        root_links = {local[0] for target in link_targets(unfence(self.root.body)) if (local := local_link(self.entry, target))}
        for group in self.groups.values():
            if group.path not in root_links:
                self.add("navigation", self.entry, f"Missing Markdown link to {group.path}.")
            group_links = {local[0] for target in link_targets(unfence(group.body)) if (local := local_link(group.path, target))}
            for task in self.tasks.values():
                if task.meta.get("group") == group.meta.get("id") and task.path not in group_links:
                    self.add("navigation", group.path, f"Missing Markdown link to {task.path}.")

    def validate_inventory(self):
        if not self.inventory:
            self.add("inventory-not-supplied", self.entry, "Independent obligation inventory not compared; semantic completeness requires source review.", "warning")
            return
        data = json.loads(Path(self.inventory).read_text(encoding="utf-8"))
        items = data.get("obligations") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise ValueError("Inventory needs an obligations list.")
        seen = set()
        for item in items:
            if not isinstance(item, dict) or not all(isinstance(item.get(key), str) for key in ["id", "source", "disposition", "reason"]):
                raise ValueError("Each inventory entry needs string id, source, disposition and reason.")
            oid = item["id"]
            if oid in seen:
                self.add("inventory-duplicate", self.entry, f"Duplicate inventory obligation {oid}.")
            seen.add(oid)
            row = self.coverage.get(oid)
            if not row:
                self.add("inventory-missing", self.entry, f"Missing source obligation {oid}.")
                continue
            if row["Source"] != item["source"] or row["Disposition"] != item["disposition"]:
                self.add("inventory-mismatch", self.entry, f"{oid}: source/disposition differs from inventory.")
            if item["disposition"] in {"Deferred", "Excluded"} and row["Reason"] != item["reason"]:
                self.add("inventory-reason", self.entry, f"{oid}: inactive reason differs from inventory.")
        for oid in self.coverage.keys() - seen:
            self.add("inventory-extra", self.entry, f"{oid}: plan obligation absent from independent inventory.")

    def run(self):
        self.root = self.load(self.entry, "plan", ROOT_SECTIONS)
        if not self.root:
            return self.report()
        if type(self.root.meta.get("schema_version")) is not int or self.root.meta.get("schema_version") != 1:
            self.unsupported = True
            self.add("schema-version", self.entry, "Supported schema_version is 1.")
            return self.report()
        self.enum(self.root, "readiness", READINESS)
        self.validate_sources()
        self.validate_repositories()
        self.collect_groups()
        graph = self.validate_dependencies()
        self.validate_coverage()
        self.validate_surfaces(graph)
        for task in self.tasks.values():
            for key, allowed in [("readiness", READINESS), ("status", STATUSES), ("risk", {"low", "medium", "high"}), ("test_strategy", {"test-first", "alongside", "checks-only"}), ("visual_review", {"required", "not-applicable"})]:
                self.enum(task, key, allowed)
            if task.meta.get("readiness") != "Ready":
                self.gap("task-readiness", task.path, "Task instructions are not Ready.")
            self.validate_evidence(task)
        retired = set()
        for row in self.table(self.root, "Retired tasks", ["Task", "Replaced by", "Reason"], required=False):
            if row["Task"] in retired or not TASK_ID.fullmatch(row["Task"]) or row["Task"] in self.tasks or row["Reason"] in EMPTY:
                self.add("retired-task", self.entry, "Retired IDs must be valid, unique, inactive, and have a reason.")
            retired.add(row["Task"])
            for replacement in ids(row["Replaced by"]):
                if replacement not in self.tasks:
                    self.add("retired-replacement", self.entry, f"Unknown replacement {replacement}.")
        self.validate_links()
        self.validate_inventory()
        if self.root.meta.get("readiness") == "Ready" and any(f["severity"] == "gap" for f in self.findings):
            self.add("ready-with-gaps", self.entry, "Root claims Ready while source/task/coverage gaps remain.")
        return self.report()

    def report(self):
        counts = {key: sum(f["severity"] == key for f in self.findings) for key in ["error", "gap", "warning"]}
        return {"entry": str(self.entry), "groups": len(self.groups), "tasks": len(self.tasks), "obligations": len(self.coverage), "counts": counts, "findings": self.findings, "limitations": "Structural checks do not establish semantic completeness, actual passing software, reviewer independence, or visual quality."}


if yaml:
    class UniqueLoader(yaml.SafeLoader):
        pass

    def unique_mapping(loader, node, deep=False):
        pairs = loader.construct_pairs(node, deep=deep)
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate YAML key: {key}")
            result[key] = value
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true", help="Fail on unresolved gaps as well as structural errors.")
    args = parser.parse_args(argv)
    code = 2
    try:
        if yaml is None:
            raise RuntimeError("PyYAML is unavailable in this Python runtime; no checks ran.")
        checker = Checker(args.entry, args.inventory)
        report = checker.run()
        code = 2 if checker.unsupported else int(report["counts"]["error"] > 0 or (args.strict and report["counts"]["gap"] > 0))
    except (OSError, UnicodeError, ValueError, RuntimeError, TypeError, RecursionError) as exc:
        report = {"entry": str(args.entry), "counts": {"error": 1, "gap": 0, "warning": 0}, "findings": [{"severity": "error", "code": "input", "path": str(args.entry), "message": str(exc)}]}
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for finding in report["findings"]:
            print(f"{finding['severity'].upper()} {finding['code']} {finding['path']}: {finding['message']}")
        counts = report["counts"]
        print(f"{counts['error']} errors; {counts['gap']} gaps; {counts['warning']} warnings.")
        print(report.get("limitations", "Input could not be fully checked."))
    return code


if __name__ == "__main__":
    sys.exit(main())
