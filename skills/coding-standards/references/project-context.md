# Discover project context

Read this reference once for the affected components; reuse the findings until files or requirements change. This is shared guidance for the portable A2A skill collection, not a request to restructure a project.

## Establish the working contract

- Read applicable project instructions and the user’s request, accepted decisions, and existing approvals. Follow the current mode and filesystem permissions. In Plan mode, inspect and propose; do not implement or persist new plans.
- Identify each affected component’s language, runtime, framework, package manager, manifests, lockfiles, and nearby implementation. A repository may contain several languages and several versions. Work per component rather than assigning one stack to the whole repository.
- Find actual build, test, lint, type-check, migration, and generation commands in project documentation, scripts, task runners, and CI. Record their working directories and prerequisites. Prefer these commands to guessed ecosystem defaults. Mark a check inapplicable when the component has no such concept; never fabricate a successful check.
- Discover architecture decisions, public boundaries, data contracts, database engines, and documentation conventions. Existing naming, error handling, paths, and native language idioms take precedence over illustrative examples in these skills. Use schemas, documented shapes, modules, traits, records, classes, or functions as appropriate; static types and object-oriented layers are not universal requirements.
- For an unfamiliar language or API, inspect local tooling/help and authoritative version-matched documentation. Ask only about unresolved choices that materially affect behavior. Missing tools permit honest inspection-only results, not invented execution or automatic installation.

## Execution and scope

Use the user’s authorized scope and existing approvals. Revisit approval only for a material design change or an action requiring authorization not already given. Installation or discovery of a skill does not itself authorize setup scripts, hooks, commits, publications, deployments, or destructive actions. Respect denied operations; report the blocked part and continue independent permitted work.

Use available Codex tools rather than assuming Copilot/Claude commands, a particular todo API, writable memory paths, model controls, or named preconfigured agents. Inherit the current model unless the user requests otherwise. Delegate only when permitted and beneficial; if unavailable, work sequentially and identify the loss of independent review. Independent reads can run together; dependent edits and integrations stay ordered.

Scale planning and verification to the task. Reuse an approved design and established test boundaries. A small correction does not require an architectural interview, new plan file, full security audit, or extra completion approval. Complete authorized work, fix findings introduced by the change, and distinguish unrelated baseline failures and unavailable checks from passes. Avoid assurance such as “secure” or “production-ready” beyond the evidence.

## Completion evidence

For the changed behavior, retain the requirement, relevant interface, validation command or inspection, actual result, and meaningful remaining limitations. Keep temporary fixtures outside the project when allowed. Follow the project’s established artifact location when producing requested documentation; global skill installation never creates project artifacts by itself.
