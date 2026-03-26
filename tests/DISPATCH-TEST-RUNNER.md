# Dispatch Test Runner

Master instructions for validating skill dispatch routing and prompt behavior.
Run these tests after any changes to SKILL.md files, dispatch tables, or argument-hints.

## Overview

Each `sf-*` skill has a `tests/dispatch-tests.md` file containing test cases.
Tests run in two phases sharing the same input:

1. **Phase 1 (Static)**: Parse SKILL.md and validate dispatch routing, tool references, menu options
2. **Phase 2 (Prompt)**: Simulate skill invocation and validate model behavior

Phase 2 only runs for test cases that pass Phase 1.

---

## Test Case Format

Each test case in `dispatch-tests.md` uses this structure:

```markdown
## test name

- **Input**: `/sf-skill arguments here`
- **Dispatch**: Workflow Name | (none — present menu) | (ambiguous)
- **Init required**: yes/no
- **Init timing**: before-workflow | after-menu | n/a
- **Path**: fast | full | n/a
- **First tool**: `tool_name`
- **Tool params**: `key: value`
- **Should call**: `tool_a`, `tool_b`
- **Should NOT call**: `tool_c`, `tool_d`
- **Should ask user**: yes/no (reason)
- **Menu options**: Option1, Option2 (for no-args tests only)
- **Follow-up skills**: `sf-skill1`, `sf-skill2`

**Notes**: Free-text validation criteria and behavioral expectations.
```

### Field Definitions

| Field            | Required | Description                                                                                                                                                                                                      |
| ---------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Input            | yes      | The exact user prompt including `/skill-name`                                                                                                                                                                    |
| Dispatch         | yes      | Expected workflow name from dispatch table, or `(none — present menu)` / `(ambiguous)`                                                                                                                           |
| Init required    | yes      | Whether `cirra_ai_init()` must be called for this operation                                                                                                                                                      |
| Init timing      | yes      | `before-workflow` = init then execute; `before-menu` = init then present menu (when init is needed for capability detection); `after-menu` = present menu first, init after user selects; `n/a` = no init needed |
| Path             | yes      | `fast` = simple request, bypass full workflow; `full` = multi-step workflow; `n/a` = no workflow selected                                                                                                        |
| First tool       | no       | First MCP tool expected after init                                                                                                                                                                               |
| Tool params      | no       | Key parameters for the first tool call                                                                                                                                                                           |
| Should call      | no       | Additional tools expected during the workflow                                                                                                                                                                    |
| Should NOT call  | no       | Tools that must NOT be called for this input                                                                                                                                                                     |
| Should ask user  | yes      | Whether the model should prompt for clarification                                                                                                                                                                |
| Menu options     | no       | Expected menu items (only for no-args/ambiguous tests)                                                                                                                                                           |
| Post-action      | no       | Required follow-up action (e.g., FLS prompt after field creation)                                                                                                                                                |
| Batch limit      | no       | Record batch constraints (for DML operations)                                                                                                                                                                    |
| Follow-up skills | no       | Skills that should be offered as next steps                                                                                                                                                                      |
| Notes            | no       | Free-text behavioral expectations and edge case notes                                                                                                                                                            |

---

## Phase 1: Static SKILL.md Analysis

Parse each skill's SKILL.md and dispatch-tests.md. For each test case, validate:

### 1.1 Dispatch Table Coverage

- [ ] The SKILL.md has a `## Dispatch` section with a markdown table
- [ ] Every `Dispatch` value in the test file matches a workflow name in the dispatch table (exact string match)
- [ ] The `(none — present menu)` and `(ambiguous)` cases are handled by a catch-all row in the dispatch table

### 1.2 Argument-Hint Completeness

- [ ] The SKILL.md frontmatter has an `argument-hint` field
- [ ] Every first-word keyword used in test case inputs (e.g., `create`, `describe`, `validate`) appears in the argument-hint
- [ ] The argument-hint does not list options that have no corresponding dispatch table row

### 1.3 Tool References

For each test case where a specific workflow is matched:

