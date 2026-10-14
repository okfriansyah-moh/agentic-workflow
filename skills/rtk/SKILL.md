---
name: rtk
description: "Use an available RTK CLI to reduce verbose command output. Use when RTK is requested or suitable for large logs; fall back to ordinary tools when unavailable."
---

# RTK output compression

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Check whether `rtk` is installed in the command environment. If absent, use the original command with targeted output and state the limitation only when relevant. Installing RTK or shell hooks is a separate task; do not run a remote install script merely to use this skill.

If installed, inspect `rtk --version`, `rtk --help`, and the relevant subcommand help. Confirm the exact invocation and supported underlying tool for that version. Do not assume arbitrary shell commands can be prefixed with `rtk`, or that every command, flag, failure detail, or exit status is preserved identically. Consult official version-matched RTK documentation when help is insufficient.

Use compression for verbose text where a summary is adequate. Keep interactive sessions, binary/machine-readable output, exact patches, and evidence requiring full logs on their native path. Preserve important diagnostics and actual completion status; a compressed summary is not proof of a passing check.

If output omits needed evidence, use a documented raw-output mechanism or capture the original output. Avoid repeating a side-effectful command merely to obtain fuller logs; inspect existing logs first and establish replay safety. Keep credentials and sensitive data out of retained output.

Finish by reporting the command’s actual result, not an assumed token-saving percentage.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

