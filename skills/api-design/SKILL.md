---
name: api-design
description: "Design or evolve an external or inter-component API contract. Use for endpoint, RPC, event, or library-boundary design and compatibility decisions."
---

# API design

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Identify consumers, protocol, existing conventions, and compatibility obligations. Design the observable contract before internal implementation.

- Specify inputs, outputs, validation, authentication/authorization, error semantics, and cancellation/deadline behavior appropriate to the boundary.
- For collections, choose pagination, stable ordering, filtering, and limits that fit the access pattern. For events, define delivery, ordering, deduplication, and schema evolution. For streaming, define backpressure and termination.
- Follow existing naming and envelope conventions. REST resource routes, RPC methods, GraphQL schemas, binary messages, and in-process APIs need different representations.
- Define retry and idempotency semantics for state-changing operations. Avoid exposing internal errors or making clients infer success from ambiguous transport outcomes.
- Analyze old consumers before adding, removing, or changing fields. Select versioning or migration based on compatibility needs, not a mandatory URL pattern.

Use [dto](../dto/SKILL.md) for data contracts and [idempotency](../idempotency/SKILL.md) for replay behavior. Finish with representative requests/results or schema examples, failure cases, and compatibility tests at the chosen boundary.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

