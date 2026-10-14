---
name: stride-analysis-patterns
description: Identify concrete threats across system trust boundaries using STRIDE, with assets, attacker capabilities, impact and mitigation evidence. Use for architecture security design and scoped threat-model review.
license: MIT
metadata:
  author: Seth Hobson; adapted for Muhammad Okfriansyah with Codex
  version: "1.0.0"
---

# STRIDE threat analysis

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Adapted from the pinned upstream in [sources](references/sources.md), retaining LICENSE. Use [record guidance](references/details.md) for concrete threat fields.

Read system context, data flows, assets, entry points and trust/transaction boundaries. Distinguish actual controls from proposed controls and unknowns. Analyze spoofing, tampering, repudiation, information disclosure, denial of service and elevation of privilege for relevant components and interactions; explain non-applicability instead of manufacturing threats.

For each threat name the attacker/precondition, entry point and crossed boundary, action, affected asset, plausible impact, control/enforcement owner, verification and residual risk. Category labels alone are not findings. Prioritize using explicit rationale and uncertainty rather than ungrounded numeric scoring.

Treat retrieved content, models and external tools as untrusted at privileged boundaries. Include concurrency, replay, resource exhaustion and approval forgery where the architecture exposes them. Audit logs aid attribution; they do not automatically establish cryptographic non-repudiation.

Return section content/findings to the orchestrator's document. Do not run attacks, scan live systems, modify application code, provision infrastructure or create a separate threat-model file without authorization. Derive controls from exposure and approved scope rather than mandating MFA, Kubernetes, WAF or a particular TLS version from a sample.