- [ ] Every tool in `First tool` and `Should call` appears in the matched workflow section of SKILL.md (as a backtick-quoted tool name, not just prose mention)
- [ ] Every tool in `Should NOT call` does NOT appear in the matched workflow section
- [ ] `cirra_ai_init` is referenced in the SKILL.md when `Init required: yes`

### 1.4 Menu Options

For "no arguments" test cases:

- [ ] The SKILL.md has a menu/prompt block (typically a blockquote with numbered options)
- [ ] Every item in the test's `Menu options` field appears in the SKILL.md menu
- [ ] The SKILL.md menu does not contain options not listed in the test

### 1.5 Cross-References

- [ ] Every skill in `Follow-up skills` exists as a directory under `skills/`
- [ ] No stale `cirra-ai-sf-*` references remain in the SKILL.md

### Phase 1 Result

For each test case, report: **PASS**, **FAIL** (with specific mismatch), or **WARN** (non-blocking concern).

---

## Phase 2: Prompt Simulation

For each test case that passed Phase 1, simulate the skill invocation.

### 2.1 Setup

For each test case:

1. Read the full SKILL.md for the skill
2. Identify all skills referenced in the SKILL.md (cross-skill integration sections)
3. Read those referenced skills' SKILL.md files as well (for context)

### 2.2 Prompt Construction

Build the prompt that would be sent to a model:

**System message**: The full SKILL.md content, with `$ARGUMENTS` replaced by the arguments from the test input.

**User message**: The test's `Input` field (e.g., `/sf-metadata describe PermissionSet`).

### 2.3 Simulated Execution

Present the constructed prompt to a model instance with these instructions.

**CRITICAL**: The agent MUST follow these instructions exactly. Do not allow
the agent to skip questions, summarize, or say "I checked and it looks fine."
Every question must have an explicit answer with evidence from the SKILL.md.

```
You are tasked to test the **{skill_name}** skill.

Read the SKILL.md file at skills/{skill_name}/SKILL.md in full.
Read the dispatch-tests.md file at skills/{skill_name}/tests/dispatch-tests.md.

For EACH test case in dispatch-tests.md, you MUST answer ALL of the
following questions. Do not skip any question. Do not batch or summarize.

For each test case, report in this EXACT format:

### [test case name]
- **Dispatch decision**: [exact workflow name you selected]
- **Init**: [yes/no], [timing: before-workflow/before-menu/after-menu/n/a]
- **First tool**: [exact tool_name(param=value)] or [n/a]
- **Full tool sequence**: [tool1 → tool2 → tool3] (every tool, in order)
- **Ask user**: [yes/no] — [if yes, what exactly would you ask?]
- **Tools NOT called**: [list every tool from SKILL.md that is irrelevant]
- **RESULT**: PASS or FAIL

VERIFICATION RULES — you MUST check each of these:

1. Your Dispatch decision must EXACTLY match the test's Dispatch field.
   If it doesn't, report FAIL and explain the mismatch.

2. Every tool you list in "Full tool sequence" must appear by name in
   the SKILL.md (as `tool_name`, tool_name(), or in a code block).
   If you would call a tool not referenced in SKILL.md, report FAIL.

3. Every tool in the test's "Should NOT call" must be ABSENT from your
   tool sequence. If you would call a forbidden tool, report FAIL.

4. Your "Ask user" answer must match the test's "Should ask user" field.
   If the test says "no" but you would ask, or vice versa, report FAIL.

5. At the end, report the EXACT count: "X/Y PASS, Z FAIL".
   This count MUST equal the number of ## headings in dispatch-tests.md
   (excluding the file header). If your count doesn't match, you missed
   a test case — go back and find it.
```

### 2.4 Validation

Compare the model's response against the test case expectations:

