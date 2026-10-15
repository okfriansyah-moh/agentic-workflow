---
name: brainstorming
description: Explore substantial feature or architecture choices and turn an idea into an approved design and implementation plan. Use for brainstorming or unresolved design decisions; skip routine edits and already-approved implementation.
metadata:
  source: https://github.com/okfriansyah-moh/a2a-brainstormer/blob/main/.ai/skills/brainstorming/SKILL.md
  adapted-for: Muhammad Okfriansyah
---

# Brainstorming: ideas into designs

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Use this for an explicitly requested brainstorming session or a substantial feature or architecture decision with unresolved design choices. A typo fix, routine edit, or already specified implementation does not need a new design ceremony.

1. Explore the relevant project files, instructions, current behavior, and existing decisions. Look up discoverable facts; ask the user about goals and tradeoffs.
2. Clarify the desired outcome, audience, scope, constraints, and success criteria. Ask a small group of independent questions (normally one to three) with a recommendation for each. Ask dependent questions only after their prerequisites are settled. Use the host’s question tool when suitable.
3. Compare meaningful approaches, usually two or three when real alternatives exist. Explain the recommended choice and its tradeoffs. Avoid manufactured alternatives and unnecessary features.
4. Present one consolidated design, scaled to the change: responsibilities, relevant inputs and outputs, data flow, failure behavior, and acceptance checks. Derive stack and architecture constraints from this project; never import another project’s rules.
5. Check scope, contradictions, missing decisions, and testability. Prior approval, an instruction to implement the design, or explicit standing authorization to resolve design choices satisfies the approval checkpoint. Within that authorization, choose from the request and project conventions and continue. Otherwise ask for design approval once; reopen only a material choice outside existing authorization. No section-by-section or second written-spec approval.
6. Once approved, provide a decision-complete implementation plan with dependencies, relevant interfaces, verification, and any required migration. This handoff is self-contained; it needs no `writing-plans` skill. In Plan mode, stop at the plan. Outside Plan mode, continue implementation if already requested; otherwise finish the requested design work.

Save a design only when requested or the project workflow calls for it, using its established location. Do not automatically commit, create issues, or publish it. The default deliverable is the design and implementation plan in chat.

Matt’s `$grilling` and `$grill-with-docs` remain separate workflows. This skill borrows dependency-aware questions, not their stronger interview requirements; do not load them just to run these steps.

Adapted for Muhammad Okfriansyah from the linked a2a-brainstormer brainstorming skill and Matt Pocock’s grilling techniques. The packaged source digest and adaptation record are in the bundle manifest and provenance document.
