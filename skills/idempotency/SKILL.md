---
name: idempotency
description: "Make repeated or concurrent operations safe without duplicating effects. Use for retryable writes, request keys, jobs, and checkpoint resume."
---

# Idempotency

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Define the operation’s identity and observable effect. Choose a stable key scoped to the caller/tenant and intended operation; include or validate relevant parameters. Reusing a key with different input must have an explicit conflict policy.

Store operation state and outcome using atomic backend primitives: uniqueness constraints, transactions, compare-and-swap, conditional writes, or an appropriate durable workflow. A separate “check then insert” is unsafe under concurrency. Define ownership, in-progress responses, expired leases, and retention where relevant.

Coordinate deduplication with the side effect. For external calls, use provider idempotency support or a transactional outbox/reconciliation approach where available. Do not claim exactly-once behavior across unrelated systems without a mechanism that establishes it.

On replay, return the prior compatible result or resume incomplete work according to the contract. A file’s existence is not proof of completion: validate its version/content and publish through a unique temporary file plus a filesystem-appropriate atomic replacement when applicable. Preserve any needed durability guarantees separately from rename atomicity.

Verify sequential duplicates, concurrent duplicates, conflicting payloads, a crash between effect and acknowledgement, and changed inputs on resume. Idempotency concerns effects; it does not require every response byte or timestamp to be identical.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

