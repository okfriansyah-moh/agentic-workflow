# Conditional supporting skills

Resolve these relative to this installed bundle. Read each skill before applying it. Pass the target document, relevant source IDs, accepted constraints and requested section/finding scope. Source requirements and the single-document contract override examples and output defaults.

| When | Skill | Contribution |
| --- | --- | --- |
| Integrating context, shaping sections, reader review | A fresh reader review | Evidence-led prose and comprehension checks |
| New system/boundary design or architectural tradeoffs | [architecture-designer](../../architecture-designer/SKILL.md) | Requirements-led ownership, interactions, NFRs and options |
| Significant technical choice | [architecture-decision-records](../../architecture-decision-records/SKILL.md) | Embedded decision records and supersession |
| Trust boundaries/exposed entry points | [stride-analysis-patterns](../../stride-analysis-patterns/SKILL.md) | Concrete threats with assets, triggers and impact |
| Turning threats into implementation obligations | [security-requirement-extraction](../../security-requirement-extraction/SKILL.md) | Control and acceptance mappings |
| End-to-end features, shared boundaries, code conventions | [vertical-slice](../../vertical-slice/SKILL.md), [modularity](../../modularity/SKILL.md), [codebase-design](../../codebase-design/SKILL.md), [coding-standards](../../coding-standards/SKILL.md) | Cohesive features and language-appropriate conventions |
| Public/internal contracts | [api-design](../../api-design/SKILL.md), [dto](../../dto/SKILL.md) | Protocol semantics, data presence, errors and compatibility |
| Persistent data/schema evolution | [migration-management](../../migration-management/SKILL.md) | Migration integrity, deployment compatibility and recovery |
| Replay, concurrent mutation and durable follow-up | [idempotency](../../idempotency/SKILL.md), [failure](../../failure/SKILL.md), [pipeline](../../pipeline/SKILL.md) | Atomic boundaries, bounded retries and recovery |
| Settings, defaults and secrets | [config-validation](../../config-validation/SKILL.md) | Precedence, validation and lifecycle |
| Security design challenge | [security-audit](../../security-audit/SKILL.md) | Review assets, boundaries and controls; no unsolicited live scan |
| Verification obligations and final consistency | [test-generation](../../test-generation/SKILL.md), [docs-sync](../../docs-sync/SKILL.md) | Design-level scenarios and source reconciliation; no test-code generation |

The installed skills may describe implementation work. During techdoc creation use them only to specify and review that behavior. Their implementation actions stay inactive. Existing-code-only routes operate only when relevant code exists; absence of code does not block future-state design.

Technology-specific adapters activate only for an independently selected matching technology and an actual need. A backend language does not select a frontend framework; Markdown/Mermaid output does not select application technology. Kubernetes HPA is conditional on a selected Kubernetes deployment. Do not infer HPA from an ambiguous reference to an ORM or persistence library.

Report missing routes in the completion message. Record a technical dependency in the document only when the missing capability leaves a consequential design or verification gap. Continue with the output contract and primary references where possible. Avoid activating every installed skill or producing independent overlapping specifications.
