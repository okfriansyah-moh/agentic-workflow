# Application-focused engineering contract

Use this as the coverage guide for creation and substantive revision. Follow user-selected structure where supplied. Otherwise use the outline below, adapting sections to the project's actual architecture: a monolith has modules, a service system has services, an offline CLI has command workflows. Include applicable engineering detail; omit irrelevant specialty sections instead of inventing components. Never import a previous project's stack, service count, integrations or infrastructure.

## Default document structure

1. System overview, actors, capabilities and constraints.
2. Architecture, component boundaries, deployment and communication.
3. Frontend engineering, when a frontend exists.
4. Backend/component engineering, separated by service or module.
5. Complete API and integration contracts, including command contracts for CLI systems.
6. Complete database or persisted-data design, when persistence exists.
7. Transactions, lifecycle, concurrency and durable work.
8. Identity, security, privacy and cryptography.
9. AI/MCP integration and human approval, when applicable.
10. Seed data, initialization and migrations.
11. Configuration, startup and command contracts.
12. Operations, observability, capacity and recovery.
13. Verification strategy.
14. Technical dependencies and release criteria.
15. Appendices for decision history, requirement traceability, source fingerprints and primary references.

Scale explanation to complexity while preserving applicable obligations. Consolidate shared definitions and link to them rather than repeating schemas or rules. A user-requested single document includes its appendices and embedded specifications; it does not create additional project artifacts.

## Audience, voice and navigation

Begin with the application's purpose, actors, behavior, boundaries and constraints. Retain concise title/version/date/owner/status metadata where useful. Describe what the system does and what an engineer must implement. Express assumptions as assumptions, numerical budgets as targets until measured, and unresolved dependencies as required evidence with affected behavior and owner if known.

Keep authoring history, conversation instructions, permissions to create files, agent-review narratives, temporary checker inventories and tool-policy failures in the completion message. A technical verification section may contain concise actual evidence with environment/date and limits; it must not imply unexecuted behavior passed. Distinguish requirement commitment, design choice and runtime evidence without repeating disclaimers in every paragraph or traceability row.

Use native Markdown headings and heading links; give individually linked identifiers real headings. Schemas, code and Mermaid belong in fenced blocks. Preserve stable source/decision identifiers and update all links when headings change. Keep navigation in Markdown; simple disclosure markup is permitted under the rules below.

## Terminology and layered explanation

Write for the user-selected audience. Otherwise use plain engineering prose with concise introductory explanations where a concept is necessary to review the design. Lead with what the system does and who does it, retain precise implementation terms, and add depth only where it helps the reader understand a decision, safeguard or failure outcome.

Introduce unfamiliar terms and expand acronyms at their first meaningful use in prose or before a table that depends on them. Explain the concept's meaning and role in this system rather than expanding initials alone. Recognizable product/protocol names need an explanation of their function, not an invented expansion. Review the document in reading order, including captions, tables, diagram labels and project-tree comments. Explain a term in visible prose before the first dependent block or table; a later section or glossary definition does not satisfy first use. Contents links and literal identifiers do not need rewriting. Preserve embedded definitions/identifiers, and explain them outside the block. For a schema language, name what it describes, where its source lives and how readers/implementers use it; add a small illustrative declaration when it materially aids understanding. For independently read sections, use a brief reminder or native link instead of repeating the full definition.

Distinguish people, application roles, software identities and infrastructure credentials. Name the responsible component and enforcement boundary. Explain overloaded words in their actual contexts: for example, a request body versus encrypted storage, or a credential-revocation counter versus a worker-ownership counter. An authenticated caller still needs the specified permission; simplified language must preserve that distinction.

Replace needless jargon and compressed noun chains with direct statements. Break dense paragraphs and table cells into readable rules while preserving identifiers, limits, units and conditions. For difficult concurrency, security or recovery behavior, add a short, explicitly illustrative system example with its trigger, owner, observable outcome and important limitation. An example explains an existing rule; it does not add a guarantee, privilege, feature, configuration default or runtime claim.

