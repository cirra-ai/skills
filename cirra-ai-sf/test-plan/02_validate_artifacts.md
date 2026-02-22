# Phase 2 — Validate Artifacts

**Purpose:** Validate all artifacts created in Phases 1a and 1b using the
`/validate-apex`, `/validate-flow`, `/validate-lwc`, `/validate-data`, and
`/query-data` commands.

---

## Prerequisites

- [ ] 01a_setup_data: PASS (data records exist)
- [ ] 01b_setup_metadata: PASS or BLOCKED
  - If BLOCKED: skip all metadata validation tests (TC-090+), run data tests only

---

## Required Evidence

- [ ] Validation scores for each component
- [ ] Query results confirming data integrity
- [ ] Any error messages verbatim

---

## Data Validation Tests

> These tests require only Phase 1a (data setup). They are always runnable.

### TC-080 — Query all test Accounts

**Command:** `/query-data` —

```sql
SELECT Id, Name, Industry, Type FROM Account
WHERE Name LIKE 'CirraTest_Acct_%'
ORDER BY Name
```

**Expected:**

- Returns 5 records (CirraTest_Acct_Alpha through Epsilon)
- Industry = Technology, Type = Customer - Direct for all
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field          | Value |
| -------------- | ----- |
| Status         |       |
| Record count   |       |
| Fields correct |       |
| Notes          |       |

---

### TC-081 — Query Contacts with parent Account

**Command:** `/query-data` —

```sql
SELECT Id, FirstName, LastName, Email, Account.Name
FROM Contact
WHERE LastName LIKE 'CirraTest_Contact_%'
ORDER BY LastName
```

**Expected:**

- Returns 10 records
- Each has a non-null Account.Name from the CirraTest*Acct* set
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field                      | Value |
| -------------------------- | ----- |
| Status                     |       |
| Record count               |       |
| All Account.Name populated |       |
| Notes                      |       |

---

### TC-082 — Query Opportunity pipeline

**Command:** `/query-data` —

```sql
SELECT Account.Name, SUM(Amount) totalPipeline, COUNT(Id) oppCount
FROM Opportunity
WHERE Name LIKE 'CirraTest_Opp_%'
GROUP BY Account.Name
ORDER BY Account.Name
```

**Expected:**

- Returns 5 rows (one per Account)
- Each has oppCount = 2
- totalPipeline values are reasonable (sum of assigned amounts)
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Row count          |       |
| Aggregates correct |       |
| Notes              |       |

---

### TC-083 — Verify bulk insert count

**Command:** `/query-data` —

```sql
SELECT COUNT() FROM Account WHERE Name LIKE 'CirraTest_Bulk_%'
```

**Expected:** totalSize = 200
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field  | Value |
| ------ | ----- |
| Status |       |
| Count  |       |
| Notes  |       |

---

### TC-084 — Query Cases with Account relationship

**Command:** `/query-data` —

```sql
SELECT Id, Subject, Status, Priority, Account.Name
FROM Case
WHERE Subject LIKE 'CirraTest_Case_%'
ORDER BY Subject
```

**Expected:** Returns 5 records, all with Status = New, Priority = Medium

**Result:**

| Field        | Value |
| ------------ | ----- |
| Status       |       |
| Record count |       |
| Notes        |       |

---

### TC-085 — Query Leads

**Command:** `/query-data` —

```sql
SELECT Id, FirstName, LastName, Company, Status, Email
FROM Lead
WHERE LastName LIKE 'CirraTest_Lead_%'
ORDER BY LastName
```

**Expected:** Returns 5 records, Company = CirraTest_Company for all

**Result:**

| Field        | Value |
| ------------ | ----- |
| Status       |       |
| Record count |       |
| Notes        |       |

---

### TC-086 — Query Tasks with Contact relationship

**Command:** `/query-data` —

```sql
SELECT Id, Subject, Status, Who.Name
FROM Task
WHERE Subject LIKE 'CirraTest_Task_%'
ORDER BY Subject
```

**Expected:** Returns 5 records, each with a populated Who.Name

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Record count       |       |
| Who.Name populated |       |
| Notes              |       |

---

### TC-087 — Query Events

**Command:** `/query-data` —

```sql
SELECT Id, Subject, StartDateTime, EndDateTime, Who.Name
FROM Event
WHERE Subject LIKE 'CirraTest_Event_%'
ORDER BY Subject
```

**Expected:** Returns 3 records with correct date/time values

**Result:**

