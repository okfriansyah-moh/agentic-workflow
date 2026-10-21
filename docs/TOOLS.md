# Managed external tools

Release 1.1 adds Playwright CLI, hosted Context7 MCP configuration and an isolated Strix installation. Skills explain when to use them; the executables and accounts remain separate dependencies. Tool installation never starts an application task or security assessment.

## Commands and storage

```sh
agent-workflow tools install all
agent-workflow tools status all
agent-workflow tools status context7 --probe
agent-workflow tools install context7 --repo /path/to/repository
agent-workflow tools remove context7 --repo /path/to/repository
agent-workflow tools remove all
```

A repository-local entrypoint supports the same arguments: `python3 .ai/bin/agent-workflow tools status all`. `--home PATH` selects an isolated home for tests or an explicit user installation. `--node PATH` and `--python PATH` select actual executables during installation. The runtime helper verifies their versions; GUI applications may inherit a different PATH from the terminal. Ensure the host can execute the resulting `HOME/.local/bin/playwright-cli` and `HOME/.local/bin/strix` launchers, or use their absolute paths. Restart/reload the host after configuration changes.

Runtimes, dependency locks, a field ownership ledger and local integrity hashes live under `HOME/.local/share/agent-workflow/tools`. They are external to tracked bundles. The CLI uses a file lock for tool lifecycle changes. Each tool installation is a transaction: a failed provisioning step removes its new runtime, and failed publication restores the earlier launcher. `all` completes tools in sequence; an error on a later tool leaves earlier successful installations available for a repeat invocation.

Matching installed versions are reused after integrity checks. Explicit installation from a newer reviewed workflow can provision a new pinned version; old runtimes remain recorded until removal. Unowned executables, changed launchers, modified runtime content and conflicting MCP definitions are preserved. `remove` deletes only unchanged owned content. Remove Context7 separately for each installed repository scope before removing the workflow source; `remove all` without `--repo` addresses global configuration and runtimes. Removing a workflow bundle alone does not delete external tools or host-managed credentials.

## Versions and integrity

| Tool | Pin | Verification |
|---|---|---|
| Playwright CLI | `@playwright/cli` 0.1.22 | Exact npm lock and SHA-512 SRI for all three packages, package version checks, actual CLI version and browser launch |
| Browser driver | `playwright` / `playwright-core` 1.64.0-alpha-1790635538000 | Exact transitive dependency selected by the published CLI release; its alpha status is retained |
| Chromium | Revision 1247, browser 155.0.8059.12 | Pinned driver metadata, HTTPS download, full Chromium launch and local installed-tree SHA-256 |
| Strix | `strix-agent` 1.7.0 | Python 3.13 venv, 92 exact dependency versions with permitted wheel hashes, installed package metadata and console help |
| Context7 | Hosted endpoint configuration inspected 2026-10-15 | Managed field comparison; optional public MCP connectivity and tool-list probe |

[tools-lock.json](../profiles/tools-lock.json) includes the npm lock, full hashed Python requirements, published Strix wheel hashes and resolver provenance. Runtime installers use argv arrays, `npm ci` with scripts disabled, and pip with mandatory hashes and binary wheels. Downloaded packages retain their upstream licenses. Browser revision is fixed by the integrity-checked driver, but Playwright does not publish a separate digest in that browser metadata; the local tree hash detects later modification and is not an independent publisher signature. Hosted documentation responses and OAuth service code cannot be frozen by this package.

The reviewed Strix lock was resolved for Python 3.13 with uv 0.12.9, universal markers and PyPI. This installer requires Python 3.13 even though upstream's minimum is 3.12. Linux/macOS are supported; platform-specific wheels or browser OS dependencies can still be unavailable. Such errors fail setup. No OS package manager, Docker settings or host model choices are changed automatically. Node must be at least 20 for the pinned driver; the helper prefers an installed Homebrew Node before PATH and records the actual executable/version. An explicit `--node` wins.

## Context7 configuration and authentication

| Host | Global file | Repository file |
|---|---|---|
| Codex | `.codex/config.toml` | `.codex/config.toml` |
| Claude Code | `.claude.json` | `.mcp.json` |
| Cursor | `.cursor/mcp.json` | `.cursor/mcp.json` |
| Copilot CLI | `.copilot/mcp-config.json` | `.github/mcp.json` |

Global paths are relative to the selected home; repository paths are relative to `--repo`. The helper adds only the `context7` server field/table, preserving other MCP servers and personal fields. JSON formatting may change. TOML additions use a bounded comment block so unrelated text remains intact. Existing equivalent fields are reused without claiming ownership. The ledger backs up the field's previous absence, with expected value and digest; it never copies entire account/settings files or existing secret values. In-process rollback retains original bytes only in memory. A divergent Context7 definition blocks the transaction before any host file is changed.

