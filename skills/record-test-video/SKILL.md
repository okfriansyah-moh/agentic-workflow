---
name: record-test-video
description: "Record real UI acceptance journeys with readable actions, case timestamps and linked assertions."
metadata:
  version: "1.0.0"
---

# record-test-video

Read the assigned acceptance cases and adopted design states. Plan coherent journeys so shared setup appears once, while each case has identifiable start/end timestamps and an asserted outcome. Use actual Playwright/browser execution against the required environment; a mock/demo recording has only that boundary.

Record the implementation fingerprint, browser/runtime version, viewport/theme, test data and environment without secrets. Reserve the lane's ports, database and output directory. Use stable seeded data and an isolated test identity where permitted.

Make actions and outcomes readable: show the relevant control, visible result and brief truthful captions or case IDs. Use pauses only to communicate actual state transitions; never edit a failed step into an apparent success. Assertions and raw traces remain separate evidence even when captions are present.

Capture video, relevant screenshots, traces and runner results. For backend-only cases record real requests/responses and independent state checks through acceptance-verification; rendered logs must be labeled as summaries and never presented as browser execution.

Inspect representative frames at case start, action, outcome and end. Check that important text is legible, pointers/captions do not obscure results, and secrets/personal data are absent. Keep the original recording and document any crop, redaction or transcode; preserve source/output hashes and duration mapping.

Pass the evidence manifest to verify-test-evidence with case timestamps and actual assertions. Missing recorder/ffmpeg/browser capability is a blocked recording requirement, not a successful text substitute. Return local artifacts, hashes, case mapping, inspected frames and limitations. No uploads or external messages are implicit.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

For actual helper commands, claim/check contracts and evidence proof fields, read [coordination and evidence contracts](../../docs/COORDINATION.md) before writing a brief or receipt. Use the documented structured objects and preserve captured argv/test-report requirements; do not infer a schema from narrative examples.
