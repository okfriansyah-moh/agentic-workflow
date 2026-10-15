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

`doctor` checks managed file integrity, discovers executable paths and reads saved native verification records without launching a host. File generation, TOML/JSON parsing, a passing Python parser test, or an installed executable does not prove native role loading or hook execution. A saved pass becomes stale when its runtime, configuration, launcher, selected bundle helpers, skill resources or linked evidence changes. A record copied from another installation cannot pass. Records live under `<installation-state>/state/host-verifications`; keep their linked fixture and capture files while their proof is needed.

Run the read-only preview to identify the selected runtime and configuration hash. Add `--live` only when native execution is authorized; it can use the host's account and incur model charges. Each scope receives a fresh fixture using its selected bundle. Global fixtures omit project discovery adapters; repository fixtures retain the generated pinned adapters. Neither path dispatches application tasks or edits the original repository. Discovery paths are resolved through symlinks before testing project scope.

```sh
agent-workflow verify-host --host claude --scope both --repo /path/to/project
agent-workflow verify-host --host claude --scope both --repo /path/to/project --live
agent-workflow verify-host --host codex --scope repo --repo /path/to/project --live --timeout 90
agent-workflow verify-host --host copilot --scope repo --repo /path/to/project --live
```

The preview creates no verification files and starts no native host process. It may run a bounded read-only Git worktree query to locate Claude repository-local settings. Live checks capture each command, exit code, timestamps and output hashes; retained content masks credential fields and known token forms. `--timeout` limits each native phase to 1–300 seconds. The passing phase runs Forge, which delegates the `smoke.json` edit to `aw-backend`, waits, and sends the changed file to a separate `aw-review-verify` worker. The failing phase uses Backend directly for a separate hook check. Claude and Copilot select the main role with their supported `--agent` option; Codex requests one native Forge parent and its two workers. Forge does not edit or spawn another Forge. The configured limits are USD 2.00 per Claude phase and 30 AI credits per Copilot phase. Live verification showed that USD 0.50 stopped the inherited-model delegation before review, while Copilot rejected a credit limit below its supported minimum of 30. A limit is a spending bound, not a forecast of actual cost. The default check has no model override, approval bypass, persistent permission change, login retry or automatic trust approval. Explicit `--unattended-authorized` selects broader session permissions only as described below. Stop on authentication, permission or runtime failure and retain the observed result.

Claude receives session-only `Edit` access to the absolute fixture file, `Agent(aw-backend)` and `Agent(aw-review-verify)`, with Bash denied. Read grants cover only that file, fixture AGENTS/configuration, three relevant managed skill sources and the coordination reference. `Edit(path)` is the supported file-edit permission rule, including writes. Copilot receives the same exact file read/write scope and denies shell commands. Codex retains the selected runtime's existing permission policy. If those grants cannot support the required native action, verification remains blocked. [Claude permission rules](https://code.claude.com/docs/en/permissions), [Copilot scoped tool permissions](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/allowing-tools).

Every record separates these results:

| Result | Required proof |
|---|---|
| `discovery` | Native role catalog, session initialization metadata or observed native UI |
| `role_invocation` | Completed Forge, backend and reviewer identities; both workers belong to that Forge; the backend edit completes within its lifecycle before independent review |
| `skills` | Enabled native catalog entries, with project paths for repository scope, or observed native UI |
| `hooks` | Native edits correlated with managed hook source and edit identifiers, one gate receipt per edit, distinct input fingerprints, and captured failure feedback |
| `trust` | Successful native execution of the installed hook without a trust override, or explicit native UI observation |

Assistant prose cannot establish any native lifecycle result. Unsupported event shapes, missing tool IDs, absent source paths and gate JSON without a matching host event remain blocked. The two gate phases verify same-event deduplication by requiring one gate run per edit. They do not claim coverage of every possible native event. A global Copilot hook is not assumed; its portable hook installation is repository-scoped.

Selecting `--agent aw-forge` requests that role; it does not establish that the runtime loaded it. Native metadata must identify the active Forge and its worker relationships. Reviewer-only evidence cannot pass orchestration. Claude forwards subagent events when supported; absent identity, completion or edit ownership fields remain blocked. Claude initialization skill names establish availability, but repository skill selection stays blocked when native metadata omits source paths and therefore cannot establish project precedence. A timed-out native phase cannot pass from partial hook output.

Measured Claude streams identify backend and reviewer tool calls, completed task results and edit ownership, but their main-session initialization can omit the selected role. Such records retain the worker evidence and block the overall role result. Copilot worker records connect `data.parentId` to the parent's native `agentId`; that relationship is mapped to the recorded task call. A `subagent.completed` event without a success field requires a matching successful task-tool result, and cancelled workers cannot pass. A requested main Forge profile together with an observed Forge child stays blocked when the main role is unidentified. The single-orchestrator contract fails only when native metadata connects a completed second Forge to an identified main Forge.

