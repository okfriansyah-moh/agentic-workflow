---
name: failure
description: "Design failure classification, bounded retries, partial results, and recovery. Use when defining resilience behavior or fixing repeated failures."
---

# Failure handling

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Classify failures by cause and caller-visible result: invalid input, authorization, unavailable dependency, resource exhaustion, timeout, cancellation, and internal defects. Preserve useful diagnostics with secrets redacted.

Retry only when the operation is safe to repeat and the condition can plausibly change. HTTP status alone is not the whole policy: throttling and some request timeouts may be transient; invalid credentials or validation errors usually require correction. Respect server retry guidance, deadlines, attempt limits, exponential backoff, and jitter where appropriate.

A timeout can mean the remote side effect succeeded. Consult [idempotency](../idempotency/SKILL.md) before replaying it. Cancellation should stop new work and release resources rather than enter another retry loop.

Define partial-success policy explicitly: what is durable, what can be resumed, and what consumers can rely on. Empty output, stale cache, and reduced capability are fallbacks only when the contract permits them. Record which fallback was used.

Use configured thresholds proportional to the operation and observed failure pattern. Repeated identical remediation without new evidence is not progress; stop at the budget and report the concrete blocker. Verify permanent failures, transient recovery, exhausted retries, cancellation, and uncertain remote outcomes.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

