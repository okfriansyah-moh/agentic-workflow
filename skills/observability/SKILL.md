---
name: observability
description: "Implement or review useful application logs, metrics, traces and alerts with redaction and operational checks."
metadata:
  version: "1.0.0"
---

# observability

Start from the changed user operation, its failure modes and the approved operational requirements. Define which question each signal answers before adding instrumentation.

Use structured logs with timestamp, severity, service/operation and safe correlation IDs. Keep credentials, tokens, sensitive payloads and unnecessary personal data out of logs. Avoid unbounded labels or request IDs in metric dimensions. Propagate trace context across supported service/transport boundaries without treating external correlation values as trusted identity.

Measure rates, errors, duration and resource saturation appropriate to the component. Choose histogram boundaries and aggregation that serve the stated latency/availability objective. Document units and sampling. Instrument retries and partial failures so a successful final result does not hide repeated dependency failures.

Alerts need an owner, symptom, query/window, threshold rationale, severity and actionable runbook. Check missing-data behavior and deployment noise. Do not create paging integrations or contact teams as an incidental implementation action.

Validate emitted telemetry during real success/failure paths. Query the actual receiver when the acceptance boundary requires it; asserting that a mock logger was called is only unit evidence. Verify redaction and ensure telemetry failures do not break application behavior.

For an existing alert use analyze-alert to correlate observed events. Report what was measured, which revision/environment produced it, query/time range, expected versus observed result and the remaining visibility gap.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