| Check            | Expected (from test case)       | Actual (from model response)                             | Result    |
| ---------------- | ------------------------------- | -------------------------------------------------------- | --------- |
| Dispatch routing | `Dispatch` field                | Model's "Dispatch decision"                              | PASS/FAIL |
| Init behavior    | `Init required` + `Init timing` | Model's "Init" answer                                    | PASS/FAIL |
| First tool       | `First tool` + `Tool params`    | First tool in model's "Tool sequence"                    | PASS/FAIL |
| Required tools   | `Should call`                   | Present in model's "Tool sequence"                       | PASS/FAIL |
| Excluded tools   | `Should NOT call`               | Absent from model's "Tool sequence" + "Tools NOT called" | PASS/FAIL |
| User interaction | `Should ask user`               | Model's "User interaction"                               | PASS/FAIL |
| Menu content     | `Menu options`                  | Options presented in model's response                    | PASS/FAIL |
| Follow-up skills | `Follow-up skills`              | Skills mentioned in model's "Follow-up"                  | PASS/WARN |
| Post-action      | `Post-action`                   | Present in model's workflow                              | PASS/FAIL |
| Notes criteria   | `Notes` free-text               | Manual review against model behavior                     | PASS/WARN |

### Phase 2 Result

For each test case, report: **PASS**, **FAIL** (with specific mismatch), or **WARN** (behavioral concern but not a hard failure).

---

## Running the Tests

### Programmatic Phase 1 (required — run first)

```bash
python3 tests/validate_dispatch_tests.py              # all skills
python3 tests/validate_dispatch_tests.py sf-metadata   # one skill
```

This script mechanically validates every test case against its SKILL.md.
No LLM involved — pure string matching. It checks:

- Dispatch values match SKILL.md dispatch table rows
- Every tool in Should call / First tool exists in SKILL.md
- No tool appears in both Should call and Should NOT call
- Menu options match SKILL.md menu block
- Follow-up skill directories exist
- Required fields are present
- Init timing is consistent with Init required

**Phase 2 agents must NOT run until Phase 1 passes with 0 defects.**

### Quick Run (Phase 1 only)

Validate all skills statically:

```
For each skill in skills/sf-*/tests/dispatch-tests.md:
  1. Parse the dispatch-tests.md into structured test cases
  2. Parse the corresponding SKILL.md (frontmatter + dispatch table + workflows)
  3. Run Phase 1 checks (1.1 through 1.5) for each test case
  4. Report results
```

### Full Run (Phase 1 + Phase 2)

```
For each skill in skills/sf-*/tests/dispatch-tests.md:
  1. Run Phase 1 for all test cases
  2. For each test case that passed Phase 1:
     a. Construct the prompt (Phase 2.1 + 2.2)
     b. Send to model (Phase 2.3)
     c. Validate response (Phase 2.4)
  3. Report combined results
```

### Targeted Run (single skill)

```
Run Phase 1 + Phase 2 for skills/{skill-name}/tests/dispatch-tests.md only
```

---

## Report Format

The final report should include:

### Summary Table

```
Skill Dispatch Tests — {date}
==============================

| Skill | Tests | Phase 1 Pass | Phase 1 Fail | Phase 2 Pass | Phase 2 Fail | Phase 2 Warn |
|-------|-------|-------------|-------------|-------------|-------------|-------------|
| sf-apex | 10 | 10 | 0 | 10 | 0 | 0 |
| sf-data | 10 | 10 | 0 | 9 | 0 | 1 |
| ... | ... | ... | ... | ... | ... | ... |
| TOTAL | N | N | 0 | N | 0 | N |
```

### Failure Details

For each FAIL:

```
FAIL: sf-data / "natural language query" / Phase 2 / Dispatch routing
  Expected: Query Data
  Actual:   Build Optimized Query
  Reason:   Model interpreted "open opportunities over $1M" as needing optimization
  Impact:   Wrong workflow selected — different tool sequence and output format
```

### Warnings

For each WARN:

```
WARN: sf-data / "raw SOQL query" / Phase 2 / Follow-up skills
  Expected: sf-metadata, sf-permissions
  Actual:   sf-metadata only
  Reason:   Model didn't suggest sf-permissions as a follow-up
  Impact:   Low — follow-up suggestions are advisory
```

### Recommendations

Based on failures and warnings, recommend:

1. **SKILL.md fixes** — dispatch table ambiguities, missing tool references, unclear workflow boundaries
2. **Test case updates** — overly strict expectations, missing edge cases
3. **Argument-hint gaps** — keywords not covered by the hint

---

## Skill Coverage

