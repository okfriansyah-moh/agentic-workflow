# Release 1.1 verification

Release 1.1.0 contains eight native roles and 74 skills: 47 packaged existing skills, 14 new skills, seven workflow adaptations and six anti-slop adaptations. Installation, native discovery, authentication, hook trust, fixture execution and application acceptance have separate results. The source remains local; publication was not requested. No movie-app application task was executed. No delivery remote is configured and no PR was published; the verification clone uses a local-only origin.

## Installation and preservation

The final runtime integration, source revision `93b15d46a452c28379a9aaebddfb8392be405074`, passed all 198 tests with zero failed or skipped tests and was explicitly installed globally and into movie-app. Both update results report version 1.1.0 and zero conflicts. Both structural doctor results are healthy, with 74 skill entries, no findings and no preserved conflicts. These structural results do not establish native host readiness.

The preservation check found 113 protected documents unchanged. All 46 tasks across 20 groups indexed without errors, and every task remained `Not started`. Final repeated global update, repository update and selected skill resolution each reported zero changes; 47 existing skill installations remain reused. Earlier revision `674e8f4005dbbe5f40ccedc8f8bc039a2168148c` and its 182-test result remain historical.

A fresh movie-app clone ran with an empty home and no global `agent-workflow` on PATH. Its local entrypoint reported 1.1.0, doctor reported healthy with 74 skills and no findings/conflicts, and indexing returned 46 tasks, 20 groups and no errors. All 296 discovery symlinks resolved inside the clone and Git was clean. Movie-app commit `1424b450b70f3170531b3beb60523f208203bb9b` records the workflow installation; `4ef1c84dfadf8bb8efb2ce78252842f1dd1f0e64` excludes generated Python caches and removes 24 cache entries from tracking while preserving local files. Neither commit implements an application task.

Durable machine-local rollout evidence is retained under `/Users/mekari/Developer/personal-project/movie-app/.ai/evidence/release-1.1.0`. This path identifies this installation's evidence, not a runtime dependency. Its `browser-tools/` subtree contains the byte-preserved capture package and passed verification at that location. The six final CLI runs are retained under `native/final/<scope>/<run-id>/`; `rollout/host-matrix.json` summarizes their results. The `rollout/` directory also retains the combined tests, doctor results, repeat-install results, document-preservation check, fresh-clone result and authored-wording scan. The scan covered 46 changed authored files and passed.

The browser/tool package preserves 795 raw files and 800 inventoried files, including all 21 hashes listed by the independent browser review. The inventory SHA256 is `48aacc20e11b1cc664977fabf6728b1c81e78e5bf5a02226c9977588aab884ea`. Verification passed after copying the package to another directory and rejected a deliberately changed file. Its `relocation-map.json` resolves original absolute paths without rewriting evidence. Run `python3 verify-inventory.py` from the retained `browser-tools/` directory after moving it.

## Native host results

The following observations came from retained runs on 2026-10-15. Codex, Claude and Copilot probes used disposable fixtures; they do not establish loading in movie-app's existing chat. All four hosts still have blocked final native readiness. Later adapter or configuration changes require fresh evidence for any newly claimed result.

| Host and observed runtime | Observed result | Remaining boundary and user step |
| --- | --- | --- |
| Codex desktop engine, `0.162.0-alpha.17.2` | Both final scopes timed out at 120 seconds with the fixture unchanged, no edits and no gate runs. The user reports reviewing and trusting both exact global and project hooks; this is user-attested trust. | Role/skill catalogs, completed worker lifecycles and actual hook execution remain blocked. The CLI's read-only sandbox previously denied a backend write; desktop UI automation is unavailable. No permission bypass was used. |
| Claude Code, `2.1.283` | Final native initialization listed the roles in both scopes and all 74 required global skills. The repository catalog exposed 155 skill names. In each scope, passing and failing native edits each produced exactly one gate receipt. | The metadata omits the selected main Forge identity and exact hook source/edit correlation. Repository skill names establish availability but omit selected project paths. Complete orchestration, project precedence and hook trust therefore remain blocked. |
| Cursor GUI, `3.24.12` | Native global and repository Customize views listed exactly eight `aw-` roles and preserved five personal roles. Both native Forge/backend/independent-reviewer chains completed. After dispatch corrections, global passing and failing writes each produced exactly one gate receipt with two managed hooks configured; the repository failing write produced one with four managed hooks configured. | The locked desktop blocked the repository passing write and inspection of visible failure feedback. All 74 skills and project precedence remain unverified: a global plugin shadows `design-system`, and the repository picker opened a global `acceptance-verification` path. Explicit pinned-skill reads were observed. |
| Copilot CLI, `1.0.94` | Both final scopes listed all 74 required enabled skills among 83 total entries, and instruction-source discovery passed. Both delegation phases timed out at 120 seconds. The repository run wrote the passing value but produced no gate receipt, completed no reviewer and had a truncated capture. | The final streams omitted native custom-agent catalog events. The earlier interactive `/agent` capture proves eight user roles for its observed session; historical event replay is separate. User profiles win over project profiles. Final project role selection, complete orchestration and hook execution/trust remain blocked. |

