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

| Field | Required | Description |
| --- | --- | --- |
| Input | yes | The exact user prompt including `/skill-name` |
| Dispatch | yes | Expected workflow name from dispatch table, or `(none — present menu)` / `(ambiguous)` |
| Init required | yes | Whether `cirra_ai_init()` must be called for this operation |
| Init timing | yes | `before-workflow` = init then execute; `after-menu` = ask user first, init after; `n/a` = no init needed |
| Path | yes | `fast` = simple request, bypass full workflow; `full` = multi-step workflow; `n/a` = no workflow selected |
| First tool | no | First MCP tool expected after init |
| Tool params | no | Key parameters for the first tool call |
| Should call | no | Additional tools expected during the workflow |
| Should NOT call | no | Tools that must NOT be called for this input |
| Should ask user | yes | Whether the model should prompt for clarification |
| Menu options | no | Expected menu items (only for no-args/ambiguous tests) |
| Post-action | no | Required follow-up action (e.g., FLS prompt after field creation) |
| Batch limit | no | Record batch constraints (for DML operations) |
| Follow-up skills | no | Skills that should be offered as next steps |
| Notes | no | Free-text behavioral expectations and edge case notes |

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

Present the constructed prompt to a model instance with these instructions:

```
You are tasked to test the **{skill_name}** skill.

You have access to the {skill_name} skill and any skills it explicitly
references: {referenced_skills}. Ignore any other skills in your environment.

The {skill_name} SKILL.md is provided below as your system prompt.

Given this user prompt:

    {test_input}

Describe step by step what you would do. Specifically report:

1. **Dispatch decision**: Which workflow did you select and why?
2. **Init**: Would you call `cirra_ai_init()` first? Why or why not?
   At what point — before selecting a workflow, or after?
3. **Tool sequence**: List every MCP tool you would call, in order,
   with the exact parameters you'd pass.
4. **User interaction**: Would you ask the user anything before proceeding?
   What and why?
5. **Output format**: How would you present the results?
6. **Follow-up**: What would you offer as next steps?
7. **Tools you would NOT call**: List any tools from the skill that are
   explicitly irrelevant for this input.

Be precise — include actual tool names and parameter values.
```

### 2.4 Validation

Compare the model's response against the test case expectations:

| Check | Expected (from test case) | Actual (from model response) | Result |
| --- | --- | --- | --- |
| Dispatch routing | `Dispatch` field | Model's "Dispatch decision" | PASS/FAIL |
| Init behavior | `Init required` + `Init timing` | Model's "Init" answer | PASS/FAIL |
| First tool | `First tool` + `Tool params` | First tool in model's "Tool sequence" | PASS/FAIL |
| Required tools | `Should call` | Present in model's "Tool sequence" | PASS/FAIL |
| Excluded tools | `Should NOT call` | Absent from model's "Tool sequence" + "Tools NOT called" | PASS/FAIL |
| User interaction | `Should ask user` | Model's "User interaction" | PASS/FAIL |
| Menu content | `Menu options` | Options presented in model's response | PASS/FAIL |
| Follow-up skills | `Follow-up skills` | Skills mentioned in model's "Follow-up" | PASS/WARN |
| Post-action | `Post-action` | Present in model's workflow | PASS/FAIL |
| Notes criteria | `Notes` free-text | Manual review against model behavior | PASS/WARN |

### Phase 2 Result

For each test case, report: **PASS**, **FAIL** (with specific mismatch), or **WARN** (behavioral concern but not a hard failure).

---

## Running the Tests

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

| Skill | Test file | Tests |
| --- | --- | --- |
| sf-apex | `skills/sf-apex/tests/dispatch-tests.md` | create trigger, create test-class, update class, validate name, validate file, validate All, no-args, fast path, ambiguous |
| sf-audit | `skills/sf-audit/tests/dispatch-tests.md` | (see file) |
| sf-data | `skills/sf-data/tests/dispatch-tests.md` | raw SOQL, NL query, build-query, insert, bulk delete, validate, describe, no-args, bare object |
| sf-diagram | `skills/sf-diagram/tests/dispatch-tests.md` | (see file) |
| sf-flow | `skills/sf-flow/tests/dispatch-tests.md` | (see file) |
| sf-kugamon | `skills/sf-kugamon/tests/dispatch-tests.md` | (see file) |
| sf-lwc | `skills/sf-lwc/tests/dispatch-tests.md` | (see file) |
| sf-metadata | `skills/sf-metadata/tests/dispatch-tests.md` | describe, create field, update, delete, no-args, ambiguous, describe-all |
| sf-orders | `skills/sf-orders/tests/dispatch-tests.md` | (see file) |
| sf-permissions | `skills/sf-permissions/tests/dispatch-tests.md` | hierarchy, who-has, user trace, debug, audit, create/clone/update/delete PS, agent-access, no-args, NL field access |
