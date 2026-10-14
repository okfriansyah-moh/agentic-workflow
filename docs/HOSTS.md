# Host adapters and verification

The shared role catalog generates eight native roles with an `aw-` name prefix. Model choices are omitted so the host inherits the user's active settings. A role's prompt restricts its responsibility; this does not create a separate permission sandbox. Hosts retain their normal approval and trust rules.

| Host | Project roles | Global roles | Skill discovery entries |
|---|---|---|---|
| Codex | `.codex/agents/*.toml` | `~/.codex/agents/*.toml` | Project `.agents/skills`; user `.codex/skills` |
| Claude Code | `.claude/agents/*.md` | `~/.claude/agents/*.md` | `.claude/skills` in each scope |
| Cursor | `.cursor/agents/*.md` | `~/.cursor/agents/*.md` | `.cursor/skills` in each scope |
| Copilot | `.github/agents/*.agent.md` | `~/.copilot/agents/*.agent.md` | Project `.github/skills`; user `.copilot/skills` |

Codex role files contain `name`, `description`, and `developer_instructions`. Claude and Cursor use Markdown with `name` and `description` frontmatter. Copilot adds `include-custom-instructions: true` so delegated workers receive repository instructions. Each role also directs workers to read root AGENTS.md and use the pinned project bundle before a global fallback. [Codex roles](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Claude roles](https://code.claude.com/docs/en/sub-agents), [Cursor roles](https://cursor.com/docs/subagents), [Copilot profiles](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli).

The three worker limit is enforced by Forge's dispatch policy, capped by native host capacity. The installer does not rewrite a user's global concurrency, model, permission or MCP settings. Worktree creation uses the recorded integration revision through the shared helper; do not rely on a host's default-branch worktree shortcut for a different integration base.

Root AGENTS.md is installed with a managed block. Claude receives a matching CLAUDE.md block, Copilot receives `.github/copilot-instructions.md`, and Cursor receives a small always-applied `.cursor/rules/agent-workflow.mdc` pointing to the project policy. Global Codex and Claude instruction files receive a short dispatch block; existing personal content stays intact.

| Host | Hook installation | Event | Setup boundary |
|---|---|---|---|
| Codex | Project/user `.codex/hooks.json` | `PostToolUse` for Edit/Write | Trust the exact hook definition in the active runtime |
| Claude Code | Project/user `.claude/settings.json` | `PostToolUse` for Edit/Write | Review host trust and restart when new discovery directories need loading |
| Cursor | Project/user `.cursor/hooks.json`, version 1 | `postToolUse` for Write/Delete | Workspace must be trusted |
| Copilot | Project `.github/hooks/agent-workflow.json`, version 1 | `postToolUse` | Verify hook loading in the intended CLI or IDE; no user hook path assumed |

Hooks run the fast stage and report failures back to the agent. They run after edits and cannot block an edit already made. Required explicit integration/delivery gates remain the completion authority. Script errors, timeouts, host-disabled hooks and unsupported clients cannot establish a passing result. Both dispatchers select the repository entrypoint. Same-event results are deduplicated only when the implementation fingerprint matches; otherwise checks run again. No local trust or loading state is inferred from installed files. [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude hooks](https://code.claude.com/docs/en/hooks), [Cursor hooks](https://cursor.com/docs/hooks), [Copilot hooks](https://docs.github.com/en/copilot/reference/hooks-reference).

`doctor` checks managed file integrity and discovers executable paths. It deliberately labels native runtime loading as unverified. File generation, TOML/JSON parsing, a passing Python fixture, or an installed executable does not prove that a GUI or CLI session loaded a role or executed a trusted hook.

For a live host check, use the exact executable or application runtime in which work will run. Open a harmless temporary repository with the bundle installed. Confirm that its eight roles and relevant skill names are visible, read the root instruction marker, delegate a read-only task to one role, and perform a small fixture edit to observe the configured hook. Record the runtime/version, discovery result, hook invocation, actual result, and required trust/reload action. Restart sessions whose discovery directories were created after they started. Do not change trust records or run paid model work merely to convert an unverified status to passed.

Do not validate a standalone Codex CLI as evidence for a different desktop app-server version. An absent host, unavailable account, or unapproved hook remains an explicit setup limitation. Native host validation records belong in the delivery report; fixture results remain labelled as fixtures.
