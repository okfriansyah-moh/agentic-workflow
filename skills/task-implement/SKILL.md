---
name: task-implement
description: "Implement one bounded approved task, apply its selected test strategy and return a verifiable receipt."
metadata:
  version: "1.0.0"
---

# task-implement

Resolve the selected bundle from the repository .ai/config.json: its bundle value is relative to the .ai directory. Open each required skills/<name>/SKILL.md directly under that bundle, even when a same-named global skill is already available or loaded. Resolve supporting resources relative to the selected skill file. Use the selected global bundle only when the repository has no .ai/config.json; resolve its bundle value relative to the global configuration directory. Name-based discovery never overrides the repository pin.

Read the assigned task, cited source sections and existing nearby code. Verify repository/worktree, base revision, ownership claims, allowed paths, acceptance cases and required checks. If the brief conflicts with the actual checkout or another writer's claim, report it before writing.

Follow the task's test strategy: test-first uses the agreed public seams in tdd, alongside adds meaningful behavior coverage with implementation, and checks-only applies to work without applicable executable behavior. Reuse approved test boundaries; do not reopen approval. Load relevant stack skills and actual project conventions rather than generic frameworks.

Implement the smallest complete behavior within scope. Keep contracts and naming aligned with the task, preserve unrelated changes and coordinate shared-file edits through Forge. Missing facts that materially change behavior go to the parent; ordinary implementation decisions use the approved design and existing examples.

Run required lint/type/build/tests and inspect the diff. Self-review correctness, failure paths, security-sensitive boundaries, dependency cycles, changed-line coverage and the relevant design/anti-slop criteria. Self-review does not replace the independent reviewer.

Capture commands/exit codes through the shared helper, selected case counts, proof boundaries, actual changed paths, environment and revision/input fingerprint. State missing or unavailable checks honestly. Do not mark task execution fields done; Forge owns that update after independent review.

On corrections reuse the current task/worktree, address the specific findings and rerun affected checks. Return scoped commits or uncommitted state as requested, receipt paths, completed acceptance IDs, unresolved findings and next action. No nested orchestration or external publication originates from this worker.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

For actual helper commands, claim/check contracts and evidence proof fields, read [coordination and evidence contracts](../../docs/COORDINATION.md) before writing a brief or receipt. Use the documented structured objects and preserve captured argv/test-report requirements; do not infer a schema from narrative examples.
