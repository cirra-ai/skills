# Phase 1a — Data Setup

**Purpose:** Insert test data records across standard Salesforce objects using
`/insert-data` and verify with `/query-data`. This phase depends only on MCP
connectivity and standard objects — it does not require metadata deployment.

---

## Prerequisites

- [ ] 00_smoke_test: TC-001 PASS (MCP connectivity)
- [ ] 00_smoke_test: TC-002 PASS (data path)
- [ ] Org confirmed connected

---

## Required Evidence

- [ ] Record IDs for every insert operation
- [ ] Query results confirming record creation
- [ ] Any error messages verbatim

---

## Tests

### TC-011 — Insert Accounts (single)

**Command:** `/insert-data` — insert 5 Account records:
```
Names: CirraTest_Acct_Alpha, CirraTest_Acct_Beta, CirraTest_Acct_Gamma,
       CirraTest_Acct_Delta, CirraTest_Acct_Epsilon
Industry: Technology
Type: Customer - Direct
```
**Expected:** 5 records inserted, 5 record IDs returned
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record IDs | |
| Notes | |

---

### TC-012 — Insert Contacts (with Account relationship)

**Command:** `/insert-data` — insert 10 Contact records linked to the Accounts
from TC-011:
```
LastName pattern: CirraTest_Contact_01 through CirraTest_Contact_10
FirstName: Test
Email: cirratest_contact_NN@testfactory.example.com
AccountId: distribute across the 5 Accounts from TC-011 (2 each)
```
**Expected:** 10 records inserted, all linked to valid AccountIds
**Verify:** `/query-data` — `SELECT Id, LastName, Account.Name FROM Contact WHERE LastName LIKE 'CirraTest_Contact_%'`
- Returns 10 records, each showing the parent Account name
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record IDs | |
| Relationship verified | |
| Notes | |

---

### TC-013 — Insert Opportunities

**Command:** `/insert-data` — insert 10 Opportunity records:
```
Name pattern: CirraTest_Opp_01 through CirraTest_Opp_10
StageName: Prospecting
CloseDate: 2026-12-31
Amount: 10000 to 100000 (increment by 10000)
AccountId: distribute across the 5 Accounts from TC-011
```
**Expected:** 10 records inserted with correct stage, amounts, and Account links
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record IDs | |
| Notes | |

---

### TC-014 — Insert Cases

**Command:** `/insert-data` — insert 5 Case records:
```
Subject pattern: CirraTest_Case_01 through CirraTest_Case_05
Status: New
Priority: Medium
AccountId: link to first 5 Accounts from TC-011
```
**Expected:** 5 records inserted
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record IDs | |
| Notes | |

---

### TC-015 — Insert Leads

**Command:** `/insert-data` — insert 5 Lead records:
```
LastName pattern: CirraTest_Lead_01 through CirraTest_Lead_05
FirstName: Test
Company: CirraTest_Company
Status: Open - Not Contacted
Email: cirratest_lead_NN@testlead.example.com
```
**Expected:** 5 records inserted
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record IDs | |
| Notes | |

---

### TC-016 — Insert Tasks

**Command:** `/insert-data` — insert 5 Task records:
```
Subject pattern: CirraTest_Task_01 through CirraTest_Task_05
Status: Not Started
Priority: Normal
WhoId: link to first 5 Contacts from TC-012
```
**Expected:** 5 records inserted, each linked to a Contact
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record IDs | |
| Notes | |

---

### TC-017 — Insert Events

**Command:** `/insert-data` — insert 3 Event records:
```
Subject pattern: CirraTest_Event_01 through CirraTest_Event_03
StartDateTime: 2026-03-01T09:00:00Z, 10:00:00Z, 11:00:00Z
EndDateTime: 1 hour after each start
WhoId: link to Contacts from TC-012
```
**Expected:** 3 records inserted
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record IDs | |
| Notes | |

---

### TC-018 — Bulk insert (200 records)

**Command:** `/insert-data` — insert 200 Account records:
```
Name pattern: CirraTest_Bulk_001 through CirraTest_Bulk_200
Industry: Education
```
**Expected:**
- 200 records inserted (may be batched into multiple DML calls of ≤200 each)
- All 200 record IDs returned
**Verify:** `/query-data` — `SELECT COUNT() FROM Account WHERE Name LIKE 'CirraTest_Bulk_%'`
- Returns totalSize = 200
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record count confirmed | |
| Notes | |

---

### TC-019 — Query with relationship traversal

**Command:** `/query-data` —
```sql
SELECT Id, LastName, Account.Name, Account.Industry
FROM Contact
WHERE LastName LIKE 'CirraTest_Contact_%'
```
**Expected:**
- Returns 10 records
- Each record shows the parent Account name and Industry
- Relationship fields are populated (not null)
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Record count | |
| Relationships populated | |
| Notes | |

---

### TC-020 — Query with aggregate

**Command:** `/query-data` —
```sql
SELECT Account.Name, COUNT(Id) contactCount
FROM Contact
WHERE LastName LIKE 'CirraTest_Contact_%'
GROUP BY Account.Name
```
**Expected:** Returns 5 rows, each with contactCount = 2
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Row count | |
| Counts correct | |
| Notes | |

---

### TC-021 — Pre-flight data validation

**Command:** `/validate-data` — validate a DML operation before executing:
```json
{
  "tool": "sobject_dml",
  "params": {
    "sObject": "Account",
    "operation": "insert",
    "records": [{"Name": "CirraTest_ValidateCheck", "Industry": "Technology"}]
  }
}
```
**Expected:**
- Validator returns a report with no errors
- Warnings (if any) are advisory only
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field | Value |
|-------|-------|
| Status | |
| Errors | |
| Warnings | |
| Notes | |

---

## Phase 1a Summary

| TC | Description | Status |
|----|-------------|--------|
| TC-011 | Insert Accounts | |
| TC-012 | Insert Contacts | |
| TC-013 | Insert Opportunities | |
| TC-014 | Insert Cases | |
| TC-015 | Insert Leads | |
| TC-016 | Insert Tasks | |
| TC-017 | Insert Events | |
| TC-018 | Bulk insert 200 | |
| TC-019 | Relationship query | |
| TC-020 | Aggregate query | |
| TC-021 | Pre-flight validation | |

**Total records created:** _____ (expected: ~248 + 1 smoke test)
