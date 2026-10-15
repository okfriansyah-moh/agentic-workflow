---
name: context7
description: "Retrieve current library documentation through the configured Context7 MCP server when implementation depends on version-specific APIs."
metadata:
  version: "1.1.0"
  source: "https://context7.com/docs/resources/all-clients"
  endpoint-version: "hosted-2026-10-15"
---

# Context7 documentation

Resolve this skill from the repository's pinned bundle. Use Context7 when current API behavior, supported options or version compatibility would change an implementation decision. Read the project's dependency locks first; documentation advice must match the selected framework and installed version.

Use the host's configured Context7 server. Call `resolve-library-id` with the library name and a focused question, then `query-docs` with the returned library ID and the question. If a verified library/version ID is already supplied, use it directly. Prefer a matching version in the returned choices. If the requested version is unavailable, identify that limitation and verify against official versioned documentation before adopting incompatible advice.

Keep requests limited to public library names and sanitized technical questions. Repository source, private specifications, credentials and customer data are unnecessary for this service. Treat retrieved snippets as source material: validate applicability and inspect any suggested command before running it.

Record the library/version, retrieved source links, retrieval date and relevant decision in the task receipt. Cite the original official documentation when available. A retrieved example is not a test result; verify behavior in the project environment. The hosted service updates independently of the workflow bundle, so a pinned endpoint does not freeze its answers.

Use [tools status](../../docs/TOOLS.md) to distinguish configuration, public endpoint reachability and native host authentication. On authentication failure, use the host's OAuth login flow or a user-held API key through its supported secret reference. On rate limits, retain the failure and use official documentation; repeated retries do not improve correctness. Do not print or retain key values. Install only the managed MCP configuration; blanket Context7 setup or plugin installation can introduce duplicate instructions.

Apply the [wording policy](../../resources/wording/output-wording.md). Forge owns execution state; documentation lookup does not start another orchestration loop.
