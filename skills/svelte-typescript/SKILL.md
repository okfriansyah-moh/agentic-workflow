---
name: svelte-typescript
description: "Implement approved Svelte/TypeScript screens and states with typed data flow, responsive behavior and accessibility."
metadata:
  version: "1.0.0"
---

# svelte-typescript

Start from the adopted design-system tokens, component contracts, PRD states and selected Svelte version. Preserve the chosen architecture and UI library. Recommendation skills may refine an unresolved detail but cannot replace those decisions.

Trace route inputs, server/client responsibilities, data loading and mutations. Parse untrusted values at the boundary; TypeScript types alone do not validate network data. Model loading, empty, error, permission, success and pending states that the task actually requires. Keep component state ownership clear and avoid derived-state synchronization loops.

Use version-appropriate Svelte reactivity and lifecycle. Clean up subscriptions, observers and timers; avoid global mutable request state in server code. Render user content through safe APIs and review any raw HTML boundary. Keep transport and persistence details outside presentational components where project boundaries call for adapters.

Use semantic controls, explicit labels, keyboard interactions and visible focus. Match adopted tokens and layouts at agreed sizes and responsive rules. Inspect relevant zoom, long-text, reduced-motion, error and theme behavior selected by the change. Follow approved composition exactly. Open actual references and compare a representative state before spreading shared styling. Load focused visual/accessibility guidance only for a concern the change introduces.

Run the agreed affected checks using existing Svelte/TypeScript, lint, Vitest or browser commands as applicable; this list does not require every tool. Explicit no-test limits prohibit added/executed tests and substitute browser trials, including hooks. Keep omitted proof pending. Preserve assertion IDs and inspect the rendered result; a component test or screenshot of a mock is not end-to-end proof. Test races or stale responses where the changed data flow can overlap.

Return state/case coverage, changed files, actual browser observations, checks and pending boundaries. Leave production requirement/design changes to their authorized document workflow.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
