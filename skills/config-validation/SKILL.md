---
name: config-validation
description: "Design or validate configuration sources, precedence, defaults, and startup checks. Use when adding configuration or diagnosing inconsistent settings."
---

# Configuration validation

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Find the actual sources and ownership: files, environment, command arguments, service configuration, or secret providers. Document precedence and distinguish unset from explicitly empty, false, or zero. Apply overrides according to presence, not truthiness.

Validate syntax, types, ranges, dependencies, and required secrets at the appropriate lifecycle boundary. Fail with actionable redacted errors. Defaults should be deliberate; configuration failures must not silently select a different provider, environment, or unsafe behavior.

Centralize resolution where the project’s architecture supports it, while allowing legitimate runtime refresh and secret-provider access. Keep secrets out of committed configuration and diagnostic output. Use secret references or the existing secure credential facility rather than requiring environment variables exclusively.

Treat renamed and removed keys as a compatibility change: document migration, deprecation, or rejection behavior. Promote true deployment/user tunables to configuration; domain constants need not become settings.

Test precedence including false/zero/empty values, missing requirements, invalid combinations, redaction, and supported reload behavior. Use the project’s native config format and validation library.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

