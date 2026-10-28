---
name: acceptance-verification
description: "Map assigned ATDD cases to executable verification at their required proof boundary and evaluate feature acceptance."
metadata:
  version: "1.2.0"
---

Resolve the pinned bundle from .ai/config.json and read [selection delivery](../../docs/DELIVERY.md). That policy governs review timing, quality gates, recovery budgets and literal delivery status. Reuse it while unchanged.

# Verify the assigned behavior

Map assigned case IDs to their actual setup, action, assertions, boundary and current implementation. Preserve requirements and distinguish local contributions from full release outcomes. Missing required cases or empty test selections block acceptance.

Use units for isolated rules and real database, transport, browser or client observations where required. Mocks establish only their stated boundary. Use existing runner results with command, exit, count, input and environment provenance.

Browser assertions/direct inspection can establish ordinary UI behavior. Require screenshots, recordings or actual reader observations only when the required observation needs them or the user asks. Actual speech obligations need speech observation; DOM or audio energy cannot substitute. Exhaustive matrices and media provenance belong to their release owners unless expressly required here.

Reassign deferred proof explicitly and keep it pending. Inspect assertions and source behavior within the one combined selection review. Reuse valid results at unchanged inputs; rerun affected checks after changes. No standalone task/evidence review or method-approval loop is required.

Apply the [shared wording policy](../../resources/wording/output-wording.md) before delivery.

Apply the [permanent quality contract](../../docs/GATES.md#permanent-quality-contract) for configured checks and feature acceptance. Installation, native loading and passing product evidence require separate results; existing failures remain blocking.
