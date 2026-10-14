---
name: coding-standards
description: "Establish or apply coding conventions for the affected language and component. Use when implementing code or reviewing consistency with project standards."
---

# Coding standards

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Use the shared project-context reference below before prescribing a convention. Read adjacent code and configured formatters/linters to separate enforced standards from personal style.

1. Apply project naming, imports, visibility, error handling, resource lifetime, async, and documentation conventions for each component. Keep generated files under their generator’s control.
2. Make the public contract and failure behavior clear using the language’s native mechanisms. Add types, schemas, or documentation where the project uses them; avoid imposing interfaces or annotations on every language.
3. Treat complexity, argument counts, and long functions as prompts to inspect cohesion and testability, not universal failure thresholds. Extract an abstraction only when it improves a real boundary.
4. Preserve intentional output: CLI stdout is a product interface; services may require structured logs and redaction. Distinguish diagnostics from user output.
5. Use configured checks for mechanical enforcement. Explain conflicts between documented standards and current code instead of silently introducing a repository-wide rewrite.

For module/interface design questions, consult [codebase-design](../codebase-design/SKILL.md). For a change review use [code-review](../code-review/SKILL.md); this skill supplies conventions rather than another review loop.

## Project adaptation

Before applying this workflow, read [shared project context](references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

