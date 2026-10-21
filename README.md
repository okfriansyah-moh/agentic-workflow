# Agentic Workflow

A portable workflow for getting software work from an approved brief to verified delivery in **Codex, Cursor AI, Claude Code, and GitHub Copilot**.

Version [**1.3.0**](https://github.com/okfriansyah-moh/agentic-workflow/releases/tag/v1.3.0) combines 74 bundled skills, native agent roles, and a small Python standard-library CLI. Your existing chat coordinates the work. Helpers track scope, ownership, checks, review findings, and recovery state; no separate agent service is required.

The workflow is:

**Read the approved outcome → implement → run agreed checks → obtain one independent combined review → correct findings → deliver.**

Use it to bring the same working agreements into multiple projects and coding agents, keep project-specific instructions with the code, and resume work with recorded evidence instead of relying only on chat history.

## Requirements

- macOS or Linux, Python **3.11+**, and Git.
- At least one supported coding-agent client, installed and authenticated separately.
- Your project's own language tools, dependencies, scanners, and browser tools for the checks you select.
- A separate supported reviewer for independent review. Reviewing your own changes does not meet that requirement.

The CLI itself uses only the Python standard library. Installing the workflow does not install application dependencies, configure accounts, or start application tasks.

## Quick start

Clone the [version 1.3.0 release](https://github.com/okfriansyah-moh/agentic-workflow/releases/tag/v1.3.0):

```sh
git clone --branch v1.3.0 https://github.com/okfriansyah-moh/agentic-workflow.git
cd agentic-workflow
python3 scripts/agent-workflow --version
```

### Install into a project

From the cloned version 1.3.0 source directory, replace `/path/to/project` with an existing project:

```sh
python3 scripts/agent-workflow install --repo /path/to/project --profile general
python3 scripts/agent-workflow doctor --repo /path/to/project
```

`general` is the default profile. Configure the project's actual check commands before requesting implementation. Use `--profile movie-app` only for projects adopting the bundled Kotlin/Spring/JPA, Svelte/TypeScript, Node, and PostgreSQL checks; inspect its tool requirements first.

Open the target project in your coding agent, load its project instructions, and request a bounded task. For example:

> Implement the approved task in docs/tasks/T001.md. Follow this project's workflow instructions, run the agreed affected checks, obtain one independent combined review, and deliver within my existing authorization.

### Optional global installation

From the same version 1.3.0 source directory, make the bundle available across projects:

```sh
python3 scripts/agent-workflow install --global
python3 scripts/agent-workflow doctor --global
```

Add `~/.local/bin` to your shell's PATH to use the global `agent-workflow` command. A project installation is self-contained and uses its own pinned bundle before global fallback.

## How it works

- **Skills** provide guidance for planning, implementation, design, verification, and delivery. Load the guidance relevant to the task rather than every skill.
- **Native roles** separate coordination, backend, frontend, operations, evidence collection, security, integration, and independent review. Models and permissions remain controlled by the coding-agent host.
- **Python helpers** manage installation, task indexing, ownership, selection state, check execution, and verification receipts.
- **Project bundles** pin the workflow version so a global update does not silently change another project's rules.
- **Verification receipts** retain the inputs and results behind delivery claims. Missing tools, unavailable services, and unobserved host behavior remain explicit limitations.

Work is serial by default. Authorized workers can own separate contributions, followed by one independent combined review. See the [delivery policy](docs/DELIVERY.md), [role catalog](agents/catalog.json), and [skill catalog](docs/SKILLS.md).

## Integrate with an existing project

Installation creates `.ai/config.json`, a versioned `.ai/bundles/1.3.0/` bundle, a local `.ai/bin/agent-workflow` launcher, and host-specific discovery files. Commit the generated project configuration, bundle, launcher, adapters, discovery links, and ownership metadata together. Keep transient state, reports, evidence, and installation backups out of version control according to your project's policy; review generated files before committing.

Existing instructions receive a bounded managed block. Unrelated settings, skills, hooks, permissions, and Git work are preserved. Conflicting managed files are reported rather than silently overwritten. Copy or clone the complete project, including dot directories and symlinks, when moving it.

| Coding agent | Project entry points |
| --- | --- |
| Codex | `AGENTS.md`, `.codex/agents`, `.agents/skills` |
| Cursor AI | `AGENTS.md`, `.cursor/rules`, `.cursor/agents`, `.cursor/skills` |
| Claude Code | `CLAUDE.md`, `.claude/agents`, `.claude/skills` |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/agents`, `.github/skills` |

Reload or restart the host's discovery view after installation. A successful `doctor` result checks installation structure; it does not prove that an IDE loaded the instructions, trusted hooks, or invoked an independent reviewer. See [host setup and verification](docs/HOSTS.md).

From the target project, inspect its installation and approved plan:

```sh
python3 .ai/bin/agent-workflow doctor --repo .
python3 .ai/bin/agent-workflow task-index --plan docs/06-PLAN.md
python3 .ai/bin/agent-workflow resources --repo .
```

Replace the example plan path with your own. The shared resource controller admits substantial checks using the execution device's available capacity. Unsafe or unmeasured checks stay pending; resource stops require inspection and explicit healthy recovery. See [check configuration and resource budgets](docs/GATES.md).

## Everyday use

Give the agent the desired outcome, allowed changes, relevant requirements or designs, acceptance checks, and delivery destination. Ordinary language works; saved tasks are useful for larger selections.

**Start a saved task:**

> Use running prompt for T001.

**Implement a group:**

> Implement G02 from docs/06-PLAN.md using its approved references and agreed checks. Implement directly; use scoped workers only when useful. Obtain one independent combined review and deliver within existing authorization.

**Resume, including in another host:**

> Resume the retained selection. Restore its scope, ownership, constraints, valid results, and next action. Preserve correction and repair limits.

**Request review:**

> Review the complete selection independently against the approved requirements, project standards, and actual verification results. Return actionable findings without changing implementation or task status.

Resume uses retained Git-shared selection state; chat history does not transfer between hosts. Transfer ownership before another coordinator changes the same selection. A plain task request does not replace host permissions or authorize unrelated external messages.

## Update, rollback, and uninstall

Review the release notes before updating. From an existing source checkout, select version 1.3.0:

```sh
git fetch origin tag v1.3.0
git checkout --detach v1.3.0
python3 scripts/agent-workflow update --global
python3 scripts/agent-workflow update --repo /path/to/project
python3 scripts/agent-workflow doctor --repo /path/to/project
```

Run only the update commands for installations you use. Updates retain project profiles, preserve unrelated configuration, and refuse conflicting edits to managed files. Installation changes keep transactional backups.

To restore a repository installation, replace `TRANSACTION` with the backup reported by the installer:

```sh
python3 scripts/agent-workflow rollback --repo /path/to/project --backup /path/to/project/.ai/install-backups/TRANSACTION
```

Later edits to managed files can block rollback to protect your work. Keep backups intact until the installation is accepted.

```sh
python3 scripts/agent-workflow uninstall --repo /path/to/project
python3 scripts/agent-workflow uninstall --global
```

Uninstall preserves unrelated content and reports edited files it retained. See the [installation guide](docs/INSTALLATION.md) for conflict resolution, global skill selection, and recovery details.

## Troubleshooting and limits

| Situation | Next step |
| --- | --- |
| Global command is missing | Add `~/.local/bin` to PATH, or use the project's Python launcher. |
| Installer reports a conflict | Inspect the reported file and preserve personal edits; use the documented update or recovery procedure. |
| Roles or skills do not appear | Reload discovery, check workspace trust, and inspect the host-specific paths in the host guide. |
| A check cannot run | Install its required project tool or record the check as pending; do not count unavailable checks as passes. |
| A resource stop is retained | Inspect capacity and stop details before the documented explicit recovery action. |
| No independent reviewer is available | Leave review pending; implementation and self-review alone do not establish acceptance. |

Managed edit hooks provide notifications only and never execute checks. Explicit verification and CI remain necessary. File generation, CLI fixtures, live host loading, and product behavior are separate observations. Historical verification reports establish only the versions and environments they assessed.

## Repository guide

| Location | Purpose |
| --- | --- |
| `agent_workflow/`, `scripts/agent-workflow` | Python CLI and source-checkout launcher |
| `skills/`, `manifest.json` | Bundled guidance, provenance, dependencies, and content digests |
| `agents/`, `adapters/`, `prompts/` | Shared roles, host integration, and task entry points |
| `profiles/`, `schemas/`, `resources/` | Check profiles, configuration schemas, and shared resources |
| `docs/`, `tests/` | Detailed contracts, release evidence, and helper tests |

## Contributing

Read `AGENTS.md`, the installation manifest, the affected helper, and [delivery policy](docs/DELIVERY.md) before changing behavior. Test installers with temporary homes and repositories; preserve unrelated settings and Git work. Runtime changes require:

```sh
python3 -m unittest discover -s tests -v
```

Use shared resource admission before substantial checks. Changed external-tool profiles also require the optional fixture runner described in [tool integration](docs/TOOLS.md). Keep skill digests current after skill edits, align documentation and adapters with CLI behavior, and obtain independent review before publication.

## Documentation and attribution

Start with [installation](docs/INSTALLATION.md), [host setup](docs/HOSTS.md), [coordination](docs/COORDINATION.md), [checks](docs/GATES.md), and [release 1.3.0](docs/RELEASE-1.3.md).

This repository combines project-authored workflow material and adapted skills. The owner has confirmed permission to publish the bundled material. Existing third-party licenses, notices, and attribution remain applicable; publication does not assign a blanket license to every component. Consult [provenance](docs/PROVENANCE.md), `manifest.json`, and each skill's retained license files for source details.
