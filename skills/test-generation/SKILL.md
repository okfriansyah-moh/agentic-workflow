---
name: test-generation
description: "Add meaningful behavior tests or assess missing coverage using the project test framework. Use for regression tests, boundary coverage, and test-suite improvements."
---

# Generate behavior tests

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Identify the public behavior, known regression or coverage gap, and relevant existing tests. Follow the guidance on [good tests](../tdd/tests.md) and [boundary mocking](../tdd/mocking.md). When TDD is requested, use the installed tdd workflow and its agreed seams rather than creating a second test-first process.

Use project-native naming, placement, parameterization, fixtures, and runner commands. Keep expected results independent of the implementation. Prefer examples from requirements or known cases; cover reachable failures and important boundaries rather than mirroring every branch.

Use controlled clocks/random sources where reproducibility matters. Property-based tests and parameterized loops are valid when failures are reproducible and assertions express real properties. Test external effects at suitable boundaries; use real compatible integration fixtures where mocks would miss the behavior under test.

Select unit, integration, contract, or end-to-end tests according to the failure they can catch. Avoid fragile tests of private call order or internal method names. For a regression, demonstrate failure on the faulty behavior when feasible, then verify the correction.

Follow configured coverage requirements when present, but do not invent universal percentage quotas or claim coverage proves correctness. Run the relevant suite and report actual results, skipped cases, prerequisites, and the important behavior the new tests establish.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.


Apply the [permanent quality contract](../../docs/GATES.md#permanent-quality-contract) when planning, scaffolding, implementing, testing, reviewing or accepting work. Keep existing failures blocking and reuse only matching evidence.
