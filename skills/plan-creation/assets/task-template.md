---
kind: task
id: T001
group: G01
depends_on: []
readiness: Draft
status: Not started
risk: medium
test_strategy: alongside
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

{{Ordered checkable changes and relevant interfaces. Complete the journey through success, return destination and retained context. For UI, link exact references/tokens/assets/states and agreed comparison sizes; compare a representative state before propagating shared styling. Include relevant failures and compatibility.}}

## Development guidance

{{Applicable shared rules and task-specific consequences. Protect workflow code, bundled instructions, gate policy and unplanned Python files during product work. Harness maintenance requires its own requested scope.}}

## Acceptance

{{Named criteria with fixture/input/action/expected outcome, meaningful boundaries, negative assertions and failure signals.}}

## Tests

{{Select the agreed strategy explicitly; alongside is a placeholder, not mandatory TDD. Specify only meaningful affected checks, source cases, fixtures, expected values and proof limits. Explicit no-test limits prohibit new/executed tests and substitute browser trials; leave excluded proof pending.}}

## Validation

| Check | Method or command | Working directory | Expected result | Required |
|---|---|---|---|---|
| behavior | {{exact_command_or_observation}} | {{workdir}} | {{independent_expected_result}} | yes |
| self-review | Compare changes to source and acceptance | {{workdir}} | All task criteria addressed; defects corrected | yes |
| independent-review | Reference the one final selection review covering this task | {{workdir}} | Combined selection findings resolved for the current revision | yes |

## Review and evidence

{{Reviewers, source/baseline/change evidence, concrete review focus and risk-based scrutiny. When UI is affected set visual_review: required, add required visual-review check/evidence row, and specify design references, state/actor/fixture/theme/viewport, captures, comparison and interaction/accessibility checks. Otherwise explain why visual review is inapplicable.}}

Implement → run agreed affected checks → inspect the diff → include in one combined selection review → correct findings → rerun affected checks. Preserve unresolved findings and next action when unfinished. Source changes need an authorized decision.

## Evidence

| Check | Result | Artifact | Revision | Environment | Reviewer |
|---|---|---|---|---|---|
| behavior | Not run | — | — | — | — |
| self-review | Not run | — | — | — | — |
| independent-review | Not run | — | — | — | — |

## Completion and handoff

{{Task exit criteria, feature-integration obligations, changed paths, evidence references and actual next action. Do not claim task/group completion from unexecuted checks.}}
