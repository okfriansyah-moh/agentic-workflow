---
name: modularity
description: "Design or validate module boundaries, ownership, and public interfaces. Use when changing cross-module dependencies or isolating responsibilities."
---

# Module boundaries

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Consult [codebase-design](../codebase-design/SKILL.md) when deciding interface depth. Map the actual public boundary, consumers, owned data, and side effects before changing it.

- Keep internal details private using the language/package system. Cross-module calls should use intentional public APIs; legitimate dependencies are not automatically violations.
- Place persistence and external integrations at the boundaries chosen by the project. A module can own a repository or SDK adapter; it need not be a pure function or expose exactly one method.
- Minimize shared mutable state and accidental shared ownership. Specify transaction, concurrency, and lifecycle responsibilities where modules interact.
- Share genuinely common contracts, not unrelated implementation internals. Watch for a catch-all shared package that creates coupling.
- For parallel work, define file ownership and sequence shared-interface changes before their consumers.

Use [dependency-analysis](../dependency-analysis/SKILL.md) to inspect the graph and [dto](../dto/SKILL.md) for serialized boundaries. Completion means callers use the intended boundary and relevant integration behavior still works, not that a prescribed folder tree exists.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

