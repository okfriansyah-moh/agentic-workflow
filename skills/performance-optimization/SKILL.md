---
name: performance-optimization
description: "Investigate and improve a measured performance bottleneck. Use for latency, throughput, memory, query, or resource-consumption problems."
---

# Performance optimization

Apply [the personal output wording policy](../../resources/wording/output-wording.md) to generated deliverables and completion text. Before handoff, run its shared read-only checker on the complete output, rephrase flagged text without changing meaning, and require a clean result.

Define the user-visible metric and representative workload. Establish a reproducible baseline with the stack’s actual profiler, tracing, query plan, or benchmark tooling. Separate warmup, cache state, input scale, and environmental noise.

Find the dominant cost before changing code. Consider algorithmic complexity, query count and plans, allocation, serialization, I/O, contention, and downstream limits. Indexes, batching, pooling, asynchronous I/O, and compression have tradeoffs; choose them from measurements rather than a universal checklist.

Bound concurrency, buffers, collections, and caches according to workload. For slow stream consumers, define backpressure, disconnect, coalescing, or permitted event loss explicitly; silent fire-and-forget loss may break correctness. Cache keys and invalidation must cover all dependencies and freshness requirements.

Change one meaningful bottleneck, verify correctness, then compare the same workload and metric. Include regressions in tail latency, memory, write cost, and complexity where relevant. If measurements are unavailable, distinguish a hypothesis from a demonstrated improvement and identify the next useful measurement.

## Project adaptation

Before applying this workflow, read [shared project context](../coding-standards/references/project-context.md) once for the affected components. It governs language/tool discovery, scope, modes, permissions, and validation. Reuse it while the context is unchanged.

