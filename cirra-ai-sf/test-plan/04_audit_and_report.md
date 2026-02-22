# Phase 4 — Audit and Report

**Purpose:** Run a full org audit using `/audit-org` and verify that it produces
scored reports across Apex, Flows, and LWC components.

---

## Prerequisites

- [ ] 01b_setup_metadata: PASS (Apex, Flow, and LWC components must exist in org)
  - If BLOCKED: This entire phase is BLOCKED. Generate a partial report using
    REPORT_TEMPLATE.md covering data-only test results.
- [ ] 01a_setup_data: PASS (data records exist for context)

---

## Required Evidence

- [ ] Org audit output (component counts, scores, recommendations)
- [ ] Generated report files (Word, Excel, HTML) if produced
- [ ] Any error messages verbatim

---

## Tests

### TC-160 — Run full org audit

**Command:** `/audit-org`
**Expected:**
1. `cirra_ai_init()` called (or confirmed already initialized)
2. Component counts displayed:
   - X Apex classes, Y active Flows, Z LWC components
3. Each component scored against its rubric:
   - Apex: 150-point scale
   - Flows: 110-point scale
   - LWC: 165-point scale
4. Report files generated in `./audit_output/`:
   - `Salesforce_Org_Audit_Report.docx`
   - `Salesforce_Org_Audit_Scores.xlsx`
   - `Salesforce_Org_Audit_Report.html`
5. Summary displayed:
   - Overall org health score
   - Components below threshold
   - Top issues per domain

**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Apex classes audited | |
| Flows audited | |
| LWC components audited | |
| Overall health score | |
| Report files generated | |
| Notes | |

---

### TC-161 — Verify CirraTest components appear in audit

**Command:** Review the audit output from TC-160.
**Expected:**
- CirraTest_AccountService, CirraTest_AccountBatch, CirraTest_AccountTrigger
  appear in the Apex section
- CirraTest_Account_Create_Task, CirraTest_Case_Intake_Screen appear in the
  Flow section
- cirraTestDashboard, cirraTestContactCard appear in the LWC section
- Scores for CirraTest_ components should be reasonably high (they were just
  created/validated by the plugin)

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| CirraTest Apex found | |
| CirraTest Flows found | |
| CirraTest LWC found | |
| Notes | |

---

### TC-162 — Verify report file contents

**Command:** Check the generated report files.
**Expected:**
- Word report has executive summary, per-domain sections, recommendations
- Excel report has separate sheets for Apex, Flows, LWC, and Summary
- HTML report is viewable and contains score data
- All three contain consistent data

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Word report valid | |
| Excel report valid | |
| HTML report valid | |
| Notes | |

---

## Phase 4 Summary

| TC | Description | Status |
|----|-------------|--------|
| TC-160 | Full org audit | |
| TC-161 | CirraTest components in audit | |
| TC-162 | Report file contents | |