Keep essential explanations beside the relevant behavior. Add a linked glossary inside the same document when recurring terminology warrants lookup; group or alphabetize entries with native headings and references to the authoritative rules. Choose terms used in this project rather than a stock acronym catalog. A glossary complements local explanations and does not replace implementable contracts or turn the design into a general tutorial.

During terminology-only refinement, preserve embedded specifications and requirement acceptance text; clarify them through surrounding prose and glossary references. Check explanations against the precise original rules, especially omission/clearing, identity versus authorization, duplicate effects, uncertain outcomes, expiry, version checks, encryption and recovery. Keep existing scope and architecture; adapt the depth to a service system, monolith or offline tool without inventing unrelated components.

## Code presentation and progressive disclosure

Make code reviewable before making it compact. Inventory existing blocks during refinement and retain their complete technical meaning. Give every block a descriptive native heading or caption, a short purpose, and a clear classification: **Contract specification**, **Database definition**, **Code example**, or **Diagram**. Source schemas and database definitions remain authoritative; illustrative snippets explicitly say **Code example — request**, **Code example — successful response**, or **Code example — validation/authorization failure**, with their scenario and expected result. Identify placeholders and illustrative IDs, hashes, dates or credentials; examples do not establish runtime evidence.

Use accurate language fences, consistent indentation and semantic line breaks. Put each schema field, enum value and RPC declaration on its own line, expand long argument lists/constraints, and pretty-print structured examples. Target 100-character lines where syntax permits. Preserve literals, identifiers, defaults, precision, nullability, constraints and wire numbers; never break a string or change data to satisfy width. Show long embedded query strings as a native query plus variables and explain how the transport envelope is assembled.

Group long specifications by responsibility: shared values, projections, inputs, operations and selected components/services. Keep each definition once, provide local navigation, and state assembly rules for fragments that constitute one source schema. Distinguish standalone schemas from fragments; preserve shared references when grouping tool contracts. Formatting must not replace complete specifications with sketches.

Combine visible Markdown headings and explanations with named, collapsed disclosures for blocks over 30 lines, table DDL and detailed sequence diagrams. Keep short examples, the architecture overview, ownership, important rules and data dictionaries visible. Use only `<details>` and plain-text `<summary>` wrappers with blank lines around language-fenced Markdown; keep heading anchors outside wrappers and avoid nested disclosures. This markup is progressive disclosure, not executable code: no scripts, event handlers, styling or custom HTML anchors. Honor a user-selected presentation and use open fenced blocks under the same headings when the target renderer is confirmed to mishandle disclosures.

Check collapsed and expanded rendering where tools permit, including code fences, syntax highlighting, scrolling and disclosure keyboard operation. Unknown renderer support is reported as a limitation rather than a verified result. Private/reference examples can inform presentation without importing business content, technology choices, corporate approval workflows or additional deliverables.

## Naming register and contract compatibility

For systems with multiple naming surfaces, include a concise register linking product/component display names to physical storage, source/build/generated paths, wire namespaces and owner values, service/security identities, domain terms and required framework/protocol keywords. Distinguish current target names from historical titles, actual paths, source wording and stable identifiers. Explain a component's purpose beside its name so a storage or service name does not imply duplicate domain ownership. Use the selected project's names and architecture; a brand change alone does not rename domain concepts or reserved vocabulary.

Before changing names, inventory occurrences and classify them by surface. Apply the approved map to diagrams, source trees, dictionaries/examples, generated consumers, receiver audiences, issuers/certificate names, fully qualified method/probe names, startup and observability. Preserve source fingerprints, stable IDs and protocol-required literals; account for every retained legacy spelling in the register. Keep actual checkout/runtime names distinct from target specifications.

Record compatibility explicitly for changes to wire namespaces, owner identifiers or security bindings. State whether old values remain supported, how consumers regenerate/deploy together and what evidence verifies the transition. Retaining protobuf field numbers does not preserve a renamed RPC path or issuer. Reconcile additive projections with storage, ORM, authorization, client display and verification; a projection over existing columns does not require invented DDL.

