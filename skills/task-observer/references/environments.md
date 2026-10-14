# Codex activation and storage

Global activation lives in `the host user-level instruction file`. Read the installed skill at the start of substantive work, inspect relevant pending observations, and capture useful lessons when execution and filesystem permissions permit. A global instruction is guidance, not a guaranteed runtime hook.

Pinned root: `${AGENT_WORKFLOW_OBSERVATIONS:-$HOME/.codex/skill-workspace}`.

- `skill-observations/observation-log/`: one complete record per observation.
- `skill-observations/observation-log/archive/`: resolved records retained for provenance.
- `skill-observations/last-review-date.txt`: `never` until a review actually finishes.
- `skill-updates/<skill>/<unique-run>/`: baseline, proposed bundle, and manifest.

Keep this state outside skill discovery and project folders. Do not scan other users, chats, or unrelated projects to populate it. Do not install hooks, create scheduled work, or change sandbox configuration as part of activation.

Initialize explicitly during setup with the helper’s `init` command. On later sessions, `list` is read-only and fails visibly if storage is missing or malformed. An unavailable log is not an empty log. In Plan mode do not initialize, capture, archive, or stage. If writes are denied, explain once, preserve useful proposals in the current response, and continue the main task. Use the host’s normal approval mechanism for authorized writes; never evade a denial or repeatedly retry it.

Newly installed files may be discoverable on the next turn. Automatic AGENTS.md activation must be checked in a fresh session. Until then, report installation and static validation as complete but fresh-session activation as unverified. No checkpoint or observation should be fabricated as proof.
