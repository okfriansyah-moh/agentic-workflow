# Persistence decisions

First honor the selected engine and service ownership. Where genuinely open, evaluate access patterns, data relationships, transaction/isolation guarantees, constraints, query/index needs, durability/recovery, migration, operational expertise and cost.

Use official documentation for the specific engine/version. Avoid blanket claims that a database category cannot support transactions, schemas or scaling. Document the actual limitations and configuration relevant to this workload. Compare native query behavior and compatibility against the selected engine rather than assuming an in-memory substitute establishes correctness.

Specify owner, identifiers, indexes and constraints, transaction boundaries, lifecycle/retention, migration/backfill and backup/restore. Consider query plans and stable ordering. Parameterize values and constrain dynamic identifiers. Explain safe seeds, reruns and concurrent effects when required. A choice of database is not permission to run a migration.