Synchronize related consumer documents within their authorized ownership. Hand off the finalized name map, exceptions, contract additions, document version/hash and changed anchors to another owner when coordination is requested; preserve their stable IDs and execution statuses. Documentation synchronization is distinct from builds, live migration and runtime compatibility evidence.

## Architecture and communication

Explain context, components, trust boundaries, ownership, dependency direction, runtime and deployment. Use diagrams where they resolve responsibility, ordering or failure. Separate synchronous call dependencies from asynchronous reconciliation and avoid implying distributed transactions where none exist.

Provide a communication inventory: caller, receiver, purpose/operation, protocol, identity/authorization, timeout, retry owner, idempotency and outcome reconciliation. Include browser/client, internal service, background-worker, provider and operational interactions that actually exist. Every component has an explicit public interface and persistence boundary.

## Project source and build structure

Include a detailed source/build layout in the architecture section unless the user-selected scope or structure excludes it. Inspect the actual checkout first. Distinguish existing paths from target implementation paths; a proposed directory tree is a design specification, not proof of implementation or permission to scaffold files. Preserve established layout conventions and explain only justified changes.

Provide a labeled language-fenced tree with visible purpose/ownership and native navigation. Group large layouts into cohesive views using the code-presentation rules. Show applicable application/module entry points, routes or commands, feature code, handlers/domain/persistence boundaries, shared contracts, migrations, seed inputs, operations/configuration and verification. Give useful concrete paths and explain placeholders and illustrative filenames instead of listing a generic empty skeleton. Map each major feature/component to its location and responsibility; readers should be able to find where a change belongs.

Specify source dependency direction, shared-library limits, build/workspace membership and the relationship between build modules and deployed processes. Adapt to the selected architecture: a monolith needs module boundaries, an offline CLI needs commands and native file persistence, and a service system needs owner boundaries. Do not import a stock stack, service count, build tool, CI provider or deployment directory into unrelated projects.

Identify the authoritative source for each schema/token input, where generated types/resources land, which build step produces them, and what stays ignored or is packaged. Keep handwritten code distinct from generated outputs and avoid independently maintained contract copies. Locate unit, owner-boundary and applicable cross-component/client verification, with isolated fixtures and evidence outputs. State dependency/build ordering where it prevents stale generation or unsafe startup effects.

Explain where nonsecret configuration examples, real secrets, persistent runtime data, temporary processing data and disposable test state belong, according to the project's actual security and lifecycle rules. A source tree must not imply secrets/user data belong in version control or that proposed test folders contain executed proof. Preserve the requested artifact boundary; documentation of future source/infrastructure paths does not authorize creating them.

Reconcile layout and engineering sections in both directions. Every route/command, required operation, persisted structure, worker/operational endpoint and verification family needs an owner and a source/test location; every meaningful tree entry needs a documented responsibility. Consolidate long inventories in linked maps rather than copying contracts into multiple sections. Verify framework-major-specific configuration names and entry points against primary documentation when needed; a familiar template can be wrong for the selected version.

Trace each source schema/token/seed input through its generator or validator, derived output, compile dependency, packaged/mounted location and actual runtime consumer. Cover boundary DTOs as well as frontend clients, include private probes/exporters and administrative paths, and distinguish privileged bootstrap/migration/maintenance from ordinary request credentials. Avoid missing resource files, independently authored generated copies, undeclared resource servers, extra runtime services or database access across owners.

Map verification families to unit, owner integration, cross-component, UI and external-client/provider locations as applicable. Define command/task selection, generation prerequisites, isolation/cleanup and required-versus-unavailable evidence. Static layout checks, emulator/component fixtures and real external-host checks provide different evidence. Repair related trees, owner descriptions, database mappings and verification obligations together; leave genuine unresolved technical dependencies explicit rather than inventing an interface or silently weakening a requirement.

## Frontend engineering

