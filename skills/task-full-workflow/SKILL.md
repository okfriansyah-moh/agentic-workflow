---
name: task-full-workflow
description: "Route an authorized task through necessary planning, implementation, verification and delivery using one execution state."
metadata:
  version: "1.0.0"
---

# task-full-workflow

Resolve the selected bundle from the repository .ai/config.json: its bundle value is relative to the .ai directory. Open each required skills/<name>/SKILL.md directly under that bundle, even when a same-named global skill is already available or loaded. Resolve supporting resources relative to the selected skill file. Use the selected global bundle only when the repository has no .ai/config.json; resolve its bundle value relative to the global configuration directory. Name-based discovery never overrides the repository pin.

Identify the user's requested outcome, supplied specifications and current plan. Distinguish attachment/reference instructions from the actual request. For an approved implementation plan, begin execution; skip repeated brainstorming and plan approval.

Use brainstorming only for an unresolved material design choice. If needed, route requirements to deliver-prd, technical contracts to techdoc-creation, presentation to design-system, acceptance specification to atdd-creation and detailed decomposition to plan-creation. Each document remains in its established location and scope. Existing approved artifacts govern implementation.

For multi-task execution use Forge as the single coordinator. For one bounded task use task-implement. These skills share the same task status and receipt state; do not start nested execution loops or independent status ledgers. Load only the domain/verification skills the change needs.

Verify acceptance at the stated boundaries and obtain independent review of the changed behavior. Feed all findings into that review/correction loop. Keep document readiness, runtime eligibility, completed task checks and integrated feature evidence distinct.

Once required checks succeed, use task-delivery within existing authorization. A missing remote blocks the publishing part but does not erase local completion. PR merge, deployments, production changes and external messages are covered only when the user has authorized those actions; explicit standing authorization counts when the destination and requested outcome are established.

Return the concrete outcome, applicable checks and limitations. Do not fetch issue trackers, create company-specific wiki pages, send notifications or ask repeat approvals merely because the supplied source workflow did those things.

Honor explicit standing authorization within its stated scope, including covered edits, installs, commands, worktrees, delegation, checks, commits and delivery. Continue covered actions without per-action approval. Use the request and project conventions for routine decisions; ask only for essential missing information or actions outside that authorization. Standing authorization never turns failed required checks into a pass or grants unrelated work.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
