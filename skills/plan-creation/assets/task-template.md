---
kind: task
id: T001
group: G01
depends_on: []
readiness: Draft
status: Not started
risk: medium
test_strategy: test-first
visual_review: not-applicable
---

# T001 — {{task_title}}

[Feature group](../group.md) · [Overall plan](../../../06-PLAN.md)

## Purpose and scope

{{Observable result, ownership, scope boundaries and concrete risk reasoning.}}

## Traceability

| Obligation | Role |
|---|---|
| {{source_obligation_id}} | both |

## Prerequisites

{{Exact outputs from dependency tasks, established interfaces, environment needs and unresolved blockers.}}

## Change surface

| Repository | Action | Path | Responsibility |
|---|---|---|---|
| app | create | {{repository_relative_path}} | {{owner_and_intended_change}} |

## Knowledge

{{Precise source links/case rows and what to read them for; critical facts, contracts, design states and pitfalls.}}

## Implementation

{{Ordered checkable changes, relevant interfaces, states, enforcement, persistence, failure/recovery and compatibility.}}

## Development guidance

{{Applicable shared rules and their task-specific consequences; authored/generated ownership and guardrails.}}

## Acceptance

{{Named criteria with fixture/input/action/expected outcome, meaningful boundaries, negative assertions and failure signals.}}

## Tests

{{Test strategy and reason, assigned source cases/rows, unit/component/real-boundary coverage, fixtures/reset, independent expected values, planned test paths and proof limits.}}

## Validation

| Check | Method or command | Working directory | Expected result | Required |
|---|---|---|---|---|
| behavior | {{exact_command_or_observation}} | {{workdir}} | {{independent_expected_result}} | yes |
| self-review | Compare changes to source and acceptance | {{workdir}} | All task criteria addressed; defects corrected | yes |
| independent-review | Fresh reviewer checks source compliance, code and evidence | {{workdir}} | Required findings resolved for the current revision | yes |

## Review and evidence

{{Reviewers, source/baseline/change evidence, concrete review focus and risk-based scrutiny. When UI is affected set visual_review: required, add required visual-review check/evidence row, and specify design references, state/actor/fixture/theme/viewport, captures, comparison and interaction/accessibility checks. Otherwise explain why visual review is inapplicable.}}

Implement → test → self-review → independent review → correct → rerun affected checks → reassess. Preserve unresolved findings and next action when unfinished. Source changes need an authorized decision.

## Evidence

| Check | Result | Artifact | Revision | Environment | Reviewer |
|---|---|---|---|---|---|
| behavior | Not run | — | — | — | — |
| self-review | Not run | — | — | — | — |
| independent-review | Not run | — | — | — | — |

## Completion and handoff

{{Task exit criteria, feature-integration obligations, changed paths, evidence references and actual next action. Do not claim task/group completion from unexecuted checks.}}