For each route/screen or client workflow specify actor access, navigation, feature/component responsibilities, design-system reuse and exact API operations. Define typed requests/results, generated-code ownership, state lifetimes, URL/filter state, ordering/pagination, invalidation, cancellation and out-of-order responses.

Cover session initialization, credentials/CSRF where applicable, permission boundaries, private draft isolation, form validation, normalization/counting, omission/clearing, policy changes, optimistic conflict handling and safe recovery. For uploads specify preparation, measured transfer, processing, confirmation and cancellation separately. Detail loading, empty, denied, stale, failed, uncertain and recovered states, responsiveness, accessible semantics, focus, announcements and keyboard behavior. UI controls do not substitute for backend enforcement.

## UI references and implementation handoff

When approved UI artifacts exist, inspect their pages, component contracts, state inventories, tokens and visual references alongside product and technical requirements. Put a visible map beside frontend/client engineering: production route, screen or embedded view → exact design page/state → component and feature owner → API/command dependency → relevant acceptance case or planned verification obligation. Keep source state identifiers stable. Link the complete applicable states, not only a happy-path gallery page, and reconcile the map with the project layout and contracts.

Distinguish full routes from embedded panels, shared session/validation states, native/mobile views and external-host interfaces. Reference filenames, fragment selectors, specimen role switches and demonstration controls do not become production routes/selectors/features. Map design component responsibilities to selected implementation components without inventing duplicate implementations or a UI library. Future implementation-plan slices must retain the applicable source links/state IDs, owners, contracts and acceptance references so task generation does not discard UI detail.

Use existing approved previews when requested or useful, with descriptive alternative text and a caption stating screen/state/theme/viewport where known, fixture status and limitations. Link full-size/live references; an overview image does not cover every flow or constitute a runtime/pixel baseline. Do not generate assets or copy private screenshots beyond the authorized scope. Keep previews and concise expectations readable with native Markdown navigation.

Separate fixed approved copy, anatomy, controls, accessibility and action meanings from replaceable fixture names, counts, dates and simulated progress. Effective validation, presence, permissions, audit fields and receipt outcomes follow governing contracts; an incomplete illustration cannot remove a committed field or override policy. Explain discrepancies and material gaps rather than silently selecting contradictory mockup behavior. Production verification observes actual states at the named boundary, not a successful fixture timer.

Use available project artifacts rather than requiring a design-system folder or screenshot package universally. A component-only interface needs its local states and host responsibilities; a service/offline command with no graphical UI does not acquire pages. Where consumer documents are separately owned, finalize source version/hash/anchors before synchronizing references and avoid concurrent writes or circular governing-source fingerprints.

## Backend/component engineering

Separate responsibilities by selected service/module, including protocol adapters when present. Describe feature boundaries and the path from transport handler through authorization/validation/domain rules to owned persistence and effects. Define transactions, isolation, optimistic checks, generated types, dependency injection where suitable, coding conventions, resource/cancellation lifetimes and shutdown.

Specify cross-component data ownership and returned projections. Clients never infer access from button visibility; authoritative owners enforce object/action permissions. Document local commit versus remote work and the recovery mechanism for every consequential commit/effect gap. Avoid arbitrary shared repositories or speculative brokers and services.

## Complete contracts

Inventory every operation required by a workflow; schemas labeled merely representative are insufficient when omitted operations are required for implementation. Use the selected protocol's native embedded form, with representative requests/results and failure examples. Include auxiliary boundaries such as asset bytes, trusted UI approval, callbacks, health, metrics, alert ingestion or CLI I/O where used.

For each operation specify consumer/owner, fields and types, units/precision, required/optional/presence/clearing, authorization, validation, accepted bounds, defaults, success/partial/failure results, safe error codes, ordering/pagination, deadlines, cancellation, replay/idempotency and uncertainty recovery. Reconcile frontend types, backend DTOs, persistence types and wire contracts. Preserve compatible field numbering and reserve removed protobuf numbers; define compatibility and schema evolution rules for the selected protocols.

## Complete embedded database design

