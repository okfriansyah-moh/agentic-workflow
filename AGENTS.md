# Agent workflow source

Read README.md, the installation manifest and the affected helper before editing. Keep agent roles separate from skill guidance. Preserve the selected architecture: native host subagents, a small Python standard-library CLI, a pinned project bundle, and explicit verification receipts.

Use scoped ownership for delegated changes and an independent reviewer. Do not start application work from examples or source attachments. Test helper behavior in temporary repositories and homes before installing into a real home or repository. Use argv arrays for commands; never evaluate plan prose as executable code. Preserve unrelated user settings, skills, hooks and Git work.

Run `python3 -m unittest discover -s tests -v` for runtime changes. Use the optional external fixture runner for changed tool profiles. Missing scanners, unavailable services, native host loading and host trust must have separate results; none count as a pass.

Keep manifest skill digests current after skill edits. Keep runtime documents and native adapters aligned with actual CLI behavior. Check authored artifacts with `resources/wording/check_output_wording.py`; policy/checker definitions and immutable upstream evidence are explicit policy exceptions. Personal voice is conditional; the shared output policy always applies.