The default endpoint is `https://mcp.context7.com/mcp/oauth`. Complete the host's OAuth flow and trust/reload steps in the native application. Codex supports `codex mcp login context7`; Claude exposes server authentication through `/mcp`; Cursor displays its MCP connection action; Copilot CLI supports `/mcp auth context7`. No login or token acquisition is performed by the installer. These local hosts support OAuth; cloud Copilot behavior is outside this adapter's scope. Optional `--auth anonymous` configures the public `/mcp` endpoint with service limits, and will conflict with a different existing managed mode until that scope is explicitly removed.

`tools status` reports file configuration and local runtime integrity. It does not certify native discovery or OAuth login. Use native host verification records for those claims. `--probe` initializes the public endpoint and lists its two expected tools; it reports `anonymous` or `api-key-provided`, never host OAuth success. The probe reads `CONTEXT7_API_KEY` from the process environment only when present and never records it. Authentication errors, denied access, rate limits and unavailable transport remain distinct blocked results. This public probe does not send project content or execute a library query.

Custom `CODEX_HOME`, `COPILOT_HOME`, XDG configuration locations and host profiles are not remapped by this first adapter. For such installations, review the documented target paths before use and register native verification against the actual host location. Configurations written to an unused default location do not count as loaded. Duplicate Context7 definitions in another project configuration file also require native inspection.

Primary references: [Context7 clients](https://context7.com/docs/resources/all-clients), [Claude MCP](https://code.claude.com/docs/en/mcp), [Cursor MCP](https://docs.cursor.com/context/model-context-protocol), [Copilot configuration paths](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) and [Copilot CLI commands](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).

## Browser evidence

Use tools only for agreed observations in the single [workflow](DELIVERY.md). Explicit no-test requests prohibit hidden browser trials. Inspect changed approved screens and complete journeys with existing tools; tool installation does not authorize a new acceptance campaign.

The managed launcher supplies the browser cache and defaults to pinned Chromium; an explicit CLI browser argument selects a different installed browser. Use one session name per owned browser resource. The supported CLI commands include `video-start`, `video-stop`, `video-chapter` and `video-show-actions`. `recording-start` / `recording-stop` produce test code. Inspect the installed command's help before using annotation options. This distinction was verified against CLI 0.1.22 help. See [playwright-cli](../skills/playwright-cli/SKILL.md), [record-test-video](../skills/record-test-video/SKILL.md) and [verify-test-evidence](../skills/verify-test-evidence/SKILL.md).

The installation's browser smoke check proves a local full Chromium process can launch and close. It does not prove a journey, visual fidelity, accessibility, transport behavior or acceptance case. Runtime sessions and reports belong in the contribution’s assigned outputs, and actual frames must be compared with adopted design artifacts. The parent release verification separately records a real browser fixture. Inspect original frames: the CLI capture can scale browser content into a larger canvas after a viewport resize. If the result is unreadable, preserve it as a capture failure and recapture a fresh context per viewport with matching Playwright `recordVideo` dimensions, retaining trace, assertions and hashes.

## Strix stays inactive until requested

```sh
agent-workflow tools strix-preflight
agent-workflow tools strix-report --report /path/to/run/vulnerabilities.json --target https://authorized.example
```

The preflight checks managed integrity, reads Docker daemon availability and reports whether `STRIX_LLM` and `LLM_API_KEY` exist in the environment. It does not print values, inspect stored credentials, authenticate with a provider, pull an image or run an assessment. Existing Strix OAuth/stored configuration may be usable, but this helper reports it as uninspected. A ready preflight is not scan authorization.

Report ingestion accepts the pinned Strix JSON findings list with sibling `run.json`. It requires completed status, an end timestamp, a matching target and valid finding IDs/severity. It outputs only hashes and severity counts, preserving the original evidence in place. It does not execute proof scripts or mark security acceptance. Source revision, evidence validity and any remediation require independent review. Unknown formats, incomplete runs and mismatched scopes fail rather than becoming empty findings.

[Strix](https://github.com/usestrix/strix) can actively test targets and download its sandbox image on first use. Use the [explicit assessment skill](../skills/strix-security/SKILL.md) with the user's authorized scope. This release includes no scan hook, scheduled assessment, cloud upload or provider selection. The standard quality gates remain separate.

## Verification boundaries

`python3 scripts/run-behavior-tests.py --pattern test_tools.py --output .ai/reports/tools-tests.json` runs isolated lifecycle tests with controlled runtime fixtures. They cover field preservation, conflicts, partial-write rollback, global/repository coexistence, modified content, executable publication/removal, authentication/rate limits and report handling. They do not replace real dependency installation or native host verification.

The tool helper's command errors retain an exit code and omit subprocess streams to avoid leaking secrets. For an installation failure, independently inspect the relevant executable, version, network access and package availability; do not copy raw account configuration into a bug report. Actual install results and host authentication limitations belong in the release verification record.
