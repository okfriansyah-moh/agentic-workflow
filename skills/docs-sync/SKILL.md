---
name: docs-sync
description: "Reconcile documentation and implementation against current requirements. Use when behavior changes, documentation drifts, or a documentation consistency review is requested."
---

# Documentation synchronization

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Find the documents that describe the changed behavior: usage, contracts, architecture decisions, operational procedures, or plans. Compare them with the accepted requirement, actual code, and observable behavior.

Classify each discrepancy: implementation defect, stale documentation, authorized requirement change, or unresolved ambiguity. A document is not automatically correct because it exists, and code is not automatically authoritative because it runs. Resolve conflicts using the current request and approved decisions; ask only when intent cannot be established.

Update the authoritative document in its existing location and style when the task authorizes documentation changes. Propagate references or examples that would become misleading, without rewriting unrelated documents. For review-only tasks, report proposed corrections with evidence instead of applying them.

Verify commands, paths, links, configuration names, and described outcomes. Run examples only when safe and permitted; label unexecuted examples. Keep generated documentation under its generator. Do not automatically commit, publish, or create duplicate suffixed documents.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

