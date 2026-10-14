# Quality questions

For each applicable quality attribute record the source, workload/environment, stimulus, expected response, proposed measurable target, measurement method and evidence status. Unknown baselines stay unknown.

| Attribute | Questions |
| --- | --- |
| Performance/capacity | Which operations, payloads, concurrency, percentiles, saturation and resource budgets? |
| Reliability | Which failures, retry budgets, idempotent effects and recovery bounds? |
| Availability/recovery | Which dependencies, data-loss/recovery objectives and tested restore procedures? |
| Security/privacy | Which assets, exposed boundaries, identity, authorization, sensitive data and retention? |
| Maintainability | Which ownership, conventions, compatibility, tests and explanation requirements? |
| Operability | Which logs, metrics, alerts, runbooks, change/rollback and response owners? |
| Cost | Which approved environments, budget limits and unresolved provisioning choices? |
| User experience | Which accessibility, feedback, uncertainty and state-recovery contracts? |

Do not copy sample latency, uptime, replica, load or coverage targets into requirements. Proposed targets must be justified and distinguishable from measured performance or contractual SLAs. Identify assessment/release commitments separately from production follow-up.
