---
name: code-review
description: 'Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo''s documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Evaluates both axes and reports evidence-backed findings. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".'
---

Resolve the pinned bundle from .ai/config.json and read [selection delivery](../../docs/DELIVERY.md). That policy governs review timing, quality gates, recovery budgets and literal delivery status. Reuse it while unchanged.

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

An independent review-verify agent evaluates both axes in one review. For a large change the coordinator may allocate separate reviewers within the same worker budget; reviewers do not start nested orchestration.

Use the supplied task, local specification, or authorized issue source. A tracker installation is optional.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). Reuse the base revision in the worker brief or recorded integration revision; ask only if no relevant base can be resolved.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref blocks review. An empty requested comparison is reported as no changes to review, without creating reviewers.

### 2. Identify the spec source

Use the task and source references supplied by the coordinator or user first. Read the accepted local specification and relevant acceptance cases. If no source was supplied, inspect project documentation and commit references for the originating requirement; fetch an external issue only through an available authorized tool. No tracker-specific setup or missing tracker document is a prerequisite.

If the behavior cannot be assessed without a missing source, report that exact gap. Continue the standards review and label specification verification unavailable. The existing independent reviewer owns this decision and both review axes; do not start a second reviewer or orchestration loop.

### 3. Identify the standards sources

Search the repo for every file that documents how code should be written. When `CODING_STANDARDS.md` or `CONTRIBUTING.md` exists, it must be on the list.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Evaluate both axes

Inspect changed files and the relevant callers or contracts needed to test each concern. For standards, cite the rule and concrete violation; treat smell heuristics as judgment, not automatic failure. For specification, map each assigned acceptance criterion to implementation and actual evidence, reporting missing behavior and unapproved scope.

Run the applicable checks at the reviewed revision. Report unavailable tools and environment failures separately from code defects. Preserve the independent reviewer identity and findings ledger; return actionable findings to the existing coordinator for correction.

### 5. Aggregate

Keep the Standards and Spec labels in one findings ledger. Deduplicate the same defect while preserving both source obligations. Report severity, file or case reference, evidence, and required correction.

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.


## Codex execution

The parent coordinator assigns the independent reviewer. This reviewer evaluates the scoped change and returns findings to that parent; it does not dispatch more agents. If independent review is unavailable, record that limitation rather than presenting self-review as independent. Respect the current mode and authorized scope; installing this skill does not execute a review.
