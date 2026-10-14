# Conditional supporting skills

The combined core stands alone. Resolve available skills through the current skill catalog; these relative links identify the installed sibling skills in this environment. Read each selected skill before using it. If unavailable, apply the core guidance and primary sources, report any consequential coverage limitation, and continue independent work.

Pass the target ATDD document, relevant source/obligation IDs, accepted decisions and the specific review question. Parent scope controls outputs: all findings and scenarios are consolidated into the main document. Supporting implementation actions, source edits and publication remain inactive during ATDD authoring.

| Trigger | Supporting skill | Document contribution |
| --- | --- | --- |
| Outline, difficult terminology or final reader review | A fresh reader review | Clear narrative and a reader's ability to execute/judge a case |
| Source disagreement or revision reconciliation | [docs-sync](../../docs-sync/SKILL.md) | Classify drift and reconcile the ATDD without changing source policy |
| Public/internal boundary contracts | [api-design](../../api-design/SKILL.md), [dto](../../dto/SKILL.md) | Presence, errors, permission, compatibility and serialization cases |
| Threats and control enforcement | [stride-analysis-patterns](../../stride-analysis-patterns/SKILL.md), [security-requirement-extraction](../../security-requirement-extraction/SKILL.md) | Concrete threat/control/observable-test mappings |
| Schema evolution and data recovery | [migration-management](../../migration-management/SKILL.md) | Migration/backfill interruption, integrity, compatibility and recovery cases |
| Duplicate effects, retries and durable work | [idempotency](../../idempotency/SKILL.md), [failure](../../failure/SKILL.md), [pipeline](../../pipeline/SKILL.md) | Replay, uncertain outcomes, fault boundaries and recovery cases |
| Settings, limits, secrets or startup | [config-validation](../../config-validation/SKILL.md) | Source precedence, validation, lifecycle and redacted failure checks |
| Interactive UI contracts | [fixing-accessibility](../../fixing-accessibility/SKILL.md) | Keyboard, focus, semantics, contrast and error-feedback specifications |
| Time, randomness, ordering or races | [determinism](../../determinism/SKILL.md) | Reproducible fixtures and stable observations |
| Scenario testability or coverage challenge | [test-generation](../../test-generation/SKILL.md) | Meaningful assertion and boundary review only |

Reuse the requested product's established performance targets and measurement design. The performance-optimization skill requires a measured bottleneck and is not a prerequisite for writing prospective performance cases. Technology-specific skills activate only for an independently selected matching technology and a concrete need.

The installed test-driven-development/tdd workflow belongs to a later, explicitly requested executable implementation phase. The core already adapts Superpowers' assertion-quality principles without importing a competing TDD loop, code deletion rule, test runner or blanket approval gate.
