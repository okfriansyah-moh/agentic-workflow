# Ownership, execution, integration, and evidence

The chat's native Forge coordinator owns task-status updates. Python helpers read plan files, reserve writing lanes, create worktrees, capture actual commands, and inspect receipts. They do not launch an agent, interpret Markdown as commands, edit source requirements, or dispatch an application task during installation.

## Index an existing plan

```sh
.ai/bin/agent-workflow task-index --plan docs/06-PLAN.md --output .ai/state/task-index.json
```

The supported version-1 format uses `kind: plan`, a `plan_root`, source IDs/paths/SHA-256 values, and group IDs/paths. Each group names member tasks and an integration-owner task. Task frontmatter contains its ID, group, dependencies, readiness, status, test strategy, and visual-review applicability. The reader supports simple scalars, inline scalar lists, indented mappings, and block lists. It rejects duplicate keys and unsupported YAML expressions instead of guessing their meaning. No YAML constructors or executable expressions are evaluated.

The index checks source digests, linked files and Markdown section targets, unique task/group ownership, integration-owner membership, known dependency IDs, and dependency cycles. It preserves IDs, references, acceptance IDs, change surfaces, and task statuses. `execution_eligible` means Ready with Done dependencies; it does not establish installed tools, available services, accepted reviews, task completion, or feature acceptance. Task files remain the execution record. Index output can be rebuilt at any time.

## Reserve a writing lane

Create a JSON brief under `.ai/state/`. The coordinator supplies exact sources, case IDs, and checks from the accepted task. The `plan` field is recommended for planned implementation: it derives dependencies, verifies eligibility, and rejects claims outside task change surfaces. Omit it for a bounded request without a saved plan, providing explicit dependency IDs instead.

```json
{
  "owner": "backend-worker-1",
  "task_ids": ["T001"],
  "plan": "docs/06-PLAN.md",
  "base_revision": "FULL_GIT_REVISION",
  "paths": ["build.gradle.kts", "gradle"],
  "resources": ["port:43001", "database:task-t001", "output:run-t001"],
  "source_references": ["docs/06-PLAN.md", "docs/plan/01-reproducible-foundation/tasks/T001-lock-the-build-and-isolated-verification-harness.md"],
  "acceptance_ids": ["T001-A1", "T001-A2", "T001-A3"],
  "required_checks": [
    {
      "id": "local-tests",
      "kind": "test",
      "argv": ["python3", "tests/run_selected.py", "--task", "T001"],
      "cwd": ".",
      "timeout": 300,
      "test_report": {"path": ".ai/evidence/tests.xml", "format": "junit"}
    },
    {"id": "self-review", "kind": "check", "argv": ["python3", "scripts/check_local_review.py"]}
  ]
}
```

```sh
.ai/bin/agent-workflow claim --repo . --spec .ai/state/brief.json --output .ai/state/claim.json
.ai/bin/agent-workflow worktree --repo . --claim lane-ID --owner backend-worker-1 --path ../worktree-t001 --branch work/t001
```

The requested base must equal the integration checkout's current commit. Creating the worktree checks the base again and refuses an existing destination or already-used claim. Models and native worker sessions remain host-owned. The coordinator must include the resulting worktree and claim in the native worker's prompt and reduce concurrency if host capacity is smaller than three.

Claims are stored in `agent-workflow/registry.json` under Git's shared metadata directory. `flock` serializes writers across participating chats and worktrees; atomic replacement avoids partial registry writes. It does not coordinate unrelated clones. Locks are released by the operating system if a process exits. An old timestamp is an attention flag, never permission to steal a claim.

Overlapping directories, duplicate task IDs, and resource-name collisions block claims. Common schema, generator, dependency-lock, build-config, and migration paths also add shared resource claims. Unusual project generators and external resources still need explicit names. Reserve distinct ports, databases, namespaces, and output directories. Directory claims without a file extension conservatively reserve every shared mutation category, including planned files that do not exist yet. Use narrow file claims when independent lanes need concurrency. Writing lanes are limited to the minimum of three, repository `max_workers`, and the brief's optional `host_capacity`; only one active integrator is allowed.

An integrator brief uses `"role": "integrator"`, a unique integration task label, empty `paths`, and the combined check contracts in `required_checks`. Its writes consist of accepting reviewed worker commits and resolving their integration defects. The integrator also receives an isolated worktree from its recorded base.

## Capture actual command results

Commit the bounded implementation before capturing the receipt. Place command specifications and output under `.ai/state/` and `.ai/evidence/` so bookkeeping does not change the tested input fingerprint.

