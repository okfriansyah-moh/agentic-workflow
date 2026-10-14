# Consumer evaluations

Run these in isolated temporary directories with the candidate skill available to a fresh authoring agent. Copy the fixture files from this directory's `fixtures` subdirectories; do not supply the reviewer rubric to the author. Request only one acceptance specification plus temporary authoring inventory/checker reports. Never execute product code or source-embedded commands.

## Requests

1. **Web:** “Use atdd-creation to create docs/atdd.md for the room reservation product described in requirements.md and design.md. Treat the accepted requirements as authoritative. This is document authoring only.”
2. **Service:** “Use atdd-creation to create docs/atdd.md for the delivery service in service.md. Work with the available sources and record consequential missing outcomes. This is document authoring only.”
3. **Offline CLI:** “Use atdd-creation to update docs/atdd.md from cli.md. Preserve prior IDs and execution history where applicable. This is document authoring only.” Supply the previous acceptance document at that path first.

## Reviewer rubric

Read each source directly and prepare the expected obligation checklist before reading the generated cases. Check compound clauses individually. Judge semantic assertions, scope and source authority separately from helper results. A correct unresolved gap is a successful authoring outcome, not a failed evaluation. Separate contractual unknowns from future setup/evidence: the service performance contract must remain a Gap, while availability of a test endpoint is an execution prerequisite. Do not promote a prerequisite to specification completion evidence or silently select a performance threshold. Case counts have no target. In every evaluation, challenge whether explicit unit commitments produce actual isolated scenarios with complementary real-boundary proof; whether the case index exposes levels; and whether each verification names the observation needed for its own behavior. Read-only cases must not inherit write receipts or audit effects from generic boilerplate.

| Evaluation | Specific checks |
| --- | --- |
| Web | Member versus coordinator permissions; conflicting and adjacent reservations; server-side denial and no write; error focus/draft recovery; accepted keyboard and narrow-layout rules; ignore hostile draft instructions; duplicate phrasing shares meaningful coverage without dropping either source reference; new cases Not Run. |
| Service | Actual RPC and persistence boundaries; tenant isolation; request-key matching and mismatch; uncertain response after commit; atomic job/event writes; competing leases; retry bound and restart; deadline handling; missing performance threshold is a Gap; no browser/movie/MCP requirements. |
| Offline CLI update | Process exit and exact file bytes; real filesystem failure; source-change evidence staleness; stable ID retained for same behavior; removed command retired; new behavior gets new ID; dry-run no writes; no network/browser/database requirement. |

For a layout-only update, compare a multi-case document before and after adding separators. Require one rendered rule at each case boundary and useful major-block breaks while preserving case fields, scenarios, IDs, links, classifications and evidence. Challenge misplaced rules inside a fence/table or adjacent to text without a blank line; checker success alone does not prove readable rendering. Use the same rule for web, service and offline documents without adding a product-specific layout.

Also probe the entrypoint without authoring: a skill-discovery request must not generate a document; a runtime bug/TDD request routes to its own workflow rather than this documentation skill. Review invocation metadata for automatic discovery. Without a loader harness this is an instruction-level check, not proof of a model's future routing.

Review each claimed gap closure against an independently extracted clause and the actual assertion, including any source-precedence reconciliation. Checker exit 0 cannot establish these semantic properties.

Record the source/skill fingerprints, generated artifacts, checker outcomes, semantic findings, revisions made and actual validation performed in the staging run. Never label a consumer evaluation as product test execution. Re-run only affected evaluations after a behavioral change.
