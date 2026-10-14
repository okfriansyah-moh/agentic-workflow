---
name: worktree-integration
description: "Coordinate concurrent repository writers with claimed paths, isolated worktrees and verified semantic integration."
metadata:
  version: "1.0.0"
---

# worktree-integration

Use the project-local CLI and the recorded integration revision. Read the task brief, dependency order and Git state before accepting a claim. All participating chats share the registry in Git's common metadata directory.

1. Claim allowed files or directories and resources before dispatch: ports, databases, output directories, schema ownership, dependency locks, build configuration, generators and migration allocation. Directory claims overlap their descendants. Shared write surfaces require one owner or explicit serialization.
2. Create each writing lane from the recorded integration revision in an isolated worktree. Record the worker, branch, base, task IDs and claims. A native host's default worktree base must be checked rather than assumed. Keep uncommitted user work in its original checkout.
3. Use separate ports/databases/output roots per lane. Read-only review may inspect the worker revision without a writing claim. Reuse a worker for related corrections; update its brief when ownership changes.
4. Accept only commits with applicable gate receipts and independent review. One integrator holds the integration claim and merges accepted commits in dependency order. Preserve valid behavior from all lanes; resolve conflicts against shared contracts and acceptance cases. Git's literal union merge driver is unsuitable for application code.
5. Check the combined tree and all affected integration cases. Worker success alone does not establish feature acceptance. Return newly found defects to the owning worker or scoped integration correction lane.
6. After two failed correction rounds, retain branches, worktrees, receipts and claims needed for recovery, then report the exact blocking condition and next action. On resume reconcile task files, branch tips, base ancestry, claims and input fingerprints before reusing evidence.
7. Clean up only owned worktrees after their contribution is integrated and preserved. Inspect dirty/untracked state; never force-reset or delete another lane's work.

Return branch/base/head, claim IDs, integrated commits, conflict decisions, combined checks, remaining work and recovery paths.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

For actual helper commands, claim/check contracts and evidence proof fields, read [coordination and evidence contracts](../../docs/COORDINATION.md) before writing a brief or receipt. Use the documented structured objects and preserve captured argv/test-report requirements; do not infer a schema from narrative examples.
