---
name: kotlin-spring
description: "Implement approved Kotlin/Spring Boot service and transport behavior with explicit validation, lifecycle and error handling."
metadata:
  version: "1.0.0"
---

# kotlin-spring

Read the project's resolved Kotlin, Spring Boot and JVM versions, source layout, shared contracts and build tasks. Reuse selected architecture and the task's test strategy. This skill does not choose new framework versions or generate a new service topology.

Keep domain behavior independent of transport and persistence adapters where the approved architecture defines those boundaries. Validate untrusted requests at the entry boundary and preserve distinct validation, authorization, missing-resource, conflict and infrastructure errors. Use explicit DTOs so entities and internal exceptions do not leak through REST, GraphQL or gRPC.

Use Kotlin nullability to model real absence. Avoid unchecked casts and force-unwrapping at external boundaries. Keep immutable values where practical, bounded collections, explicit time sources and stable ordering where observable. Translate cancellation, deadlines and error types at transport boundaries without swallowing failures.

Load spring-dependency-injection for bean wiring and jpa-hibernate for persistence. Keep transaction scopes short and move slow network calls outside database transactions unless the contract deliberately requires coordination. Model retries/idempotency where the operation can repeat.

For GraphQL check resolver authorization, error shape, pagination and N+1 behavior. For gRPC check protobuf compatibility, deadlines, status mapping and real client behavior where ATDD requires it. Serialization contracts and schema generators are shared resources with one owner.

Run formatting/static checks and the smallest relevant behavioral tests, then compilation and required integration checks. Include invalid input, permissions, failure mapping and concurrency cases when they are part of the changed behavior. A mocked repository does not prove PostgreSQL behavior. Return contract IDs, changed paths, checks and known gaps.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
