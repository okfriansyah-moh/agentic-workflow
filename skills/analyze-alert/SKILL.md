---
name: analyze-alert
description: "Investigate a supplied alert using observed telemetry, source context and a bounded incident timeline."
metadata:
  version: "1.0.0"
---

# analyze-alert

Resolve the alert time range, timezone, affected environment/service, symptom and available telemetry source from supplied data and project configuration. Read-only investigation is the default. Use real credentials/tools only when available; do not assume a company's dashboards or hardcoded labels.

Build an ordered timeline from actual logs, metrics and traces. Correlate safe request/trace IDs, deployment revision, resource saturation and dependency behavior. For latency, identify observed spans and gaps; a silent interval is a measurement gap, not proof of a particular query or upstream call. Bound queries and redact sensitive values.

Inspect relevant code, database queries/indexes, transaction/retry behavior and configuration to test the leading hypotheses. Keep observed facts, supported inference and missing evidence distinct. Describe whether a claim is telemetry-confirmed, source-confirmed or unverified. No synthetic logs, invented impact counts or guessed service ownership.

Propose immediate containment and a durable fix, each connected to evidence and verification. Production restarts, scaling, queue clearing and paging are proposals until authorized. Monitoring recommendations need a concrete signal/window/threshold rationale and owner decision.

When a change is authorized, route it through task-implement and the normal independent review. Verify the symptom after the change against comparable measured conditions; absence of logs alone is not recovery proof.

Return impact/time range, concise timeline, evidence links or local paths, cause/confidence, exact remaining gap and next actions. This adaptation removes company-specific selectors, forced timezone conversion and messaging side effects.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
