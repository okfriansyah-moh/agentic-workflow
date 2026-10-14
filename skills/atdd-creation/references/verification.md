# Verification and independent coverage inventory

## Prepare before drafting

Create a temporary JSON inventory outside project deliverables from direct source inspection. It is an input to validation, never an extraction from the ATDD's own references. Read all applicable source areas, including tables, compound criteria, design-state inventories, contracts and operational obligations. Existing source IDs and counts are a starting point; IDs alone do not establish clause coverage.

Record each source's exact bytes and SHA-256. For remote sources, retain a temporary text snapshot of the retrieved content and the original source URL; report access limits honestly. Hash binary/visual source files as appropriate and inventory behavior established by their accompanying specifications or inspected states. Do not place secrets in snapshots or examples. A changed source requires inventory reconciliation before its new hash is accepted.

The JSON contract is version 1:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "id": "SRC-BRIEF",
      "path": "source-snapshot.md",
      "location": "brief.md",
      "sha256": "actual SHA-256 of the inspected source bytes"
    }
  ],
  "obligations": [
    {
      "id": "AC-01",
      "source": "SRC-BRIEF",
      "locator": "Section 2, AC-01",
      "statement": "A failed replacement preserves the previously saved content and reports failure.",
      "scope": "Required",
      "reason": ""
    }
  ]
}
```

`path` is absolute or relative to the inventory file, naming the actual source or its retrieved snapshot. `location` is the public/document-relative source link to display in the ATDD source register. The SHA-256 value must be 64 lowercase hexadecimal characters. IDs are unique single tokens; qualify collisions without changing the source's original identifier. `locator` identifies the precise source clause/state/contract. `statement` captures the full testable obligation. Scope is Required, Excluded or Deferred; the latter two need source-grounded reasons. Supplemental inferred risks receive separate stable IDs and precise source context; unknown product policy is a gap rather than an invented expected result.

Do not hardcode requirement counts in the reusable skill or project prompt. Re-extract in a fresh pass after drafting and reconcile any omissions with the inventory and document. Record source changes and scope decisions rather than silently editing the inventory to fit generated cases. The temporary inventory can be removed after validation; all human-relevant source, scope and mapping information remains in the document registers.

## Deterministic checker

Run the bundled helper with Python 3.9+ (standard library only):

```sh
python3 /absolute/path/to/atdd-creation/scripts/check_coverage.py --inventory /temporary/source-inventory.json --document /project/docs/atdd.md
```

On updates, add `--previous /temporary/previous-atdd.md` using a copy captured before editing. The checker only reads files and prints JSON. Exit 0 means structural checks passed and every Required obligation is mapped as Covered; exit 1 means malformed inputs or structural inconsistencies; exit 2 means structurally valid explicit coverage gaps. Exit 0 never proves semantic completeness or passing software. A useful draft with exit 2 can be delivered as Draft with gaps, naming the affected obligations and decisions.

Checks include source bytes/fingerprints, exact source/obligation register membership, scope dispositions, unique case IDs, required fields, Given/When/Then structure, reference reciprocity, exact duplicate scenarios, supplied-evidence metadata and update ID/evidence hygiene. Misspelled required labels are reported as missing; additional explanatory fields are allowed. Gap rows may retain partial case mappings. The script cannot derive arbitrary requirements, assess semantic assertion adequacy, authenticate evidence, verify UI pixels, or prove source extraction was complete.

## Semantic and reader review

1. Compare the source inventory with the actual sources, not with generated case counts. Review each compound clause, permission row, UI transition and engineering invariant for an observable assertion.
2. Check format, source relevance, duplicate behavior, uncovered obligations and edge categories in that order. For required/requested unit coverage, verify actual isolated cases and their integration complements rather than accepting a level label or a unit command alone. Keep distinct risks even when their titles look similar; priority alone does not justify duplicates.
3. Review negative and uncertain paths: no prohibited data/effects, correct actor/owner, state preserved after failure, bounded retries and truthful outcome signals where committed.
4. Challenge each expected result independently of implementation logic. Identify a concrete defect it would catch. Confirm real-boundary requirements and limitations of doubles or local sinks.
5. Review every gap closure against its source rationale and actual assertions; distinguish consequential missing decisions from implementation details and execution prerequisites. Review classifications and evidence. A mockup is interaction evidence, not functioning backend proof. New cases stay Not Run; retained evidence is attributable and reviewed for freshness. References to supplied executions do not authorize new execution.
6. Read as a new tester: find the setup, concrete inputs, action, observable oracle, isolation/cleanup and unresolved prerequisite without using chat context. Use doc-coauthoring within the parent scope.
7. Check Markdown rendering, heading links, source links, visible case-index levels, literal source-markup escaping, rendered reachability of later cases and long table/case readability where tools permit. Check that case/major-section breaks render as horizontal rules with complete cases on each side, without splitting fields, fenced scenarios, tables or disclosures or duplicating a group boundary. Record unperformed rendering or runtime checks in the completion message.

## Expected UI reconciliation

Apply the [expected UI rules](output-contract.md#expected-ui-and-design-references). Review every case's actual outcome for UI applicability, not its platform label alone. Check conditional field position, exact page/state links, production route/panel/host context, concise independently observable expectations and relevant component/accessibility contracts. Pure backend/command cases must not acquire invented pages; component fixtures need not invent an application route.

Compare each state-table trigger and oracle with the inspected source and current technical contract. Catch wrong-but-resolving state links, generic commit language on reads, hidden controls treated as authorization and example records/limits treated as fixed production guarantees. Keep pending/empty/failed/denied/uncertain/recovered meanings distinct and retain committed copy/fields. Check the flow index, source fingerprints, referenced images/alternative text/captions and representative rendered navigation where available.

The bundled structural checker accepts explanatory fields but does not decide UI applicability, verify image pixels or judge semantic state agreement. Exercise bounded web UI, component-only UI and offline-command fixtures on skill changes, including semantic and missing-reference counterexamples. Report actual reviewer/evidence limits; state/specimen rendering is not a product acceptance execution.

## Security and cross-document challenge

Use the [security/consistency acceptance rules](output-contract.md#security-first-and-consistency-acceptance) as a semantic checklist, not a claim the structural checker can enforce them. Compare exact contract operations, field presence/types, owners, permissions, quota settings/scopes, retry identities, database constraints and audit projections against independently inspected technical sources. Check API-only validation separately from direct database assertions; reads cannot require mutation-only arguments. Review newly changed source contracts and existing case evidence together.

For every applicable family, inspect concrete fixtures and oracles for safe handling of hostile inputs, preserved valid content, permitted versus denied identities, concurrent admission, limiter outages, duplicate versus distinct writes, rollback, stale versions, lease loss and lost responses. Ensure old replays cannot resurrect expired/deleted data or expose private receipts. Review workload settings and admitted/completed counts before accepting a performance oracle. Require the selected real persistence/transport/browser proof boundary; simulated success does not establish it.

When revising this guidance, exercise bounded service, monolith and offline-tool cases from raw sources. Include counterexamples that are structurally valid but semantically wrong: generic sanitization, application policy claimed as a database constraint, unauthorized entity fields, mutation inputs on reads, unscoped quotas and replay resurrection. Record reader judgments and fixture limitations. Do not label same-agent examples as independent evaluations or authored Not Run cases as executed security tests.

## Skill maintenance checks

After changing the bundle, run the installed skill-creator metadata validator, task-observer bundle validator and `evals/test_check_coverage.py`. Those structural/code checks complement independent consuming-agent evaluations described in [workflow scenarios](../evals/workflow-scenarios.md). Store evaluation artifacts and actual results in the shared staging run, not in a user's product directory. Preserve upstream identities and notices when revising adaptations.

## Persistence redesign review

Re-extract the new storage definitions before updating old table cases. Confirm every retained risk still has an observable assertion, each expected API value maps to permitted stored/derived data, and removed tables are referenced only historically. Check variant constraints separately from application rules, expiry against permanent evidence, and concurrent/replayed/recovered effects against the actual owner boundary. Preserve case identity, source mappings and truthful execution status.

Challenge one excessive-splitting and one unsafe-consolidation counterexample using the selected source model; include a no-database fixture when testing reusable behavior. The checker proves structure and source consistency, not that the model is minimal or that a database constraint works at runtime. Record semantic review and fixture limitations explicitly.

## Browser persistence and session review

Trace each approved browser store and cookie purpose through its owner, values, lifetime, exposure and failure handling. Inspect issuance/renewal/deletion examples independently; zero-age deletion must not be mistaken for persistent issuance. Verify sensitive response/cache and history/account cleanup, session restoration, exact credential delivery and readable anti-forgery exceptions. Check cookie/HTTPS configuration cannot weaken the approved protections, and do not use browser closure or localhost exceptions as false security proof.

Verify CWE meanings and selected standards versions against primary sources; map persistence and missing-Secure concerns to specific controls/observations without claiming certification or total XSS immunity. Exercise bounded browser/service, monolith and offline-CLI fixtures plus counterexamples with positive cookie lifetimes, omitted Secure, readable CSRF incorrectly classified as a login token, and private caches left behind. Preserve existing technical/acceptance identifiers and record static, reader, browser and runtime evidence separately.

## Logging and browser-lifecycle reconciliation

Apply the logging contract alongside browser-security guidance when relevant. Trace each emitted field/level to its producer, safe construction and observable consumer; compare configuration, framework mappings, trace versus existing UUID IDs, command/protocol output and sink failures. Challenge raw Cookie/Set-Cookie/CSRF/error dumps, multiline injection, drop-value leaks, misleading HTTP-200 classification and diagnostic output treated as transactional audit. Check no-context boot, concurrent/cancelled context cleanup and recovery when present. Require actual emitted-boundary evidence later, not only illustrative JSON parsing.

Review browser storage, readable CSRF, cookie issuance/deletion, confirmed/uncertain logout, server expiry and restored/delayed page responses as one lifecycle. A cross-reference should carry the precise rule without contradictory shorthand elsewhere. Preserve version-correct CWE-539/CWE-614 meanings and standards exceptions. Exercise bounded service/browser, monolith and offline-CLI fixtures with negative counterexamples; offline products acquire only their applicable logging/storage rules. Report same-agent sketches, structural validation, rendering and future runtime evidence separately.

