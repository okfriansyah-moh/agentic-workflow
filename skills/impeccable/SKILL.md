---
name: impeccable
description: Review and refine existing frontend designs using Impeccable visual craft, hierarchy, responsive, state, and accessibility criteria. Use as a targeted review companion for a chosen design direction or PRD-based design-system package.
license: Apache-2.0
metadata:
  author: Paul Bakaus and contributors; Codex adaptation for Muhammad Okfriansyah
  upstream_version: "4.5.2"
  source_commit: "d631a8827f99414d2b6daba4ef08b7f8701751d7"
  local_version: "1.0.0"
---

# Impeccable review

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Apply the upstream design-review criteria to existing UI while preserving the user's selected direction, product behavior and scope. For a PRD-based design-system package, use its design specification and shared tokens as context; for ordinary UI work, inspect existing project design/context documents when present.

This local entry point adapts Impeccable's reference material for direct file and browser tools. It does not activate upstream binary launchers, detector/live-overlay services, native agent configuration, edit hooks, root PRODUCT.md/DESIGN.md generation, forced independent-assessment workflows, or permission questions for routine local review. Original packaged source is retained in the installation baseline recorded by provenance.json. These tooling/workflow branches in retained references are inactive; read their design criteria only through the routes below. Report manual/heuristic review as such rather than claiming an unavailable detector result or full accessibility certification.

## Route by the requested review

- For visual hierarchy, information architecture, product fit and usability, read the **Assessment A: Design Review**, **Cognitive Load Assessment**, and **Heuristics Scoring Guide** sections of [reference/critique.md](reference/critique.md). Use applicable criteria; mark heuristics that do not apply as such. The surrounding upstream orchestration/reporting workflow is outside this adapter.
- For markup, theming, responsive behavior, motion and performance issues, read the **Diagnostic Scan** criteria in [reference/audit.md](reference/audit.md). Record concrete evidence rather than unsupported numerical compliance claims.
- For missing/loading/error/validation/conflict outcomes, read [reference/harden.md](reference/harden.md) for relevant state-design guidance; implement only states within the approved product scope.
- Before an authorized visual correction, read [reference/craft-floor.md](reference/craft-floor.md). For task-oriented applications, use applicable Operate guidance in [reference/operate.md](reference/operate.md). The user's adopted fonts, palette and other choices override upstream aesthetic defaults.

## Execution and completion

Inspect the requested files and real rendered surfaces using available tools. Review consequential states and desktop/mobile together. Report the most useful evidence-backed issues, then make corrections when the request authorizes them. Preserve existing content and unrelated UI.

Use one batched inspection, correct observed issues, then one confirmation pass. Continue only for unresolved defects or new changes. If browser tools are unavailable, complete source review and explicitly mark visual/keyboard checks pending. Completion requires the requested review/corrections and honest verification notes; no mandatory subagent or external-service step is introduced by this skill.
