# Requested observation review

Run when the user asks to review observations or update named skills. No schedule is configured. Scope the review to the requested skills or backlog slice.

1. Read relevant observation bodies and the current installed skills. Group duplicates and separate project-specific constraints from reusable guidance. Verify whether the issue is already resolved.
2. Check pending staged versions for the same skill. Reuse an applicable proposal rather than silently replacing it. Use the helper’s `stage` command to retain an exact baseline and a proposed copy under a unique run directory.
3. Edit proposed files, following skill-creator. Record observation IDs, source provenance, and the intended change in the manifest. Preserve licenses and personal customizations.
4. Validate the proposed bundle and test observable behavior. Present a concise explanation and concrete diff. If the user already authorized the specific update, continue; otherwise ask for approval before installation.
5. Immediately before authorized installation, compare the live bundle with the recorded baseline. If it changed, reconcile against the new live files and revalidate. Never overwrite concurrent edits. Back up affected files and install only the reviewed change through normal filesystem permissions.
6. Read back the result. Mark only resolved observations actioned, with a date and explanation. Keep unapplied portions open or split them into a linked remaining finding. Staged-only proposals remain open and name their stage path.
7. Record the actual completion date in `last-review-date.txt` only after the review completes; summarize applied, staged, declined, and remaining findings truthfully.

Keep review artifacts under the pinned workspace. Publication, upstream feedback, and scheduling require a separate user request. Installation records are local audit data, not an automatic update mechanism.
