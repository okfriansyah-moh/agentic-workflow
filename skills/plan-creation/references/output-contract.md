# Planning package contract

## Layout and authority

The root is `docs/06-PLAN.md` by default. Its `plan_root` resolves relative to that file; each immediate child folder combines a zero-padded numerical order and a lowercase hyphenated feature name, such as `01-catalog-discovery`, with `group.md` and `tasks/T001-catalog-backend.md`. Start numbering at `01-`, use consecutive numbers, and widen all prefixes consistently if the package needs more than 99 groups. Keep stable group IDs inside metadata; the numerical prefix is display order, not group identity. The group H1 must exactly match the complete folder name, for example `# 01-catalog-discovery`. Supporting capabilities can have meaningful names such as `application-foundation`. Group related technical tasks under their feature; a feature can consist of one full-stack task.

The root owns source/obligation registers, shared rules, repository paths, feature navigation, cross-feature ordering, and release criteria. A group owns common feature knowledge, its task index, and integrated completion. A task owns its instructions, current status, evidence, and handoff. Indexes link to task records; they do not duplicate task status or evidence. Use Markdown links for navigation. Author only real content; leave future evidence folders uncreated.

All paths in metadata are relative to the containing document unless explicitly absolute. Repository roots in the root header resolve from the root document. Change-surface paths resolve from their named repository. Markdown links resolve from their own file. A user-specified root or plan folder changes paths, not the meaning of fields.

## Root document

Required YAML metadata:

```yaml
kind: plan
schema_version: 1
readiness: Draft
plan_root: plan
repositories:
  app: ..
sources:
  - id: PRD
    path: 02-PRD.md
    sha256: "source-byte-digest"
groups:
  - id: G01
    path: plan/01-catalog-discovery/group.md
```

Use actual SHA-256 digests of local source bytes. Record each governing local source that materially affects the plan, including relevant design tokens, component contracts and state references. Source IDs are package-local handles, distinct from requirement IDs. A remote source may use `url` instead of `path` and must carry a `revision` identifying the consulted version/date; add a digest or accessible snapshot when available. The checker does not fetch remote sources. Missing source access remains a disclosed gap, not an invented hash. A draft may use `sha256: pending` for an unavailable local source.

Repositories may point to existing roots or explicitly proposed roots. For a proposed root, use `{path: ../new-service, planned: true}`. A simple path means an existing root. Never create the repository during planning. Even with planned roots, `modify`, `delete`, and `inspect` targets need existing files or a dependency that creates them.

Required sections:

- `## Goal and scope`: audience, included outcomes, boundaries, source authority, assumptions/open decisions and their impact.
- `## Shared execution rules`: instructions inherited by all tasks; accepted constraints, development conventions, source loading, review defaults, safe handling of evidence, and selected repository tooling. Give command/workdir/prerequisite/expected-result entries and distinguish actual commands from contracts a foundation task will implement.
- `## Feature groups`: links, feature outcomes, prerequisites, dependency graph or equivalent ordering, safe parallel opportunities and conflict conditions. Do not invent schedules or estimates.
- `## Obligation coverage`: the register below, derived from an independent source inventory.
- `## Release verification`: cross-feature acceptance, compatibility/migration/recovery/operations obligations where applicable, verification owners, and evidence required for eventual release. No implicit deployment authorization.

Use this exact coverage table header for deterministic checking:

```markdown
| Obligation | Source | Locator | Disposition | Implementing tasks | Verification tasks | Reason |
|---|---|---|---|---|---|---|
```

One row per independently inventoried obligation or separately assigned case row. Preserve source IDs; qualify collisions with source IDs. If a source has no IDs, assign stable plan-local IDs and link exact source text without pretending the IDs came from the source. `Locator` is an explicit Markdown link into the declared source. Lists of task IDs are comma-separated; use `—` for empty values. Escape literal table pipes as `\|`.

`Disposition` is `Covered`, `Gap`, `Deferred`, or `Excluded`. Covered requires at least one verification owner and sufficient assertions; an already implemented behavior may need verification without new implementation. Split a compound case into row/obligation references when different tasks own its proof. Partial work stays Gap with its contributing tasks and a precise missing outcome in Reason. Deferred/Excluded require source-backed reasons and no active owners; they cannot hide included requirements. Draft gaps may remain; Ready requires all included obligations covered and all active task instructions Ready.

Optional `## Retired tasks` uses `| Task | Replaced by | Reason |`. Keep retired IDs here, without active task definitions or dependencies on them. A replacement is an existing active task ID or `—`. IDs are never recycled.

## Feature group

List root group paths and navigation in numerical folder order. Number groups by a feasible order of first starts derived from the task dependency graph, using a documented stable tie-break for equally eligible work. A group may resume after another group supplies a prerequisite; explain these returns instead of suggesting that every task in folder01 must finish before folder02 can begin. Preserve existing IDs when paths or display order change.

Required header: `kind: group`, `id: G01`, `tasks: [T001, T002]`, `integration_owner: T002`. IDs are stable; ordering in the list is display order, while dependencies govern execution. The integration owner is a member task whose verification establishes the feature outcome. This can be the sole task of a small feature, not necessarily a separate QA task.

Required sections: `## Outcome and scope`, `## Shared context`, `## Task list`, `## Dependencies`, `## Integrated acceptance`.

Explain the actors/outcome, adopted interfaces and visual references, shared pitfalls and prerequisites, links to every member task, internal dependency order and write/resource conflicts. Integrated acceptance names actual source cases/obligations and the real boundary required. Give applicable failure/recovery, accessibility, security and operational checks. Backend/CLI groups explain their observable non-UI result; omit invented visual work. Feature completion requires every required task Done plus integrated acceptance evidence from the named owner. A group summary is not separate authority to bypass task evidence.