Use the selected engine's actual types and semantics. For file/document persistence, specify the native format/schema, atomic writes, locking, compatibility, retention and recovery instead of inventing SQL structures. Identify physical ownership, roles, database/schema boundaries, application versus framework/migration structures, and justified extensions. Include ER diagrams and separate logical cross-owner references where applicable.

For every table document purpose, owner, lifecycle, cardinality assumption, sensitivity, retention and access patterns. For every column document exact type/size, numeric precision/scale, timestamp precision/timezone, units, nullability, default/generation, bounds/accepted values and unknown semantics; keys, uniqueness, checks, cardinality and update/deletion behavior; encryption/hashing/lookup treatment and telemetry exposure; applicable ORM and wire mappings with presence/clearing.

Specify every key, constraint and index, including order, predicates/included columns where supported and the query it serves. Separate storage envelopes from configurable application validation so policy changes preserve existing data. Justify unbounded text, arrays or JSON/document storage versus normalized relations.

Embed DDL covering all designed structures, cross-referenced to the column dictionary. Include consequential parameterized queries, transaction/isolation/lock ordering, concurrent writes, deadlocks, audit/outbox atomicity, idempotency, worker claiming/leases/fencing and crash recovery. Cross-owner references need reconciliation when no physical constraints or distributed transaction exist.

Specify migrations/locking, compatibility, expand/contract/backfills, failed migration recovery and rollback limits; frozen seeds/provenance/checksums, partial initialization recovery and preservation of edits/deletions; roles/grants, pools/timeouts, purge, backup/restore, keys, disk/capacity assumptions and query-plan/index maintenance. Include persisted security controls only when justified by requirements.

## Cohesive persistence and schema growth

Choose the smallest understandable persistence model that meets the current requirements. Name structures for their responsibility. For each separate entity, explain the identity, cardinality, ownership, lifecycle, privacy boundary, integrity rule or query that earns the split. A future feature is not evidence that its table is needed now; introduce new structures when a concrete requirement establishes that need, without adding a separate approval ceremony.

Evaluate consolidation by total implementation complexity, not table count alone. Records with the same identity and lifecycle may fit one entity with typed fields; independently varying relationships, protected access boundaries or incompatible lifetimes usually need separate structures. Preserve real keys, uniqueness and references. Use bounded validated document/JSON fields where their access pattern warrants them; moving relational data into a generic blob is not by itself simplification.

For typed combined records, define allowed variants, required/forbidden fields, unique identities, state transitions, query/index access and retention per variant. Distinguish scheduler completion from business/delivery evidence. Preserve durable retries, concurrency controls, atomic commits, attribution, exact-content approval, encryption/key safety and recovery obligations where applicable. Permanent initialization/deletion evidence must survive shorter ordinary-result retention.

On a redesign, provide an old-to-new field and guarantee map, including removed relationships, replacements and compatibility/migration disposition. Reconcile dictionaries, schema definitions, queries, ORM/DTO/wire mappings, diagrams, resource owners, operations and consumer acceptance documents. Classify physical tables separately from views, replicated owner copies and framework metadata. Show responsibility overviews with complete relationships available for detailed review; a repeated table in a focused diagram is not another physical table.

Adapt this method to the selected engine or file format and architecture. No project-specific table count, naming set, service topology, event model or consolidation becomes a reusable default. A simpler model must still make the actor, action, enforcement boundary and failure outcome clear.

## Security-first enforcement and data projections

Trace each applicable entry point to its authoritative permission/validation owner, dangerous use of input, and observable verification. Include browser/API, asset delivery, internal calls, tools/resources, operational endpoints, imports and workers where present. Use a linked enforcement matrix: boundary/operation, trusted actor or identity, control owner, input/output or effect, failure outcome and verification anchor. Authentication of a service does not grant a user's object/action permissions. Alternate transports and background jobs must not bypass the owner's rules. Adapt to actual exposure; an offline tool does not acquire a browser or server.