The final CLI records all report overall status `blocked`:

| Host | Global run | Repository run |
| --- | --- | --- |
| Codex | `20261015-094106-7c15fc4a` | `20261015-094312-c67db7fe` |
| Claude | `20261015-094105-db323061` | `20261015-094327-ac692528` |
| Copilot | `20261015-094102-bcbf8f27` | `20261015-094310-1d988f09` |

Native records retain each runtime and configuration fingerprint. The earlier corrected CLI runs, catalog-event replay and screenshots remain historical evidence for their recorded inputs; they are not substituted for the final runs.

Cursor's completed role lifecycles predate the dispatch correction; the relevant role profile hashes are unchanged, and final record binding is separate. The post-correction gate counts establish one gate receipt per observed write, while confirmation that each configured wrapper executed remains blocked. Controlled concurrent tests passed for all four generated wrappers; this is fixture proof, separate from native execution. The locked desktop prevents the remaining UI inspection and repository passing edit; unlocking that session is the concrete next step for those retained checks. Codex's user-attested trust does not establish successful hook execution. These are recorded limitations, not promised passes or additional application work.

Use the [native host procedure](HOSTS.md) for read-only previews, evidence imports, trust and reload steps. Native verification uses the host's inherited model settings and may consume normal model usage. Review the exact hook in its host's native trust interface. No approval bypass or inferred trust is accepted.

## Managed tools and Context7

The actual global installation and status records report Playwright CLI 0.1.22 installed with a successful full Chromium launch, and Strix 1.7.0 installed but inactive. The tool lock retains the CLI's exact Playwright dependency, `1.64.0-alpha-1790635538000`; its prerelease status is explicit. Chromium revision 1247 was downloaded through the pinned driver. Local runtime hashes detect later modification; the browser metadata does not supply an independent publisher checksum.

Global and repository Context7 configuration results cover Codex, Claude, Cursor and Copilot, with host authentication unverified. An anonymous public probe reached the service and listed `resolve-library-id` and `query-docs`; separate public requests resolved Svelte documentation and retrieved TypeScript props examples. This establishes the recorded public retrieval only. Cursor's native OAuth attempt timed out after two minutes. Native OAuth remains blocked until a successful host connection is observed.

Complete authentication inside the selected host: `codex mcp login context7`, Claude `/mcp`, Cursor's Context7 connection action, or Copilot `/mcp auth context7`. Restart or reload affected sessions after configuration changes. Authentication credentials stay with the host; this report contains no tokens. See [Context7 setup and native paths](TOOLS.md#context7-configuration-and-authentication).

