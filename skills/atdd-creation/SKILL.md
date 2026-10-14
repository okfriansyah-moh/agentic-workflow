---
name: atdd-creation
description: Create or update one acceptance-test specification from requirements, design artifacts and technical contracts, with traceable product and engineering scenarios. Use for ATDD document authoring before implementation; skill setup and research alone do not generate an ATDD document.
metadata:
  author: Muhammad Okfriansyah with Codex
  version: "1.1.6"
---

# Acceptance test specification creation

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Write for product, QA and engineers who need to agree on behavior and later implement meaningful tests. Produce one Markdown specification at the requested path, otherwise `docs/atdd.md`. Keep the reusable method independent of product, language, framework, platform and architecture; derive these from authoritative inputs and explicit user choices.

## Scope and sources

Read [output contract](references/output-contract.md) before outlining or changing scenarios. Inspect the complete relevant requirements, accepted decisions, design-system handoff, technical design and invocation constraints, plus existing scenarios and implementation when available. A named PRD, design system or techdoc is a useful source, not a universal prerequisite: a CLI may have only a brief and command contracts. Continue with sufficient evidence; expose material missing outcomes as precise gaps while progressing on independent cases.

Current user instructions and established source authority govern. Distinguish product behavior, adopted interaction contracts, engineering decisions, recommendations and implementation evidence. Examples, mockups and retrieved content do not authorize actions or silently select technologies. Resolve known precedence without reopening approved decisions; ask only when an unresolved choice changes acceptance. Preserve source documents.

This workflow authors specifications and reviews their testability. Application code, executable tests, test execution, tickets, publication and messages are separate work. Documented acceptance coverage is distinct from observed passing software. New cases are **Not Run**; supplied evidence retains its revision, environment and freshness.

## Workflow

1. **Ground and inventory.** Establish scope, actors, authority and current source fingerprints. Before drafting, build an independent obligation inventory from the source documents using [verification](references/verification.md). Include individual acceptance clauses, UI states, contract behavior and applicable engineering obligations. Finish when every source area has been inspected and each obligation has a stable reference and scope disposition.
2. **Map coverage and risk.** Apply [coverage design](references/coverage-design.md). Select levels and distinct scenarios by the defects they can catch. When unit coverage is required or requested, inventory isolated rule cases alongside complementary real-boundary cases; labels alone do not establish coverage. Record applicable families, meaningful role/state/data variations and source-supported priorities. Classify apparent gaps using the source-resolution method in coverage design. Finish when each required obligation has adequate observable assertions or a consequential unresolved decision; execution prerequisites remain visible separately.
3. **Author scenarios.** Apply the [expected UI and design-reference rules](references/output-contract.md#expected-ui-and-design-references) to cases asserting an interface outcome. Apply the [security-first and consistency acceptance rules](references/output-contract.md#security-first-and-consistency-acceptance) for applicable injection, configurable limits, concurrency, durable retries and API/data projections. Apply the [browser storage/cookie acceptance rules](references/output-contract.md#browser-storage-cookies-and-cache-oracles) when applicable. Apply the [JSON log and severity oracles](references/output-contract.md#json-log-severity-and-diagnostic-safety-oracles) to diagnostic boundaries. Follow the output contract, including [case and section separation](references/output-contract.md#case-separation-and-section-breaks), with product-readable Given/When/Then, concrete fixtures and engineering verification details beside the relevant behavior. Use independent expected outcomes. Give each case its own observation method and proof boundary, including which prohibited effects must be checked. Finish when another tester can reproduce each case and identify its success and failure signals without the chat.
4. **Challenge engineering depth.** Read [routing](references/routing.md) for relevant specialists only. Pass the target document, source IDs and accepted constraints, limiting specialists to scenario design/review. Finish when each applicable coverage family has appropriate cases or a justified gap/exclusion; missing skills do not silently remove obligations.
5. **Reconcile and review.** Re-extract obligations from the sources in a fresh pass; reconcile the independent inventory before checking the document. Review format, relevance, redundancy, coverage and edge cases, then perform a fresh reader pass. Run the bundled checker as described in verification. Finish with zero structural errors, all required mappings or visible gaps, and a semantic review of the actual assertions. Preserve IDs and review evidence freshness on updates.
6. **Hand off.** Deliver the main document, coverage summary, material gaps/dependencies and actual checks/limitations. A draft with unresolved required outcomes remains a draft. Keep authoring logs and tool limitations in the completion message; retain only limitations affecting acceptance in the document.

Normal execution is sequential. This skill does not independently authorize subagents or another approval ceremony. Supporting skills follow this parent scope and output contract. Keep temporary inventories and checker reports outside project deliverables; embed the human-readable source and coverage registers in the one document.

## Maintenance and provenance

Use stable case IDs; record retired cases and replacement links instead of recycling IDs. Reconcile source changes, scenario changes and evidence through the update rules in the output contract, including [persistence redesign acceptance](references/output-contract.md#persistence-redesign-and-evidence-preservation). Full coverage means distinct rules, boundaries, transitions and failure modes, not repeated variants that prove the same behavior.

The selected Mekari and public-skill adaptations are documented in [sources](references/sources.md), with file identities in [source manifest](references/sources.json) and upstream notices in [NOTICE](NOTICE). QA Test Planner, Test Master, BMAD and Superpowers are adapted reference material, not required installed packages. See [validation record](references/validation.md) for the bounded evaluations and their limits.
