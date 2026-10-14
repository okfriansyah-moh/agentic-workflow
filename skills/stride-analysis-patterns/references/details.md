# Threat record guidance

| Field | Required meaning |
| --- | --- |
| ID / category | Stable threat identity and relevant STRIDE categories |
| Source and asset | Requirement/context anchor and protected asset |
| Actor and preconditions | Capabilities, access and conditions needed |
| Entry and trust boundary | Where hostile data/action enters and authority changes |
| Trigger and impact | Concrete abuse sequence and resulting harm |
| Control and owner | Prevention/detection/recovery and enforcing component |
| Verification | Negative scenario with observable expected behavior |
| Evidence / residual risk | Proposed versus inspected/tested controls, remaining limitations |

Check spoofed callers, tampered input/state, missing attribution, unauthorized disclosure, resource exhaustion and privilege expansion. Evaluate interactions as well as components. Actual threat coverage comes from system-specific analysis, not generating one row per category. Risk scoring, when used, requires defined scales and justified values. Record uncertain facts instead of treating generic templates as evidence.
