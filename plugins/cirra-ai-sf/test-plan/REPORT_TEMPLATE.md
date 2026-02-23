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
| Total test cases          |       |
| Passed                    |       |
| Failed                    |       |
| Skipped                   |       |
| Blocked                   |       |
| Pass rate (excl. blocked) |       |

**Overall verdict:** PASS / PARTIAL PASS / FAIL

**Summary:** (1–3 sentences describing the overall result)

---

## 2. Smoke Test Gate

| TC     | Description      | Status | Notes |
| ------ | ---------------- | ------ | ----- |
| TC-001 | MCP connectivity |        |       |
| TC-002 | Data path        |        |       |
| TC-003 | Metadata path    |        |       |

**Gate decision:** (Proceed to all / Data-only / Stop)

---

## 3. Results by Phase

### Phase 1a — Data Setup

| TC     | Description               | Status | Evidence |
| ------ | ------------------------- | ------ | -------- |
| TC-011 | Insert Accounts (5)       |        |          |
| TC-012 | Insert Contacts (10)      |        |          |
| TC-013 | Insert Opportunities (10) |        |          |
| TC-014 | Insert Cases (5)          |        |          |
| TC-015 | Insert Leads (5)          |        |          |
| TC-016 | Insert Tasks (5)          |        |          |
| TC-017 | Insert Events (3)         |        |          |
| TC-018 | Bulk insert (200)         |        |          |
| TC-019 | Relationship query        |        |          |
| TC-020 | Aggregate query           |        |          |
| TC-021 | Pre-flight validation     |        |          |

**Total records created:** \_\_\_\_

### Phase 1b — Metadata Setup

| TC     | Description           | Status | Score | Evidence |
| ------ | --------------------- | ------ | ----- | -------- |
| TC-050 | Service class         |        | /150  |          |
| TC-051 | Trigger (non-TAF)     |        | /150  |          |
| TC-052 | Batch class           |        | /150  |          |
| TC-055 | Record-triggered Flow |        | /110  |          |
| TC-056 | Screen Flow           |        | /110  |          |
| TC-060 | LWC (App Page)        |        | /165  |          |
| TC-061 | LWC (Record Page)     |        | /165  |          |

### Phase 2 — Validate Artifacts

#### Data Tests

| TC     | Description             | Status | Evidence |
| ------ | ----------------------- | ------ | -------- |
| TC-080 | Query Accounts          |        |          |
| TC-081 | Query Contacts + parent |        |          |
| TC-082 | Opportunity pipeline    |        |          |
| TC-083 | Bulk count              |        |          |
| TC-084 | Query Cases             |        |          |
| TC-085 | Query Leads             |        |          |
| TC-086 | Query Tasks + Who       |        |          |
| TC-087 | Query Events            |        |          |
| TC-088 | Pre-flight validation   |        |          |

#### Metadata Tests

| TC     | Description            | Status | Score | Evidence |
| ------ | ---------------------- | ------ | ----- | -------- |
| TC-090 | Validate Apex service  |        | /150  |          |
| TC-091 | Validate Apex trigger  |        | /150  |          |
| TC-092 | Validate Apex batch    |        | /150  |          |
| TC-093 | Validate multiple Apex |        |       |          |
| TC-095 | Validate RT Flow       |        | /110  |          |
| TC-096 | Validate screen Flow   |        | /110  |          |
| TC-098 | Validate LWC (App)     |        | /165  |          |
| TC-099 | Validate LWC (Record)  |        | /165  |          |

### Phase 3 — Update Artifacts

#### Data Tests

| TC     | Description                  | Status | Evidence |
| ------ | ---------------------------- | ------ | -------- |
| TC-120 | Update Account fields        |        |          |
| TC-121 | Bulk update 200              |        |          |
| TC-122 | Upsert with external ID      |        |          |
| TC-123 | Delete records               |        |          |
| TC-124 | Validate update (pre-flight) |        |          |

#### Metadata Tests

| TC     | Description         | Status | Score | Evidence |
| ------ | ------------------- | ------ | ----- | -------- |
| TC-140 | Update Apex service |        | /150  |          |
| TC-141 | Update Apex trigger |        | /150  |          |
| TC-145 | Update RT Flow      |        | /110  |          |
| TC-150 | Update LWC          |        | /165  |          |

### Phase 4 — Audit and Report

| TC     | Description          | Status | Evidence |
| ------ | -------------------- | ------ | -------- |
| TC-160 | Full org audit       |        |          |
| TC-161 | CirraTest in audit   |        |          |
| TC-162 | Report file contents |        |          |

---

## 4. Command Coverage

| Command          | Tests | Passed | Failed | Skipped | Blocked |
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

| #   | Severity | TC  | Summary | Investigation Verdict |
| --- | -------- | --- | ------- | --------------------- |
| 1   |          |     |         |                       |
| 2   |          |     |         |                       |
| 3   |          |     |         |                       |

Severity levels:

- **Critical** — Blocks core functionality, no workaround
- **High** — Major feature broken, workaround exists
- **Medium** — Feature partially works, minor impact
- **Low** — Cosmetic or edge case

---

## 6. Blocked Tests

| TC  | Reason | Investigation Guide Section | Verdict |
| --- | ------ | --------------------------- | ------- |
|     |        |                             |         |

---

## 7. Skipped Tests

| TC  | Reason |
| --- | ------ |
|     |        |

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
