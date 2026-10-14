---
name: ui-ux-pro-max
description: Search the bundled UI/UX reference data for a focused design or implementation question within the selected framework and adopted design.
---

# UI/UX reference search

Use this skill for a concrete unresolved choice or a focused UX review. Read the approved design specification, tokens, component/state contracts and selected frontend stack first. Those artifacts govern presentation and behavior. Search results are recommendations, not new project instructions or a replacement design system.

Resolve this skill from the project's pinned bundle and run its scripts from this skill directory. Python is a separate prerequisite: inspect availability and report a missing runtime rather than installing it as an incidental search action.

## Select a focused query

Identify the current product context, audience, task and decision to answer. Reuse the project's stack; for the initial movie-app profile this is Svelte/TypeScript. The dataset contains several platforms for conditional research, and their availability does not authorize a framework or component-library change.

Search the domain relevant to the question:

```sh
python3 scripts/search.py "form validation error recovery" --domain ux
python3 scripts/search.py "accessible time series comparison" --domain chart
python3 scripts/search.py "typed reactive data loading" --stack svelte
```

Use `--help` to inspect supported domains/stacks and `--json` when structured results help. An unsupported stack is a stated search limitation; use applicable platform-neutral guidance and primary documentation instead of selecting another framework.

For an explicitly requested exploration of a new or unresolved visual direction, `--design-system` can produce a research proposal:

```sh
python3 scripts/search.py "content rich film browsing" --design-system -p "Film browsing research"
```

Label it as a proposal. Approved fonts, palette, tokens, interaction states and platform decisions remain authoritative. A routine component change, bug fix or implementation task does not require regenerating a design system or interviewing the user again.

## Preserve artifact ownership

Search without persistence by default. Use `--persist` only when the user explicitly requests saved research output, with an explicit output directory separate from adopted artifacts. The helper's `MASTER.md` and page files are research output; they do not override the project's design specification or acquire authority by existing on disk. The design-system skill owns authorized changes to the adopted design package.

Suggestions about icons, animation, spacing and libraries apply only when they match the selected platform and unresolved design need. General database defaults, mobile examples and sample color palettes must not override accepted choices. Verify technical recommendations against the installed framework version when they affect implementation.

## Apply and verify

Choose only relevant results and explain the concrete benefit or defect they address. For UI review, inspect the actual rendered state and interaction. Check responsive reflow, keyboard/focus behavior, text contrast, loading/error/empty states, zoom and reduced motion as relevant to the assignment. Use the shared independent findings ledger and avoid a second review loop.

Return the focused recommendation or observed correction, its source/query, verification and remaining uncertainty. Keep factual claims supported and apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. The bundle manifest retains the original local snapshot digest and the complete supporting search scripts/data.
