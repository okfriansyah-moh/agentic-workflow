---
name: node-backend
description: "Implement Node/TypeScript services or the selected MCP adapter with validated input, cancellation and controlled I/O."
metadata:
  version: "1.0.0"
---

# node-backend

Identify the selected runtime, module format, package manager, lockfile and service contract. Implement the approved Node component; this does not introduce a new server or framework merely because a skill exists.

Validate input at public boundaries using the project's schema convention. Type annotations do not validate JSON. Separate domain behavior from protocol envelopes and I/O adapters; inject clocks, persistence or clients when they represent real substitutable dependencies. Keep dependency direction acyclic without creating empty abstraction layers.

Bound request sizes, concurrency, timeouts, retries and output. Propagate cancellation/deadlines into supported I/O and close owned handles. Keep secrets out of errors/logs; classify user errors separately from infrastructure failures. Use argument arrays for child processes and allowlisted operations where shell execution is part of the approved contract.

For MCP follow the selected protocol/SDK version: validated tool arguments, bounded content, truthful errors, capability declarations and transport cleanup. Keep diagnostics away from protocol stdout for stdio transports. Authorization and tool exposure derive from project requirements, not the ability to invoke a process.

Preserve GraphQL/gRPC/API compatibility and schema generation ownership. Coordinate dependency lock updates with the owner. Use deterministic fixtures and real transport/client checks when the acceptance contract requires them; directly calling a handler proves only that boundary.

Run agreed affected checks with existing lint, type, dependency and behavioral/security tools as applicable. Explicit no-test limits prohibit added/executed tests and substitute trials; keep omitted proof pending. Record runtime versions, request/response observations, resource cleanup and any transport/database boundary still unverified.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
