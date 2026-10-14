# Security, reliability and operational assurance

Apply by exposure and approved requirements. Read current primary guidance for the selected technology; record standards editions and exact control references only when verified. Keep controls, measured results and unresolved evidence distinct in concise technical sections.

## Security baseline

Map actors, assets, entry points, trust boundaries, privileged actions and sensitive data. Trace input from browser/API/RPC/file/configuration/third-party/AI sources to its use and output. For each significant threat record a concrete trigger, impact, prevention/detection/recovery control, enforcement owner, verification obligation and residual risk. Threat-model all applicable STRIDE categories; a category name is not a threat description.

- Validate syntax, type, length, ranges and business relationships at authoritative boundaries. Normalize only as permitted by field semantics: preserve exact credentials and legitimate Unicode where required; do not silently truncate or rewrite user data. Specify counting and normalization consistently across clients and services.
- Apply the [injection and projection rules](output-contract.md#security-first-enforcement-and-data-projections), [rate/resource limits](output-contract.md#configurable-rate-and-resource-limits) and [concurrency/idempotency requirements](output-contract.md#concurrency-and-durable-idempotency). Link controls to concrete owners and negative verification; avoid a generic sanitizer or an unsupported claim of complete security.
- For uploads validate actual content/type, accepted MIME/format, byte size and bounded decoded resources. Treat filenames and declared MIME as untrusted; select safe storage identifiers, constrain paths, isolate processing and authorization, and specify safe serving content type/disposition/nosniff behavior. Document replacement, orphan cleanup and reference races.
- Define authentication/session lifecycle, credential hashing, object/action authorization, internal identity propagation and least privilege where in scope. If authentication is explicitly excluded, state the exposure assumptions, consequences and required perimeter; do not infer that it is excluded because no code exists.
- Define narrow CORS origins/methods/headers where applicable, credential handling, CSRF protections when applicable, trusted proxies, TLS boundaries, cookie/header policies and rate/resource limits. CORS does not replace authorization.
- Prevent secrets and sensitive payloads in source, examples, logs, traces, errors and metrics. Specify provisioning/access/rotation, dependency and container supply-chain controls, redacted diagnostics and stable public errors that do not expose internals.

## AI and tool boundaries, when applicable

Treat retrieved metadata, documents, model output and tool results as untrusted data. Define minimum tool capabilities, authorization enforced outside model reasoning, content validation, provenance, outbound access controls and secret/PII boundaries. Approval is a verifiable human action tied to exact content, actor, scope and expiry, not a model-generated claim. Changed content requires fresh approval. Replays and uncertain commits use the original operation identity. Include direct/indirect injection, confused-deputy, exfiltration, forged approval and client-specific failure scenarios; filtering alone is not the control boundary.

## Cryptography and compliance, when applicable

When authenticated encryption such as AES-GCM is required, specify a vetted library, key size, nonce uniqueness per key (including concurrent/restarted writers), authentication tag verification, associated data and versioned ciphertext/key envelope. Define key access, new-write versus old-read behavior, rotation trigger/cryptoperiod, resumable safe re-encryption, key retirement and backup/restore compatibility. Fail closed on unavailable keys or failed authentication; never substitute plaintext or overwrite protected data with invented empty values. Use one-way password hashing for passwords, not recoverable encryption. Do not hardcode a universal algorithm or key-management provider into unrelated projects.

ISO/IEC 27001 concerns an organization's ISMS. Record relevant risks, controls, owners, evidence and limitations without asserting certification or organization-wide conformity from application features. If exact ISO text/control mapping is unavailable, state that verification gap instead of inventing clause wording. Preserve any explicit compliance scope and distinguish design coverage from audit evidence.

Primary reference entry points (verify applicable editions when authoring):

- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) and [ASVS cheat-sheet mapping](https://cheatsheetseries.owasp.org/IndexASVS.html)
- [SQL injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html), [XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [OS command injection defense](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)
- [Input validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html), [file upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [GraphQL security](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [Prompt injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [Cryptographic storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html), [key management](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html), [NIST SP 800-38D](https://csrc.nist.gov/pubs/sp/800/38/d/final)
- [ISO/IEC 27001](https://www.iso.org/standard/27001)

## Monitoring baseline

Specify structured logs with validated request/correlation IDs across service calls and durable work, excluding credentials and sensitive payloads. Separate process liveness, dependency readiness and user-operation success. Define metric name/meaning, measurement boundary/window, permitted low-cardinality labels and telemetry access/retention.

Cover request/error/latency, protocol-level and application-level failures (including GraphQL errors under HTTP 200), gRPC status/deadlines, upload transfer/processing/attachment outcomes, dependency health, retry exhaustion and pending-work age where relevant. Expected validation/access/conflict outcomes are distinguishable from system failures. A health endpoint alone is not operation monitoring.

Specify dashboards and actionable alert proposals: metric/query, threshold/window, severity, deduplication, routing, owner if known, recovery condition and linked runbook anchor. Include notification-provider failure and safe exhaustion recovery. Label numerical thresholds/SLOs as proposed until justified and tested; an SLO is not an SLA. Distinguish release/assessment commitments, verified implementation and production follow-up without deferring existing commitments by relabeling them.

## Reproducible runtime and operational readiness

For a selected container/Make setup define prerequisites, configuration, version strategy, networks, persistence and secrets; dependency ordering, database readiness, serialized/locked migrations, safe initial seeding, service startup and bounded readiness checks. Specify a repeatable command contract, failure exit behavior, redacted diagnosis and the browser/service entry point. Repeated/concurrent startup must not duplicate migrations/seed effects or destroy data. Keep external account provisioning and credentials explicit; containers cannot manufacture third-party authorization.

Explain stop/restart persistence, isolated tests, backup/restore and keys, rollback/schema compatibility, safe recovery from partial startup, graceful shutdown and workload/capacity assumptions. Autoscaling/HPA is conditional on selected infrastructure and measured resource/latency signals; explain state/worker/limiter consistency before recommending replicas. Local Compose does not establish production high availability.

Runbooks state symptom, safe inspection, eligible recovery, success verification and escalation. Distinguish documented commands from commands actually run. Do not run destructive migrations or deploy infrastructure to validate a design document.