- **SQL/query injection:** Bind values with the selected driver or ORM, including native queries and query languages such as HQL. Keep query structure fixed; select identifiers, sort expressions and field masks from allowlists. Escaping search wildcards preserves literal matching and is separate from parameter binding. Do not rely on an ORM label, input rejection or a sanitizer to establish safe queries.
- **Cross-site scripting (XSS):** Use context-appropriate escaped interpolation or text nodes for permitted text. Validate dynamic URL schemes/destinations and route projections. Prohibit untrusted raw HTML, script evaluation and event-handler construction. When approved rich HTML is required, define reviewed sanitization and allowed contexts. Content Security Policy (CSP) is an additional control, not a replacement for safe rendering. Preserve legitimate Unicode, apostrophes and markup-looking plain text under the field's accepted semantics.
- **Command, script and argument injection:** Prefer in-process libraries. Where a subprocess is necessary, select fixed executable paths/options and structured arguments, constrain argument semantics and use generated/validated paths. Avoid shell interpolation; shell-free arguments still need protection against injected options. Bound upload/import decoding and processing. Untrusted filenames, metadata, retrieved evidence and model instructions cannot become commands, executable templates, arbitrary network destinations or privileged actions.

Map sensitive data through explicit returned DTOs/projections, not automatic entity serialization. For each exposed field reconcile column or derived source → ORM/domain representation → wire field → authorized consumer. Record transformations, joins, encrypted storage/decryption owner, units/precision, presence/clearing and exposure/redaction. A compatible scalar type does not establish an actual API field or permission to expose it. Internal timestamps, identifiers, tokens and ciphertext stay internal unless the selected contract explicitly projects them. Reconcile audit actor/subject/outcome meanings and approval versus later execution results without collapsing distinct events.

Separate database-enforced invariants from configurable application policy. State the exact constraint and the operation that enforces each rule; `NOT NULL` does not reject blank strings, and a text type does not enforce a current name-length policy. A direct storage test cannot prove checks absent from the schema or arbitrary cryptographic correctness. Tightened validation must follow the approved existing-value policy. Read-only operations do not inherit mutation-only version, policy or receipt arguments.

## Browser storage and cookie security

For an application with a browser surface, classify credentials, anti-forgery values, user/private content, recovery data and non-sensitive preferences. Specify an explicit application storage allowlist covering localStorage, sessionStorage, IndexedDB, application caches and cookie purposes. Derive allowed preference keys/values, validation and storage-unavailable behavior from the selected project. Protected information must not gain a script-readable persistence fallback; client-side encryption with a script-accessible key is not an XSS boundary. Keep approved server-side recovery and temporary state responsibilities explicit. An offline or native project uses its own applicable storage model.

For cookie-authenticated sessions, define issuer, name/host/path, Secure, HttpOnly, SameSite, credential delivery, issuance/renewal versus deletion, and whether persistence is allowed. Default to opaque credentials delivered only through Set-Cookie and non-persistent session cookies unless an approved requirement justifies another design. Non-persistent issuance omits Expires/Max-Age; deletion may use Max-Age=0 without allowing persistent issuance. Define authoritative server expiry/revocation and browser-restoration behavior; browser closure does not establish logout or guarantee that nothing reaches disk. Account for local-browser transport exceptions and the fact cookies are not port scoped. Do not treat HttpOnly as universal XSS prevention.

Keep JavaScript-readable CSRF material separate from the inaccessible session credential, preserving the selected anti-forgery mechanism. Define sensitive-response no-store headers, permitted static caching, protected-state cleanup and history restoration/revalidation. A no-store header is not a substitute for session checks or DOM/controller cleanup. Configuration cannot silently remove approved cookie/HTTPS protections.

Map CWE concerns to concrete owners and observations with version-qualified standards references. CWE-539 concerns persistent cookies containing sensitive information; CWE-614 concerns missing Secure on sensitive HTTPS cookies. Preserve historical source IDs while checking the selected ASVS version's actual clauses; distinguish stronger project choices from what a standard explicitly requires. Reconcile frontend state, HTTP headers, identity handling, storage dictionaries, examples and consumer acceptance without inventing API/DDL changes. Use project-appropriate keys/lifetimes and no universal previous-project topology or feature list.

