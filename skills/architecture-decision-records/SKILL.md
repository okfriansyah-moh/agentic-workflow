---
name: architecture-decision-records
description: Record significant architectural decisions with source context, alternatives, consequences and stable history. Embed records in a parent document when requested, or use an explicitly selected existing ADR convention.
license: MIT
metadata:
  author: Seth Hobson; adapted for Muhammad Okfriansyah with Codex
  version: "1.0.0"
---

# Architectural decisions

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Adapted from the pinned upstream in [sources](references/sources.md), retaining LICENSE.

Identify choices that change boundaries, compatibility, security, consistency, operation or cost. Reuse accepted decisions before creating new ones. Read requirements and current user authority; a stock example or source recommendation is not an accepted project decision.

For each record provide a stable ID and anchor, title, status, source requirement IDs, context/drivers, decision, considered alternatives, positive/negative consequences, affected interfaces and verification obligations. Use proposed, accepted, rejected, deprecated or superseded accurately; acceptance requires recorded authority, not a template's default status. Implementation/test evidence is separate.

Keep records in the requested document when the parent specifies one output, including its decision index. Otherwise follow an existing ADR convention or the user's destination. Correct factual errors transparently and preserve decision history; supersede a changed decision rather than silently erasing its rationale. Do not create standalone ADR files, install ADR tooling, open PRs, notify reviewers or generate tickets unless separately authorized.

Review alternatives against real constraints, name unresolved tradeoffs and identify dependent work. A mandatory reviewer count, arbitrary page cap or fixed approval ceremony is not a universal requirement. Reuse existing authorization; ask only for material unresolved decisions.
