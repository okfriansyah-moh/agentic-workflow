---
name: antislop-code
description: "Review comment hygiene while preserving necessary explanations and leaving executable code quality to its owning skills."
metadata:
  version: "1.0.0"
---

# antislop-code

Apply this skill only to comments and documentation adjacent to code; code-review/coding-standards own implementation correctness and maintainability. A comment review does not authorize unrelated executable changes.

Remove comments that merely restate the next line, decorative separators, empty labels, redundant step narration and vague promises of future improvement. Retain comments that explain domain rules, concurrency constraints, protocols, security decisions, non-obvious algorithms, workarounds or public API behavior.

Keep language precise and proportionate to the constraint. A short comment is often enough, but necessary legal notices, subtle invariants and externally required documentation may need more detail. Do not shorten meaningful explanation merely to satisfy a line-count aesthetic.

Preserve license/copyright notices, tool directives, annotations and documentation with machine consumers. Check whether a comment-like form affects execution before editing it. A TODO should name an actionable task and useful context; vague speculative work should not remain as filler.

When asked for comment-only cleanup, keep tokens, identifiers, formatting and behavior outside comments unchanged and inspect the diff. If the comment reveals a code defect, report it to the code reviewer or implementer within the task scope. Feed findings into the existing ledger and run required project checks for the actual changes.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
