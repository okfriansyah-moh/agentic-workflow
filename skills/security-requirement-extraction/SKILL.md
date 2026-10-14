---
name: security-requirement-extraction
description: Translate concrete threats and approved security obligations into enforceable requirements, control mappings and observable acceptance criteria. Supports technical-design sections without generating implementation or claiming compliance.
license: MIT
metadata:
  author: Seth Hobson; adapted for Muhammad Okfriansyah with Codex
  version: "1.0.0"
---

# Security requirement extraction

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Adapted from the pinned upstream in [sources](references/sources.md), retaining LICENSE. Read [mapping guidance](references/details.md) when creating records.

Use the system's threat model, exposure, data classification and approved requirements. For each material risk define the protected outcome, enforcement boundary, failure behavior, owner, acceptance/negative scenario and remaining limitation. Link to source requirements, threat IDs and technical contracts; several controls may address one threat and one control may address several threats.

Separate functional controls, measurable quality needs and external constraints. Make input/use/output safety, auth, privacy, errors, telemetry, resource limits and cryptography specific to their applicable boundaries. Preserve explicit exclusions and document their consequences; do not infer exclusions from missing implementation.

Verify current standard editions and exact control IDs with authoritative sources. A generic domain-to-control lookup is not compliance evidence. ISO ISMS scope and certification are distinct from application-control coverage. Mark unavailable control text, unverified mappings and implementation gaps honestly.

Return requirements and verification obligations in the parent's single document when requested. Formal ATDD suites, epics/tickets, scans and implementation require their own authorization. No automatic numerical priority, mandatory provider, cryptographic algorithm or unsupported compliance guarantee comes from this skill.
