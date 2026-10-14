# Verification record

Validation ran on macOS arm64 with Python 3.13.2, Node 24.7.0 and OpenJDK 22.0.1. The installation is deliberately separate from movie-app application execution.

## Executed checks

- Standard-library behavioral suite: **81 tests passed**. Covers managed install/update/rollback/removal/relocation, cross-worktree claims, exact-base integration, retained conflicts, bounded corrections, command contracts, fingerprint freshness and evidence boundaries.
- External web/JVM fixtures: **13 of 13 passed**, including expected failures for function size, types, dependency cycles, deep nesting and field injection. Positive fixtures compile or execute with actual tools.
- Security fixtures: **8 of 8 passed**, including clean and unsafe Semgrep/Gitleaks/OSV results and malformed input errors. OSV fixtures resolve real registry metadata; a package count alone was insufficient without an ecosystem/version.
- All **71** skill entries pass structure, manifest digest and dependency graph validation. Native roles have eight definitions rendered into four host formats.
- Movie-app index: **46 tasks, 20 groups**, valid source hashes, file references and dependency order. Only T001 is currently dependency-eligible. No application task was dispatched.

## Boundaries still requiring a live project or host

These fixtures do not establish application acceptance. Spring context startup, PostgreSQL/JPA behavior, GraphQL/gRPC transport, full Kover integration, Playwright browser journeys/accessibility and Compose behavior await the actual application and its selected tasks. The video validator was tested using real encoded media and frame decoding; a human or visual reviewer still judges readability and truthful UI assertions.

No remote Sonar instance was configured. Mandatory missing/stale Sonar paths are tested and blocked. Scanners used for fixture validation are temporary test dependencies, not global application prerequisites. Install supported versions through the project's chosen tool management before applicable application checks.

The desktop Codex executable reports 0.162.0-alpha.17.2; the separate command on the shell PATH reports an older installation and was not used to start an app-server. Claude Code reports 2.1.283; Copilot reports 1.0.94. Cursor desktop is installed, with no cursor-agent executable on PATH. Role syntax and hook dispatch are fixture-tested; actual loading and hook trust are reported separately below. No trust bypass was used.

## Reproduce

Run the standard-library suite from the source root. External web dependencies are pinned in tests/fixtures/web/package-lock.json. JVM and scanner download provenance is recorded in verification-tools.json; downloads were checked against published upstream digests. Semgrep used version 1.180.0 and explicit system CA certificates, with metrics/version checks disabled for these fixtures.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check-fixtures.py --jvm-tools /path/to/verified/jars --output /tmp/fixtures.json
python3 scripts/check-security-fixtures.py --tools /path/to/scanners --semgrep /path/to/semgrep --output /tmp/security.json
```

The local Semgrep rules are a small reviewed baseline, not exhaustive security coverage. Missing toolchains or malformed reports fail applicable checks. All commands retain actual exit codes; a failed scanner is not reported as a clean scan.

## Installation and native discovery

Both real installations passed doctor with 71 manifest entries and no missing or modified managed files. Repeating installation changed zero files. A fresh local Git clone independently passed doctor (71 entries), task indexing (46 tasks/20 groups), and the project-local fast-stage smoke check; see verification-relocation.json. The source package is under the requested agent-workflow folder and the movie-app copy is self-contained.

All 113 pre-existing movie-app files retain their original SHA-256 hashes. All 1,212 pre-existing global skill files/symlinks remain unchanged. Movie-app received a Git baseline for its approved documents; no application task status changed.

Four native skill-name conflicts were retained: design-system and ui-ux-pro-max under the existing Claude and Cursor user skill locations. Their personal versions remain intact. The complete portable versions are installed in the global bundle, and project roles explicitly select their project bundle paths.

| Host | Actual result | Remaining step |
| --- | --- | --- |
| Codex desktop | Checked the app's own executable version and generated protocol schemas. Its existing app-server proxy socket was unavailable; no new daemon was started. Native role TOML parses. | Reload a session, inspect the eight aw-* roles and project skills, then review and trust the exact hook definition using the host's supported trust interface. Live role/skill/hook loading is unverified. |
| Claude Code | Installed supported user/project paths and parsed role frontmatter; existing settings/hooks preserved. | Reload the session and inspect aw-* roles and skills. Actual role activation and hook execution remain unverified. |
| Copilot CLI | Native skill list discovers all 71 expected skills from movie-app, enabled. Native instruction list discovers .github/copilot-instructions.md. | Role activation and hook execution remain unverified until a trusted session loads them. |
| Cursor | Desktop app is present; native role files and JSON hook structure parse. No cursor-agent command was found. | Reload Cursor's project and inspect agents/skills/hooks. Live loading is unverified. |

Hook dispatch, duplicate-event suppression, timeout termination and pinned project routing were verified as subprocess fixtures. These results do not assert host trust. Explicit gate commands remain the completion authority. Global hooks dispatch to the project's selected bundle; they do not substitute a newer global version.

The installed movie-app fast stage reports its application checks not applicable because planned component source does not exist yet. This is an installation smoke test, not application verification. Documentation mockup scripts remain requirement inputs and are excluded from application component selection.

The source repository remains local. Movie-app has no GitHub remote, so no push or draft PR was attempted. Provide its remote URL when repository delivery is needed.

Fixture JSON records replace temporary directory prefixes with descriptive placeholders and are diagnostic records, not implementation-task receipts. Full command captures are produced by rerunning the supplied fixture scripts. No credentials or account data are included.
