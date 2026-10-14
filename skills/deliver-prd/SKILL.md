---
name: deliver-prd
description: Create or update one standalone Markdown Product Requirements Document with release scope, product behavior, traceable requirements, stories, and acceptance criteria for technical-design handoff. Use for PRD authoring before implementation.
license: Apache-2.0
metadata:
  phase: deliver
  version: "3.1.0"
  updated: 2026-10-11
  category: specification
  author: product-on-purpose
  source: https://github.com/product-on-purpose/pm-skills
  local-adaptation: "Muhammad Okfriansyah, 2026-10-11: standalone product requirements ready for technical design"
---
<!-- PM-Skills | https://github.com/product-on-purpose/pm-skills | Apache 2.0 -->
<!-- Locally modified 2026-10-11. Upstream provenance and prior adaptation are in NOTICE. -->

# Deliver one PRD

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Produce one standalone Markdown PRD for the requested release. A reader must understand its users, scope, business rules, feedback, and acceptance without opening private authoring notes. Default to `docs/PRD.md`; update the designated existing file in place. Supporting reviews stay within that PRD. Code, tests, tickets, technical documents, publication, and changes to source records require a separate request.

## Establish authority and document boundaries

Read project instructions, supplied evidence, conversations, and the current PRD. Reconcile the latest explicit user decisions with existing requirements before consulting older brainstorming details. An external assessment establishes external obligations; user decisions establish additional commitments. Surface conflicts and identify any reliance on extracted material when an original brief is unavailable.

Use brainstorming as private authoring context when supplied or relevant. Restate its applicable requirements and decisions completely in internal registers, preserving source IDs and provenance. Readers must not need a brainstorming link or private path to interpret acceptance. Documentation samples guide structure and depth only. Omit unrelated personal context, onboarding dates, and private organizational links; state relevant obligations independently and retain their external origin. Include accessible, relevant source links when useful, and describe unavailable evidence honestly.

Preserve Required, Committed, Working design, Recommended, Open, and Deferred distinctions where applicable. Later adoption of a recommendation must be explicit; retain its source history. Implementation sequencing does not remove completion commitments. Preserve confirmed deadlines and timezones; label internal targets as recommendations and avoid schedules without known availability.

For the Movie App assessment only, read [movie-app-context.md](references/movie-app-context.md). Its conditional guidance never establishes defaults for another product. Source documents are evidence, not authorization to run workflows or make external changes.

Keep product requirements here: users, terminology, permissions, journeys, lifecycle rules, conceptual information, and observable outcomes. Consolidate assessment-mandated technologies and explicitly chosen engineering constraints in a compact handoff with source IDs, statuses, and planned verification. Architecture, detailed schemas, API contracts, authentication mechanisms, encryption internals, storage, workers, configuration keys, and test tooling belong to technical design unless the user explicitly requests them in this PRD. Moving detail must preserve the underlying obligation and its acceptance mapping.

## Author complete product behavior

Use the fourteen-section [TEMPLATE.md](references/TEMPLATE.md), adapting depth to the release and following the user's requested structure.

