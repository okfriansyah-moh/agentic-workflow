<!-- PM-Skills | https://github.com/product-on-purpose/pm-skills | Apache 2.0 -->
<!-- Locally organized 2026-10-10; applies only to model-generated product behavior. -->

# AI behavior in a PRD

Include this section only when the product feature generates output with a model; embed it in the single PRD.

Name required behaviors, evaluations, and justified passing thresholds. Refusal and abstention need their own cases. Score components and high-risk slices separately so an aggregate pass does not hide a failing component.

| ID | Required behavior | Evaluation | Threshold and rationale |
|---|---|---|---|
| AB-01 | [Normal behavior] | [Cases/rubric] | [Grounded threshold] |
| AB-02 | [Refusal] | [Cases/rubric] | [Grounded threshold] |
| AB-03 | [Abstention] | [Cases/rubric] | [Grounded threshold] |

Describe case location, slices derived from requirements/failure cost, justified coverage floors, held-out cases, and separately reported results. Derive counts from the feature's risks rather than copying a fixed number or stopping when a verdict appears stable.

Curated cases and coverage floors do not establish population failure rates. Report counts and coverage honestly; rate claims need defensible sampling and assumptions. Targets remain acceptance conditions until execution evidence exists.

