---
name: task-delivery
description: "Deliver verified scoped changes through commits and an authorized draft pull request when the remote is configured."
metadata:
  version: "1.0.0"
---

# task-delivery

Read the task completion evidence, required gate results, independent review and integrated feature evidence. Confirm that they match the current implementation inputs and branch. Failed mandatory checks, stale evidence or unresolved required findings block delivery.

Inspect Git status and stage only authorized task-related files. Preserve unrelated user changes and secrets. Use the repository's commit convention and a message describing the resulting behavior. Capture the final reviewed revision; a new implementation change requires affected checks/review before publishing.

If the user has already authorized push and draft PR creation for this workflow, proceed without another approval loop once a valid remote exists. Confirm the intended remote/base from configuration and project context. If no remote exists, retain local commits/evidence and report the missing URL. Do not invent a destination.

Create or update one draft PR for the integration branch using the host's supported tools or CLI. Include concrete behavior, verified revision, actual checks, evidence links and known limitations. Use pr for prose when useful; do not predict Sonar or reviewer outcomes. Attach the PR to the current chat when the host provides that action.

PR merge, deployment, production mutations and messages to external teams remain separately authorized. Return branch/revision, PR URL if created, evidence and any exact blocked action. Avoid global add/force-push or replacing unrelated history.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