Strix preflight found Docker available and its daemon reachable. Provider model and key environment variables were absent, provider authentication was unverified, and stored credentials were not inspected. No assessment was authorized or executed. A future assessment requires an explicit request, authorized target and working provider configuration; installation does not authorize scanning. [Tool installation, status and removal](TOOLS.md#commands-and-storage) and [Strix preflight](TOOLS.md#strix-stays-inactive-until-requested) provide the supported commands.

## Browser fixture evidence

Independent reviewer `release11-installer` accepted the original fixture review on 2026-10-15. The reviewer inspected screenshots and original sample frames, verified listed hashes and decoded pixels at accepted video presentation timestamps, and recalculated contrast against the fixture design. This is workflow fixture verification, not movie-app screen or feature acceptance.

| Fixture | Desktop, 1280px | Mobile, 375px |
| --- | --- | --- |
| Clean, `AW11-UI-01` | All six design checks passed | All six design checks passed |
| Deliberately broken, `AW11-UI-02` | Width, text size, contrast, accessible-name and interaction defects detected | Same defects plus horizontal overflow detected |

The clean fixture used 16px body text, contrast approximately 8.26:1, a named reserve button and the observed result `One slot reserved`. The broken fixture used 9px body text, contrast approximately 1.51:1, an unnamed button and an unchanged result. Expected negative results demonstrate defect detection.

The original CLI video scaled the page into a larger gray canvas and remains supplementary. Separate viewport recordings supplied the readable samples. A mislabeled desktop clean frame was rejected and replaced with the verified frame at video time 0.5 seconds. The mobile video encoded at 374×812 although its viewport and screenshot were 375×812; the reviewer documented this and found the inspected text and results readable. Complete videos were not replayed end to end. Wall elapsed times are not assumed equal to video presentation timestamps.

The later portable helper run retained four measurement sets, screenshots, traces and separate recordings. Those captures do not inherit the original independent review: no separate original-frame review for the later videos is included. The retained original review identifies accepted samples, rejected history and exact file hashes.

To reproduce fixture captures, run the server from the source checkout in one terminal:

```sh
python3 -m http.server 45021 --bind 127.0.0.1 --directory tests/fixtures/browser
```

Then use the installed pinned CLI and matching driver:

```sh
python3 scripts/check-browser-fixtures.py --output /tmp/browser-review --session workflow-review
node scripts/record-browser-fallback.mjs --runtime /path/to/managed/playwright-runtime --output /tmp/browser-review --url http://127.0.0.1:45021
```

A successful capture is not visual acceptance. Inspect original frames, screenshots, actual results and the adopted design before accepting evidence. [Browser evidence guidance](TOOLS.md#browser-evidence) describes the recording fallback and supported CLI features.

## Backups and restoration

The four original Claude/Cursor `design-system` and `ui-ux-pro-max` directories are retained under `/Users/mekari/.local/share/agent-workflow/install-backups/20261015-085152-skills-3f9d6128/originals/`, with paths beneath `.claude/skills/` and `.cursor/skills/`. Its `transaction.json` records file hashes, modes, directories and link targets. Preserve that entire transaction outside host discovery folders.

The recorded initial update backups are global `20261015-085135-fda75390` and repository `20261015-085146-01e50eaf`. The earlier corrective backups are global `20261015-091002-e5378afd` and repository `20261015-091002-b2b80532`. The final runtime update created global `20261015-093819-bdd4f1f3` and repository `20261015-093820-c1dfc301`. Later documentation updates can add transactions; inspect current ownership and exact backup order before restoration.

These supported commands restore the named transactions when their expected state still matches:

```sh
agent-workflow rollback --global --backup .local/share/agent-workflow/install-backups/20261015-093819-bdd4f1f3
agent-workflow rollback --repo /Users/mekari/Developer/personal-project/movie-app --backup .ai/install-backups/20261015-093820-c1dfc301
agent-workflow rollback --global --backup .local/share/agent-workflow/install-backups/20261015-091002-e5378afd
agent-workflow rollback --repo /Users/mekari/Developer/personal-project/movie-app --backup .ai/install-backups/20261015-091002-b2b80532
agent-workflow rollback --global --backup .local/share/agent-workflow/install-backups/20261015-085152-skills-3f9d6128
```

These are recovery instructions, not actions performed during verification. Roll back later applicable updates in reverse order before the skill-resolution transaction: its direct rollback deliberately blocks if installation state has changed since resolution. Modified links, changed backup contents or user edits also block restoration. Inspect and preserve the reported changes instead of forcing recovery. Global uninstall is a broader alternative that removes unchanged owned workflow content and restores the selected original skill directories; external tools and credentials have separate removal procedures. See [installation recovery and uninstall](INSTALLATION.md) and [tool removal](TOOLS.md#commands-and-storage).

## Starting work after setup

Use the existing [start/resume examples](../README.md#start-and-resume-in-a-chat), [coordination contract](COORDINATION.md), [skill catalog](SKILLS.md) and [tool setup](TOOLS.md). The workflow loads relevant skills from the project's selected bundle. An unresolved mandatory check still blocks the affected task; installed skills alone do not establish available compilers, scanners, accounts or native trust.

The rollout has not dispatched movie-app's 46 tasks. A future delivery PR requires the project's remote URL and successful task verification. Source publication, PR merge, deployment and external messages remain separate actions.
