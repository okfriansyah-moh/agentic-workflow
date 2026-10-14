"""Synthetic package data for checker tests; not evidence of passing application work."""
from pathlib import Path
import hashlib
import yaml


def document(path, meta, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\n" + body, encoding="utf-8")


def metadata(path, **changes):
    text = path.read_text()
    _, header, body = text.split("---", 2)
    value = yaml.safe_load(header)
    value.update(changes)
    document(path, value, body.lstrip())


def package(base):
    """Create one structurally complete CLI task with source and reciprocal coverage."""
    base = Path(base)
    docs = base / "docs"
    source = docs / "spec.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# CLI requirements\n\n## Invalid input\n\nREQ-01: A negative count exits 2 and prints correction to stderr.\n", encoding="utf-8")
    src = base / "src/cli.py"
    src.parent.mkdir(parents=True)
    src.write_text("# Existing CLI parser fixture\n", encoding="utf-8")
    entry = docs / "06-PLAN.md"
    group = docs / "plan/01-count-validation/group.md"
    task = group.parent / "tasks/T001-count-validation.md"
    document(entry, {"kind": "plan", "schema_version": 1, "readiness": "Ready", "plan_root": "plan", "repositories": {"app": ".."}, "sources": [{"id": "SPEC", "path": "spec.md", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}], "groups": [{"id": "G01", "path": "plan/01-count-validation/group.md"}]}, """# Count validation plan

## Goal and scope
Reject negative counts in the existing CLI; product behavior comes from the source.

## Shared execution rules
Read the source, preserve unrelated flags, and retain stderr/exit evidence. No UI exists.

## Feature groups
[Count validation](plan/01-count-validation/group.md) contains one full feature task.

## Obligation coverage
| Obligation | Source | Locator | Disposition | Implementing tasks | Verification tasks | Reason |
|---|---|---|---|---|---|---|
| REQ-01 | SPEC | [Invalid input](spec.md#invalid-input) | Covered | T001 | T001 | — |

## Release verification
T001 owns the CLI subprocess acceptance for REQ-01. No deployment is included.
""")
    document(group, {"kind": "group", "id": "G01", "tasks": ["T001"], "integration_owner": "T001"}, """# 01-count-validation

## Outcome and scope
Users receive actionable feedback for an invalid count.

## Shared context
The existing argument parser owns conversion and error feedback.

## Task list
[T001 count validation](tasks/T001-count-validation.md)

## Dependencies
The existing parser and Python runtime are available; no task dependency.

## Integrated acceptance
T001 invokes the CLI as a subprocess, asserting exit 2 and stderr correction.
""")
    document(task, {"kind": "task", "id": "T001", "group": "G01", "depends_on": [], "readiness": "Ready", "status": "Not started", "risk": "low", "test_strategy": "test-first", "visual_review": "not-applicable"}, """# T001 — Validate count

[Group](../group.md) · [Plan](../../../06-PLAN.md)

## Purpose and scope
Reject negative counts; preserve other CLI behavior. Low risk: isolated parser rule.

## Traceability
| Obligation | Role |
|---|---|
| REQ-01 | both |

## Prerequisites
The existing parser, Python, and unittest are available in the fixture.

## Change surface
| Repository | Action | Path | Responsibility |
|---|---|---|---|
| app | modify | src/cli.py | Count validation at the CLI boundary |
| app | create | tests/test_count.py | Rule and subprocess regression checks |

## Knowledge
Read [invalid input](../../../spec.md#invalid-input) for exact feedback and exit semantics.

## Implementation
Write a failing rule test, reject negative integers in the parser, and keep other argument behavior intact.

## Development guidance
Preserve the existing parser's stderr handling; avoid unrelated flags or dependencies.

## Acceptance
Given count -1, invoking the CLI exits 2 with a correction on stderr. Count 0 remains valid.

## Tests
Test-first is appropriate for this reproducible rule. Add a unit boundary case and an actual subprocess case. Use separate temporary output directories; no shared state.

## Validation
| Check | Method or command | Working directory | Expected result | Required |
|---|---|---|---|---|
| count-rule | python3 -m unittest discover -s tests | repository root | Negative rejected; zero accepted; real CLI exits 2 | yes |
| self-review | Inspect changes and source expectations | repository root | Scope and acceptance agree | yes |
| independent-review | Fresh reviewer examines baseline, change and evidence | repository root | Required findings resolved | yes |

## Review and evidence
Review parser boundary, unchanged flags and stderr. Visual review is inapplicable to a CLI with no visual interface. Correct findings and repeat affected checks before fresh review.

## Evidence
| Check | Result | Artifact | Revision | Environment | Reviewer |
|---|---|---|---|---|---|
| count-rule | Not run | — | — | — | — |
| self-review | Not run | — | — | — | — |
| independent-review | Not run | — | — | — | — |

## Completion and handoff
Complete only after the required behavior and both reviews pass. Next action is to add the failing count test. This synthetic checker fixture claims no application execution.
""")
    return {"base": base, "entry": entry, "group": group, "task": task, "source": source, "src": src}


def second_task(paths):
    first = paths["task"]
    task = first.with_name("T002-count-integration.md")
    task.write_text(first.read_text().replace("T001", "T002").replace("| REQ-01 | both |", "| REQ-01 | verifies |").replace("| app | modify | src/cli.py |", "| app | inspect | src/cli.py |"))
    metadata(task, depends_on=["T001"])
    metadata(paths["group"], tasks=["T001", "T002"], integration_owner="T002")
    text = paths["group"].read_text().replace("## Dependencies", "[T002 integration](tasks/T002-count-integration.md)\n\n## Dependencies")
    paths["group"].write_text(text)
    paths["entry"].write_text(paths["entry"].read_text().replace("| T001 | T001 |", "| T001 | T001, T002 |"))
    return task
