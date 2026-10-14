# Coverage by behavior and risk

## Build the obligation inventory

Inspect requirements, business rules, permission matrices, acceptance clauses, UI states, technical contracts, persistence invariants, quality requirements and operational commitments. Retain each existing source ID, cross-reference repeated rules and map them to shared cases rather than duplicating scenarios. Keep separate clauses where a success case would otherwise hide a denial, boundary, side effect or recovery assertion.

Record the approved scope and source locator for every obligation before drafting cases. Source documents own behavior; existing code contributes facts and discrepancies, not automatic authority over approved requirements. Identify undocumented assumptions and material conflicts precisely. Missing optional documents are not a reason to invent an architecture or block all work.

## Resolve apparent gaps before assigning readiness

For each apparent gap, record the affected clause, current source authority and proposed resolution. Use these distinctions:

| Kind | Resolution |
| --- | --- |
| Source-resolved conflict | Apply established precedence or an approved override, state the superseded text, and author the resulting assertions; never claim the unchanged source already agrees |
| Consequential missing decision | Keep a precise Gap when choosing the expected result would create or change a product, security, compatibility or measurable acceptance commitment; ask only for that decision |
| Implementation detail | Test the established invariant without requiring an unselected query, private function, setting name or other realization unless it is itself contractual |
| Execution prerequisite | Specify the known rule and required future environment/evidence; retain the release dependency without calling lack of execution an unknown acceptance outcome |

A gap closes only when source-grounded reasoning and sufficient cases demonstrate the resulting obligation. Moving a row or renaming it does not close missing coverage. Parameterized settings need concrete isolated fixture values and boundary observations; record the resolved release setting when it affects later evidence. Accepted numerical thresholds and source-mandated evaluation dimensions remain binding. Missing consequential workloads, targets or provider/host guarantees remain gaps until resolved, rather than being filled with stock numbers.

## Applicability matrix

Include a compact applicability table in the document: family, relevant boundaries, case groups or gaps, and rationale when excluded. These are conditional review prompts, not new product features.

| Family | Examine when applicable |
| --- | --- |
| Product and UI | Main/alternate journeys; search/filter/sort/pagination; forms; lifecycle; permissions; loading/empty/error/success/uncertain states; drafts; navigation; responsive layouts; accessibility; localization and supported platform compatibility |
| Contracts | Allowed/denied actors; input validation; omission/null/empty/clear; output projections; errors; serialization/precision; versions/compatibility; ordering; deadlines/cancellation; partial results and consumer/provider agreement |
| Data integrity | Constraints; uniqueness versus duplicate requests; transaction boundaries; required audit/effect atomicity; concurrent updates; pagination ties; migrations/backfills; seed/import reruns; retention, deletion and restore invariants |
| Reliability | Retries and one retry owner; total attempt/deadline bounds; uncertain outcomes; idempotency; durable work; competing workers; leases/fencing if selected; crash points; restart, cancellation and exhaustion recovery |
| Security and privacy | Authentication/session lifecycle; authorization at authoritative boundaries; ownership isolation; injection and contextual output handling; uploads/path controls; resource abuse; encryption/key lifecycle where required; error/log/metric redaction |
| Operations and performance | Configuration precedence/validation; build/start/stop/readiness/exit codes; dependency outages; test isolation; workload/latency/throughput/resource targets; saturation/recovery; logs/metrics/alerts; backup/restore and rollout/rollback |
| Assistants and external providers | Tool capabilities; trustworthy exact-content human approval if required; changed/replayed/expired proposals; hostile retrieved content; actor/client isolation; real host behavior; provider rejection, ambiguous delivery and receipt evidence |
| Coverage integrity | Forward and reverse traceability; omitted clauses; source drift; explicit gaps; justified exclusions; duplicate cases; source-supported oracles; planned versus executed evidence |

For a mobile app, use its supported lifecycle, device and connectivity contracts. For a service-only product, focus on callers, workers and data boundaries. For an offline CLI, use commands, exit codes, file state, interruption and documented limits. No family silently adds a browser, server, database, tenant, assistant or external provider.

## Security and consistency coverage

