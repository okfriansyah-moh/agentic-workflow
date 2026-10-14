---
name: dependency-analysis
description: "Map component dependencies and identify cycles, coupling, or safe execution order. Use for architectural dependency analysis and parallel-work planning."
---

# Dependency analysis

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Choose the graph being analyzed: source imports, runtime calls, build packages, schema consumers, or task prerequisites. These are different graphs; a source import alone does not prove a runtime cycle.

1. Discover boundaries and graph extraction tools for each component. Include generated interfaces, dynamic loading, cross-language protocols, and build dependencies where relevant. Label inferred edges and analysis gaps.
2. Identify cycles and high fan-in/fan-out nodes, then assess their actual consequences against the project architecture. Metrics are indicators, not universal numeric pass/fail rules.
3. Separate intentional shared abstractions from accidental dependencies on internals. Propose the smallest change that fixes the observed problem, using [codebase-design](../codebase-design/SKILL.md) where a new seam is needed.
4. For execution ordering, produce prerequisites and disjoint write sets. Shared files, migrations, or interface changes need sequencing even when code modules are independent.

Deliver a concise graph or table with evidence, impacted consumers, proposed ordering, and checks for changed boundaries. Preserve legitimate public dependencies rather than forcing every module to be a leaf.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

