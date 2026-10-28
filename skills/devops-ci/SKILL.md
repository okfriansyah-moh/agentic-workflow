---
name: devops-ci
description: "Implement reproducible local/CI builds, Compose environments and operational release or recovery checks."
metadata:
  version: "1.0.0"
---

# devops-ci

Inspect the approved environment, lockfiles, image/version policy and existing CI. Use local Compose for the initial profile; Kubernetes/HPA guidance is outside this bundle.

Define reproducible commands with explicit working directories, prerequisites, failure exit codes and bounded output. Reuse the shared gate registry across local verification and CI. Run checks on the reviewed revision, retain machine-readable reports and fail when a mandatory scan/tool is unavailable.

Keep build inputs and runtime secrets separate. Use supported pinned tool/container versions, minimal privileges and sensible health checks. Avoid credentials in image layers, build arguments, logs or recordings. Record the source of externally supplied settings without persisting secret values.

Give parallel lanes distinct ports, database names, Compose project names and output directories through their claims. Serialize migrations, dependency locks and generated shared contracts. Cleanup touches only the lane's resources and preserves failure artifacts.

Verify startup, health, graceful shutdown, dependency failure and recovery where relevant. Resource limits, pool sizes and concurrency must agree with each other. Capacity claims require a measured load scenario and environment; do not infer production headroom from a local smoke test.

Prepare deployment/recovery procedures only within the authorized scope. PR merge, deployment and external-team messages remain separate actions. A runnable release procedure is not authorization to run it.

Return exact build/Compose/CI checks, image/tool versions, artifacts, recovery limits and configuration still required.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

Apply the [permanent quality contract](../../docs/GATES.md#permanent-quality-contract) for configured checks and feature acceptance. Installation, native loading and passing product evidence require separate results; existing failures remain blocking.
