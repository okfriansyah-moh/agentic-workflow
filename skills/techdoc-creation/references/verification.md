# Engineering reconciliation and completion

Perform sequential architecture, frontend/backend, contracts/database, security, operations and fresh-reader passes. Use independent agents only when separately authorized. Review the main file, fixing contradictions rather than producing sidecar specifications.

## Coverage and contract reconciliation

- Inventory actual source requirement, acceptance and UI identifiers. Reconcile behavior and dispositions, not just occurrence counts. Preserve accepted decisions and supersession history.
- Walk each client flow through its API, enforcement owner, persistence, effects and verification obligation. Every required operation has a complete native contract; every exposed operation has a justified consumer and access boundary.
- Reconcile the communication matrix, service/module responsibilities and diagrams with all RPCs, HTTP paths, tools/resources, workers and provider calls. Check both reconciliation directions and avoid circular synchronous transaction assumptions.
- Compare frontend types, native schemas, DTO presence/clearing, column dictionaries, DDL, ORM mappings and indexes. Check consequential queries and lifecycle operations against physical/logical ownership.
- Challenge denied/stale/concurrent/replayed requests, timeout after commit, claims/lease loss, partial transfer, cancellation, attachment cleanup, seed preservation, migrations, encryption rotation and restore. Every relevant gap has an owner and recovery outcome.

## Security, admission and retry reconciliation

