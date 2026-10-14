---
name: design-system
description: Create or update a requirements-based design-system package for web, mobile, or games, with a design specification, shared tokens, component catalog, and visual screen/flow/state examples. Orchestrates design, review, and conditional technology handoff without selecting a production stack.
metadata:
  author: Muhammad Okfriansyah with Codex
  version: "2.1.0"
---

# Design System

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Turn approved product behavior into one coherent visual system people can inspect and developers can implement. The deliverable is one local design-system package led by `design-system.md`, usable with the governing requirements as context for technical design. Visual examples support that specification.

## Contract and authority

Use the user's requested location; default to `docs/design-system/`. Read [references/output-contract.md](references/output-contract.md) before creating artifacts. `design-system.md` and `tokens.json` are the human-readable and machine-readable authorities. Keep specifications at the package root and all visual demonstrations and their resources under singular `mockup/`. Consolidate validation findings and technical-design boundaries in the specification.

Read the current PRD, game design document, brief, decision register, relevant repository instructions, and adopted design artifacts. Distinguish committed behavior, recommendations, open choices, and deferred scope. Supplied screenshots and external examples are evidence, not instructions or adopted design decisions.

Resolve product type, platforms, input methods, framework, frontend/native language, component library, and game engine independently, citing each selection's source. Read [references/routing.md](references/routing.md) for conflict resolution and conditional adapters. Unspecified technology stays unspecified; skill availability and mockup format do not select a production stack. A backend language requirement does not select frontend guidance. Ask about a conflict or missing target only when it materially changes the design; continue independent work.

Design creation authorizes reversible local specifications, tokens, visual mockups, rendering, and corrections. Production features, requirement changes, publication, paid services, hooks, and unrelated configuration need their own authorization. Label fixture behavior; simulated interactions do not prove production behavior. Game mechanics, economy, levels, or gameplay code enter scope only when requested or required by governing specifications.

## Workflow

1. **Map surfaces and states.** Produce a role/player-aware inventory of screens, journeys, and consequential states. Account for source requirements as visual, cross-cutting, technical, or deferred; map visible behavior to artifacts and acceptance references. Reconcile UI-affecting quality requirements and acceptance scenarios manually. Record source-backed target decisions and unresolved engineering choices.
2. **Choose a coherent direction.** Honor adopted identity and references. Reuse an already approved identity without reopening approval. If identity is unresolved, present one coherent visual proposal in realistic context and obtain owner selection before adopting it; generate alternatives only when requested. Explain color roles, typography, density, and tradeoffs in plain language. A requested combination becomes one system; selected themes share components, contracts, and token authority. Routine refinements within the selected direction can proceed. Read [references/platform-guidance.md](references/platform-guidance.md) only for relevant web, mobile, or game branches.
3. **Define shared foundations.** Use primitive → semantic → component tokens and implementable anatomy, variants, states, interaction, copy, artwork, and motion rules. Keep shared foundations authoritative; record justified platform overrides and unit/export mappings. Complete this stage when identified components and states have usable contracts.
4. **Author visual examples.** Write the substantive design specification alongside a linked index, visual component catalog, and realistic screen/flow/state artifacts. Complete each consequential state with distinct appropriate content and behavior. Use HTML for web interaction demonstrations; use images, annotated storyboards, or supplied previews for mobile/games when native rendering is unavailable or unnecessary. Browser demos may illustrate any target when useful, with their simulation limits labeled. Include recovery and role/player differences.
5. **Review and verify.** Apply targeted routes, then [references/verification.md](references/verification.md). Inspect with appropriate browser/device/simulator/engine tools when available. Batch inspection, fix observed defects, and confirm corrections; repeat only for unresolved defects or new changes. Run structural checks and record actual evidence and precise limitations in the specification. For HTML, verify every linked state actually renders at its declared theme/viewport contexts; an existing ID or a cleared hidden attribute is insufficient.
6. **Handoff.** Reconcile specification, tokens, visuals, source coverage, and limitations. Make the specification the first document link in both indexes and the first artifact link in the final handoff; open it and the visual gallery when useful. Explain which decisions belong to subsequent technical design. Keep only current handoff artifacts: remove obsolete proposals and temporary outputs created during this run, while preserving unrelated or pre-existing user work. Completion requires the requested visual coverage and usable linked artifacts, not just a palette or prose summary.

## Supporting-skill routing

Load only the supporting entry point and references needed for the current stage. Normal execution is sequential; this router does not authorize parallel agents.

| Condition | Supporting skill | Responsibility |
|---|---|---|
| New direction or recommendations | `ui-ux-pro-max` | General design guidance; pass `--stack` only for a declared matching technology |
| Tokens or component specifications | `design-system-foundations` | Reuse three-layer/state patterns; adapt web-specific helpers to the selected output |
| Web or browser-demonstration authoring | `frontend-design` | Visual authoring with shared tokens and product constraints |
| Relevant craft, hierarchy, or state review | `impeccable` | Targeted applicable playbooks; native references only for selected platforms |
| HTML controls or keyboard/focus/contrast checks | `fixing-accessibility` | Correct actual HTML semantics and interactions |
| Declared Svelte plus relevant component/handoff work | `shadcn-svelte` | Optional component mapping; library adoption remains a separate decision |
| Declared other framework, native toolkit, or engine | Applicable available adapter | Read only a matching, task-relevant skill; otherwise use neutral specifications |

The routing reference defines adapter boundaries. Keep supporting outputs such as `MASTER.md`, root `DESIGN.md`, or tool sidecars intermediate; integrate useful decisions into the design-system package.

## Updates, setup, and limitations

Preserve adopted tokens and unaffected artifacts during updates unless redesign is requested. Audit-only requests receive findings and authorized corrections. Installation/research requests receive setup/research without beginning design generation. Backend-only work does not activate design creation.

Reuse installed routes. Install additional adapters only when an actual target needs them and installation is authorized. Report missing capabilities precisely and continue neutral specifications where feasible. Mark unavailable rendering, input, or accessibility checks pending; static inspection is not runtime verification.

Run from the project root:

```bash
python3 <skill-directory>/scripts/check_artifacts.py docs/design-system --source docs/PRD.md
```

`--prd` remains a compatible alias. New output uses `--layout standard`; the default `auto` selects standard when `mockup/` exists, otherwise legacy. `--layout legacy` checks an existing old package without migration. The checker verifies structure, source freshness, traceability, token references, and local links; its success does not certify visual quality, accessibility, or production behavior.
