---
name: migration-management
description: "Create or review database schema and data migrations using the project migration system. Use for schema evolution, backfills, and migration recovery planning."
---

# Migration management

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Inspect the migration framework, version history, deployed state, and database version. Follow its naming and transaction rules. Keep already-applied/shared migrations stable; correct them with a new migration unless a coordinated history rewrite is explicitly intended.

Plan rollout compatibility between old and new application versions. For risky changes, separate expansion, backfill, validation, and contraction. Estimate locks and table rewrites; choose engine-supported online operations where justified. A logical migration may require several transactions or resumable batches.

Identify destructive effects and the recovery path before execution. Provide a reverse migration only when it can restore the required state; otherwise document forward recovery, backup restoration, or an irreversible boundary. A down migration that drops data is not a safe rollback merely because it exists.

Use [database-portability](../database-portability/SKILL.md) when multiple engines are supported. Test the upgrade from a realistic prior schema, data preservation, constraints, application compatibility, and interrupted-backfill recovery where relevant. Let the migration framework track one-time application; do not require every DDL statement to be independently idempotent.

Creating migration files does not authorize applying them to production. Report checks performed and the deployment/recovery prerequisites without automatically committing or deploying.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

