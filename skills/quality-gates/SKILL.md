---
name: quality-gates
description: "Run configured quality and security checks with revision-bound results; diagnose failed, unavailable or inapplicable gates."
metadata:
  version: "1.0.0"
---

Resolve the pinned bundle from .ai/config.json and read [selection delivery](../../docs/DELIVERY.md). That policy governs review timing, quality gates, recovery budgets and literal delivery status. Reuse it while unchanged.

# quality-gates

The project profile and shared gate registry define applicable checks for hooks, explicit verification and CI. Read their actual argv and working directory; plan prose is never executable shell input. A hook is an early signal, not proof that every required completion check ran.

Use the shared runner’s affected-component and consumer selection from the agreed baseline. Documentation-only work uses applicable document checks; shared contracts/build inputs retain necessary broader checks. Run each required command once for valid inputs, deduplicate identical commands and rerun affected checks after corrections. Hooks provide early feedback within the same procedure. Report command exit codes and raw artifact paths. Unsupported stacks or absent executables are unavailable, not successful.

Explicit no-test limits prohibit added/executed tests and substitute browser trials, including hooks. Record omitted proof as pending; source review or authorized draft publication cannot turn it into a pass.

Use the configured project policy; the bundled initial profile is 50 nonblank/noncomment lines per function, cyclomatic complexity 10, nesting 3 and 80% changed executable-line coverage per component. Use the profile's language-aware tooling and document exclusions. Generated code/data are excluded. Changes with no executable lines are not applicable; an empty selection for applicable behavior fails. A whole-repository coverage percentage cannot replace changed-line coverage.

Use configured component tools, such as Kotlin static/build/coverage tools or Svelte/Node type/lint/behavior tools, only where selected and applicable. Verify that the configured reports correspond to the tested revision and selected cases.

Use pinned local Semgrep rules, Gitleaks and OSV-Scanner over supported inventories. Record scan scope and engine limits; Semgrep CE findings do not establish complete cross-file security proof. Sonar analysis is optional until configured mandatory, and must refer to the reviewed revision. An unavailable or stale required Sonar result blocks completion.

Required failures and unresolved required findings block completion. An exception needs rule, narrow scope, rationale, owner and approval; an agent cannot relax a threshold to obtain a pass. Report passed, failed, blocked and not-applicable separately, along with actual inputs and environment.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
