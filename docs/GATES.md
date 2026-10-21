# Quality gates and proof boundaries

Follow the single four-host [delivery policy](DELIVERY.md). Thresholds remain blocking. New installation hooks use `hook_mode: feedback` and do not execute full gates after every edit; explicit final verification and CI remain required. Set `hook_mode: fast` explicitly to retain per-edit fast checks.

For a recorded base, use `gate --repo . --stage delivery --base BASE_SHA --reuse`. Affected selection includes committed, staged, unstaged, added, deleted and relevant untracked inputs. Map ordinary changes to actual components and downstream consumers; documentation-only changes select document checks, while real shared contracts, locks, build inputs and gate policy retain necessary broader checks. Missing baselines, invalid graphs and unknown executable ownership require explained conservative scope. `--affected` remains a compatibility filter, not a workflow selector. Reuse is opt-in per check and validates source/tests, command/configuration, environment/toolchain and retained artifacts; runtime/network/scanner checks stay uncached unless safely supported. See registry fields `component_inputs`, `component_dependencies`, `shared_input_patterns` and per-check `reuse`.

Explicit no-test instructions prohibit added/executed tests, hidden browser trials and hook-triggered tests. Keep required checks pending, obtain independent source review and report limits. Source review does not prove runtime acceptance. Authorized draft publication can disclose missing proof without changing its status. Hooks remain feedback; they must respect selection constraints.


The gate registry is the single command source for explicit verification, agent hook dispatch, optional Git hooks and CI. All four hosts use the same registry and thresholds; the project chooses its bundle through `.ai/config.json`. The `movie-app` profile has explicit required build contracts for the project components. Checks become applicable when their declared sources exist; installation alone does not execute application verification. An absent wrapper, script, scanner or report blocks an applicable check once source exists.

`--stage` values are technical check-set filters inside the same workflow. `gate --repo . --stage fast` runs lint, type, compilation, dependency and secret checks selected for existing sources. Integration adds behavior tests, architecture/database checks, coverage and SAST/dependency scanning. Delivery additionally selects browser acceptance. Each stage includes earlier stages. `--component NAME` limits component checks while retaining shared checks. CI must call the same command and honor its exit status. Hooks are feedback; they are not the completion authority.

The profile requires actual project commands. Inspect current build definitions before changing them; harness installation does not start foundation work. Gradle needs component `ktlintCheck`, `detekt`, `compileKotlin`, `test`, `architectureTest`, `integrationTest` and `koverXmlReport` tasks. npm workspaces need `lint`, `check`, `check:dependencies`, `test:coverage` and `build`; the root supplies `test:e2e`. Missing scripts must fail. Review the actual linter imports, report paths and test selection before accepting the first foundation task. Do not add no-op tasks with these names.

## Measurement

| Rule | Measurement |
| --- | --- |
| Function size | At most 50 nonblank, non-comment source lines. ESLint counts function declarations/body with skipBlankLines and skipComments. detekt 1.23.8 counts body tokens excluding whitespace and comments; LongMethod reports at its threshold, so threshold 51 permits 50. Nested Kotlin functions are measured separately. |
| Cyclomatic complexity | At most 10 according to each pinned language tool's control-flow rules. Tool counts can differ between languages; no cross-language score is presented. |
| Nesting | At most 3 according to ESLint max-depth and detekt NestedBlockDepth. |
| Changed coverage | At least 80% of instrumented changed executable lines in each component, intersecting Git changes from the explicit base with LCOV or Kover/JaCoCo XML. Added untracked source is included. |

Generated code/data is excluded from human-maintained source rules. Generated source directories are explicit in configs; broad exclusions need review. File-level changed source missing from coverage inventory fails. A report containing a changed file but no changed executable line records not applicable. A comment-only source file absent from instrumentation requires documented scope classification; the helper conservatively blocks it rather than guessing whether it is executable. Partial instrumentation within a listed file still needs reviewer inspection of coverage configuration.

Coverage reports must be refreshed during the run. Test checks require newly produced JUnit or Vitest reports and a nonempty executed test selection. Failures, errors and unavailable reports do not pass. A command exit code alone cannot establish acceptance behavior. Runtime gate results record commands, exit codes, log digests, selected-test summaries, source fingerprint and Git revision. Local reports live under `.ai/reports/` and must be reviewed for secrets before sharing.

## Security and architecture

The packaged Semgrep rule file is a small, pinned local baseline for dynamic evaluation/process invocation and Kotlin field injection. It is not an exhaustive vulnerability ruleset. The source hash is retained with verification records. Semgrep CE scope does not establish cross-file security proof. Include specialist security scrutiny in the one combined review when applicable threats and required controls need it. [Semgrep's documented language/analysis scope](https://docs.semgrep.dev/semgrep-ce-languages).

Gitleaks checks the current directory with redacted findings. OSV-Scanner inspects supported dependency inventories; Gradle lock files may not cover all transitive/resolved artifacts, so verify the actual supported inventory and supply an SBOM where necessary. Network or database failures block the dependency result. Installed guidance is distinct from an available scanner. [OSV supported artifacts](https://google.github.io/osv-scanner/supported-languages-and-lockfiles/).

ArchUnit and dependency-cruiser own cycles and boundaries. Annotations alone cannot prove Spring starts successfully: real wiring needs context startup tests, and JPA behavior needs PostgreSQL-backed tests. The fixture annotation has the shape of Autowired solely to test the architecture rule; it does not run Spring.

Sonar is optional until explicitly configured required. Its gate command must retrieve actual analysis and write a report containing the current revision and `status: OK`. The helper rejects missing, stale or failing reports. A guessed result or an older analysis is never evidence.

Required failures and unresolved required review findings block completion. Exceptions must identify rule, exact scope, rationale, owner and human approval. Version-control the exception alongside the applicable gate configuration; agents must not relax a rule to make a run green. The helper does not provide a blanket bypass switch.

## Git hooks and CI

Existing Git hooks are not replaced. To adopt a repository Git hook, call `python3 .ai/bin/agent-workflow gate --repo . --stage fast` from the existing pre-commit chain. Configure the chain through the repository's existing hook manager and test that it preserves current hooks. Git hooks can be bypassed, so integration and CI rerun required checks.

An explicit CI job should install locked application dependencies and the required scanners, then run `python3 .ai/bin/agent-workflow gate --repo . --stage delivery --base BASE_SHA`. Supply the reviewed base revision and retain `.ai/reports` only after redaction review. This package does not create a deployment or configure remote scan services during installation.