Review the [security/mapping](output-contract.md#security-first-enforcement-and-data-projections), [limit](output-contract.md#configurable-rate-and-resource-limits) and [concurrency/retry](output-contract.md#concurrency-and-durable-idempotency) requirements against actual entry points and owners. Check each dangerous sink, safe output context and prohibition with concrete negative oracles plus valid-content preservation. Include alternate transport/worker paths; authenticated identities still need action/object authorization.

Walk every quota from setting to validation, trusted key/scope, atomic admission, shared state, restart/config transition, safe throttle/outage result and affected operation. Review mixed profiles, public/protected reads, aliases, recovery/probe budgets and recorded performance settings. Walk every effectful operation from request identity/fingerprint through authoritative uniqueness and atomic commit to lost-response recovery, later object deletion and receipt expiry. Separate network attempts, business effects, user revocation counters and worker fencing. Check lease loss and remote-effect reconciliation independently.

Reconcile column dictionary, actual DDL/constraints, ORM/DTO transformations, declared wire fields and consumer permissions. Compatible storage types cannot justify nonexistent or unauthorized fields. Review audit projections and distinct outcomes; direct storage checks must not assert undeclared application policy. Read inputs must not inherit mutation-only conditions. Compare synchronized consumer documents against saved source versions/hashes, keeping owner boundaries and truthful execution status.

For reusable-guidance changes, exercise bounded service, database-backed monolith and offline-tool fixtures against raw approved sources. Challenge blanket sanitization, unsafe dynamic identifiers/arguments, entity serialization, app-policy-as-database checks, read-version assumptions, scope-blind quotas, replay resurrection and quota-dominated benchmarks. Inspect actual outputs and counterexamples, not just keyword matches. Report same-agent versus independent evaluation, static validation versus runtime proof, and any rendering/discovery limitations.

## UI reference reconciliation

Apply the [UI handoff rules](output-contract.md#ui-references-and-implementation-handoff). Compare adopted page/state inventories with the frontend map, exact production context, feature/component owners, API dependencies and acceptance groups. Resolve file/heading/HTML fragments and inspect referenced states; a valid fragment in the wrong page is still a semantic mismatch. Verify all relevant success, pending, denial, conflict, uncertain and recovery expectations without treating every flow as a route.

Check previews against their declared scope and captions, required copy versus replaceable fixture values, accessibility/response contexts and discrepancies governed by current contracts. Verify representative image rendering and navigation where tooling permits; do not claim mockup rendering proves the application. Review future-plan handoff completeness and source version/hash synchronization. For guidance changes, exercise focused web, component-only and no-UI fixtures, including wrong-state and broken-link counterexamples; distinguish static/source review, independent evaluation and runtime proof.

## Project layout reconciliation

Reconcile the documented tree with actual-versus-target state, selected architecture, component/feature ownership, routes/commands, contract sources, generated destinations, migrations and verification locations. Check placeholders, path spelling and supporting navigation. Build modules must not imply extra runtime services; shared code cannot bypass persistence/trust boundaries. Review change-placement examples from entry point through owner validation/persistence/recovery and test location.

Verify source dependency direction, schema/token generation, packaging and ignored outputs. Check that runtime secrets/data and disposable verification state have clear separate ownership and that examples introduce no unsafe commit/storage practice. Exercise architecture-appropriate bounded fixtures when changing reusable layout guidance, labeling actual inspection/static checks separately from an unexecuted proposed build or scaffold.

Where tooling permits, inventory route/command names, native API root operations/RPCs, dictionary structures and verification IDs and compare them with source-owner maps. Check completeness and duplicates, not just keyword occurrence. Review configuration filenames against the selected major version, and trace input → generated output → packaged location → loader/test. Confirm private probes/metrics, audit reads, rate/crypto/maintenance paths and fixture evidence have real ownership when required by the design.

Review unit/integration task selection separately: owner database tests and cross-component/client cases cannot be reported as unit evidence, and required unavailable checks cannot become passing skips. Keep parser/static preservation, packaging/build execution and real host/provider evidence distinct. When a correction affects only project-layout text, preserve established wire/DDL blocks and acceptance text; if it changes a real contract, reconcile all consumers and compatibility explicitly.

## Naming and consumer synchronization review

Use the [naming guidance](output-contract.md#naming-register-and-contract-compatibility). Compare every applicable naming surface with its approved map, including generated paths, security SANs/issuers/audiences, fully qualified RPC/probe names, database role families and telemetry values. Check retained legacy occurrences against historical references, stable IDs, actual source paths and reserved protocol/framework terms; broad text replacement must not change domain terms or reserved literals.

Compare parsed contracts against a fresh baseline with an explicit allowlist of renamed identities and additive fields. Check field numbers/defaults, permissions, constraints and lifecycle rules independently of namespace changes. Require an explicit compatibility decision and coherent regeneration/deployment expectations; distinguish static document agreement from runtime acceptance of old or new values.

Reconcile affected consumer documents through their owners. Verify version/hash/anchor handoff and its actual completion status; avoid concurrent writes or selecting another owner's readiness. Exercise bounded positive/negative fixtures retaining reserved values and historical IDs while changing approved names, and verify rejected unintended contract changes. Report fixture/static checks separately from unperformed builds, migrations, client integration or rendering.

## Reader and voice review

A new engineer should identify the product behavior, implementation boundaries, contracts, assumptions and next technical verification without the authoring conversation. The main body follows the user-selected structure or the [default engineering outline](output-contract.md). Applicable frontend/backend sections are detailed enough to implement; irrelevant specialties do not manufacture a stack or service.

Review for conversation-dependent commentary, permissions/invocation language, editing history, checker/agent reports and repeated evidence disclaimers. Keep reference governance in appendices, technical assumptions/dependencies in relevant sections, and authoring diagnostics in the final response. Preserve meaningful limitations and actual evidence without making the document a task transcript.

## Terminology review

Inventory unexplained acronyms, specialized terms, overloaded words and dense passages in prose, tables and captions. Locate the earliest reader-facing use across prose, captions, tables, diagrams and tree comments, and check that its visible explanation comes before the dependent content. A glossary-only definition or later expansion fails this check. Confirm that first meaningful uses explain the concept and its system purpose; check glossary links and independently readable section reminders. Preserve precise protocol/product names and code identifiers rather than inventing expansions or renaming contracts for readability.

Walk consequential examples against the authoritative rules: identify actor/component, action, reason, enforcement boundary, failure and recovery outcome. Check that people, browser roles, service identities and infrastructure credentials stay distinct; timeout/expiry/cancellation is not proof of no effect; explanatory security language introduces no stronger guarantee. A reader should be able to describe who runs the system, how access is checked, and how the applicable stale/replayed/interrupted work resolves without consulting the authoring conversation.

For terminology-only edits, compare embedded blocks and acceptance text byte-for-byte, alongside source hashes and requirement mappings. Exercise bounded fixtures matched to the change and report whether they are same-agent drafts or independent evaluations. Plain wording and acronym counts alone do not establish comprehension; report the reader review's actual evidence and limits.

## Structural checks

Check native heading targets, links, unique IDs, fenced specifications and source paths; allow only the simple disclosures in the [code presentation rules](output-contract.md#code-presentation-and-progressive-disclosure), and inspect unexpected raw HTML, executable tags, event handlers and unsafe link schemes outside intentional code examples. Validate available schema/JSON/protobuf tooling and diagrams when safe. A syntax check does not establish database execution, contract integration or visual rendering.

Inventory and classify every code/diagram block. Check purpose and explicit example/scenario labels, readable indentation/line breaks, width exceptions for unchanged literals, unique definitions and fragment assembly. Compare parsed contracts/data before and after formatting, including defaults, presence, SQL constraints and protobuf wire numbers; compile assembled fragments where tooling permits. Inspect collapsed and expanded rendering and the heading-only fallback when support fails. Report syntax, semantic-equivalence and visual checks separately.

Confirm only the requested project document changed and source inputs retain their baseline hashes. Keep temporary artifacts outside the project. Supporting skills preserve parent scope; documentation work does not create application code, real migrations, formal tests, tickets or infrastructure.

## Completion

Keep concise technical verification status and material dependencies in the document, with evidence/owner/affected behavior. Report the file link, actual authoring checks, unresolved dependencies and rendering/tool limitations in the completion message. Material unresolved contracts prevent an implementation-ready claim. Do not imply documented tests, deployment or controls have executed.

## Cohesive persistence review

For every separate structure, identify its current requirement and boundary; challenge speculative entities and splits that merely duplicate the same identity/lifecycle. For every consolidation, trace all former fields, relationships and guarantees to explicit replacements. Verify typed variant checks, state meanings, retention exclusions, query/index support, authorized projections and migration compatibility. Reconcile physical owner counts and diagrams with DDL/dictionaries and the consumer acceptance source.

Use bounded fixtures appropriate to the change: a service application, a database-backed monolith and a file-backed/offline workflow can expose copied topology or unnecessary tables. Include counterexamples where fewer tables lose foreign-key integrity, security separation or permanent evidence. Report whether reviews are same-agent sketches, independent generations, static validators or runtime checks; do not equate those evidence levels.

## Browser persistence and session review

Trace each approved browser store and cookie purpose through its owner, values, lifetime, exposure and failure handling. Inspect issuance/renewal/deletion examples independently; zero-age deletion must not be mistaken for persistent issuance. Verify sensitive response/cache and history/account cleanup, session restoration, exact credential delivery and readable anti-forgery exceptions. Check cookie/HTTPS configuration cannot weaken the approved protections, and do not use browser closure or localhost exceptions as false security proof.

Verify CWE meanings and selected standards versions against primary sources; map persistence and missing-Secure concerns to specific controls/observations without claiming certification or total XSS immunity. Exercise bounded browser/service, monolith and offline-CLI fixtures plus counterexamples with positive cookie lifetimes, omitted Secure, readable CSRF incorrectly classified as a login token, and private caches left behind. Preserve existing technical/acceptance identifiers and record static, reader, browser and runtime evidence separately.

## Logging and browser-lifecycle reconciliation

Apply the logging contract alongside browser-security guidance when relevant. Trace each emitted field/level to its producer, safe construction and observable consumer; compare configuration, framework mappings, trace versus existing UUID IDs, command/protocol output and sink failures. Challenge raw Cookie/Set-Cookie/CSRF/error dumps, multiline injection, drop-value leaks, misleading HTTP-200 classification and diagnostic output treated as transactional audit. Check no-context boot, concurrent/cancelled context cleanup and recovery when present. Require actual emitted-boundary evidence later, not only illustrative JSON parsing.

Review browser storage, readable CSRF, cookie issuance/deletion, confirmed/uncertain logout, server expiry and restored/delayed page responses as one lifecycle. A cross-reference should carry the precise rule without contradictory shorthand elsewhere. Preserve version-correct CWE-539/CWE-614 meanings and standards exceptions. Exercise bounded service/browser, monolith and offline-CLI fixtures with negative counterexamples; offline products acquire only their applicable logging/storage rules. Report same-agent sketches, structural validation, rendering and future runtime evidence separately.