Freshness also hashes native MCP/settings files without retaining their contents. Cursor's application metadata and package/product files are bound alongside its launcher, because an unchanged Electron launcher does not establish an unchanged application.

Claude's `~/.claude.json` also stores usage counters and project caches that change during normal sessions. Its verification digest uses user and current-project MCP definitions, MCP enable/disable/approval lists, allowed/disallowed tools, permissions, permission mode, workspace trust and external-include approval. Missing fields use their empty or disabled defaults, so creating an empty project cache does not invalidate proof. Usage, cost/session history, experiment caches and unrelated projects are excluded. The ordinary `.claude/settings.json`, `.claude/settings.local.json` and `.mcp.json` inputs remain fully hashed. MCP or permission changes still invalidate verification. [Claude MCP scopes and project choices](https://code.claude.com/docs/en/mcp).

CLI smoke results have `target.kind: disposable-fixture` and `proof_boundary: native-disposable-fixture`. They establish behavior in that generated fixture. They do not establish that the original repository's active session loaded its adapters. `doctor` reports those records as `fixture-passed`, `fixture-blocked` or `fixture-failed`, while `installation_loading` stays `unverified`. Actual installation observations require evidence captured from that installation. Structural findings remain separate from both results.

The default Codex executable on macOS is the desktop application's embedded engine when present. `--runtime` selects an exact executable when needed. Its path, version, content hash and `surface` are retained. Codex probes use normal persisted native sessions: the observed embedded runtime could not start child agents with `--ephemeral` because their rollout context was absent. Those sessions remain in normal host history. An embedded engine process is distinct from desktop UI loading, and a standalone CLI is distinct from the embedded engine. The verifier does not start an app-server against the real user home. Native metadata absent from `exec --json` remains unverified. Both `collab_tool_call` and `collab_agent_tool_call` event names are recognized; wait events with empty worker IDs or absent role metadata cannot establish delegation. Cursor uses native UI evidence; the verifier does not substitute an unrelated `agent` CLI for its GUI.

Copilot's npm launcher can execute an optional platform binary or fall back to `index.js`. Its supporting input digest includes the launcher package metadata, fallback JavaScript and installed optional platform package metadata with their selected executable exports. Direct exports and a single `.` export are supported; other export layouts block verification. An unchanged launcher cannot conceal a changed selected runtime. These paths are hashed without executing them during preview.

Copilot's native `skill list --json` and `instruction list --json` commands do not enumerate custom roles. Its live session stream can provide `session.custom_agents_updated` and `session.skills_loaded` catalogs; the interactive `/agent` picker remains another observation path. User-role entries establish global availability. Repository-role proof additionally requires project source paths; a repository session that reports user roles keeps project-role discovery blocked. Personal role IDs take precedence over matching repository IDs, so names alone do not prove which profile supplied a role. Codex exposes `skills/list` through app-server metadata; this helper does not claim that catalog from `exec` or start another server against the real home. [Copilot role selection](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli).

For UI verification, first obtain the read-only preview. Capture the native view using the authorized computer-use tool, retain its accessibility text and/or screenshot, and record its tool-call identifiers. The observer must inspect role/skill names or the actual invocation and hook result. A role-list screenshot does not establish role execution. A sample input shape follows; replace each placeholder with the observed value and the SHA-256 of the saved artifact.

```json
{
  "host": "cursor",
  "scope": "repo",
  "root": "/absolute/project/path",
  "runtime_sha256": "hash-from-preview",
  "runtime_support_sha256": "support-sha256-from-preview",
  "config_sha256": "hash-from-preview",
  "provider": "cua",
  "observer": "identified-reviewer",
  "captured_at": 1792000000,
  "tool_call_ids": ["native-capture-call-id"],
  "observations": {
    "discovery": {
      "status": "passed",
      "observed": "The native project agents view lists the eight installed aw- roles.",
      "native_identifiers": ["aw-forge", "aw-backend", "aw-frontend", "aw-qa-evidence", "aw-security", "aw-operations", "aw-review-verify", "aw-integrator"],
      "artifacts": [{"path": "/absolute/capture.txt", "sha256": "capture-sha256"}]
    }
  }
}
```

```sh
agent-workflow verify-host --host cursor --scope repo --repo /path/to/project --live --ui-evidence /path/to/ui.json --attest-ui
```

`--attest-ui` means the recorder confirms the captures came from the identified native tool. The import checks installation/runtime/configuration binding, artifact hashes, observer identifiers and capture age within 24 hours. Cursor and Copilot also require `runtime_support_sha256` from `runtime.support_sha256` in their preview, binding supporting runtime inputs captured at observation time. JSON alone cannot authenticate a computer-use provider; the proof boundary is `observer-attested-native-ui`. Partial observations leave other categories blocked. Missing runtimes cannot pass. Configuration changes during verification invalidate the run.

