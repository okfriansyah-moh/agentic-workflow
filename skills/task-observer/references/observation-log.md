# Observation records and helpers

Run the helper using its absolute installed path. Default workspace is the pinned global root; tests may pass an isolated absolute `--workspace`.

```bash
python3 scripts/observer.py list
```

During setup only, use `init`. To save an observation, create a JSON input file in a permitted temporary directory and use `add --input /absolute/path.json`. Required keys:

- `title`: concise finding.
- `skill`: list of affected installed skill names; may be empty for a new capability.
- `issue`: minimal evidence from actual work.
- `suggested_improvement`: specific proposed change.
- `principle`: reusable lesson, with its scope.

Optional keys: `proposes_skill` (list), `type` (`internal` by default or `open-source`), `session_context`, `siblings_checked`. Check neighboring skills only when the finding plausibly affects them; record the outcome without expanding the task into a library audit.

Each record has a YAML header with numeric `id`, title, status, affected skills, date, classification, and a fingerprint. The body holds Issue, Suggested improvement, and Principle. User-specific voice preferences are internal. Strip sensitive details; open-source means potentially reusable, not permission to publish.

New status is `open`. Reviews may set `parked` with an explicit condition, `declined`, `superseded`, or `actioned` with a resolution date and explanation. Mark `actioned` only after the authorized change is installed or the finding is verified already resolved; staging alone leaves it open. Read the entire body before resolving. Preserve archival records and IDs. Do not manually allocate IDs.

The helper serializes writers using a lock and atomically writes complete records. It suppresses exact repeated findings using affected skills, proposed capabilities, title, issue, proposed improvement, and principle (normalizing case and whitespace); check semantically similar findings yourself. A materially new finding that resembles an archived one should explain the new evidence. The helper fails on malformed existing records instead of silently ignoring them.

Use `stage --skill-dir /absolute/installed/skill` to create a unique update folder containing `baseline/`, `proposed/`, and `manifest.json`. Edit only proposed files. This command never installs an update. Record the observation IDs and intended changes in that manifest during review.
