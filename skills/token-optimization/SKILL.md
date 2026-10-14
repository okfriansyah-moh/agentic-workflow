---
name: token-optimization
description: "Reduce unnecessary context and tool-output volume while preserving task evidence. Use for context-pressure problems or an explicitly requested token-efficiency pass."
---

# Context efficiency

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Load relevant skill instructions and the source material needed for the actual task. Read a skill’s required procedure fully enough to follow it; a quick-reference summary is not a substitute for essential constraints. Skills guide decisions but do not replace authoritative project requirements.

Use targeted search and bounded reads to find relevant sections, expanding when context or completeness requires it. Reuse unchanged material already read. Re-read when files, requirements, or remembered details change; do not rely on a stale cache.

Summarize completed work with decisions, file/artifact pointers, actual validation, and remaining tasks. Keep exact errors, identifiers, contracts, qualifications, and source references needed for correctness. Compression must not hide failed checks or uncertainty.

Delegate bounded research only when permitted and useful; avoid duplicating all source context across workers. Use [rtk](../rtk/SKILL.md) only when its installed capabilities suit the command; ordinary targeted tool output is a valid fallback. Do not automatically activate clipped writing styles or alter the user’s Humanizer voice to save tokens.

Measure savings only with available evidence. Report an efficiency change qualitatively when token counts are unavailable rather than inventing percentages.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

