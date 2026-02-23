# cirra-ai-sf Integration Test Report

**Version:** 2.0.0
**Date:** YYYY-MM-DD
**Org:** (username)
**Executor:** (Claude session ID or human tester name)
**Plugin version:** (version from plugin.json)

---

## 1. Executive Summary

| Metric                    | Value |
| ------------------------- | ----- |
| Total test steps          |       |
| Passed                    |       |
| Failed                    |       |
| Skipped                   |       |
| Blocked                   |       |
| Pass rate (excl. blocked) |       |

**Overall verdict:** PASS / PARTIAL PASS / FAIL

**Summary:** (1–3 sentences describing the overall result)

---

## 2. Smoke Test Gate

| Step   | Description      | Status | Notes |
| ------ | ---------------- | ------ | ----- |
| TC-001 | MCP connectivity |        |       |
| TC-002 | Data path        |        |       |
| TC-003 | Metadata path    |        |       |

**Gate decision:** (Proceed to all / Data-only / Stop)

---

## 3. Results by Phase

### Phase 1a — Data Setup

| Step  | Description                | Status | Evidence |
| ----- | -------------------------- | ------ | -------- |
| 1a.1  | Initialize MCP             |        |          |
| 1a.2  | Describe objects           |        |          |
| 1a.3  | Insert Accounts (10)       |        |          |
| 1a.4  | Insert Contacts (20)       |        |          |
| 1a.5  | Insert Opportunities (15)  |        |          |
| 1a.6  | Insert Cases (10)          |        |          |
| 1a.7  | Insert Leads (10)          |        |          |
| 1a.8  | Insert Activities (10T+5E) |        |          |
| 1a.9  | Bulk insert (251)          |        |          |
| 1a.10 | Hierarchy (5→3→2→1)        |        |          |

**Total records created:** \_\_\_\_

### Phase 1b — Metadata Setup

| Step  | Artifact                            | Status | Score | Evidence |
| ----- | ----------------------------------- | ------ | ----- | -------- |
| 1b.1  | CirraTest_AccountTrigger + TA class |        | /150  |          |
| 1b.2  | CirraTest_AccountService            |        | /150  |          |
| 1b.3  | CirraTest_AccountSelector           |        | /150  |          |
| 1b.4  | CirraTest_AccountRevenueBatch       |        | /150  |          |
| 1b.5  | CirraTest_ContactTaskCreator        |        | /150  |          |
| 1b.6  | CirraTest_AccountWinChecker         |        | /150  |          |
| 1b.7  | CirraTest_Account_Before_Save       |        | /110  |          |
| 1b.8  | CirraTest_Opp_After_Save_Task       |        | /110  |          |
| 1b.9  | CirraTest_Case_Intake_Screen        |        | /110  |          |
| 1b.10 | CirraTest_VIP_Contact_Tasks         |        | /110  |          |
| 1b.11 | CirraTest_Stale_Opp_Cleanup         |        | /110  |          |
| 1b.12 | CirraTest_Order_Event_Handler       |        | /110  |          |
| 1b.13 | cirraTestAccountDashboard           |        | /165  |          |
| 1b.14 | cirraTestAccountForm                |        | /165  |          |
| 1b.15 | cirraTestRecordSelector             |        | /165  |          |
| 1b.16 | cirraTestConfirmModal               |        | /165  |          |
| 1b.17 | cirraTestContactList                |        | /165  |          |

### Phase 2 — Validate Artifacts

#### Data Tests

| Step | Description                    | Status | Evidence |
| ---- | ------------------------------ | ------ | -------- |
| 2.1  | Query Accounts                 |        |          |
| 2.2  | Query Contacts + parent        |        |          |
| 2.3  | Opportunity pipeline           |        |          |
| 2.4  | Bulk count (CirraTest*Bulk*\*) |        |          |
| 2.5  | Query Cases                    |        |          |
| 2.6  | Query Leads                    |        |          |
| 2.7  | Query Tasks + Who              |        |          |
| 2.8  | Query Events                   |        |          |
| 2.9  | Semi-join (Accounts with Opps) |        |          |
| 2.10 | Anti-join (Accounts no Opps)   |        |          |
| 2.11 | Polymorphic (Task WhoId)       |        |          |
| 2.12 | Hierarchy traversal            |        |          |

#### Metadata Tests

| Step | Artifact / Scope             | Status | Score | Evidence |
| ---- | ---------------------------- | ------ | ----- | -------- |
| 2.13 | Validate AccountService      |        | /150  |          |
| 2.14 | Validate AccountSelector     |        | /150  |          |
| 2.15 | Validate AccountRevenueBatch |        | /150  |          |
| 2.16 | Validate ContactTaskCreator  |        | /150  |          |
| 2.17 | Validate AccountWinChecker   |        | /150  |          |
| 2.18 | Validate Apex comma-list     |        |       |          |
| 2.19 | Validate Apex --all          |        |       |          |
| 2.20 | Validate Account_Before_Save |        | /110  |          |
| 2.21 | Validate Opp_After_Save_Task |        | /110  |          |
| 2.22 | Validate Case_Intake_Screen  |        | /110  |          |
| 2.23 | Validate Flow comma-list     |        |       |          |
| 2.24 | Validate Flow --all          |        |       |          |
| 2.25 | Validate AccountDashboard    |        | /165  |          |
| 2.26 | Validate AccountForm         |        | /165  |          |
| 2.27 | Validate ConfirmModal        |        | /165  |          |
| 2.28 | Validate LWC comma-list      |        |       |          |
| 2.29 | Validate LWC --all           |        |       |          |

