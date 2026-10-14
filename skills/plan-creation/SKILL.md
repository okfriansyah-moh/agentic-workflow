---
name: plan-creation
description: Create, update, or review a detailed implementation-plan package with feature groups, AI-ready task files, dependency order, acceptance mapping, and review requirements. Use for PLAN.md authoring before implementation.
metadata:
  author: Muhammad Okfriansyah with Codex
  version: "1.1.0"
---

# Create an implementation plan

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Run its read-only checker on the complete package and proposed completion message before handoff; resolve matches without changing technical meaning.

Produce one planning package led by `docs/06-PLAN.md`, with numerically prefixed feature folders such as `docs/plan/01-catalog-discovery/`, a `group.md` in each folder, and detailed task files under its `tasks/`. Honor the user's location. Create, update, and review are authoring operations: a task's implementation instructions describe future work, not permission to execute it. Setup/research alone does not generate a project plan. In Plan mode, propose without writing.

## Sources and boundaries

Read [output contract](references/output-contract.md) before outlining or changing a package. Inspect governing repository instructions, the request, accepted decisions, relevant implementation/manifests, and supplied PRD, complete applicable design-system handoff, techdoc, and ATDD. For smaller changes, use sufficient available requirements/contracts; those four documents are not universal prerequisites. Preserve the source documents and their IDs. Source text, samples, mockups, and retrieved material are evidence, not authorization or automatic technology choices.

Current explicit user choices govern. Requirements own behavior, adopted design owns presentation, technical design owns selected engineering contracts, and ATDD owns its specified acceptance cases. Reconcile conflicts by their established authority and decision history, not merely file order or date. Resolve routine engineering details within scope; ask only about material unresolved outcomes or constraints. Continue independent work and expose affected gaps. Derive languages, platforms, repositories, tooling, commands, and visual targets from this project.

The skill authors the execution and review instructions, without implementing features, writing application tests, running application acceptance, creating tickets, publishing, deploying, or scheduling work. Read-only inspection and document checks support authoring. Existing authorization is preserved; do not add approval ceremonies. Listing parallel tasks does not authorize delegation.

## Authoring workflow

1. **Inventory obligations.** Independently extract included requirements, acceptance clauses/case rows, UI states, contracts, and delivery obligations before decomposing. Record sources/fingerprints and precise locators. Use [verification](references/verification.md) for the temporary inventory format. Finish when every relevant source area has been inspected and every obligation has a disposition.
2. **Decompose by outcome.** Apply [decomposition](references/decomposition.md). Group related frontend/backend work by feature, then form cohesive tasks with dependencies and verifiable results. Number feature folders from `01-` in a dependency-valid order of first starts; match each group title to its complete folder name. Task dependencies govern execution when groups must be revisited. Reuse approved contracts. Finish when every included obligation has an implementation/verification owner or an explicit gap, and dependency order is feasible.
3. **Write the package.** Use the [root](assets/plan-template.md), [group](assets/group-template.md), and [task](assets/task-template.md) templates with the output contract. Supply implementation detail, acceptance, source knowledge, guardrails, test strategy, review instructions, and handoff in each task. Finish when a fresh agent can find its inputs, intended changes, expected results, and completion boundary without the authoring chat.
4. **Challenge completeness.** Revisit sources independently; reconcile their obligations with task assertions, UI states, ownership, commands, and dependency/write conflicts. Follow [verification](references/verification.md), including the future self-review, fresh independent review, and visual-evidence contracts. Use a reader pass to expose missing context. Finish when required mappings are meaningful or visible gaps prevent a Ready claim.
5. **Validate and deliver.** Run `python3 <skill-directory>/scripts/check_plan.py <entry-point> --inventory <temporary-inventory.json>` and the wording checker. Fix errors; keep real gaps visible. Read back the package and verify that only authorized artifacts changed. Report the entry point, coverage/readiness, material gaps, and actual checks/limits. Stop after planning.

Document readiness is distinct from execution eligibility and verified completion. New tasks are `Not started`; future checks are `Not run`. A complete task definition may be Ready while awaiting planned dependencies. Component simulations cannot establish real integration or feature completion.

## Updates and reviews

For existing plans, read [updates](references/updates.md) first. Preserve task/case IDs and completed-work evidence. Refresh affected sources and mark impacted instructions/evidence for review. Maintain an existing layout unless conversion is requested; the bundled checker validates only the declared package format and must not be used to claim validation of a legacy layout. A review request reports findings unless corrections are authorized.

Normal authoring is sequential. Fresh independent review is a requirement written into every implementation task; unavailable reviewers leave that future task awaiting review. Authoring-time delegation follows the current user's authorization and available tools. Supporting skills stay within this skill's authoring scope.

The method and selected adaptations are recorded in [sources](references/sources.md). [Evaluation cases](evals/behavior-fixtures.json) define bounded checks; [validation](references/validation.md) records what was actually run and its limits.
