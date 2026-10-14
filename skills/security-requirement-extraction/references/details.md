# Security control and acceptance mapping

For each control record stable ID, source requirement and threat IDs, intended outcome, enforcing component/boundary, mechanism/contract anchor, failure response, owner if known, verification obligation, evidence status and residual risk. Add framework edition/control ID only after verifying applicability and the primary text.

Verification obligations describe setup/preconditions, hostile or invalid action, observable rejection/recovery, forbidden side effects and the intended test boundary. Include ordinary authorized behavior so a defense does not accidentally prohibit legitimate input or access. Distinguish design completeness, code review, automated checks and live operational evidence.

Do not treat two requirements mapping to a control as proof of adequacy, or an arbitrary count as a compliance threshold. Preserve existing requirement IDs and append new technical IDs without changing the PRD. Embed the mapping in the selected technical document; generated user stories, ATDD files and ticket exports are outside a documentation-only task.