### Phase 3 — Update Artifacts

#### Data Tests

| Step | Description                | Status | Evidence |
| ---- | -------------------------- | ------ | -------- |
| 3.11 | Bulk update revenue (×2)   |        |          |
| 3.12 | Upsert mixed insert/update |        |          |
| 3.13 | Verify updated records     |        |          |

#### Metadata Tests

| Step | Artifact / Change              | Status | Score | Evidence |
| ---- | ------------------------------ | ------ | ----- | -------- |
| 3.1  | AccountService + mergeAccounts |        | /150  |          |
| 3.2  | AccountTrigger — action logic  |        | /150  |          |
| 3.3  | AccountRevenueBatch + retry    |        | /150  |          |
| 3.4  | Account_Before_Save + decision |        | /110  |          |
| 3.5  | Opp_After_Save_Task + fault    |        | /110  |          |
| 3.6  | Case_Intake_Screen + screen    |        | /110  |          |
| 3.7  | AccountDashboard + dark mode   |        | /165  |          |
| 3.8  | AccountDashboard + column      |        | /165  |          |
| 3.9  | ConfirmModal + accessibility   |        | /165  |          |
| 3.10 | AccountForm + Apex integration |        | /165  |          |
| 3.14 | Re-validate Apex               |        |       |          |
| 3.15 | Re-validate Flows              |        |       |          |
| 3.16 | Re-validate LWC                |        |       |          |

### Phase 4 — Audit and Report

| Step | Description                         | Status | Evidence |
| ---- | ----------------------------------- | ------ | -------- |
| 4.1  | Audit execution sequence            |        |          |
| 4.2  | Word report validation              |        |          |
| 4.3  | Excel report validation             |        |          |
| 4.4  | HTML report validation              |        |          |
| 4.5  | Intermediate files validation       |        |          |
| 4.6  | Cross-reference scores (Phases 2/3) |        |          |
| 4.7  | Org health summary validation       |        |          |

---

## 4. Command Coverage

| Command          | Steps | Passed | Failed | Skipped | Blocked |
| ---------------- | ----- | ------ | ------ | ------- | ------- |
| `/insert-data`   |       |        |        |         |         |
| `/query-data`    |       |        |        |         |         |
| `/validate-data` |       |        |        |         |         |
| `/create-apex`   |       |        |        |         |         |
| `/update-apex`   |       |        |        |         |         |
| `/validate-apex` |       |        |        |         |         |
| `/create-flow`   |       |        |        |         |         |
| `/update-flow`   |       |        |        |         |         |
| `/validate-flow` |       |        |        |         |         |
| `/create-lwc`    |       |        |        |         |         |
| `/update-lwc`    |       |        |        |         |         |
| `/validate-lwc`  |       |        |        |         |         |
| `/audit-org`     |       |        |        |         |         |

---

## 5. Bugs Found

| #   | Severity | Step | Summary | Investigation Verdict |
| --- | -------- | ---- | ------- | --------------------- |
| 1   |          |      |         |                       |
| 2   |          |      |         |                       |
| 3   |          |      |         |                       |

Severity levels:

- **Critical** — Blocks core functionality, no workaround
- **High** — Major feature broken, workaround exists
- **Medium** — Feature partially works, minor impact
- **Low** — Cosmetic or edge case

---

## 6. Blocked Tests

| Step | Reason | Investigation Guide Section | Verdict |
| ---- | ------ | --------------------------- | ------- |
|      |        |                             |         |

---

## 7. Skipped Tests

| Step | Reason |
| ---- | ------ |
|      |        |

---

## 8. Created Record IDs

> For cleanup verification. These should all be deleted by `99_cleanup.md`.

### Data Records

| Object      | Count | Sample IDs |
| ----------- | ----- | ---------- |
| Account     |       |            |
| Contact     |       |            |
| Opportunity |       |            |
| Case        |       |            |
| Lead        |       |            |
| Task        |       |            |
| Event       |       |            |

### Metadata Components

| Type           | Names |
| -------------- | ----- |
| Apex Classes   |       |
| Apex Triggers  |       |
| Flows          |       |
| LWC Components |       |

---

## 9. Cleanup Verification

| Category              | Created | Deleted | Verified Clean |
| --------------------- | ------- | ------- | -------------- |
| Data records          |         |         |                |
| Apex classes/triggers |         |         |                |
| Flows                 |         |         |                |
| LWC components        |         |         |                |
| Local files           |         |         |                |

---

## 10. Recommendations

1. (Actionable recommendation based on test results)
2.
3.

---

## 11. Environment Notes

- Org edition:
- API version:
- TAF installed: Yes / No
- Custom external ID fields available: Yes / No
- Sandbox restrictions encountered: (describe if any)
- Session duration:
