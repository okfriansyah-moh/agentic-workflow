# Verification and review

## Authoring checks

Before decomposing, independently inventory source obligations outside the final package. Re-read source coverage in a fresh pass after authoring; compare actual assertions, not only ID counts. Include each meaningful clause, case row, UI state and required delivery/engineering outcome. Required/committed, recommended, deferred and open remain distinct.

Temporary inventory JSON is an object with `obligations`, a list of objects containing `id`, `source`, `disposition`, and `reason` (empty for Covered). Optional extra fields can retain source locators and extraction notes. IDs are stable; every inventory ID must have exactly one root coverage row with the same source and disposition; deferred/excluded reasons agree. This records the independent pass, not an export from the plan being checked. It is neither an additional project deliverable nor proof of semantic completeness by itself.

Run from any working directory:

```bash
python3 <skill-directory>/scripts/check_plan.py /absolute/path/docs/06-PLAN.md --inventory /temporary/path/inventory.json
python3 <skill-directory>/scripts/check_plan.py /absolute/path/docs/06-PLAN.md --format json --strict
```

Requires Python 3 and PyYAML; if unavailable, report that exact limitation and use the documented checks manually. Do not install packages without authorization. The helper is read-only, never executes validation commands, and never fetches remote sources. Exit 0 means no structural errors (draft gaps may remain); exit 1 means structural errors, or gaps under `--strict`; exit 2 means unusable input/runtime or an unsupported legacy layout. `--strict` cannot upgrade a draft to Ready.

The checker validates the declared metadata, tables, simple explicit/reference Markdown links and local anchors, IDs/membership, dependencies, source hashes, declared file targets, reciprocal coverage ownership and completion evidence fields. It does not determine whether every original obligation was extracted, an assertion is sufficient, a test ran honestly, screenshots look correct, a reviewer was independent, or a runtime is safe. Source completeness, concurrency, expected values and evidence freshness need substantive review. Use explicit Markdown links with URL-encoded parentheses or angle-bracket targets; HTML `id` anchors and standard Markdown headings are supported. Dynamic JavaScript state activation requires runtime inspection later.

## Executable-test policy written into tasks

Choose a strategy explicitly for each task:

- `test-first`: only when explicitly selected in the approved strategy, for reproducible rules, state transitions and regressions. Future executor writes a meaningful failing test, confirms the intended failure (not an unrelated setup/import failure), implements, then reruns. Add characterization checks first when preserving existing behavior matters.
- `alongside`: exploration, scaffolding or visual composition where executable checks evolve with the implementation. Record why; acceptance still governs before completion. Separate exploratory prototypes from production proof.
- `checks-only`: tasks without executable behavior, such as documentation. Use substantive source, link, build/config, reader or observation checks as applicable; do not fabricate unit tests.

Explicit no-test limits prohibit added/executed tests and substitute browser trials. Retain required omitted proof as pending. Do not redefine skipped checks as checks-only success.

Tests are chosen by defects they can detect, not by requiring every level for every task. Unit rules, controlled components, real contracts/transports/databases, end-to-end user flows, accessibility, security, migration and operations have different proof boundaries. Expected values are derived independently from governing rules/fixtures rather than copied from implementation output. Name fixture reset, time/randomness/concurrency controls and prohibited effects where relevant. Never substitute mocked enforcement for a required real owner boundary.

For cross-component cases, name the observation point for each assertion: wire response, returned value, persisted state, or UI. Check that the planned path exposes the value being asserted, including failures. Resolve required type/boundary behavior before declaring affected instructions Ready; record routine implementation decisions and keep unresolved source outcomes visible as gaps.

Every source acceptance case or separately addressable row has an explicit verification owner. Other tasks may contribute implementations or narrow proofs. Preserve the source case ID and record partial contribution; a passing component case cannot mark a real integration case Passed. A feature's integration owner proves the combined outcome. Release verification assigns cross-feature responsibilities without creating redundant tests.

## One combined selection review referenced by tasks

The implementer checks the diff while working. After the whole requested selection is composed, one fresh independent reviewer evaluates source compliance and code quality. Tasks reference that shared review artifact and findings ledger; no per-task or group review ceremony is added. The reviewer gets the task, inherited group/root constraints, precise source sections, baseline and resulting change, test results and actual evidence, without treating the implementer's verdict as proof. Check missing or extra behavior, contract enforcement, maintainability, regression coverage and relevant failure paths. Risk adds depth: permission/secret boundaries, concurrency/idempotency, migration/recovery, operational limits, accessible interactions or visual states as applicable. Low-risk work remains covered by that same selection review.

Reference the shared findings, required versus advisory status, correction, recheck, reviewer identity and reviewed revision from each covered task. A reviewer may inspect and run authorized checks; implementation and external effects retain their existing authorization boundaries. Different labels in a table do not establish real independence. When no fresh reviewer is available, leave the task In review with a concrete handoff; self-review is not a replacement.

Repeat implementation/check/review while supported corrections remain. Rerun affected checks after changes, including relevant regressions; broaden tests only for a new concern. Do not weaken expected outcomes, remove case rows or refresh visual baselines just to obtain a pass. Material source decisions go through their owner. On an unresolved prerequisite or repeated lack of progress, retain exact findings, diagnostics, attempted fixes and the next action; change diagnosis rather than repeating an identical failing action. A budget ending preserves In progress/In review; genuine external dependencies may use Blocked. Neither is Done.

## Visual verification

For every UI-affecting task identify production route/panel, adopted component/design reference and stable state IDs, actor, fixture, theme, viewport/device/browser, trigger and expected visible outcome. Cover applicable loading/empty/invalid/denied/stale/failed/uncertain/recovered states, not only the successful screen. Selected contexts come from source requirements; SpoolIn's widths/themes never become universal defaults.

Compare one representative changed state before spreading shared styling. During future execution retain the approved reference and selected observations under matching conditions, with code revision, environment and state trigger. Compare layout, hierarchy, typography, color, content/identity, spacing, overflow and interaction feedback. Record differences and their verdict; use stable image diffs only where justified. Mask nondeterministic regions narrowly and explain why the mask cannot conceal required behavior. Inspect keyboard/focus, announcements, zoom and relevant input separately from pixels.

Mockup images are references, not automatically approved pixel baselines. Fixture JavaScript is not production behavior. Controlled component screenshots prove that boundary only; a real browser/service flow must establish integrated outcomes. Unavailable rendering remains unverified and cannot be labeled passed by a static HTML or link check.

## Reader handoff

Ask a fresh reader to pick one task from only the package and its explicit sources. They must find what to change, what to preserve, prerequisites, commands, expected results, proof limits, review criteria and stopping conditions without the authoring chat. If delegated evaluation is authorized and available, use a fresh agent with the minimum raw inputs and no intended answer. Otherwise perform a separate reader pass and disclose the lack of independent testing. Fix missing context in the task/group/source pointers, not in a private chat-only note.