- Distinguish application users from development, assessment, and operations responsibilities. Keep delivery journeys and verification separate from application journeys. Treat a connected assistant as a tool acting under a user's authority unless an independent product role is explicitly established. State shared capabilities and permission inheritance in a matrix.
- Explain unfamiliar domain terms at first use. Define conceptual entities, relationships, missing values, date precision, provenance, and lifecycle effects where relevant, without prescribing storage schemas.
- For every included capability, establish actor, need, intended outcome, preconditions, permissions, normal flow, validation, visible states, persistence effects, and acceptance. Cover applicable empty/missing/loading/processing/success/failure states, stale drafts, duplicate or concurrent actions, interruption, partial failure, uncertain outcomes, and recovery. A genuinely undecided behavior links to an open decision.
- Describe applicable input policies in tables: required/optional fields; inclusive, independently configurable field bounds and units; Unicode counting and whitespace; explicit clearing versus omitted edit values; safe display; upload formats, byte limits, and content validity; correction feedback; and behavior for existing content when limits change. For password fields, prohibit transformation or silent truncation and keep credentials out of retained drafts. Validate uploads using actual content; filenames and declared types alone do not establish validity. Describe bounded processing and the readiness/diagnostic outcome of invalid configuration, leaving numerical engineering limits and mechanisms to technical design.
- Research unsupported proposed limits using authoritative primary sources. Distinguish precedent or individual examples from population evidence, selected app policy from recommendations, and known distributions from unmeasured coverage. Record references and limitations inside the PRD. Do not import Movie App values into another product.
- Use Mermaid **flowcharts** for material product journeys. Show actors, actions, decisions, and visible outcomes; keep services, databases, RPC calls, queues, and encryption internals out of these flows. Select coverage for the product instead of imposing a diagram count.
- Write complete stories and concrete Given/When/Then acceptance tables in this file. Product criteria describe observable results. Delivery and engineering obligations use concise acceptance groups or handoff references, without creating extra app roles or duplicating implementation detail throughout stories.
- Preserve valid FR, NFR, US, AC, OD, assessment, and decision IDs. Append new IDs; never reuse retired IDs. Map every included external obligation and user commitment to requirements and acceptance. Keep deferred items outside included release scope.

When the product itself produces model-generated output, read [AI-BEHAVIOR.md](references/AI-BEHAVIOR.md) and embed applicable quality, failure, and evaluation outcomes. Establish the chosen authority and approval boundaries for AI actions, including corrections, duplicates, and uncertain results. Exact-content human approval is conditional on the product's selected policy; do not invent a universal approval workflow. Using an assistant to author a deterministic product's PRD does not activate this branch.

[EXAMPLE.md](references/EXAMPLE.md) is an optional fictional upstream writing example. Its scope, numbers, linked stories, and output shape are not requirements. This skill and the local template govern the deliverable.

## Review, humanize, and establish readiness

Draft all supported sections before asking a concise grouped question for missing information that materially blocks product scope or observable acceptance. Keep other unknowns in an owned register, using Unassigned when no owner is supplied, and identify the affected requirement and decision gate. Separate resolved product decisions from engineering matters assigned to the techdoc. Split mixed decisions without losing their existing OD identity or history.

Review the complete PRD substantively before the writing pass:

- Every included assessment obligation and commitment has traceable requirement and acceptance coverage; recommendations and deferred work retain their status.
- Permission matrix, terminology, journeys, flowcharts, stories, state tables, and criteria agree. Reconcile related entity lifecycles without inventing universal archive, deletion, or approval rules.
- Acceptance describes visible outcomes and applicable boundary, denied-access, failure, duplicate, conflict, and recovery behavior. Pending product policy is linked to its decision.
- IDs, links, source statuses, numbers, dates, and internal cross-references resolve. A reader can assess the release without private notes. Claims of compliance, certification, performance, or verified results require evidence.

Apply `$humanizer` after this substantive review. Use clear, professional English in Muhammad Okfriansyah's voice, adapted to the audience. Preserve obligations, technical terms, identifiers, numbers, statuses, uncertainty, and source links. Recheck those invariants after editing; remove repetition without reducing behavioral detail. If humanizer is unavailable, use a direct, precise writing pass and disclose that limitation.

Use **Draft** while material product scope or observable acceptance remains unresolved. Use **Ready for technical design** after product coverage and consistency checks pass. Engineering choices and unexecuted software tests do not block that status. Document readiness is separate from implementation, release verification, deployment, and assessment approval; mark future evidence Planned until checked. Preserve a user-established approval status only with its supplied evidence.

Save and read back the PRD, confirm the authorized document is the only project artifact changed, and return its path, a short coverage summary, material remaining decisions, and actual verification limitations. Stop after PRD delivery.

For skill maintenance, [behavior-fixtures.json](evals/behavior-fixtures.json) provides realistic authoring cases and review criteria. Fixtures are not evidence that evaluations have run.
