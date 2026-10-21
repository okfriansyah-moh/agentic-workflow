---
name: worktree-integration
description: "Coordinate concurrent repository writers with claimed paths, isolated worktrees and verified semantic integration."
metadata:
  version: "1.2.0"
---

Resolve the pinned bundle from .ai/config.json and read [selection delivery](../../docs/DELIVERY.md). That policy governs review timing, quality gates, recovery budgets and literal delivery status. Reuse it while unchanged.

# Compose contributions safely

Serial work reuses a suitable checkout. Create claimed isolated worktrees only for concurrent writers or protection of unrelated work. Record exact base, owner, paths, resources and branch; serialize contracts, locks, schemas and generators.

Use separate runtime/output resources per concurrent contribution. Preserve user changes and other writers. Reuse worktrees for corrections; read-only review needs no writing checkout.

Compose tested commits in dependency order under one owner before the full-selection review. Selection-scoped composition requires current check receipts and ownership, but no per-worker review. It establishes pending-review status only. New integration requires a valid selection before any Git mutation; historical receipts remain readable without providing another acceptance procedure.

Resolve conflicts against intended behavior; never use Git union merging for code. Run affected combined checks and obtain one independent selection review before acceptance/publication. Preserve failed branches and selection-wide counters across resumes. Clean only owned, preserved work after inspecting dirty/untracked files.

Use [coordination contracts](../../docs/COORDINATION.md) for supported helpers.

Apply the [shared wording policy](../../resources/wording/output-wording.md) before delivery.
