# Note acceptance specification — revision 1

Historical synthetic evidence used to evaluate authoring updates, not a real product run.

### Case ATDD-007: Malformed input identifies the first invalid line

**Sources:** CLI-1

**Priority:** P1

**Level:** Integration

**Platform:** Command and file

**Category:** Negative

**Automation:** Candidate

**Status:** Passed

**Preconditions:** An isolated directory contains notes.txt; the installed revision is the one in the evidence.

**Test data:** Line 1 is alpha=1; line 2 is invalid text.

**Scenario:**

```gherkin
Given notes.txt has an invalid record at line 2
When note check notes.txt runs
Then the command exits 1
And stderr identifies line 2
And the file bytes remain unchanged
```

**Verification:** Observe the real process status and stderr, then compare the file bytes.

**Cleanup:** Remove the isolated directory.

**Evidence:** [Supplied synthetic fixture log](previous-run.txt)

**Revision:** build-v1, expectation-v1

**Environment:** disposable offline fixture workstation

**Executed at:** 2026-10-01T09:00:00Z

### Case ATDD-011: Upload a note

**Sources:** CLI-4

**Priority:** P1

**Level:** Integration

**Platform:** Command and file

**Category:** Positive

**Automation:** Candidate

**Status:** Not Run

**Preconditions:** An isolated directory contains notes.txt; the installed revision is the one in the evidence.

**Test data:** alpha=1 followed by a newline.

**Scenario:**

```gherkin
Given notes.txt is valid
When note upload notes.txt runs
Then the network service receives the note
```

**Verification:** Observe the service request; no execution evidence was supplied.

**Cleanup:** Remove the isolated directory.

## Registers

| Source | Location | SHA-256 |
| --- | --- | --- |
| SRC-CLI | cli.md | 1dfa27baa8825a7450499e147d5b09da28fdf14d88134346de86c83122be6f40 |

| Obligation | Source | Locator | Disposition | Cases | Reason |
| --- | --- | --- | --- | --- | --- |
| CLI-1 | SRC-CLI | CLI-1 | Covered | ATDD-007 | Historical revision incorrectly omitted the valid-file branch; reconcile from current source. |
| CLI-4 | SRC-CLI | CLI-4 | Covered | ATDD-011 | Legacy upload behavior. |
