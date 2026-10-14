# Acceptance specification

## Document structure

Adapt organization to the product while retaining these functions in one Markdown document:

1. Product purpose, actors, scope, document revision/readiness and governing sources.
2. Test approach and coverage-family applicability, including priorities, levels, fixtures and environment prerequisites.
3. Compact case index grouped by capability or engineering concern, with each case ID linked to its detailed heading using a native Markdown anchor and its primary level visible.
4. Detailed cases with independent setups and observable outcomes.
5. Gaps, assumptions, required decisions and evidence prerequisites.
6. Source register, bidirectional coverage register and retired-case history in appendices.

Keep essential rules and short cases visible. Use native heading links and narrow tables; long engineering examples may use a named `<details>`/`<summary>` disclosure with blank lines around fenced Markdown. Keep heading anchors outside disclosures and avoid nested disclosures. If the target renderer cannot support disclosures, use ordinary visible headings. Follow the source/user's natural language; do not translate protocol literals or identifiers for prose fluency.

Quote or escape literal HTML/markup in source-derived test inputs and state oracles so the rendered specification displays the input instead of executing it or hiding subsequent content. Preserve exact payload bytes in appropriately fenced or inline-code examples.

Define unfamiliar concepts near their first use. Use product terms in scenario prose and preserve exact technical names only where they identify a tested contract. A brief linked glossary is useful for recurring specialized terms. Keep source history and authoring administration out of product journeys. A document reader must be able to find what to test, why, with what setup, and how to judge it without the authoring chat.

### Case separation and section breaks

Place one standalone Markdown thematic break (`---`), with a blank line before and after, between complete detailed cases. Put it after the previous case's final field and before the next case heading; when a capability heading intervenes, one break before that heading serves the same boundary. Keep the first case beside its group heading. Use the same breaks between major blocks such as fixtures, case details, gaps and coverage registers when they improve scanning. Headings handle smaller subsections; avoid repeated dividers between individual metadata fields.

Keep breaks outside code fences, tables, lists, frontmatter and disclosures. Retain existing case IDs, heading anchors, index links, metadata labels, scenarios and evidence status. Confirm that breaks render as horizontal rules rather than heading underlines and that both the checker and a reader can still locate complete cases.

## Classification

| Axis | Default convention |
| --- | --- |
| Priority | P0: critical release behavior or severe loss/security risk; P1: important functionality, contracts and recovery; P2: lower-risk supplementary checks. Record rationale by case or group; preserve established project labels. |
| Level | Unit, component, contract, integration, end-to-end or system as appropriate. Name the actual boundary and components exercised. For a manual review, record the reviewed boundary here and Manual under Automation. |
| Platform | The tested surface: web, mobile, API, RPC, command, file, worker, database or relevant project terminology. |
| Category | Positive, Negative or Edge. A required denial is a valid acceptance outcome; every requirement need not have a successful-action case. |
| Automation | Candidate, Manual or Undecided, with prerequisites where relevant. Candidate is not implemented automation. |
| Status | Not Run, Passed, Failed, Blocked or Stale. New scenarios are Not Run. A draft blocked by an unknown expected outcome belongs in the gap register. |

These axes are independent. A browser case is not automatically integration or UAT; UAT/smoke/regression selections follow the agreed purpose and environment. Classify a case at the lowest boundary that proves its obligation, with additional real integration/e2e proof where boundary composition matters. Data constraints, transaction rollback and crash durability may require direct persistence observations; a browser-only oracle is insufficient for those obligations.

### What each level proves

| Level | Proof boundary | Limits of that evidence |
| --- | --- | --- |
| Unit | One isolated rule or module with explicit inputs and independently derived outputs; controlled time/randomness where needed | Does not prove persistence, transport, durable recovery or real provider/host behavior |
| Component | An assembled component or interaction with controlled dependencies | Shows that component's behavior, not the replaced dependency's enforcement |
| Contract | Producer/consumer schema, generated compatibility or protocol shape | Compilation/schema checks alone do not prove a working network or database |
| Integration | Actual collaborating components and the named real persistence, transport or filesystem boundary | Simulated provider failures establish only the simulated condition; delivery/host claims need actual provider/host evidence |
| End-to-end | A complete user/caller journey through its participating real boundaries | Name which external boundaries remain simulated or unverified |
| System | Packaged runtime, commands, resource behavior or operational recovery | A local environment does not establish unmeasured deployment guarantees |

