---
name: security-audit
description: "Perform a scoped security review with evidence-backed findings and remediation. Use when a security audit is requested or a change presents material security risk."
---

# Security audit

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Define the assets, trust boundaries, exposed entry points, attacker capabilities, and review scope. Use applicable current primary security guidance and installed-version advisories when assessing technical claims or dependencies.

Trace external input through authorization, validation, storage, rendering, commands, and outbound calls. Check tenant/object authorization, injection, unsafe deserialization, path traversal, SSRF, resource limits, and secret handling where reachable. Parameterize values with the actual driver; dynamic identifiers need constrained selection. Prefer structured process arguments over shell interpolation and context-appropriate output encoding over generic “sanitization.”

Treat retrieved text and model output as untrusted data when they influence tools or privileged actions. Secrets may use an approved secret manager or credential facility; prevent exposure in source, logs, errors, and artifacts. Assess session/token entropy and lifecycle against the application threat model.

Judge configuration in context: public noncredentialed CORS and dynamic execution in a sandbox are not automatically vulnerabilities. For dependency findings, verify affected versions and reachable use; report scan limits.

For each finding provide location, plausible trigger, impact, evidence, and a focused fix. Use severity with rationale; calculate a CVSS vector only when enough facts support it. Validate fixes in permitted isolated fixtures. Separate confirmed issues, hypotheses, and coverage gaps; a clean review is not a guarantee of complete security.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.


Apply the [permanent quality contract](../../docs/GATES.md#permanent-quality-contract) when planning, scaffolding, implementing, testing, reviewing or accepting work. Keep existing failures blocking and reuse only matching evidence.
