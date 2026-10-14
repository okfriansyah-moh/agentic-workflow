---
name: conflict-resolution
description: "Resolve merge or concurrent-edit conflicts by preserving intended behavior. Use for conflicted files, integration disagreements, and incompatible parallel changes."
---

# Semantic conflict resolution

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Inspect the conflict operation, base, both contributions, task intent, and relevant history. Preserve unrelated uncommitted work. Understand whether a deletion, rename, schema change, or generated file is intentional before selecting a resolution.

Combine compatible changes; choose or redesign incompatible behavior according to accepted requirements and actual ownership. Neither a later phase nor a longer file automatically wins. A union merge can duplicate definitions, resurrect deleted behavior, or corrupt migrations and lockfiles.

For generated artifacts, resolve the source first and regenerate with the project’s tool when permitted. For migrations and shared contracts, inspect deployed/application compatibility before reconciling histories. Ask about genuine conflicting product intent rather than guessing from conflict markers.

Apply a focused resolution and inspect the complete diff, including paths without textual conflicts that may still be semantically inconsistent. Run relevant interface, build, and integration checks. Search for unresolved conflict markers as a hygiene check, not proof of correctness.

Report the intent preserved, any tradeoff, and validation. Continuing an existing authorized merge/rebase may be appropriate; publishing changes or destructive resets require established authorization. Preserve recoverable work when blocked.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

