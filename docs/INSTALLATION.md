# Install and maintain the workflow

Python 3.11 or later and Git are the shared runtime requirements. The package itself uses the Python standard library. Native coding-agent clients, language toolchains, scanners, browser tooling and external accounts remain separate dependencies. Installation does not execute application tasks or install those tools.

Run from the reusable source checkout:

```sh
./scripts/agent-workflow install --global
./scripts/agent-workflow install --repo /path/to/project --profile movie-app
./scripts/agent-workflow doctor --global
./scripts/agent-workflow doctor --repo /path/to/project
```

`--profile movie-app` selects the Kotlin/Spring/JPA, Svelte/TypeScript, Node and PostgreSQL profile. `general` is the default for other repositories; unsupported checks must be reported rather than passed. Add the user's `.local/bin` directory to the shell PATH if the command is not already discoverable. Every repository also has its own `.ai/bin/agent-workflow` entrypoint, which needs no global command or original source checkout.

The source `manifest.json` records the skill catalog, dependencies, activation, owners, source revisions and content digests. Installation verifies declared skill digests before copying. Native host skill entries point to the pinned bundle using relative symlinks. Copy or clone the whole repository, including its dot directories and symlinks, to relocate it.

| Content | Global installation | Repository installation |
|---|---|---|
| Bundle | `~/.local/share/agent-workflow/bundles/VERSION/` | `.ai/bundles/VERSION/` |
| Selection | `~/.local/share/agent-workflow/config.json` | `.ai/config.json` |
| Command | `~/.local/bin/agent-workflow` | `.ai/bin/agent-workflow` |
| File ownership | `~/.local/share/agent-workflow/install-state.json` | `.ai/install-state.json` |
| Backups | `~/.local/share/agent-workflow/install-backups/` | `.ai/install-backups/` |

The selected bundle path is relative to the configuration directory. A project copy is independent of global updates. Both global and local hooks dispatch through the project's selected entrypoint. A shared short-lived cache reuses a result only for the same host event identity and unchanged implementation fingerprint. Without a usable event identity, both invocations run; installation metadata never establishes hook trust. The local workflow still requires explicit gate verification before completion; hooks do not establish complete enforcement.

Existing instructions receive a bounded managed block. Existing JSON settings and hook entries are preserved. New native role names use the `aw-` prefix to reduce collisions. Matching global skills are reused; different pre-existing skill content is retained and reported. The portable version remains available in the pinned global bundle and every repository bundle. Review the reported versions before explicitly selecting the bundled skill with `resolve-skills`. Ordinary installation never replaces a conflicting personal skill directory. Built-in and plugin-managed skills are not installation targets.

Reused personal skill records retain their original content hash. Repeat installation recognizes these records, clears outdated conflict reports when content still matches, and reports later personal edits. `doctor` rehashes reused directories and checks their existence and type; a reused record alone does not establish integrity. Saved host verification is included when available and remains separate from structural file checks. Stale or unavailable native host verification does not become a pass.

Re-running `install` repairs missing owned files and reuses identical files. It refuses an in-place content change or a version change; use `update` after reviewing a new source bundle. Updates retain the selected profile and refuse locally edited owned files. An installation with a conflicting instruction, setting, adapter or runtime file changes nothing. Skill-name collisions may coexist because the complete bundle is still installed.

```sh
agent-workflow update --global --source /path/to/reviewed/agent-workflow
.ai/bin/agent-workflow update --repo . --source /path/to/reviewed/agent-workflow
.ai/bin/agent-workflow rollback --repo . --backup .ai/install-backups/TRANSACTION
```

Each successful change saves original regular-file bytes, symlink targets and modes in a transaction backup. Runtime write failures restore changes already made. Explicit rollback restores a completed transaction only when its changed files still match the installed snapshots; later user edits block rollback. Preserve backups until the update has been accepted. Older bundles remain available as tracked files until uninstall; changing a project's selection is an explicit configuration decision.

Select specific bundled global skills only after reviewing the conflict:

```sh
agent-workflow resolve-skills --global --hosts claude cursor --skills design-system ui-ux-pro-max --use-bundle
agent-workflow doctor --global
agent-workflow rollback --global --backup .local/share/agent-workflow/install-backups/TRANSACTION
```

`resolve-skills` uses the currently selected global bundle. It moves only the named existing skill directories into a private transaction directory under `install-backups`, outside every host's discovery folder, then creates relative bundle symlinks. The backup records each file hash, directory and file mode, empty directory, and symlink target. No symlink contents are followed when recording originals. Matching bundle symlinks are reused without another backup. The selected directories and the backup location must support renaming within one filesystem; a failed move leaves the original intact.

A recovery journal is written before any directory moves. Resolution failure restores original directories; if restoration also fails, the result provides the retained transaction path. Install, update, uninstall and further skill resolution then stop until `rollback` recovers that transaction. Keep the original backups intact. Modified links, changed backup contents or modes, and later installation-state changes block rollback rather than overwrite those changes. Rollback checks all selected paths before restoring any of them. These checks cover process interruption and ordinary I/O failures; they do not promise recovery from storage-device corruption.

Uninstall restores the original selected skill directories when their managed links and backups still match. An edited selected link or damaged original backup blocks uninstall before any files are removed. Original backups remain available after successful restoration. If an I/O failure interrupts uninstall while restoring directories, rerun uninstall; it recognizes already restored originals and retries missing links from verified backups. Unrelated skills and host settings are preserved.

```sh
agent-workflow uninstall --global
.ai/bin/agent-workflow uninstall --repo .
```

Uninstall removes unchanged owned content and the unchanged managed portions of instructions and hooks. It preserves edited files, reused personal skills, unrelated content, and backup records, then reports retained paths. Removing the local launcher during uninstall is expected. A source checkout can inspect or complete later cleanup. It never deletes unrelated worktrees or branches.

Use temporary homes and repositories for installer experiments:

```sh
./scripts/agent-workflow install --global --home /tmp/workflow-test-home
./scripts/agent-workflow install --repo /tmp/workflow-test-repo
python3 -m unittest discover -s tests -p test_installer.py -v
python3 -m unittest discover -s tests -p test_skill_resolution.py -v
```

An alternate `--home` is an installation target, not an environment override. Set the actual HOME environment consistently when testing native host discovery or global hook commands in that fixture. Do not start a different Codex app-server against a real home simply to inspect loading. See [host configuration and verification](HOSTS.md) for trust, reload, and runtime checks.