Reconcile the same lifecycle across frontend, identity handlers, HTTP filters, storage dictionaries, examples, configuration/runbooks and acceptance. State exactly which reads bootstrap anti-forgery state and which mutations require it, how confirmed versus uncertain logout behaves, which server clock/state enforces expiry, and how delayed replies/history/account transitions stay concealed. A cookie flag, timer, storage ban or diagnostic event cannot stand in for another control. Private logging excludes both credentials and anti-forgery material while deliberately readable CSRF remains permitted in the selected response/memory channel.

## Configurable rate and resource limits

For exposed request profiles, specify exact setting names, defaults, units, positive integer bounds, configuration precedence, invalid/unset behavior and validated restart or reload semantics. Define any explicitly supported disable mode separately; zero or a missing value must not silently remove protection. Derive profiles and budgets from this project's exposure and accepted choices; do not import another project's numbers, key names, counter store or algorithm.

Document quota unit (request, operation or cost), window/algorithm, trusted identity and scope, source-address/proxy rules, keyed identity treatment, atomic admission, counter owner/storage, expiry/capacity and replica/restart agreement. Explain configuration transitions for active windows. Define public versus protected read dimensions, credential/account/source dimensions where needed, and adapter-local resource limits separately from shared authoritative quotas. Deduplicate simultaneous checks by profile **and trusted scope/key**, not profile name alone; address batches/aliases and mixed public/protected operations. Multiple profiles must have specified admission/charging semantics.

Define safe throttle errors/retry information and limiter-unavailable behavior. Default protected admission to rejection when authoritative quota state cannot be consulted; any approved degraded mode needs explicit bounds and risks. Rate limits do not replace identity allowlists, deadlines, byte/complexity limits or bounded concurrency. Recovery workers and probes need their own identity/resource budgets and must not be starved by end-user quotas. Count network attempts separately from logical business effects: a replay may consume quota but cannot repeat an effect; denied admission must not reserve a new business receipt or perform its mutation.

Specify isolated, recorded limiter settings for performance verification. Keep enforcement active; distinguish offered, admitted, completed, throttled and failed work. A quota-dominated run is not proof of service latency/throughput under the intended admitted workload. Accepted workload/targets remain source-defined; missing material performance decisions stay visible.

## Concurrency and durable idempotency

Inventory every effectful operation, including drafts, deletions, uploads, imports, maintenance and callbacks where present. Define its retry identity and persistence lifetime, or a justified exception with safe retry/uncertainty behavior. Do not assume only headline create/update commands need duplicate protection. Existing contract changes require explicit compatibility/source disposition and consumer synchronization.

For each retryable effect define a stable per-intent key, owner/actor scope, operation kind, deterministic request fingerprint, authoritative uniqueness, concurrent-duplicate behavior and safe returned receipt. Protect private fingerprints with an appropriate keyed construction; do not put plaintext protected content or credentials in receipts, audits or telemetry. Distinguish transport retry IDs from a recovered business submission ID. Define same-content replay, changed-content conflict, cross-owner isolation, retention and expiry/tombstone behavior. A later edit, discard, deletion or expiry must not let an old replay recreate data, refresh its lifetime or return a fabricated original payload. Explain what safe historical outcome remains observable when the current object no longer exists.

Specify transaction boundaries/isolation, optimistic versions, current deletion-impact checks, authoritative constraints, lock ordering/deadlock recovery and atomic commits of mutation, receipt, redacted audit and durable work when required. Distinct commands that contend for the same object still need concurrency control; idempotency keys alone do not prevent lost updates. Define claim/lease ownership, expiry, fencing tokens, persisted retry budgets, bounded backoff and crash recovery where workers exist. A stale worker must not commit after losing ownership; remote effects additionally need destination deduplication or explicit reconciliation because local fencing cannot retract a remote action.

