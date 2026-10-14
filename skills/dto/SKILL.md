---
name: dto
description: "Define or evolve data contracts across process, module, or persistence boundaries. Use for DTOs, schemas, serialization, and producer-consumer compatibility."
---

# Boundary data contracts

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Determine the boundary and serialization protocol first. Represent the contract with native types, a schema, generated messages, or documented shapes appropriate to the language and consumers.

Specify required versus optional fields, absence versus null, defaults, validation ownership, units, encoding, precision, and error handling. Binary data, timestamps, unions, collections, and nested objects are valid when the protocol defines their representation. Prefer immutable transfer values where useful; distinguish shallow readonly markers from deep immutability.

Keep transport representations separate from internal models when they have different lifecycles. Validation may live with a type or at a boundary according to project conventions. Avoid forcing raw maps or forbidding them without considering the interface.

For evolution, identify producers and consumers, unknown-field behavior, wire compatibility, and migration needs. Preserve compatibility intentionally rather than declaring every contract append-only forever. Choose identifiers based on uniqueness, privacy, domain identity, and retry needs; a truncated content hash is not a universal ID.

Verify representative round trips and old/new consumer scenarios with native tooling. Reference this contract from planning and implementation instead of maintaining duplicate schemas.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