Derive applicable levels from the accepted testing commitments and the defect being tested. When unit coverage is required or requested, author concrete isolated cases rather than relabeling a multi-component case. Link complementary cases where isolated rules and real enforcement both need proof. A source that requires only a specific external boundary does not automatically require a unit counterpart.

## Detailed case format

Default IDs are `ATDD-001`, `ATDD-002`, and so on; preserve existing project IDs. Headings use `### Case ID: Descriptive title` with a single-token ID. This and the metadata labels below are the small parsing contract used by the checker. Preserve these labels even when surrounding prose is localized; a supplied incompatible format requires an explicitly documented checker limitation, not a false validation claim.

Each active case has these fields, in this order. Separate metadata paragraphs with blank lines so labels remain readable in rendered Markdown:

- **Sources:** Comma-separated obligation IDs from the independent inventory, not just a document name.
- **Priority:** One agreed priority.
- **Level:** One primary level; describe participating components under Verification.
- **Platform:** Relevant tested surface(s).
- **Category:** Positive, Negative or Edge.
- **Automation:** Candidate, Manual or Undecided.
- **Status:** Not Run unless actual evidence was supplied.
- **Preconditions:** Actor, starting state, environment and boundary; include a shared fixture reference only when fully defined in this document.
- **Test data:** Concrete values or an unambiguous deterministic fixture recipe. Use `Not applicable — reason` only when values do not affect the behavior.
- **Expected UI:** Required only for cases asserting a graphical screen/component outcome; follow [expected UI guidance](#expected-ui-and-design-references). Place it here; omit it for cases without an applicable UI.
- **Scenario:** A fenced `gherkin` block with Given, When, Then and optional And/But. Then/And statements are the expected outcomes; avoid copying the same assertions into another field.
- **Verification:** How each outcome is observed; required real boundaries versus test doubles; exact engineering assertions or evidence artifacts when needed. State the defect this case would catch where it is not already obvious. Specify the actual response, UI observation, persisted rows, file bytes, events or other evidence needed for this case. Read-only cases do not acquire mutation/receipt/audit assertions merely by sharing a fixture; choose observations relevant to their outcomes.
- **Cleanup:** Isolation/reset procedure or `Not applicable — reason`.

Cases with Passed or Failed status additionally require **Evidence**, **Revision**, **Environment** and **Executed at** fields. Evidence must link to supplied or actually observed results, identify the tested build and relevant expectation version, and record when/where execution occurred. For Blocked status require **Blocker**. New Not Run cases may describe required future evidence under Verification without implying execution.

### Example — generic documented file contract

This example assumes the source explicitly requires preservation after a failed replacement. It is illustrative, not an added requirement for every product.

#### Case ATDD-001: A failed replacement preserves the saved content

**Sources:** AC-01

**Priority:** P1

**Level:** Integration

**Platform:** File

**Category:** Negative

**Automation:** Candidate

**Status:** Not Run

**Preconditions:** An isolated workspace contains a saved entry; the replacement operation can be interrupted before commit.

**Test data:** Saved content is `alpha`; replacement content is `beta`.

**Scenario:**

```gherkin
Given the entry contains "alpha"
When replacing it with "beta" fails before the change is committed
Then reopening the entry returns "alpha"
And the operation reports a failure
```

**Verification:** Exercise the real storage boundary and reopen from a fresh reader. Capture the result and returned failure. This detects partial replacement and false success.

**Cleanup:** Remove the isolated fixture directory after inspection.

## Expected UI and design references

For every case that asserts a screen or component outcome, add **Expected UI** after **Test data** and before **Scenario**. This is a conditional explanatory field, not a universal required parser field. Identify the production route/panel/host context, direct approved design page/state references, and concise relevant expectations for layout/anatomy, controls, feedback, retained/cleared values, focus/accessibility and safe next actions. Select applicability from the actual assertions, not a Web platform label or source-ID prefix; backend-only/unit rules, database constraints and command-only outcomes need no fabricated screen.

Add a compact UI reference index connecting applicable flows/state groups to technical frontend owners/anchors and case IDs. Shared policies/session boundaries, editor panels and externally hosted views are not automatically standalone pages. Use stable source state IDs; mockup fragment selectors and fixture role/state switches are not required production selectors or features. Component-only cases can reference component specimens without inventing routes, APIs or a complete app.

Keep per-state tables concise and independently testable: source reference, actor and actual action/response producing the state, visible semantic outcome and safe next action. Review each trigger against its operation; a read failure does not have a mutation commit point. Avoid long extracted DOM text, ellipses hiding assertions and generic error/stale triggers applied to unrelated states. Preserve committed copy/controls and existing acceptance meaning; references support lookup rather than replace the case's oracle.

Separate fixed branding, selected interaction rules and required fields from replaceable fixture titles, counts, dates, widget shorthand and simulated results. Technical contracts govern effective limits, presence, permissions and distinct audit/approval/execution outcomes. Record an incomplete illustration or material conflict explicitly without introducing product policy or deleting committed behavior.

Use existing approved visual previews when requested/useful, with alternative text and captions identifying scope, fixture status and known theme/viewport context; link full references. No screenshot is universally required, and an overview is not evidence of every state or a pixel-perfect production baseline. Keep test data synthetic and preserve permitted asset/source scope. UI verification uses the actual interface and declared boundaries, with both visual/accessible observations and real backend/host proof where required; mockup rendering is design evidence only.

For projects without graphical UI, use their native observable contract and omit this field/index. Inspect available artifacts instead of requiring a stock design-system package. Synchronize technical source versions/hashes and links through their owners; retain case IDs, review changed expectations/evidence freshness and keep planned cases Not Run.

## Security-first and consistency acceptance

Derive cases from the selected technical contracts and accepted security obligations using the [coverage method](coverage-design.md). Trace entry point → authoritative permission/validation owner → dangerous input use or returned projection → observable result. Cover applicable API/browser, asset, internal transport, tools/resources, operational endpoints, imports and workers; do not invent absent components. A missing consequential quota, replay or failure policy is a source gap, not permission to add one silently.

### Injection and authorization oracles

Test the actual selected control, alongside legitimate content that must remain usable. For SQL/ORM queries, injection-looking values must remain bound data; assert authorized result boundaries and absence of extra reads/changes through the real database when integration enforcement matters. Include dynamic sort/identifier rejection and literal wildcard behavior separately. A source/code review can check binding, but neither a single payload nor a mock proves universal injection resistance.

For XSS, observe the real rendered context, URL handling and absence of executable nodes, event handlers or unwanted navigation. Permitted markup-looking plain text must display as text; do not invent blanket stripping/rejection. Policy-header checks complement browser behavior. Fence/escape hostile examples in the document itself. For process/import/upload boundaries, include malicious filenames, paths and option-like inputs; observe the actual argument/path boundary and absence of extra commands, external fetches or writes outside the allowed location. Fixed executables and shell-free calls still need argument controls. Treat retrieved/model instructions as untrusted content where tools exist.

Test authenticated-but-unauthorized callers, spoofed internal identities, wrong receiver/scope and cross-owner reads/replays against the owner's contract. Rejections must expose only safe errors and leave prohibited effects absent. Do not infer authorization from a hidden UI control, successful mTLS or a schema field alone.

### Browser storage, cookies and cache oracles

Derive the browser persistence allowlist and cookie lifecycle from approved source contracts. Use isolated rule cases for preference validation/fallback/storage failures, and real browser/HTTP/identity boundaries for forbidden application writes, response caching, credential delivery and session transitions. Give each planned observation a concrete oracle and scope: a fresh empty store does not prove the application never writes sensitive data; inspect actual application calls and resulting values. Do not imply that an allowlisted storage adapter prevents arbitrary XSS from using browser APIs.

For non-persistent cookies, inspect issuance and renewal without Expires/Max-Age separately from confirmed deletion with Max-Age=0. Assert the exact selected Secure/HttpOnly/SameSite/name/path/domain rules, raw-credential Set-Cookie-only delivery, server expiry/revocation and valid versus expired/revoked browser restoration. Browser close and localhost plaintext experiments are not reliable expiry/Secure oracles; verify actual attributes and the configured secure listener. Keep intended script-readable CSRF values distinct from credentials, so a blanket HttpOnly/forbid-all-token assertion does not break anti-forgery behavior.

Observe sensitive-response headers including early errors, approved static caching, account transitions and history-restored DOM/controller state. No-store alone cannot prove cleanup. Map CWE-539 persistence and CWE-614 missing-Secure to the actual enforcing owner and cases; retain historical standards context and use the selected version's requirements, not unverified numeric aliases. A project-specific stricter policy is stated as that policy. Cases stay Not Run until executed evidence exists. Projects without browsers need no manufactured cookie, UI or storage scenarios.

Cross-check session/CSRF/storage oracles across the actual selected reads and mutations: bootstrap is not a mutation requiring the token it supplies. Distinguish confirmed revocation, uncertain logout, authoritative expiry and restored-cookie presence; verify concealed history/account state and stale replies without demanding extra API arguments. Diagnostic assertions exclude both raw credentials and CSRF values while preserving intentionally readable anti-forgery channels. Record the actor, enforcing owner and failure signal for each transition.

### JSON log, severity and diagnostic-safety oracles

Derive emitted-log expectations from the technical source's selected JSON schema, fields, level vocabulary/aliases, verbosity settings and sink scope. Include isolated formatter/level/bound/config rules and complementary actual process/framework/boundary capture. Parse each physical line independently; test UTC timestamp/type/identity, event outcome versus transport status, early denials, worker recovery and valid bounded records. Pretty-printed examples and parser-only success do not prove emitted output or security. Retain existing scenario IDs/statuses; add distinct source-supported cases only where they catch an uncovered defect.

Observe safe correlation across trusted calls and independent concurrent/cancelled contexts, no-context boot and worker restart where applicable. Keep trace/span formats distinct from established operation/correlation IDs and authorization. Use canaries in credentials, CSRF, bodies, query values, filenames and exception causes; verify every permitted verbosity and alternate sink excludes them without persisting raw captured secrets as test artifacts. Challenge CR/LF/quotes, duplicate/nested fields, dropped-attribute leaks and decoded-viewer script execution. Log injection tests must inspect record boundaries as well as valid JSON.

Exercise bounded queues, oversized records, unavailable/full sinks, rotation, drop signals, command filtering and protocol stdout protection at the source-defined proof boundary. Compare durable receipt/audit/work evidence independently: missing log completion is not rollback, a request-start is not success, and diagnostics cannot replace transactional history. Declare third-party native-stream and simulated-sink limits. Adapt to a monolith or offline CLI without inventing browser sessions, distributed tracing, collectors or employer infrastructure. These are Not Run obligations until real evidence exists.

### Configurable throttling and resource admission

Use concrete isolated values for the source-defined setting names, defaults, units, bounds and precedence. Cover invalid/unset configurations, any explicitly supported disable mode, restart/reload and active-window transitions. Test just below, at and above each selected quota, reset/expiry with controlled time, and safe retry information. No stock request counts, windows, algorithm or counter database become acceptance defaults.

Coordinate concurrent calls through the actual shared counter boundary where selected; observe admitted counts, persisted state and rejected effects rather than relying on sleeps. Include replica agreement, trusted source/credential/account dimensions, permitted independence across scopes, and duplicate profile checks keyed by profile plus trusted scope/key. Cover protected/public reads, mixed operations, batches/aliases and adapter-local limits only when the source supports them. Exercise limiter-unavailable behavior and confirm denied admission creates no new business mutation/receipt. Record end-user-quota exclusions and separate identity/resource bounds for recovery workers and probes.

Separate quota consumption from business idempotency: repeated attempts may be throttled while successful replays must not repeat effects. For performance cases, record positive isolated quota settings, keep enforcement enabled, and report offered/admitted/completed/throttled/failed work. A throttled workload cannot satisfy a source-defined admitted-throughput or latency claim merely because rejection was fast.

### Concurrency, retries and durability

Inventory all effectful interactions, including draft save/discard, uploads, imports, lifecycle changes and maintenance where present. Use source-defined stable per-intent keys, owner scope, fingerprints and lifetimes; distinguish a saved submission's ID from the operation saving it. Cover same-content and concurrent replay, changed-content conflicts, permitted independence for another scope and forbidden receipt inspection. Include response loss after commit: replay returns the original safe outcome with no duplicate mutation, audit or follow-up work beyond the contract's explicit attempt logging. Receipts must not leak protected payloads.

Test later edits/deletion/discard/expiry followed by old replay: no resurrection, stale mutation, refreshed lifetime or invented original payload. Follow the specified receipt retention/tombstone rule; missing consequential expiry behavior remains a gap. Include distinct-operation stale writes, uniqueness races, current deletion-impact freshness, lock-order/deadlock recovery, rollback and required mutation/receipt/audit/work atomicity. Inject faults at named commit/effect boundaries and observe persisted state from a fresh reader.

Where workers exist, coordinate competing claims, crash/restart, lease expiry and stale-owner commits. Test remote-effect deduplication or reconciliation separately; fencing a local lease does not by itself prove one external effect. Use meaningful isolated rule cases where requested and complementary real selected database/filesystem/transport integration for persistence, locks and durability. Keep unexecuted cases Not Run and simulated-provider limits explicit.

### API, database and consumer reconciliation

Map accepted wire fields through owner DTOs/ORM to actual stored or derived values and authorized consumers. Check units/precision, omission/null/clear, encryption/decryption boundary, field exposure and audit actor/subject/outcome meanings. Compatible scalar types do not establish a declared response field; do not demand internal columns be serialized or return persistence entities. Distinguish an approval outcome from later publication/execution.

Direct database cases assert only actual types, keys and constraints. Test application-only policy through the enforcing API/module: `NOT NULL` does not prohibit blank text, and a text column does not imply a configurable maximum. Do not assert cryptographic validity as a storage constraint without a declared mechanism. Test policy tightening according to existing-value semantics. Reads do not acquire mutation-only version/policy/receipt inputs or audit side effects. Reconcile native contracts, examples, fixtures and coverage mappings together; preserve stable IDs and review evidence freshness on changes.

## Persistence redesign and evidence preservation

Derive storage cases from the current authoritative model, including typed variants and owner-specific extensions. A removed table does not imply its behavioral risk disappeared. Keep the same case ID for the same obligation, update its fixture and observation boundary to the replacement storage, and retain distinct risks instead of duplicating a new full-table scenario under every old ID. Preserve accepted outcomes and evidence status; a static document check cannot make an unexecuted acceptance case pass.

Use the technical design's old-to-new field/guarantee map to reconcile identities, uniqueness, foreign keys, authorized API projections, state transitions, retention and recovery. Check partial/invalid variant records through actual declared constraints, and cross-row/current-authorization rules through the enforcing transaction. When applicable, cover expiry versus permanent evidence, duplicate/replayed writes, concurrent initialization, worker start/completion/fence loss, notification recording versus delivery, immutable approval evidence and reference-safe cleanup.

Challenge both excessive splitting and unsafe consolidation. Scenario coverage follows observable obligations, not a quota of tables or cases. Do not introduce new storage, features, SQL engines or external integrations to make a fixture resemble a previous project. File-backed and offline systems retain their native locking, atomic replacement and recovery expectations.

Refresh source versions/hashes, case locators, UI expectations and bidirectional coverage against the finalized owner document. Preserve stable source identifiers and existing case IDs; use the established retirement/replacement mechanism only when an obligation actually changes. Report consistency checks separately from real database, transport or application evidence.

## Parameterization and shared fixtures

Use Scenario Outline/Examples when setup, trigger and observation are the same and each row supplies explicit inputs and independent expected outcomes. Include row labels when individual results must be traceable. Mixed passed/failed/not-run rows cannot become one Passed case; retain row evidence and use Failed if any executed row fails, otherwise Not Run until all rows pass. Keep separate cases for materially different enforcement boundaries, transitions, failure injection or outcomes.

Shared fixtures reduce setup text, not independence. Shared observation procedures may define how to inspect a boundary, but each case must identify its concrete expected observation; a generic verification paragraph is not an oracle. Each case must recreate/reset its prerequisites; group/run-order hints do not authorize dependence on another case passing. Name controlled clocks, randomness, ordering and synchronization for timing or race-sensitive checks. Avoid sleeps as the sole proof of completion; specify observable readiness/terminal conditions with source-defined bounds.

## Registers and parser contract

The checker recognizes the following exact table headers anywhere in the document. Use one table of each kind, plain IDs and comma-separated case IDs; retain the header spelling even when prose uses another language. Table cells must stay on one line; escape literal pipes as `\|`. Place full explanations outside the register and link them. Source locations are relative document links or URLs; source hashes describe the exact bytes inventoried, not rendered output.

| Source | Location | SHA-256 |
| --- | --- | --- |
| SRC-BRIEF | brief.md | The actual 64-character SHA-256 recorded in the independent inventory |

| Obligation | Source | Locator | Disposition | Cases | Reason |
| --- | --- | --- | --- | --- | --- |
| AC-01 | SRC-BRIEF | Section 2, AC-01 | Covered | ATDD-001 | The linked case asserts preserved content and failure feedback |

Each independently inventoried obligation appears once. Dispositions are Covered, Gap, Excluded or Deferred. Required obligations use Covered only when the mapped assertions are sufficient; otherwise use Gap, retaining any partial cases and naming what remains unknown/uncovered. Excluded/Deferred rows need a source-grounded reason and no active cases. They must match the independently recorded scope, never provide an escape from a missing required test. A missing scope decision remains a Gap until resolved.

Case Sources and coverage Cases must agree in both directions. Every mapped case needs a real obligation; supplemental risk cases use stable `RISK-...` inventory IDs with a source locator and a label explaining that the risk is inferred. An inferred risk can test an established invariant; if its passing outcome requires new product policy, record the unresolved decision instead of inventing a guarantee.

Use source-qualified obligation IDs only when existing IDs collide between documents. Preserve the original ID in the locator. Split compound acceptance criteria into stable clause references when one mapping would conceal an untested outcome. When different source IDs restate the same rule, retain a separately addressable inventory/register entry for each and map them to the shared cases; deduplicate scenarios, not source identifiers. The fresh source review verifies clause completeness; a numerical mapping count is not semantic proof.

## Updates and evidence

Retain IDs for the same behavior. New behavior gets a new ID; retired IDs are never reused. Record removed cases in this table, with a reason and replacement IDs where appropriate:

| Retired case | Reason | Replaced by |
| --- | --- | --- |

Leave Cases or Replaced by empty, or use an em dash (`—`), when there is no mapping/successor; words such as `None` are not IDs. Copy the inventory's source-grounded exclusion/deferral reason exactly into Reason; place additional discussion outside the register.

Review changes against a temporary copy of the previous document. If a case's expectation, setup, verification or governing source changes, mark previous execution evidence Stale until its continued applicability is established by a recorded impact review or a new execution. Preserve historical evidence and the reason for staleness. Do not relabel old evidence as a fresh run.

Document readiness is separate from execution status. `Ready for implementation` requires completed semantic review and no required coverage gaps; it does not assert passing software. Otherwise use `Draft with gaps`, identify affected obligations and retain useful completed work. Report source coverage, applicable categories and known gaps without claiming exhaustive testing of all possible inputs.
