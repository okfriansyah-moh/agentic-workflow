---
name: verify-test-evidence
description: "Independently validate acceptance evidence mapping, provenance, freshness and recording readability."
metadata:
  version: "1.2.0"
---

Resolve the pinned bundle from .ai/config.json and read [selection delivery](../../docs/DELIVERY.md). That policy governs review timing, quality gates, recovery budgets and literal delivery status. Reuse it while unchanged.

# Inspect results within the selection review

Read assigned requirements, tested inputs, runner reports and relevant artifacts. Verify actual command exits, nonempty executed case counts, assertions, boundary and environment. Missing, failing or stale required proof does not pass.

Use the same independent reviewer and findings ledger as the full-selection review. Do not create a separate evidence-approval stage. Check existing artifact integrity where relevant; avoid duplicate copies and manifests.

Ordinary browser cases can use assertions/direct inspection without video. For explicitly required recordings, inspect actual decoded frames, duration/readability, action/result timing and source association; a media file alone proves no behavior. Verify real speech for announcement obligations.

Record observable required findings and exact missing proof. A capture command or trace path is provisional until the actual artifact and observation are inspected. Preserve failed results and share the selection-wide optional repair limit.

Apply the [shared wording policy](../../resources/wording/output-wording.md) before delivery.
