---
name: workflow-install
description: "Install or maintain a managed agent-workflow bundle globally or in a repository; inspect conflicts, portability, upgrades and removal."
metadata:
  version: "1.0.0"
---

# workflow-install

Resolve the selected bundle from the repository .ai/config.json: its bundle value is relative to the .ai directory. Open each required skills/<name>/SKILL.md directly under that bundle, even when a same-named global skill is already available or loaded. Resolve supporting resources relative to the selected skill file. Use the selected global bundle only when the repository has no .ai/config.json; resolve its bundle value relative to the global configuration directory. Name-based discovery never overrides the repository pin.

Read the bundle README and run the local entrypoint with `--help` to use the installed CLI contract. Inspect the target host, existing managed manifest, repository profile, personal instructions, hooks and skill discovery paths before changing them.

1. Establish the installation scope from the request. A project installation includes its pinned bundle and a local launcher; a global installation supplies defaults and discovery. Reuse matching files; preserve unrelated content and report differing existing versions.
2. Run `install --global` or `install --repo PATH` with an explicit source bundle. Use isolated temporary homes and repositories when testing the installer. Runtime tools and services are separate dependencies; installing a skill does not install a compiler, scanner, browser or account.
3. Verify managed hashes, all 71 skill entries, native role discovery locations, supporting resources and project-relative links. A copied repository must resolve its scripts without the source checkout or original user home.
4. Apply upgrades only through an explicit `update`. Inspect edited-file conflicts, backups, selected version and rollback outcome. Repository configuration continues to select its own bundle after a global update.
5. Run `doctor` through the same runtime used by the host app where available. Report config/schema checks separately from a live skill/agent/hook discovery test. Trust and reload requirements remain visible; never fabricate user trust.
6. For `uninstall`, remove only unchanged managed content. Preserve user edits and unrelated hooks, settings, skills and instructions. Report retained paths and the reason.

Completion requires an actual install/doctor receipt, scope/version inventory, unresolved conflicts, available command path, and exact next steps for unavailable hosts.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
