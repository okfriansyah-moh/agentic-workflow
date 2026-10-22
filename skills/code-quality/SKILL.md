---
name: code-quality
description: "Assess maintainability and correctness of changed code against project conventions. Use for a focused quality pass; use code-review for a full branch or PR review."
---

# Code quality

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Read [coding-standards](../coding-standards/SKILL.md) for the convention source. Review the actual diff and its callers, not every unrelated file.

- Check whether each changed path implements the requirement, handles reachable errors, releases resources, and preserves public compatibility.
- Trace ownership of mutable state and side effects. Look for hidden dependencies, duplicated business rules, races, and abstractions that make behavior harder to test.
- Apply the [reuse and cleanup policy](../../docs/DELIVERY.md#reuse-and-evidence-based-cleanup) to shared logic and deletions, checking actual consumers and affected behavior.
- Check logs and errors for useful context without disclosing secrets. Judge output according to the application interface.
- Verify through observable behavior and relevant configured checks. A formatter pass does not establish correctness, and a style preference is not a defect.

Report actionable findings with location, trigger, impact, and a concrete correction. Separate required fixes from optional improvements and identify checks not run. When [code-review](../code-review/SKILL.md) is already active, contribute these findings to it rather than starting a competing approval or review cycle.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

