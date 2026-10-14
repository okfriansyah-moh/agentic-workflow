---
name: antislop-layoutmobile
description: "Verify responsive reflow, content sizing, touch interactions and mobile navigation across meaningful viewport widths."
metadata:
  version: "1.0.0"
---

# antislop-layoutmobile

Read antislop and the adopted responsive layout contracts. Derive breakpoints from where the content stops working; phone/tablet/desktop samples help inspection but do not prove every width between them.

Inspect continuous resizing and representative narrow/intermediate/wide states. Reflow columns, order and navigation deliberately. Keep type, spacing and content measure appropriate to available space while preserving target sizes. Avoid a desktop page merely compressed into a narrow viewport.

Check flexible grid/flex children, long text, images, tables and code. Investigate horizontal overflow rather than hiding it. Use a labeled local scroll region for content that genuinely needs two dimensions. Cropping belongs to intentional imagery, not hidden controls or text.

Verify touch interactions and visible feedback without requiring hover. Keep primary navigation discoverable with meaningful labels. Reserve content space for fixed bars and safe-area insets, and ensure the last item/action can be reached.

Test zoom and the mobile keyboard, landscape where relevant, reduced motion and every shipped theme. Dynamic viewport units may suit a deliberate full-height view; ordinary content should size naturally. A fixed device list cannot substitute for the adopted content behavior.

Return screenshots/state references and observed defects through the shared review. Distinguish browser emulation from real-device testing and leave unsupported device behavior explicitly unverified.

Apply the [shared wording policy](../../resources/wording/output-wording.md) to authored output. Read supporting skills only for the current task.
