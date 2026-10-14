# Worker brief contract

Resolve the selected bundle from the repository .ai/config.json: its bundle value is relative to the .ai directory. Open each required skills/<name>/SKILL.md directly under that bundle, even when a same-named global skill is already available or loaded. Resolve supporting resources relative to the selected skill file. Use the selected global bundle only when the repository has no .ai/config.json; resolve its bundle value relative to the global configuration directory. Name-based discovery never overrides the repository pin.

Forge supplies task IDs, goal, source document paths/sections, group integration owner, repository/worktree, branch and base revision, allowed paths, path/resource claim IDs, acceptance IDs, test strategy, required checks and receipt output location. Include dependencies and prior review findings when relevant. A worker reads only enough source context to implement correctly; compact briefs never justify skipping required contracts.

Implement this bounded task using task-implement and applicable domain skills. Validate the actual checkout and claims before writes. Preserve unrelated changes. Capture changed files, tested revision/input fingerprint, commands with exit codes, selected cases/counts, proof boundaries, environment and artifact hashes. Return the receipt plus unresolved findings. Leave task execution fields to Forge. Do not spawn a second orchestration loop.

Read [coordination and evidence contracts](../docs/COORDINATION.md) for the current structured helper inputs and receipt/evidence requirements. Required checks are full command contracts, not names alone. Keep briefs consistent with that shared definition.
