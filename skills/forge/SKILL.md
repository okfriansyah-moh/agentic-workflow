---
name: forge
description: "Execute an approved multi-task plan through native subagents, claimed worktrees and independently verified receipts."
metadata:
  version: "1.0.0"
---

# forge

Resolve the selected bundle from the repository .ai/config.json: its bundle value is relative to the .ai directory. Open each required skills/<name>/SKILL.md directly under that bundle, even when a same-named global skill is already available or loaded. Resolve supporting resources relative to the selected skill file. Use the selected global bundle only when the repository has no .ai/config.json; resolve its bundle value relative to the global configuration directory. Name-based discovery never overrides the repository pin.

Read the root/group/task plan directly and index it with the bundled helper. Preserve IDs and source references. Reuse the existing approved plan; a request to implement it already supplies execution authorization. Distinguish readiness from prerequisites that actually exist at runtime.

Forge is the one parent coordinator. It dispatches native host subagents and never another Forge. Default to three concurrent workers, reduced by host capacity; a single bounded fix can run in one worker. Inherit host model settings. Reuse workers for related tasks/corrections and keep review independent from implementation.

Determine dependency-eligible tasks and claim files/directories/resources before starting isolated writing worktrees from the recorded integration revision. Serialize shared contracts, schema/migration allocation, locks, generators and build configuration. Use the worker prompt for exact task/source IDs, allowed paths, base revision, cases and required checks.

Each worker implements only its brief, returns captured checks and changed-file evidence, and leaves task execution-field edits to Forge. Review-verify checks source compliance and actual results; send actionable findings to the same worker. Keep one findings ledger for quality, security, accessibility and anti-slop. After two failed correction rounds stop that work group and retain branches/receipts with the exact next action.

The integrator merges accepted commits in dependency order under an exclusive integration claim, preserving valid contributions, then checks combined behavior. Only its verified feature evidence establishes integrated acceptance. Literal Git union merging is unsuitable for application code.

On resume reconcile task files, Git tips/base ancestry, claims and receipt input fingerprints. Stale successful records are not completion. Forge alone updates task execution status/evidence fields; Change PRD, technical design, design-system and ATDD content only when the request or explicit standing authorization covers those changes.

Continue through task-delivery when its actions are already authorized and a remote exists. Missing remote/trust/tools is a precise limitation, not permission to fabricate success or bypass checks. Return task statuses, checks, branch/revision, evidence, findings and recovery action.

Honor explicit standing authorization within its stated scope, including covered edits, installs, commands, worktrees, delegation, checks, commits and delivery. Continue covered actions without per-action approval. Use the request and project conventions for routine decisions; ask only for essential missing information or actions outside that authorization. Standing authorization never turns failed required checks into a pass or grants unrelated work.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

For actual helper commands, claim/check contracts and evidence proof fields, read [coordination and evidence contracts](../../docs/COORDINATION.md) before writing a brief or receipt. Use the documented structured objects and preserve captured argv/test-report requirements; do not infer a schema from narrative examples.