```json
{
  "claim_id": "lane-ID",
  "owner": "backend-worker-1",
  "environment": "isolated development fixture",
  "selected_cases": ["T001-A1", "T001-A2", "T001-A3"],
  "commands": [
    {
      "id": "local-tests",
      "kind": "test",
      "argv": ["python3", "tests/run_selected.py", "--task", "T001"],
      "test_report": {"path": ".ai/evidence/tests.xml", "format": "junit"},
      "timeout": 300
    },
    {"id": "self-review", "kind": "check", "argv": ["python3", "scripts/check_local_review.py"]}
  ]
}
```

The example commands are illustrative project interfaces, not preinstalled commands. Use actual registered checks. Each check contract contains `id`, `argv`, explicit `kind: "check"` or `"test"`, optional `cwd` (default `.`), optional `timeout` (default 300 seconds), and a `test_report` for tests. Receipt commands must match the normalized brief contracts exactly; changing a test into a successful no-op check is rejected. `receipt --repo WORKTREE --spec SPEC.json` executes each `argv` directly without a shell and captures stdout, stderr, times, exit codes, log hashes, changed paths, tested Git revision, input hashes, and a small environment description. It does not capture environment-variable values. Use isolated synthetic data and inspect retained logs for secrets before sharing them.

Test commands need a fresh machine-readable report: `junit` test cases, Vitest JSON test counts, or `workflow-test` JSON containing integer `selected`, `executed`, and `failed` counts. Zero selections, skipped/unexecuted selected tests, failures, stale reports, unsupported reports, missing executables, timeouts, and implementation changes during checks block the receipt. A zero command exit alone is insufficient for a declared test check. Reviewers check the selected cases against the source task; a custom report adapter must derive counts from the test runner.

The fingerprint covers all tracked and unignored files, including executable modes. It excludes `.ai/evidence/`, `.ai/state/`, `.ai/reports/`, `.ai/install-backups/`, dependency/cache and known generated-output directories (`node_modules`, `.gradle`, `.svelte-kit`, `__pycache__`, virtual environments, `.cache`, `test-results`, `playwright-report`, `coverage`, `build`, `dist`, and `generated`), filesystem metadata, and a task's status/Evidence section. Requirement text, source documents, acceptance criteria, implementation, tests, and configuration remain inputs. Editing a task's acceptance criteria invalidates proof; writing its evidence row does not. Do not place implementation inputs in excluded output directories. Source files and checked bundle code remain inputs. The CLI `fingerprint` command returns this same implementation hash under its `sha256` field; copy that value into evidence `input_fingerprint`. Git repositories use one shared algorithm across gates, receipts, and evidence. Non-Git fingerprinting is fixture-only and cannot replace Git-bound implementation receipts.

## Independent review and integration

A different native worker reads the brief, source requirements, commit diff, receipt, test output, and evidence. It records JSON such as:

```json
{
  "reviewer": "review-verify-worker-2",
  "tested_revision": "FULL_WORKER_REVISION",
  "input_fingerprint": "RECEIPT_INPUT_FINGERPRINT",
  "verdict": "accepted",
  "findings": []
}
```

Each nonempty finding records its ID, whether it is required, and its resolution status. Only resolved required findings can accompany acceptance. Identity equality blocks self-review; the coordinator and host must also ensure actual reviewer independence. These files are local attestations, not cryptographic proof of a person's identity.

`integrate --repo INTEGRATION_WORKTREE --spec integration.json` consumes:

```json
{
  "owner": "integrator-worker",
  "integration_claim_id": "lane-INTEGRATOR",
  "expected_head": "FULL_INTEGRATION_HEAD",
  "group_id": "G01",
  "workers": [
    {
      "claim_id": "lane-WORKER",
      "commit": "FULL_WORKER_REVISION",
      "receipt": "PATH_TO_WORKER_RECEIPT",
      "review": "PATH_TO_INDEPENDENT_REVIEW",
      "depends_on": []
    }
  ],
  "commands": [
    {"id": "combined-lint", "kind": "check", "argv": ["npm", "run", "lint"]}
  ]
}
```

Checks must match the integrator brief's exact required contracts. The checkout must still be on its claimed integration branch. The helper verifies every worker before modifying the integration branch: active ownership, exact reviewed revision, unchanged input and artifact hashes, successful command capture, independent review, clean tracked files, ancestry from the recorded base, and changed paths within the claim. It orders worker commits by declared dependencies. Dependencies outside the selected workers must have a successful integration record already contained in the integration checkout.

Accepted commits are merged with ordinary Git merge semantics. The workflow does not use the line-union merge driver. Merge conflicts remain in the integration worktree with both branches and the exact next action retained. Resolve conflicts against behavior and source contracts, commit the resolution, obtain fresh review as appropriate, and rerun combined checks. A successful merge/check receipt still requires independent review of the integrated result and the feature owner's acceptance evidence.

Two failed integration/correction attempts stop that group with branches and records retained. An operator must inspect the failures and define a revised work-group decision before using a new group identifier; renaming a group to hide a failure is not a repair. The helper does not auto-reset a branch, discard changes, delete a worker, or publish a PR.