| Field        | Value |
| ------------ | ----- |
| Status       |       |
| Record count |       |
| Notes        |       |

---

### TC-088 — Validate data operation (pre-flight)

**Command:** `/validate-data` — validate a hypothetical insert:

```json
{
  "tool": "sobject_dml",
  "params": {
    "sObject": "Contact",
    "operation": "insert",
    "records": [
      { "LastName": "CirraTest_ValidateOnly", "FirstName": "Test", "Email": "test@example.com" }
    ]
  }
}
```

**Expected:** Validator returns a clean report (no errors). Do NOT execute the operation.
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field    | Value |
| -------- | ----- |
| Status   |       |
| Errors   |       |
| Warnings |       |
| Notes    |       |

---

## Metadata Validation Tests

> These tests require Phase 1b (metadata setup). If 01b is BLOCKED, mark all
> tests below as BLOCKED.

### TC-090 — Validate Apex service class

**Command:** `/validate-apex CirraTest_AccountService`
**Expected:**

- Fetches class body from org
- Runs 150-point validation
- Score should match or be close to the score reported at deployment time (TC-050)
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Score (out of 150) |       |
| Notes              |       |

---

### TC-091 — Validate Apex trigger

**Command:** `/validate-apex CirraTest_AccountTrigger`
**Expected:**

- Fetches trigger body from org (may need to look up as ApexTrigger)
- Validation runs successfully
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Score (out of 150) |       |
| Notes              |       |

---

### TC-092 — Validate Apex batch class

**Command:** `/validate-apex CirraTest_AccountBatch`
**Expected:**

- Validation runs successfully
- Score reported
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Score (out of 150) |       |
| Notes              |       |

---

### TC-093 — Validate multiple Apex classes (comma list)

**Command:** `/validate-apex CirraTest_AccountService,CirraTest_AccountBatch,CirraTest_AccountTrigger`
**Expected:**

- All three are fetched, validated, and displayed in a summary table
- Table sorted by score ascending (worst first)
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field               | Value |
| ------------------- | ----- |
| Status              |       |
| Summary table shown |       |
| Notes               |       |

---

### TC-095 — Validate record-triggered Flow

**Command:** `/validate-flow CirraTest_Account_Create_Task`
**Expected:**

- Fetches flow XML from org via `metadata_read`
- Runs 110-point validation
- Score returned
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Score (out of 110) |       |
| Notes              |       |

---

### TC-096 — Validate screen Flow

**Command:** `/validate-flow CirraTest_Case_Intake_Screen`
**Expected:**

- Validation runs successfully
- Score returned
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Score (out of 110) |       |
| Notes              |       |

---

### TC-098 — Validate LWC (App Page)

**Command:** `/validate-lwc cirraTestDashboard`
**Expected:**

- Fetches bundle from org
- Validates each file (HTML, CSS, JS)
- Per-file and combined scores reported
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field      | Value |
| ---------- | ----- |
| Status     |       |
| HTML score |       |
| CSS score  |       |
| JS score   |       |
| Notes      |       |

---

### TC-099 — Validate LWC (Record Page)

**Command:** `/validate-lwc cirraTestContactCard`
**Expected:**

- Validation runs successfully
- Per-file scores reported
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field             | Value |
| ----------------- | ----- |
| Status            |       |
| Validation scores |       |
| Notes             |       |

---

## Phase 2 Summary

### Data Tests

| TC     | Description                    | Status |
| ------ | ------------------------------ | ------ |
| TC-080 | Query Accounts                 |        |
| TC-081 | Query Contacts + parent        |        |
| TC-082 | Opportunity pipeline aggregate |        |
| TC-083 | Bulk count verification        |        |
| TC-084 | Query Cases                    |        |
| TC-085 | Query Leads                    |        |
| TC-086 | Query Tasks + Who              |        |
| TC-087 | Query Events                   |        |
| TC-088 | Pre-flight data validation     |        |

### Metadata Tests

| TC     | Description                    | Status |
| ------ | ------------------------------ | ------ |
| TC-090 | Validate Apex service class    |        |
| TC-091 | Validate Apex trigger          |        |
| TC-092 | Validate Apex batch class      |        |
| TC-093 | Validate multiple Apex (comma) |        |
| TC-095 | Validate record-triggered Flow |        |
| TC-096 | Validate screen Flow           |        |
| TC-098 | Validate LWC (App Page)        |        |
| TC-099 | Validate LWC (Record Page)     |        |
