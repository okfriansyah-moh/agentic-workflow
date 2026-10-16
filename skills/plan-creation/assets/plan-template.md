---
kind: plan
schema_version: 1
numbering: sequential
readiness: Draft
plan_root: plan
repositories:
  app: ..
sources:
  - id: SPEC
    path: "{{source_path}}"
    sha256: "{{source_sha256}}"
groups:
  - id: G01
    path: "plan/{{order_prefix}}-{{feature}}/group.md"
---

# {{product}} implementation plan

## Goal and scope

{{Audience, outcome, included boundaries, authoritative decisions, assumptions and material gaps.}}

## Shared execution rules

{{Source loading, accepted constraints, project conventions, review/evidence rules, repository command map with workdirs and prerequisites.}}

## Feature groups

| Group | Outcome | Prerequisites | Detail |
|---|---|---|---|
| G01 | {{observable_outcome}} | {{prerequisites}} | [{{order_prefix}}-{{feature}}](plan/{{order_prefix}}-{{feature}}/group.md) |

{{Sequential stage order derived from task dependencies, shared feature labels across split stages, and safe parallel opportunities with write/resource conflicts.}}

## Obligation coverage

| Obligation | Source | Locator | Disposition | Implementing tasks | Verification tasks | Reason |
|---|---|---|---|---|---|---|
| {{source_obligation_id}} | SPEC | [Source]({{source_path}}#{{anchor}}) | Covered | T001 | T001 | — |

## Release verification

{{Cross-feature/release obligations, verifying tasks, expected evidence and release limits. Keep future results Not run.}}