## Verify acceptance evidence

Requirements JSON lists nonempty unique case IDs with exact proof boundaries:

```json
{
  "cases": [
    {"id": "ATDD-001", "boundary": "database", "independent_state": true}
  ],
  "feature_completion": true,
  "integration_owner": "T009"
}
```

Evidence JSON supplies `requirements_sha256` and `input_fingerprint`, different `implementer` and `reviewer` identities, matching `integration_owner` for feature completion, and a `cases` array. Each case has `id`, matching `boundary`, `result: "passed"`, nonempty observable `assertions`, and nonempty `artifacts` with repository-relative `path` and `sha256`. The requirements hash is SHA-256 of UTF-8 JSON serialized with sorted keys, no whitespace between items, and non-ASCII characters preserved. It binds the exact supplied requirements even when that JSON lives in an excluded evidence/state directory or outside the repository. The evidence command reports the expected digest with its result. If independent state is required, `state_observation` contains a concrete `method` and its retained `artifact` path/hash. Real database or transport proof cannot be relabeled unit/mocked output.

Browser or client-UI cases additionally contain a `recording` with media `path`, `sha256`, `[start, end]` timestamps, `redaction_checked: true`, and `inspected_frames`. Each frame records its path/hash, timestamp, source `recording_sha256`, inspector identity, `readable: true`, and observations of visible actions/results. `ffprobe` verifies that the recording contains video with positive duration and that case intervals fit. Frame files must decode as actual images. `ffmpeg` compares their decoded RGB pixels with the recording at each declared extraction timestamp; a renamed text file or unrelated screenshot cannot establish a sampled video frame. Missing tools/media/frames, mismatched hashes, bad timestamps, unreadable-frame findings, absent mappings, or stale inputs block verification.

A complete database evidence object follows this shape:

```json
{
  "requirements_sha256": "HASH_OF_REQUIREMENTS_JSON",
  "input_fingerprint": "CURRENT_IMPLEMENTATION_INPUT_HASH",
  "implementer": "backend-worker-1",
  "reviewer": "review-verify-worker-2",
  "integration_owner": "T009",
  "cases": [
    {
      "id": "ATDD-001",
      "boundary": "database",
      "result": "passed",
      "assertions": ["A separate database connection observed the expected committed row"],
      "artifacts": [{"path": ".ai/evidence/request-response.json", "sha256": "ARTIFACT_HASH"}],
      "state_observation": {
        "method": "Fresh PostgreSQL connection after the request completed",
        "artifact": {"path": ".ai/evidence/state-query.json", "sha256": "STATE_ARTIFACT_HASH"}
      }
    }
  ]
}
```

A UI case uses `boundary: "browser"` or `"client-ui"` and adds:

```json
{
  "recording": {
    "path": ".ai/evidence/journey.mp4",
    "sha256": "VIDEO_HASH",
    "timestamps": [2.0, 8.0],
    "redaction_checked": true,
    "inspected_frames": [
      {
        "path": ".ai/evidence/at-5.png",
        "sha256": "FRAME_HASH",
        "recording_sha256": "VIDEO_HASH",
        "timestamp": 5.0,
        "inspector": "review-verify-worker-2",
        "readable": true,
        "observations": "Submission result and case caption are visible at the tested viewport"
      }
    ]
  }
}
```

```sh
.ai/bin/agent-workflow evidence --repo . --requirements .ai/state/acceptance.json --evidence .ai/evidence/acceptance.json
```

Hash and metadata checks establish provenance and completeness of declared review. They cannot establish human readability, redaction, truthful assertions, or the actual service boundary by themselves. The independent reviewer must inspect real captures, sampled frames, traces, request/response output, and separate state observations. No automated verdict substitutes for that inspection.

## Resume and cleanup

```sh
.ai/bin/agent-workflow resume --repo .
.ai/bin/agent-workflow release --repo . --claim lane-ID --owner backend-worker-1 --reason "Accepted contribution integrated; evidence retained"
.ai/bin/agent-workflow worktree --repo . --claim lane-ID --owner backend-worker-1 --cleanup
```

Resume reports current worktree revisions/fingerprints, merge conflicts, old claim timestamps, prior integration records, correction counts, and a next action. Reconcile task files, source revisions, claims, and current evidence before resuming execution. Prior success records are not trusted as proof of current inputs.

Release retains the worktree and branch. Cleanup requires a released claim owned by the caller and a recorded successful integration containing the worker head. It refuses any local tracked/untracked content or retained evidence directory. Archive evidence into the integration checkout's evidence area and inspect all other files first. Cleanup uses Git's ordinary worktree removal without force and retains the branch. It never deletes unrelated branches or worktrees.
