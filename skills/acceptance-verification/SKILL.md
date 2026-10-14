---
name: acceptance-verification
description: "Map assigned ATDD cases to executable verification at their required proof boundary and evaluate feature acceptance."
metadata:
  version: "1.0.0"
---

# acceptance-verification

Read assigned case IDs, task traceability and group integration ownership from the existing plan package. Keep document readiness, execution eligibility, task completion and feature acceptance as separate decisions.

Build a case-to-check map with required boundary, setup, action, assertions, environment, implementation fingerprint and artifacts. Preserve requirement/task/design/case IDs. Missing mappings block the assigned acceptance scope. Do not invent cases or silently substitute easier tests.

Use unit tests for domain logic, real PostgreSQL for persistence semantics, real transport/client calls for API contracts and an actual browser journey for UI behavior as each case requires. Mocks establish only their stated boundary. A log-rendering image is a rendered log summary; it does not prove a UI action.

Capture command results through the receipt helper. Keep test selection/count and exit code, observed requests/responses, state checks, screenshots/traces/recordings, artifact hashes and reviewer identity. Empty relevant selections fail. Inspect assertions as well as runner success so a screenshot alone cannot imply business correctness.

Use record-test-video for coherent UI journeys and verify-test-evidence before acceptance. Changes to implementation, configuration, tests or governing requirements invalidate affected proof; evidence-only bookkeeping does not invalidate unchanged inputs. Reuse evidence only after the fingerprint and case boundaries match.

Task completion requires its required checks and independent review. Group/feature completion additionally requires the named integration owner's combined-behavior evidence. Return passed/failed/blocked/stale cases and exact missing proof; only Forge updates task execution fields.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

For actual helper commands, claim/check contracts and evidence proof fields, read [coordination and evidence contracts](../../docs/COORDINATION.md) before writing a brief or receipt. Use the documented structured objects and preserve captured argv/test-report requirements; do not infer a schema from narrative examples.
