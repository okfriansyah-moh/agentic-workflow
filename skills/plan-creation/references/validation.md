# Validation record

Evaluated locally on 13–14 October 2026. The installation audit in the shared skill workspace retains the full reports, generated temporary packages, source fingerprints, checker output and reviewed file hashes. These records evaluate the skill and its document checker; they do not establish application success.

## Checker and bundle

The 50 CLI-level checker tests pass. They cover valid unexecuted plans, read-only behavior, text/JSON output, proposed and existing paths, multiple repositories, IDs/membership, missing links/anchors, reference-style links, dependency cycles, source freshness, coverage/inventory ownership, independent-review fields, visual-review requirements, unsupported completion, evidence files/revisions, shared writes, retired IDs and unsupported legacy layouts. Explicit negative fixtures include duplicate IDs, broken links, cycles, missing verification ownership and unsupported Done claims.

The official skill validator passes for plan-creation and the updated writing-plans route. The bundle validator passes for plan-creation. The personal wording checker passes for the complete authored bundles. These structural checks do not prove that every source obligation was extracted or that an acceptance assertion is sufficient.

Independent implementation review found three checker defects: reference-style links in table cells lost document definitions; Passed evidence could link only to a directory; retired IDs lacked syntax/uniqueness checks. All were corrected and independently rechecked. Additional controls cover valid retirement, ordered shared writes, inspection-only overlap, and fenced reference definitions. No unresolved finding remained in that recheck.

A separate final reviewer approved the two instruction refinements described below, confirmed the unchanged checker/tests and routing, reran all 50 tests and five saved controls, and reported no actionable findings. That review excluded this subsequently completed factual validation record; its content is reconciled to the retained reports by the author.

## Authoring and reader evaluations

| Evaluation | Observed result | Boundary |
|---|---|---|
| SpoolIn catalog discovery | One feature, frontend/backend/integration tasks, 96 scoped obligation rows: 89 Covered and 7 Excluded. Strict inventory check reports no findings. Includes seven visual states, source-derived contexts, ATDD ownership and real/controlled proof separation. | Initial scope omitted backend production; review corrected the evaluation to include it while preserving existing task IDs. Shared foundations and runtimes remain explicit external prerequisites. No application tests or screenshots were produced. |
| Small CLI change | One cohesive task with three obligations; standard/strict inventory checks pass. | No UI, database or extra scaffold was invented. Future local and subprocess assertions are distinct. |
| Cross-repository feature | Three tasks across producer, consumer and shared resources, with a single generated-output owner and serialized integration resources. Checks pass. | Repository separation alone did not authorize concurrency or agent launch. |
| Conflicting source decisions | Independent export task stays Ready; retention task stays Draft with two conflicting policy obligations. Standard check reports three gaps; strict exits 1 as intended. | No policy choice or governing-source rewrite was fabricated. |
| Accepted source update | Stable task/group/source IDs retained; completed synthetic task reopened, affected evidence Stale, old source and evidence preserved. Checks pass. | Historical records are explicitly synthetic; no new execution was claimed. |
| Unsupported completion claim | Negative fixture is rejected for unfinished dependencies and missing independent review. Manual review also identifies component-only proof mislabeled as real integration. | The checker cannot infer proof sufficiency from an existing report file. The review-only fixture retains its deliberate defects. |
| Fresh-session pickup | Separate reader used only the cross-repository entry point and explicit sources. Final verdict is PASS; next task, ownership, commands, proof boundaries and review gates are discoverable. | Initial reader found malformed-ID and error-observation ambiguities; recheck found a completion dependency conflict. Corrections were reviewed until all were resolved without changing source files. |

The reader findings led to two focused instruction improvements: name each cross-component assertion's observation point, and inspect completion criteria for backward dependencies as well as the declared task graph. Contributors can complete their local obligations while the feature retains its assigned integration proof.

## Limits

Evaluations use one real document corpus for a bounded feature and synthetic inputs for the other cases. They are not a complete SpoolIn release plan, automatic discovery benchmark, or proof across every project. Fresh-reader testing used the cross-repository package; the SpoolIn package received an author reader pass and parent scope review. The original project files and existing plans are preserved.

The checker requires Python 3 with PyYAML and validates only the declared package format. Remote sources are not fetched, semantic source completeness and evidence authenticity remain review responsibilities, and legacy layouts need manual checks unless conversion is requested. Planned commands, review results and visual evidence remain unexecuted until a separately authorized implementation supplies them.

## Numbered feature folders — 14 October 2026

The requested default now uses consecutive zero-padded numerical feature prefixes in a dependency-valid order of first starts. Group H1 titles match complete folder names; stable group/task IDs and task dependencies keep their existing meaning. Templates, output/update contracts, fixture helpers and the checker agree. An existing unprefixed layout is converted only under an authorized request.

All 54 CLI-level checker tests pass, including four added controls for an absent prefix, zero start, skipped first number and mismatched group title. Skill-creator validation and the bundle validator pass on the proposed bundle. These checks validate the naming contract and retained checker behavior; they do not establish application success or prove that a chosen first-start order is semantically optimal.
