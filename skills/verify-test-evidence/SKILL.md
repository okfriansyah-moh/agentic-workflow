---
name: verify-test-evidence
description: "Independently validate acceptance evidence mapping, provenance, freshness and recording readability."
metadata:
  version: "1.1.0"
---

# verify-test-evidence

Read the case contract, implementation fingerprint, receipt and evidence manifest before inspecting the artifacts. Use an independent reviewer identity; the implementer's statement is not an independent review.

Verify every assigned case maps to an actual check and its required boundary. Confirm runner exit code/count, test selection, assertion result, environment and source inputs. A passing unit test does not prove real database, transport or browser behavior. Missing/empty artifacts and empty applicable selections fail.

Recompute artifact hashes and compare input fingerprints. Implementation, test, configuration or source requirement changes make affected evidence stale. Evidence-only bookkeeping may preserve proof when the tested inputs are unchanged. A timestamp alone cannot establish freshness.

Compare actual browser screenshots with the adopted design for the assigned viewport/theme and required states. Record observable differences in the single review ledger. A video file, generated test code or an accessibility score alone cannot establish design fidelity. Read [Playwright CLI guidance](../playwright-cli/SKILL.md) when interpreting captured artifacts; its action recording and video capture commands produce different evidence.

For recordings validate media readability/duration and inspect actual frames for case starts, actions and results. Compare timestamps to the video and assertions. Verify captions are legible and accurate; identify obscured controls, missing states, unexplained cuts and sensitive material. A decodable video is not proof of readable or correct behavior.

For backend cases inspect real request/response records and independently observed state when required. Label screenshots rendered from logs accurately. Do not accept a fabricated fixture or placeholder file as a real-system result.

Return one ledger with case ID, result, boundary, reviewed fingerprint, evidence paths/hashes, frame inspection and findings. Task acceptance requires all assigned mandatory proof plus independent review; feature acceptance also requires the integration owner's combined result. Request a specific rerun/capture for missing proof rather than changing requirements. Forge records the outcome in task execution fields.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

For actual helper commands, claim/check contracts and evidence proof fields, read [coordination and evidence contracts](../../docs/COORDINATION.md) before writing a brief or receipt. Use the documented structured objects and preserve captured argv/test-report requirements; do not infer a schema from narrative examples.

Inspect original decoded frames before accepting a recording. If viewport resizing or capture scaling makes the UI unreadable, retain that original as a failed capture and recapture each viewport in a fresh Playwright context with its matching `recordVideo` size, using the same pinned driver. Keep timestamps, hashes, traces and actual assertions for the replacement; a CLI command succeeding does not establish readable evidence.
