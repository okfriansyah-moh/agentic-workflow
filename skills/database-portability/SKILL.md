---
name: database-portability
description: "Assess or implement compatibility across explicitly supported database engines. Use for database abstraction, dialect differences, or multi-engine behavior."
---

# Database portability

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Establish the supported engines, versions, drivers, and ORM/query layer. Portability has a declared target matrix; it does not mean all databases accept one SQL dialect.

Compare types, parameter binding, generated IDs, upserts, constraints, JSON, collations, time zones, isolation, DDL transactions, and locking where the feature uses them. SQL placeholders and identifier quoting come from the actual driver. Parameterize values; validate dynamic identifiers against intentional choices.

Keep engine-specific behavior behind the existing persistence boundary when multiple engines require it. Use the configured ORM or query builder when appropriate. Do not replace native capabilities with weaker abstractions without a demonstrated portability need.

Design against required behavior, including uniqueness and concurrent writes. Syntax that executes on two engines may still have different semantics. Use [migration-management](../migration-management/SKILL.md) for schema evolution.

Run relevant integration scenarios on each supported engine/version or report untested entries. A lightweight test database is not evidence that a different production engine behaves identically. Deliver the compatibility matrix, intentional dialect branches, and known limitations.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