Cover failure before commit, commit before response, remote effect before local receipt, restart and delayed replay. Name the retry/reconciliation owner and observation that resolves uncertainty. Use real selected storage/transport boundaries for future verification of locking, constraints, atomic counters and durability; mocks prove only their simulated behavior.

## Reliability, security and operations

Apply [assurance](assurance.md) to concrete threats and approved obligations. Specify authentication, action/object authorization, privacy, safe input/output/upload use, cryptographic key/nonce/rotation/restore behavior, AI trust and exact-content approval where relevant. Map concrete threats to enforcement owners, controls, residual risk and negative verification. Standards inform control mappings; application design does not establish certification.

Define retries by operation/class: owner, total deadlines, backoff/jitter, persisted attempt budgets, cancellation, exhaustion and controlled recovery. Account for uncertain remote effects, provider limitations and notification states. Define configuration sources/precedence, unset/empty/false/zero, validation, units, secrets and reload/compatibility.

Cover reproducible startup, persistence, isolated verification commands, bounded readiness, graceful shutdown, observability, alert routing, retention, backup/restore, rollout/rollback, capacity targets and troubleshooting runbooks. Each runbook states symptom, safe inspection/action and success verification. External accounts and integration credentials are explicit prerequisites rather than assumed startup effects.

## JSON diagnostic logs and severity

Specify an operational logging contract whenever the product emits diagnostics. Use UTF-8 newline-delimited JSON: one independently parseable object per physical line, with explicit lowercase severity, UTC event timestamp, fixed message and emitting component/build/environment identity. Define required/optional fields, types, bounds and severity aliases against the adopted standard; a reference example does not substitute for the selected contract. Explain normal outcomes, handled denials/conflicts, degraded behavior, system failure and unrecoverable startup separately. Define configurable verbosity, defaults/validation/restart and controls that remain enabled at every permitted level.

When calls cross boundaries, define trusted trace/span context and existing correlation/retry IDs separately, including ingress trust, propagation, untraced startup, worker restart and context cleanup on reused threads/tasks. Preserve established wire/database identifiers; adding hexadecimal trace IDs does not rename a UUID column or authorize new response fields. Treat identifiers as diagnostics, never authentication. A monolith or offline command need not acquire distributed tracing or a collector.

Construct allowlisted fields before JSON serialization. Exclude credentials, cookies, CSRF values, private payloads, query/bind values, source/model instructions and unsafe exception data at every level, including framework and alternate sinks. Escape control characters through an encoder; decoded viewers render text safely. Redaction cannot be undone through dropped-attribute arrays or nested error/cause serialization. Specify record/queue bounds, backpressure/drop visibility, sink/rotation/access/retention and truthful failure behavior. Diagnostic delivery is not durable evidence or a lossless guarantee; transactional audit, receipts and worker evidence retain their separate ownership and guarantees.

Reconcile log producers, framework output, command/protocol streams, observability/runbooks, configuration and acceptance oracles. Protocol stdout remains reserved when required; JSON diagnostics use the designated other stream. Declare third-party native-output scope without silently rewriting its format or requiring new infrastructure. Keep examples explicitly illustrative and explain pretty-printed review versus compact emitted lines. Adopt relevant external field/level conventions, but not employer SDKs, historical availability claims, business content or extra integrations. Derive concrete limits and component names from the selected product.

## Verification, dependencies and appendices

Verification obligations describe setup, trigger, observable result, boundary/failure variant, fixture and test level. Include real selected database/protocol boundaries when their semantics matter; fakes do not prove engine-specific behavior. Keep actual executed evidence concise and distinguish it from planned checks.

Technical dependencies list unresolved decisions, affected capabilities/requirements, owner if known and required resolution. A material unresolved contract leaves dependent work blocked; do not call the design implementation-ready merely because static checks pass.

Appendices preserve existing source/decision IDs, accepted and superseded choices with rationale, requirement/acceptance/UI-state mappings, operation/storage links and verification obligations. Record source paths/versions/hashes and primary reference access dates. Source precedence is traceable reference information, not the opening narrative. Retain source obligations without turning project-management or authoring history into application behavior.
