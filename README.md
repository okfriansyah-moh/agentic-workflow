# Portable agent workflow

Version **1.3.0** provides one implementation workflow for **Codex, Cursor AI, Claude Code and GitHub Copilot**. Start in your existing chat; the current chat coordinates and implements directly. Python helpers manage existing selection state, ownership and verification without a separate agent service.

**Read the approved outcome → implement → run agreed affected checks → obtain one independent combined review → correct findings → deliver.** There are no workflow tiers. Optional workers, resume actions and delivery destinations use the same completion rules. Read [delivery policy](docs/DELIVERY.md); load other guidance only when needed.

## Start or resume

In any supported host:

> Use running prompt for T001.

For a group:

> Implement G02 from docs/06-PLAN.md using its approved references and agreed checks. Implement directly; use scoped workers only when useful. Obtain one independent combined review and deliver within existing authorization.

To resume, including in another host:

> Resume the retained selection. Restore its scope, ownership, constraints, valid results and next action. Preserve its correction and repair limits.

A task can also be requested in ordinary language. The approved brief supplies outcome, complete journey, exact design references, allowed changes, dependencies, checks and destination. Protect harness files and unplanned Python files during product work. Match approved UI and verify completion/return behavior instead of reopening design. Explicit no-test requests prohibit tests, hooks that execute tests, and hidden browser trials; report pending verification.

These examples do not start application work during installation. Preserve existing tasks, source requirements and evidence. Models and permissions remain host-owned. Separate reviewer availability is necessary for independent review; self-review cannot substitute.

## Install and inspect

Python 3.11 or newer and Git are required on macOS/Linux. From this reviewed source checkout:

```sh
python3 scripts/agent-workflow install --global
python3 scripts/agent-workflow install --repo /path/to/project --profile movie-app
python3 scripts/agent-workflow doctor --global
python3 scripts/agent-workflow doctor --repo /path/to/project
```

Use `general` for other stacks and configure actual project checks before implementation. Managed edit hooks notify only; they never execute checks, even with retained older hook settings. Installation preserves unrelated settings, permissions, skills, hooks and Git work; it does not install accounts/application dependencies or resume product tasks.

Commit `.ai/bundles/1.3.0/`, configuration, native adapters, discovery links and `.ai/bin/agent-workflow` together. A repository pin governs all hosts before global fallback; global updates leave other project pins unchanged.

```sh
python3 .ai/bin/agent-workflow doctor --repo .
python3 .ai/bin/agent-workflow task-index --plan docs/06-PLAN.md
python3 .ai/bin/agent-workflow gate --repo . --stage delivery --base BASE_COMMIT --reuse
python3 .ai/bin/agent-workflow resume --repo .
```

`--stage` selects a technical check set, not an execution tier. Use agreed affected checks and existing project thresholds. See [gates](docs/GATES.md).

## Device-aware execution

One shared controller admits substantial checks according to the execution machine's effective CPU/memory, container limits, disk headroom and current pressure. Work stays serial; unsafe or unmeasured checks remain pending. Inspect with `python3 .ai/bin/agent-workflow resources --repo .`. A resource stop requires inspection and explicit healthy recovery; no automatic retries or user-wide tuning. See [budgets, platform limits and recovery](docs/GATES.md#execution-device-budgets-and-recovery).

## Four host adapters

| Host | Project entry points | Start/resume |
|---|---|---|
| Codex | Root AGENTS.md, `.codex/agents`, `.agents/skills` | Use the chat examples above. |
| Cursor AI | Root AGENTS.md, `.cursor/rules`, `.cursor/agents`, `.cursor/skills` | Use the same chat examples in the trusted workspace. |
| Claude Code | Managed CLAUDE.md, `.claude/agents`, `.claude/skills` | Use the same chat examples after loading project instructions. |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/agents`, `.github/skills` | Use the same chat examples; inspect CLI/IDE discovery separately. |

Adapters translate formats, not workflow semantics. Read [host setup and verification](docs/HOSTS.md) for discovery paths, inheritance, precedence, reload and trust. Generated files establish configuration only; CLI results do not establish desktop/IDE behavior. [Release 1.3.0](docs/RELEASE-1.3.md) separates candidate implementation from installed/live verification.

## Maintain the installation

```sh
python3 scripts/agent-workflow update --global
python3 scripts/agent-workflow update --repo /path/to/project
python3 scripts/agent-workflow uninstall --repo /path/to/project
python3 scripts/agent-workflow uninstall --global
```

Update explicitly from reviewed source. Managed-file conflicts are retained, and transactional backups support rollback. See [installation](docs/INSTALLATION.md), [coordination](docs/COORDINATION.md), [skill catalog](docs/SKILLS.md), [tools](docs/TOOLS.md) and [provenance](docs/PROVENANCE.md).

## Develop this package

```sh
python3 -m unittest discover -s tests -v
```

For changed external-tool profiles only:

```sh
cd tests/fixtures/web
npm ci --ignore-scripts --include=optional
cd ../../..
python3 scripts/check-fixtures.py --jvm-tools /path/to/verified/jars --output /tmp/workflow-fixtures.json
```

Source changes, independent review, publication and installation are separate results. The standalone source repository has no remote. This release is published as a source bundle through the movie-app PR; a separate harness repository will be created by its owner later. Retained [1.1 verification](docs/VERIFICATION-1.1.md) and [earlier fixtures](docs/VERIFICATION.md) are historical evidence, not proof for this release. Measure later task overhead from available counters without creating automation or claiming unmeasured savings.