Apply the [security-first acceptance guidance](output-contract.md#security-first-and-consistency-acceptance) when the corresponding boundary exists. Inventory injection sinks and returned projections, configurable quota admission, all effectful retry identities, concurrent integrity and actual storage/wire rules from governing sources. Keep enforcement evidence and negative/no-effect oracles case-specific. If a consequential expected outcome is missing, use the gap-resolution method above rather than selecting another project's stack, schema, numbers or policy.

## Select distinct cases

- Cover successful behavior and applicable rejection/error paths. A deny-only rule needs a case proving denial and absence of prohibited effects, not a fabricated positive operation.
- Partition values by distinct outcomes; use boundaries just below, at and above actual limits with units. Consider absent, empty, zero, false, malformed and Unicode inputs where the contract distinguishes them.
- Enumerate allowed and forbidden state transitions, repeat operations, stale reads/writes and concurrent actors. Use decision tables for interacting rules; use pairwise combinations only when sufficient for the risk. Document higher-order combinations when the rule depends on them.
- Specify fault locations around important boundaries: before commit, after commit/before response, before external send, after remote effect/before receipt, and restart where relevant. Assert both required effects and prohibited partial effects.
- Separate duplicate logical operations from distinct same-looking records. Include reordered, delayed, cancelled and repeated requests when behavior depends on them.
- When a rule is scoped to an owner, tenant, room, directory or another source-defined partition, test both enforcement within that scope and permitted independence across scopes. This distinguishes missing enforcement from an overbroad global restriction; do not invent a partition absent from the source.
- State workload, duration, percentile, resource limit, measurement boundary and threshold for performance cases from accepted sources. An unselected threshold is a decision gap, not a stock number.
- For security, test the actual control and source policy. Potentially hostile text may be valid content needing safe encoding; do not universally require stripping/rejecting it. Use synthetic isolated fixtures rather than real private data.

Prioritize by impact and likelihood with explicit rationale. Priorities order work; they do not remove low-priority committed requirements. Count independent rules and failure modes, not merely case rows or cosmetic role/data variants.

## Testability and assertion quality

Name the real defect or invariant violation each case catches. Challenge generic verification text: can a reader identify exactly what to observe and what would falsify this case? Match read, write, rejection and uncertain-outcome oracles to their actual behavior rather than attaching all fixture observations to every case. Derive expected results independently from requirements, hand-checked examples or established properties. Avoid copying implementation calculations into expected values or asserting the existence of a mock. Preserve exact copy/visual details only where the approved design makes them part of acceptance.

When unit coverage is committed/requested, enumerate isolated decision tables, boundaries and state rules explicitly, then identify which obligations also require integration. Keep one primary level per case; platform, category, automation and status are separate. Use doubles for controlled dependency responses at unit/component boundaries. Contracts, real persistence semantics, network cancellation, distributed recovery and provider/host claims need the corresponding real boundary in later verification. A mock or emulator proves only the explicitly simulated contract. State which evidence is local, simulated, sandbox-provider or actual client/provider evidence and which obligations remain unproven.

Use controlled clocks, seeds and coordinated actors for reproducibility. Every case must establish its state independently. Annotate manual/exploratory checks with a concrete mission and observable acceptance criteria; keep open-ended discovery distinct from a claim that a requirement passed.

ATDD specification precedes implementation. Superpowers' useful test-first principle informs the later handoff: for each new behavior, establish the intended failing assertion before implementing the change, then verify the correction using the project's selected tools. This authoring skill neither runs a red/green loop nor deletes existing implementation. Supplied evidence of already-working behavior is valid evidence, not a reason to force a failure artificially.

## Deduplication and challenge pass

Compare boundary, role/state/data partition, trigger, outcome and risk. Merge scenarios that differ only in wording or equivalent data. Keep cases whose variations expose a different authorization, transition, contract or fault. Different priority tags alone do not justify duplicating the same assertions.

Review cases against the full sources, not titles alone. Run a fresh edge sweep even for requirements with many cases. Check rejected operations leave required data unchanged; successful operations persist the right effects; recovery does not duplicate effects; and unknown outcomes remain honestly unknown until reconciled.
