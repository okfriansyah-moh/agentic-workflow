---
name: pipeline
description: "Design or verify staged processing, dependency ordering, handoffs, and checkpoint recovery. Use for data or application pipelines, including fan-out and fan-in."
---

# Pipeline reasoning

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Map stages, inputs, outputs, prerequisites, side effects, and completion states. Use the actual orchestration mechanism rather than inventing an orchestrator directory or database adapter.

Separate logical dependency order from scheduling. Independent stages may run concurrently; conditional stages may be skipped only under a defined contract. For fan-in, define required inputs, partial-result behavior, and ordering. For streams, define backpressure and bounded buffering.

Validate contracts at trust boundaries and where a stage relies on an invariant; avoid redundant conversions with no purpose. Specify who owns each output and shared-state update.

Checkpoint only after the associated result is durable, or use an atomic transaction/outbox appropriate to the system. Resume must reconstruct required inputs and detect changed input/configuration versions. “Stage finished” is insufficient if its output is missing or invalid.

Use [failure](../failure/SKILL.md) and [idempotency](../idempotency/SKILL.md) for interrupted execution and retries. Verify normal ordering, concurrent independent branches, missing prerequisites, partial failures, and resume without duplicated side effects. Distinguish parallel development of stages from concurrent execution at runtime.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

