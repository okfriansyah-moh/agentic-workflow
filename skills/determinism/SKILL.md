---
name: determinism
description: "Establish reproducible behavior within a defined computation or test boundary. Use for stable ordering, repeatable outputs, hashing, and nondeterminism diagnosis."
---

# Determinism

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

State the guarantee: semantic equivalence, stable ordering, byte-identical serialization, numerical tolerance, or reproducible builds. Identify the inputs and environment included in that guarantee.

Make time, randomness, locale, iteration order, concurrency scheduling, dependency versions, and external state explicit where they affect the result. Inject or capture them at a testable boundary. Secure tokens and other deliberately random values should remain cryptographically random; separate them from deterministic business calculations.

Define deterministic serialization before hashing and specify tie-breakers that form a total order when stable output requires one. Consider Unicode normalization, floating-point behavior, time zones, and missing versus null values. Choose hash length and identity strategy from collision/privacy requirements rather than a fixed prefix length.

For LLM or remote services, pin and record supported parameters and validate outputs, but report residual nondeterminism. Temperature zero alone does not guarantee repeatability.

Test repeated runs, shuffled input ordering, relevant environment differences, and concurrent schedules within the declared boundary. Report the boundary and remaining environmental assumptions; avoid claiming machine-independent byte equality when it was not established.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