A UI `role_invocation` pass additionally requires `native_lifecycles` for Forge, backend and reviewer. Each entry supplies `id`, `role`, `parent_id`, `started` and `completed` event indices. Workers must be distinct children of Forge, with complete implementation before review. `implementation_edit` supplies `owner`, `started` and `completed`; its indices must fall inside the backend lifecycle. These values must come from inspected native captures, not an assistant's description of its intended workflow.

Restart sessions whose discovery directories were created after they started. Review the exact changed hook in the actual host's trust UI; configuration files do not establish that it was approved. An unavailable account, denied computer-use surface, missing host or unapproved hook stays an explicit limitation with its concrete next step. Do not work around a denied native surface through another UI route.

## Unattended execution

Explicit standing authorization satisfies workflow approval checkpoints within its stated scope. The shared bundle does not grant blanket permission to every user. It preserves required gates, independent review, claims and correction limits. A known destination and a requested outcome are still required for publication, merge, deployment and production changes; authorization covering those actions can already exist in personal instructions or the active request.

Host permission defaults are a separate user choice. Configure them only when explicitly requested, preserve unrelated settings and keep a backup. Ordinary install, update and `doctor` never select these values:

| Host | User settings for unattended execution | Override candidates |
|---|---|---|
| Codex | `~/.codex/config.toml`: `approval_policy = "never"`, `sandbox_mode = "danger-full-access"` | `CODEX_HOME`, project `.codex/config.toml`, profiles, launch flags and organization policy |
| Claude Code | `~/.claude/settings.json`: `permissions.defaultMode = "bypassPermissions"` | `CLAUDE_CONFIG_DIR`, project and local settings, managed settings, permission rules and session flags |
| Copilot | User-editable `~/.copilot/settings.json`: `defaultPermissionMode: "allow-all"`, `defaultMode: "autopilot"`; use `copilot config` | `COPILOT_HOME` and session flags; internal JSONC `config.json` is not the user settings interface |
| Cursor CLI | `~/.cursor/cli-config.json`: `approvalMode: "unrestricted"`, `sandbox.mode: "disabled"` | CLI session flags and organization controls |
| Cursor desktop | Run Everything in the desktop settings; installed runtimes that support it read `~/.cursor/permissions.json` with `approvalMode: "unrestricted"` | Runtime version, workspace trust, enterprise policy and active session |

`doctor.hosts.HOST.autonomy` reports recognized permission values, settings paths, missing/invalid sources and profile/project candidates without executing a host or exposing arbitrary settings, rule contents or parse errors. `configuration.observed_defaults` describes file defaults; `sources` identifies each value's file. Codex project/profile candidates are listed separately because this command cannot establish active profile selection or project trust. Claude default modes are layered user, project, local and managed, with rule counts reported separately. Current Claude CLI versions read root-local settings from the main checkout in linked worktrees, after any older starting-directory local file. Diagnostics and verification hashes include both paths. Windows, home-root repositories and entries owned by another user retain the starting-directory location; unresolved Git metadata produces an unknown result. See [Claude local settings locations](https://code.claude.com/docs/en/settings#where-claude-code-keeps-the-local-file-in-a-git-repository). Cursor CLI and desktop configuration have separate results. Cursor `manual` and `allowlist` modes are restricted. Unknown values and invalid files remain unknown. An unattended configuration result does not establish live behavior: `live_verification` remains unverified. Existing native discovery/hook records stay separate and do not prove the absence of approval prompts.

For explicitly authorized unattended native verification, add:

```sh
agent-workflow verify-host --host copilot --scope repo --repo /path/to/project --live --unattended-authorized
agent-workflow verify-host --host claude --scope repo --repo /path/to/project --live --unattended-authorized
```

This option records the supplied authorization and adds Copilot `--allow-all` or Claude `--permission-mode bypassPermissions` for the disposable smoke sessions. Without it, exact fixture grants and the shell denial remain. Spend/time limits, inherited models, fixture-only task instructions and required evidence remain in both modes. Codex continues inheriting its current policy; Cursor still needs separate desktop observation. Inspect captured events and any actual UI prompts and record authentication, denied actions and pending approvals independently. Fresh and resumed sessions, CLI and desktop are different verification boundaries; this helper's fresh CLI fixture does not prove the others.

Platform-enforced confirmations, account authentication, OS permission dialogs, organization policies and connector controls can still require a human. Preserve their concrete observed result; changing workflow prose cannot remove them. Native permission references: [Codex sandboxing](https://learn.chatgpt.com/docs/sandboxing), [Claude permissions](https://code.claude.com/docs/en/permissions), [Copilot settings](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference), [Cursor modes](https://cursor.com/docs/agent/security/run-modes).
