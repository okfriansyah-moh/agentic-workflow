# Release 1.4.0: permanent quality contracts

Agentic Workflow 1.4.0 retains 74 bundled skills, native roles for four coding-agent hosts, and the Python standard-library CLI.

## Changes since 1.3.0

- Permanent quality contracts require per-component unit and changed-line coverage of at least 80%, analyzer line and combined line/condition coverage of at least 80%, and zero security, reliability and raw duplication counts.
- Feature acceptance requires registered full quality evidence tied to source, tests, configuration, commands, toolchains and successful gate results. Missing reports and unsupported component ownership remain blocking.
- Pinned Docker toolchains, bounded commands and sequential resource admission govern substantial verification. Linux process monitoring accepts valid kernel process-group rows.
- Shared reuse and cleanup guidance prioritizes implementation, existing owners and evidence of consumers before removal.
- Expanded workflow diagrams and examples connect requirements, design, technical contracts, acceptance cases, planning and delivery.

See the [quality contract](GATES.md#permanent-quality-contract), [delivery policy](DELIVERY.md), and [installation guide](INSTALLATION.md).

## Installation and upgrade

Check out tag `v1.4.0`, then follow the [README](../README.md#quick-start). Test upgrades and rollback in temporary homes and repositories before updating selected installations. Existing project pins and unrelated configuration remain protected.

## Verification boundaries

Release publication checks assess bundle integrity, temporary installation behavior and publication documentation. They do not certify application quality, native host loading, hook trust or live reviewer invocation. Product acceptance still requires the configured evidence. Historical results apply only to the revisions and environments they measured.

Component licenses, notices and attribution remain applicable; see [provenance](PROVENANCE.md).