| Skill          | Test file                                       | Tests                                                                                                                      |
| -------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| sf-apex        | `skills/sf-apex/tests/dispatch-tests.md`        | create trigger, create test-class, update class, validate name, validate file, validate All, no-args, fast path, ambiguous |
| sf-audit       | `skills/sf-audit/tests/dispatch-tests.md`       | (see file)                                                                                                                 |
| sf-data        | `skills/sf-data/tests/dispatch-tests.md`        | raw SOQL, NL query, build-query, insert, bulk delete, validate, describe, no-args, bare object                             |
| sf-diagram     | `skills/sf-diagram/tests/dispatch-tests.md`     | (see file)                                                                                                                 |
| sf-flow        | `skills/sf-flow/tests/dispatch-tests.md`        | (see file)                                                                                                                 |
| sf-kugamon     | `skills/sf-kugamon/tests/dispatch-tests.md`     | (see file)                                                                                                                 |
| sf-lwc         | `skills/sf-lwc/tests/dispatch-tests.md`         | (see file)                                                                                                                 |
| sf-metadata    | `skills/sf-metadata/tests/dispatch-tests.md`    | describe, create field, update, delete, no-args, ambiguous, describe-all                                                   |
| sf-orders      | `skills/sf-orders/tests/dispatch-tests.md`      | (see file)                                                                                                                 |
| sf-permissions | `skills/sf-permissions/tests/dispatch-tests.md` | hierarchy, who-has, user trace, debug, audit, create/clone/update/delete PS, agent-access, no-args, NL field access        |

---

## Report Documentation Standards

### No unexplained notes

Every entry in the report must be self-contained. Do not add cryptic column values like "edge case with conflicting keywords tested" or "lwc test has nuanced soql_query scope note" without explaining what they mean. If a test case has a nuance worth noting, explain it fully inline:

**Bad**:

```
| sf-audit | 8 | 8 | 0 | lwc test has nuanced soql_query scope note |
```

**Good**:

```
| sf-audit | 8 | 8 | 0 |
```

With a separate section:

```
### sf-audit: soql_query scope in LWC test

The "lwc audit" test specifies `Should NOT call: soql_query` but this
applies only to the C5 (LWC deep-dive) phase. Phase A inventory always
calls soql_query for PS/Profile counts. The test's own Notes field
documents this distinction. Not a defect — the test is correct as written.
```

### Classify issues correctly

- **PASS**: Test expectations match SKILL.md and model behavior
- **DEFECT**: A concrete mismatch between test expectations and SKILL.md (or between SKILL.md sections). Requires a fix PR.
- **WARN**: A behavioral concern that doesn't break the test but suggests a potential improvement. Must include a recommendation.

Do not use "WARN" to paper over issues that are actually defects. If the test references a nonexistent workflow, that's a defect, not a warning.

---

## Test Count Verification

When running Phase 2, agents may miscount tests in their summary lines (e.g., reporting "7/7 PASS" when they actually tested 8 cases). This is a known issue with model-generated summaries.

### Required verification steps

After all Phase 2 agents complete:

1. **Count test cases in each dispatch-tests.md file**:

   ```
   For each skills/sf-*/tests/dispatch-tests.md:
     Count the number of ## headings (excluding the file header)
   ```

2. **Cross-check against agent reports**: Verify that each agent's reported count matches the actual test count from step 1. If an agent says "7/7 PASS" but the file has 8 test cases, the agent missed one.

3. **Verify total**: Sum all per-skill counts and confirm the total matches. Do not invent explanations for discrepancies (e.g., "agent miscounts account for the difference"). If counts don't match, investigate which test cases were missed and re-run them.

4. **Report actual counts**: The summary table must use actual test counts from the dispatch-tests.md files, not the agents' self-reported counts.

### Example verification

```
File counts:
  sf-apex:        9 tests (## headings)
  sf-audit:       8 tests
  sf-data:        9 tests
  ...
  Total:          88 tests

Agent reports:
  sf-apex agent:  "9/9 PASS"  ✓ matches
  sf-audit agent: "7/7 PASS"  ✗ file has 8 — check which test was skipped
  sf-data agent:  "9/9 PASS"  ✓ matches
```

If an agent skipped a test, either re-run that specific test or document it as "NOT TESTED" in the report — never silently adjust the numbers.
