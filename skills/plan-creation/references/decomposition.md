# Decompose by a reviewable result

Start with user outcomes and the complete obligations inventory. A feature group binds the work needed to demonstrate one coherent outcome; frontend/backend/operations are task responsibilities within the group. A group may have one full-stack task when a reviewer can assess that change coherently. A broad feature can be split by actor, business rule, workflow step, data variation or failure/recovery capability when each slice has a meaningful result.

Split when ownership, a prerequisite contract, an independently testable responsibility, a dangerous migration, or the amount of source context makes one review unwieldy. Do not split merely to satisfy a minute/file/endpoint quota or to create a database/service/UI assembly line. Unit/component tests normally belong beside the code they verify. Give real integration proof an owner; use a separate integration task only when its fixtures, dependencies or work justify one.

Build one thin working path early. Introduce shared foundations only when they support actual included features. Contract tasks implement adopted source contracts, not a second architecture phase. For multiple repositories, name each root and ownership explicitly; use separate implementation tasks when independent checkout/build/release boundaries warrant it, and an integration owner across the real boundary.

## Dependencies and concurrency

For each task identify inputs and produced artifacts, not just numeric predecessors. A contract/type artifact can unblock frontend work before backend behavior exists; frontend mocks remain component evidence. Real feature acceptance waits for actual producers and consumers.

Derive dependencies from schemas, contracts, shared primitives, environment setup and acceptance fixtures. Detect cycles before writing waves. Derive a feasible task order, then number feature folders by their first appearance in that order. Use a stable tie-break for independent tasks, such as an accepted priority followed by task ID. Folder order communicates where to start; explicit task dependencies still govern eligibility, including later returns to earlier groups. A task depends on a producer even if the files do not overlap. A verification task depends on every implementation surface it must exercise.

Check completion criteria as well as declared dependency edges. Contributors may finish their assigned checks and reviews while feature integration remains pending; a downstream integration task cannot also be a prerequisite for completing its own inputs. Keep its remaining proof in the contributor's handoff and the feature's closure criteria.

Parallel eligibility requires no dependency path in either direction and compatible ownership/resources: source files, generated outputs, migrations, lockfiles, shared configuration, test fixtures/ports/databases and integration destinations. Disjoint filenames alone are insufficient. Explicitly serialize shared write surfaces or assign them to a prerequisite owner. Waves are an optional presentation of the dependency graph, not an extra scheduling authority or permission to spawn agents.

## Knowledge and detail

Keep task instructions complete for a fresh agent with source access: locate exact source sections, restate the essential task-specific invariant, describe intended edits, and specify expected results. Keep large schemas, shared rules and acceptance catalogs in their owning documents. Refer to a case's exact rows and proof boundary; a giant range of IDs without assigned assertions hides gaps.

Distinguish observed existing files/commands from proposed targets in a greenfield design. New targets are concrete planned paths, with a producer task for shared scripts/fixtures. Do not claim nonexistent commands ran. Reconcile names with the source design and implementation; visible naming differences require a recorded mapping, not parallel implementations.

Global guidance lives at the root, feature guidance in the group, local consequences in tasks. An implementer reads that short chain plus selected sources, not the entire project documentation corpus per task. The planner still inventories the complete relevant sources once and performs a fresh coverage reconciliation before handoff.

## Scope control

No generic requirement for caching, a database, authentication, containers, a UI library, AI features, full application hosting, an epic key, Jira, story points or deployment. Add them only from actual source obligations or explicit choices. Record material missing behavior as an owned decision/gap with its affected tasks. Ordinary reversible implementation choices can be specified without reopening accepted architecture.
