---
name: antislop-human
description: "Verify that changed UI works for users with different input, vision and motion needs."
metadata:
  version: "1.0.0"
---

# antislop-human

Use the adopted design and the task's accessibility contract. Use semantic controls, meaningful labels and keyboard reachability as the starting point. Automated accessibility checks support manual interaction checks; they do not establish complete compliance.

Verify text contrast against the actual background, including image/gradient surfaces and every shipped theme. Use 4.5:1 for ordinary text and 3:1 where the standard's large-text definition applies; controls/focus indicators need applicable nontext contrast. The included contrast-check.py supports color-pair arithmetic, not a whole-page audit.

Operate the journey by keyboard: sensible focus order, visible focus, proper dialog focus containment/return and an available escape/close action. Confirm touch operation without hover-only information and ensure names/roles/states are conveyed by appropriate semantics.

Check loading, empty, error, disabled, selected and success states that the task requires. Communicate status with text/semantics in addition to color. Associate validation messages with fields and preserve entered data where the behavior calls for it.

Inspect 200% zoom, long labels, responsive reflow and reduced motion. Make focused inputs reachable when the mobile keyboard is present; fixed navigation must not cover content. Prefer adequate target size/spacing within the adopted design and applicable accessibility requirements.

Capture the exact browser/device, checks and remaining limitations. Feed actionable usability/accessibility defects into the shared findings ledger. Report an untested assistive-technology boundary honestly instead of certifying it from source markup.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.

## Contrast reference

Run `python3 contrast-check.py COLOR1 COLOR2` from this skill directory. The table is a retained upstream arithmetic reference; use the applicable WCAG definition of large text (18pt, or 14pt bold), not a generic 18px label. Evaluate actual UI backgrounds separately.

| Pairing (text on background) | Ratio | Normal text (4.5) | Large text (3.0) |
|------------------------------|-------|-------------------|------------------|
| Black on white | 21.00 | Pass | Pass |
| White on black | 21.00 | Pass | Pass |
| White on #333333 | 12.63 | Pass | Pass |
| White on #666666 | 5.74 | Pass | Pass |
| #777777 on white | 4.48 | Fail | Pass |
| White on #888888 | 3.54 | Fail | Pass |
| White on #999999 | 2.85 | Fail | Fail |
| #555555 on black | 2.82 | Fail | Fail |
