# cirra-ai-sf Integration Test Plan

**Version:** 2.0.0
**Plugin:** cirra-ai-sf
**Last updated:** 2026-02-22

---

> **Core Principle: These are integration tests.** Each test calls a skill
> command as an end-user would and checks the observable outcome. The skill is a
> black box. Only open it when a test fails.
>
> If a test step involves reading a file inside the plugin's `skills/` or
> `hooks/` directory, it belongs in `BUG_INVESTIGATION_GUIDE.md` — not in the
> main test flow.

---

## Overview

This plan exercises every slash command exposed by the cirra-ai-sf plugin:

| Category | Commands |
|----------|----------|
| **Data** | `/insert-data`, `/query-data`, `/validate-data` |
| **Apex** | `/create-apex`, `/update-apex`, `/validate-apex` |
| **Flow** | `/create-flow`, `/update-flow`, `/validate-flow` |
| **LWC** | `/create-lwc`, `/update-lwc`, `/validate-lwc` |
| **Audit** | `/audit-org` |

All test records use the `CirraTest_` prefix so cleanup is pattern-based and
idempotent (see `99_cleanup.md`).

---

## Test Naming Convention

Every test case has a unique ID: **TC-NNN**

| Range | Phase |
|-------|-------|
| TC-001 – TC-010 | 00 — Smoke tests |
| TC-011 – TC-049 | 01a — Data setup |
| TC-050 – TC-079 | 01b — Metadata setup |
| TC-080 – TC-119 | 02 — Validate artifacts |
| TC-120 – TC-159 | 03 — Update artifacts |
| TC-160 – TC-179 | 04 — Audit and report |

---

## Execution Flow

```
1. Read TEST_PLAN.md             → understand scope, principle, report format
2. Run 00_smoke_test.md          → if all green, proceed
                                    if hook error → BLOCKED, skip 01b+
3. Run 01a_setup_data.md         → always runnable; collect record IDs
4. Run 01b_setup_metadata.md     → only if smoke test (metadata) passed
5. Run 02_validate_artifacts.md  → data queries always; validators always
                                    deployment validation only if 01b passed
6. Run 03_update_artifacts.md    → bulk update always
                                    upsert only if custom ExternalId__c exists
7. Run 04_audit_and_report.md    → only if 01b passed; otherwise partial report
8. Run 99_cleanup.md             → always safe to run; pattern-based deletes
9. Fill in REPORT_TEMPLATE.md    → structured output, not assembled from memory
```

At no point in steps 1–9 does the executor need to open `skills/` or `hooks/`
directories. If any step fails unexpectedly, the executor opens
`BUG_INVESTIGATION_GUIDE.md`, follows the decision tree, reaches a verdict in
2–3 steps, and moves on.

---

## Smoke Test Gate

```
SMOKE TEST GATE
───────────────
All three smoke tests must return "success" or a validation result
(not a hook/subprocess error) before proceeding to Phase 1.

If any smoke test returns a hook/subprocess error → STOP, file Bug,
mark all metadata tests as BLOCKED, and proceed with data-only tests.
```

See `00_smoke_test.md` for the three smoke tests.

---

## Phase Dependencies

```
00_smoke_test
├── 01a_setup_data         ← depends only on: MCP connectivity + standard objects
│   └── 02_validate (data queries, bulk count, relationships)
│   └── 03_update (bulk update, delete)
└── 01b_setup_metadata     ← depends on: smoke test gate (metadata path must be green)
    └── 02_validate (deployment validation, local validators)
    └── 03_update (Apex/Flow/LWC update)
    └── 04_audit_and_report
```

`01a` is runnable even if `01b` is blocked. Many Phase 2 query tests (SOQL,
relationships, bulk count) only need data records — they are not gated on
whether Apex deployed successfully.

---

## Test Result Structure

Every test case uses this format:

```markdown
### TC-NNN — Short description

**Command:** `/command-name` — what to do
**Expected:**
- Success case description
- Alternative outcome for org variants (if applicable)
**Known limitation:** (if any — org-specific, field-specific, etc.)
**SKIP condition:** (if the test cannot run in some orgs)
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Section Name
```

Result recording per test:

| Field | Description |
|-------|-------------|
| **Status** | PASS / FAIL / SKIP / BLOCKED |
| **Evidence** | Return value, record IDs, error message verbatim |
| **Notes** | Any deviation from expected outcome |

---

## Required Evidence Per Phase

Each phase specifies what evidence to collect. At minimum:

- [ ] Text output of each skill command result (or error message verbatim)
- [ ] List of created record IDs (for cleanup tracking)
- [ ] Validation scores (if applicable)
- [ ] Any error messages — copied verbatim, not paraphrased

---

## Final Report Format

Use `REPORT_TEMPLATE.md` to produce the final report. Required sections:

1. **Summary table** — pass/fail per command
2. **Bug list** — with severity (Critical / High / Medium / Low)
3. **Created record IDs** — for cleanup verification
4. **Blocked tests** — with reason and investigation verdict
5. **Recommendations** — actionable items for next release

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `TEST_PLAN.md` | This file — scope, principles, execution flow |
| `00_smoke_test.md` | 3 smoke tests, ~2 min, hard gate before Phase 1 |
| `01a_setup_data.md` | Data record insertion (always runnable) |
| `01b_setup_metadata.md` | Apex/Flow/LWC creation (gated on smoke test) |
| `02_validate_artifacts.md` | Query, validate, and verify all artifacts |
| `03_update_artifacts.md` | Update, upsert, bulk modify, and delete |
| `04_audit_and_report.md` | Full org audit via `/audit-org` |
| `99_cleanup.md` | Pattern-based idempotent cleanup |
| `BUG_INVESTIGATION_GUIDE.md` | Decision trees for failure diagnosis |
| `REPORT_TEMPLATE.md` | Structured template for the final test report |
