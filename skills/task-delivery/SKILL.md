---
name: task-delivery
description: "Deliver verified scoped changes through commits and an authorized draft pull request when the remote is configured."
metadata:
  version: "1.2.0"
---

Resolve the pinned bundle from .ai/config.json and read [selection delivery](../../docs/DELIVERY.md). That policy governs review timing, quality gates, recovery budgets and literal delivery status. Reuse it while unchanged.

# Publish reviewed selection changes

Confirm the entire requested selection has current passing required checks and one independent review with no unresolved required findings. A worker contribution or unreviewed composition is not selection acceptance.

Inspect Git status and stage only authorized related files. Commit recoverable changes and preserve unrelated work. Verify the reviewed base/head and affected results; implementation changes require affected verification and review of the fixes.

Under existing authorization, push the selection branch and create/update its draft PR after review. Confirm the remote/base and account access. Attach every created or requested PR using the host tool when available. Missing remote/access blocks publication, not the existence of local work. Merge/deployment/external messages require authorization covering their outcome and destination.

Record local head, remote PR head and the actual change: source commits, metadata only, or no publication. State implemented tasks, passed checks, review and remaining work literally. Do not report title/body edits as source delivery or imply unimplemented tasks are complete.

Apply the [shared wording policy](../../resources/wording/output-wording.md) before delivery.
