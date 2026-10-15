# Portable agent workflow

Version 1.1.1 provides eight native agent roles, 74 skills, worktree ownership, command receipts, quality gates and acceptance-evidence checks. Start work in your existing Codex, Claude Code, Copilot or Cursor chat. Python helpers coordinate files and verification; they do not launch a separate agent service.

Use [the skill catalog](docs/SKILLS.md) to see every installed skill and its purpose. [Installation](docs/INSTALLATION.md), [host setup](docs/HOSTS.md), [coordination](docs/COORDINATION.md), [quality gates](docs/GATES.md) and [release 1.1 verification](docs/VERIFICATION-1.1.md) describe the operational details.

## Install and inspect

Python 3.11 or newer and Git are required. macOS and Linux are supported. From this source checkout:

```sh
python3 scripts/agent-workflow install --global
python3 scripts/agent-workflow install --repo /path/to/project --profile movie-app
python3 scripts/agent-workflow doctor --global
python3 scripts/agent-workflow doctor --repo /path/to/project
```

Use the `general` profile for another stack. Configure its actual checks before implementation; unsupported language checks are reported as blocked. The installer does not install application dependencies, scanners, browsers or accounts. It preserves existing user content and reports conflicts. Host trust and reload requirements remain visible.

Each project contains its selected version at `.ai/bundles/1.1.1/`, native role adapters, skill discovery links, and `.ai/bin/agent-workflow`. Commit these together. Links point inside the project; no source-repository path is needed after a clone. A project pin governs its workflow even when the global bundle changes.

```sh
python3 .ai/bin/agent-workflow doctor --repo .
python3 .ai/bin/agent-workflow task-index --plan docs/06-PLAN.md
python3 .ai/bin/agent-workflow gate --repo . --stage integration --base BASE_COMMIT
python3 .ai/bin/agent-workflow resume --repo .
```

## Start and resume in a chat

To execute a bounded task: “Use task-full-workflow to implement T001 from docs/06-PLAN.md. Reuse the approved documents and its test strategy. Use the installed Forge role for coordination, then independent review and evidence.” Native role profiles use the `aw-` prefix, such as `aw-forge` and `aw-review-verify`.

To execute a task group: “Use Forge to implement the eligible tasks in G02. Claim isolated lanes from the recorded integration revision, use at most three workers, and integrate only accepted receipts.” Reduce worker count to host capacity. Forge never delegates to another Forge.

To resume: “Resume the retained workflow. Reconcile task files, Git revisions, claims, receipts and evidence before continuing. Reuse valid work and report the precise next action for stale or blocked work.”

These are usage examples, not instructions to dispatch movie-app tasks during installation. The installation indexes all 46 existing tasks without starting them. PRD, technical design, design system and ATDD remain unchanged. A draft PR requires a configured remote. Merge, deployment, production changes and external messages require authorization covering those actions; explicit standing authorization counts within the requested outcome and established destination.

## Maintain the installation

```sh
python3 scripts/agent-workflow update --global
python3 scripts/agent-workflow update --repo /path/to/project
python3 scripts/agent-workflow uninstall --repo /path/to/project
python3 scripts/agent-workflow uninstall --global
```

Updates are explicit. A locally edited managed file is retained and reported; inspect it before choosing how to reconcile it. Backups support rollback, and uninstall removes only unchanged managed content. Existing unrelated and host-managed skills remain host-owned.

## Develop this package

```sh
python3 -m unittest discover -s tests -v
```

The optional external-tool fixtures have a committed npm lock and run separately:

```sh
cd tests/fixtures/web
npm ci --ignore-scripts --include=optional
cd ../../..
python3 scripts/check-fixtures.py --jvm-tools /path/to/verified/jars --output /tmp/workflow-fixtures.json
```

See [release 1.1 verification](docs/VERIFICATION-1.1.md) for current rollout results and [historical fixture verification](docs/VERIFICATION.md) for the earlier tool versions and jar digests. Fixture validation does not establish live application behavior or native hook trust. Keep source changes, a versioned release and explicit installation in that order. This source repository is local; publication has not been requested.

## Release 1.1 commands

```sh
agent-workflow resolve-skills --global --hosts claude cursor --skills design-system ui-ux-pro-max --use-bundle
agent-workflow tools install all
agent-workflow tools status --probe
agent-workflow verify-host --host codex --scope both --repo /path/to/project --live
```

Read [tool setup](docs/TOOLS.md), [native host verification](docs/HOSTS.md) and the [release results](docs/VERIFICATION-1.1.md). Context7 host authentication and exact hook trust are reported separately from configuration. Strix stays inactive until an assessment is explicitly scoped.

## Release 1.1.1 autonomy

The workflow honors explicit standing authorization without repeated action approvals. `doctor` reports sanitized permission defaults and override candidates for each host separately from native verification. Installation and diagnostics preserve host permission settings. See [unattended execution](docs/HOSTS.md#unattended-execution) for opt-in host settings, session overrides and bounded native checks. Release 1.1 verification records above remain historical evidence.
