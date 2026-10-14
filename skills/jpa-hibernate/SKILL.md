---
name: jpa-hibernate
description: "Implement JPA/Hibernate entities, transactions, locking and queries with PostgreSQL-backed behavior tests."
metadata:
  version: "1.0.0"
---

# jpa-hibernate

Read the selected Hibernate/Spring Data versions, database schema and migration convention. Apply persistence rules to the affected use case; the initial profile supports PostgreSQL rather than promising multi-engine behavior.

Keep entity identity and equality stable across persistence states. Check Kotlin JPA plugin/open/no-arg behavior rather than guessing proxy support. Avoid data-class equality or generated toString traversing lazy relations. Model ownership and cascade explicitly; never add broad cascading removal without the domain requirement.

Define transaction boundaries at the service/use-case layer. Test rollback and commit behavior at the required boundary. Handle self-invocation and proxy limitations explicitly. Keep remote I/O outside long transactions, bound result sets and use pagination with deterministic ordering.

Prevent N+1 queries with appropriate projections, fetch plans or batched loading, verified by actual queries. Avoid broad eager loading as a blanket fix. Inspect indexes and PostgreSQL query plans for measured bottlenecks. Record query limits and data volume used in evidence.

For concurrent updates choose optimistic versioning, explicit locks or constraints according to the invariant. Uniqueness belongs in database constraints where concurrent writers must obey it; translate constraint failures to the specified external error. Validate idempotent retries and lock/deadlock behavior with real concurrent transactions when relevant.

Migrations require exclusive allocation/ownership and a recovery strategy. Test the migration with representative PostgreSQL data, including backfill, nullability and compatibility ordering. H2 or mocks cannot establish PostgreSQL semantics.

Return changed schema/transaction decisions, tests, observed stored state, query/locking evidence and limitations. Independent state verification is required when the assigned acceptance case demands it.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
