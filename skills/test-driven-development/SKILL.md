---
name: test-driven-development
description: "Run test-first development through the installed tdd workflow. Use when explicitly requested by this name or when an accepted task calls for TDD."
---

# Test-driven development

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Read and follow [tdd](../tdd/SKILL.md), the shared workflow for this installation. This entry keeps the upstream invocation name available without defining a second competing loop.

Use the already-agreed public test boundaries from the user’s request or approved plan. If those boundaries are unresolved, propose concrete seams and what each covers before writing tests. Existing explicit agreement counts; do not re-ask for the same boundary.

Choose the test runner, naming, placement, and fixture strategy from the affected component. Work one behavior at a time: a meaningful failing test, then the minimum implementation that passes it. Refactoring belongs to the review stage under the shared tdd policy. There is no automatic commit after a passing test.

Use native database/protocol integration fixtures where those semantics matter; a different lightweight backend is not interchangeable evidence. For additional test coverage outside a requested TDD loop, use [test-generation](../test-generation/SKILL.md). Documentation-only and trivial nonbehavioral changes should not be forced into artificial production-code test cycles.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

