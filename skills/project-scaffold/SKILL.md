---
name: project-scaffold
description: "Initialize a requested new project or component using its chosen ecosystem and conventions. Use for scaffolding; do not trigger setup for ordinary feature work."
---

# Project scaffold

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Establish what is being created, its target location, chosen stack, and required capabilities. Inspect existing workspace conventions before selecting a generator. Ask about consequential missing stack choices; reuse decisions already provided.

Use the ecosystem’s supported initializer or a minimal manual scaffold, checking version-matched documentation and generator side effects. Configure only required components: a library need not have an HTTP server, database, containers, or agent pipeline.

Create the smallest runnable path with appropriate package metadata, entry points, ignore rules, useful startup instructions, and native validation. Preserve existing files and user changes; compare before overwriting an existing component. Dependency installation must fit current authorization and permissions.

Run the documented minimal build/test/start check in an isolated environment where possible. State actual commands and prerequisites that remain missing. Git initialization, commits, hooks, cloud resources, and publication are separate actions requiring task authorization; scaffolding does not imply them.

Apply [coding-standards](../coding-standards/SKILL.md) to native conventions. Add architectural layers only when the selected design needs them.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

