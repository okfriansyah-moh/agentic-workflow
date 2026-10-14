---
name: vertical-slice
description: "Organize a feature around its end-to-end behavior when vertical slices fit the architecture. Use for feature boundaries or an explicitly requested vertical-slice refactor."
---

# Vertical slices

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Identify the use case, entry point, business behavior, data access, and observable result. Preserve the surrounding architecture unless changing it is part of the task.

Keep code that changes together near the feature using the project’s native structure. Handler, service, repository, contract, and instrumentation are responsibilities, not mandatory separate files or classes. Omit layers with no work to do.

Expose intentional public boundaries between features. Reuse cohesive domain rules and data access where ownership warrants it; duplicating everything is not isolation. Keep transport parsing separate from domain decisions when that distinction helps testing and reuse.

Plan one thin, working path from input to outcome and verify it at a public seam. Add failure behavior incrementally. Avoid a repository-wide move merely because horizontal directories already exist.

Apply [modularity](../modularity/SKILL.md) for ownership and [dto](../dto/SKILL.md) where data crosses a boundary. Report the feature’s entry point, dependency direction, and testable outcome.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