## Task metadata and sections

Required header:

```yaml
kind: task
id: T001
group: G01
depends_on: []
readiness: Draft
status: Not started
risk: medium
test_strategy: test-first
visual_review: not-applicable
```

IDs use `T` plus at least three digits and `G` plus at least two digits. Preserve older IDs when maintaining a legacy format; conversion must explicitly map them without losing identity. Filename starts with the task ID followed by a descriptive lowercase slug. Task group matches its containing feature; each task appears once in its group's list. Dependencies are active task IDs anywhere in the package; explain external prerequisites in prose rather than inventing task IDs.

Allowed values:

| Field | Values and meaning |
|---|---|
| readiness | `Draft`, `Ready`, `Needs update`; describes settled instructions, not completed dependencies |
| status | `Not started`, `In progress`, `In review`, `Blocked`, `Done`; describes actual execution |
| risk | `low`, `medium`, `high`; explain concrete impact in the task |
| test_strategy | `test-first`, `alongside`, `checks-only`; explain selection, with checks-only for work without executable behavior |
| visual_review | `required`, `not-applicable`; explain applicability in Review and evidence |

Use these sections in every task, marking irrelevant conditional content with a concise reason rather than fabricated work:

1. `## Purpose and scope`: goal, owned result, exclusions, risk reasoning.
2. `## Traceability`: table `| Obligation | Role |`, one row per obligation, Role `implements`, `verifies`, or `both`. It must agree with the root coverage owners. Include direct source links in the knowledge/acceptance text.
3. `## Prerequisites`: dependencies' concrete outputs, runtime/tool/access prerequisites and blockers; normal unfinished dependencies differ from unresolved requirements.
4. `## Change surface`: table `| Repository | Action | Path | Responsibility |`; Action `create`, `modify`, `delete`, or `inspect`. Paths are exact files/directories within declared repository roots. Avoid glob guesses. A target created by a dependency can be modified later; identify that producer. Implementation may reconcile a moved path by recording the actual owner without silently changing scope.
5. `## Knowledge`: exact source sections/cases and what to read them for, source-backed rules, contract input/results, design state IDs, difficult algorithms/pitfalls and reasons. Agent reads root shared rules → group context → task → explicitly selected source sections, expanding only when a dependency requires it.
6. `## Implementation`: ordered, checkable changes; relevant types/signatures/schema references; state, ordering, side effects, failure/recovery, compatibility and migration constraints. Use targeted pseudocode/examples for fragile logic; avoid prewriting the entire solution.
7. `## Development guidance`: relevant conventions, generated versus authored ownership, shared primitives, security/permission and scope guardrails; link shared guidance once and state task-specific consequences.
8. `## Acceptance`: named criteria with concrete initial state/input/action/expected results, failure signals and prohibited side effects. Include role/state/boundary variations that sources require. Case IDs alone are insufficient.
9. `## Tests`: assigned ATDD assertions/rows, fixtures and cleanup, test levels, test order, independent expected results, real/controlled boundaries, test locations and what they cannot establish. Explain test strategy. Keep acceptance specification and execution evidence distinct.
10. `## Validation`: table described below with exact commands or observation procedures, working directories, prerequisites and success signals. Planned commands must name their producing dependency.
11. `## Review and evidence`: implementer and independent review scope, source compliance, code quality and risk-specific scrutiny; UI context/reference/capture/comparison contract when required; findings and refinement procedure.
12. `## Evidence`: initially the table below with unexecuted results. Runtime records are added only from supplied or observed evidence, with current revision/environment and clear proof boundaries.
13. `## Completion and handoff`: checklist of task acceptance/review, remaining feature integration obligations, changed files, evidence, blockers and the exact next action for resumption. Preserve legacy evidence on updates.

Validation table:

```markdown
| Check | Method or command | Working directory | Expected result | Required |
|---|---|---|---|---|
```

Check IDs are task-local. Every task includes `self-review` and `independent-review`, both Required `yes`. Self-review is the implementation diff check; independent-review references the one final selection review covering all requested task IDs, not a separate task ceremony. Other checks name assigned behavior (for example `unit-rules`, `real-query`, `visual-states`); Required is `yes` or `no`. Reserve `visual-review` as a required check when metadata says visual review required. Procedures can be human/agent observations rather than fabricated shell commands. Existing project commands are used as found; future commands are explicitly dependent contracts.

Evidence table:

```markdown
| Check | Result | Artifact | Revision | Environment | Reviewer |
|---|---|---|---|---|---|
```

One current row per validation check. Results: `Not run`, `Passed`, `Failed`, `Blocked`, `Stale`. Future rows use `Not run` with `—` in evidence fields. Passed requires an explicit link to a nonempty local evidence file, implementation revision/content fingerprint, and actual environment. Review rows also identify reviewers; independent and self-review identities must differ. Tool/agent IDs or named humans are useful, not untraceable labels alone. Keep previous run reports linked in prose; the table reflects the current verdict. Authenticity and sufficiency need review; the checker only validates recorded structure and reachable artifacts.

Done requires Ready instructions and Passed evidence for every required check, including both reviews and applicable visual review. In-review/blocked records identify next action and unresolved findings. A stopped execution budget preserves progress; it is not evidence of an external blocker. Neither missing tools nor self-review can substitute for required independent review.

## Completion boundary

Planning completion means a coherent package, meaningful coverage or explicit gaps, valid references/dependencies, and an honest readiness verdict. It never means the application passed. The authoring response names the entry point, group/task coverage, gaps and actual checks; temporary inventories and reports stay outside project deliverables. Supporting-source constraints and invocation authorization continue to govern future executors.
