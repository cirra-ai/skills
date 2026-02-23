# Phase 3 — Update Artifacts

**Purpose:** Test update, upsert, bulk modify, and delete operations using
`/insert-data` (for DML operations), `/update-apex`, `/update-flow`, and
`/update-lwc` commands.

---

## Prerequisites

- [ ] 01a_setup_data: PASS (data records exist for update/upsert/delete tests)
- [ ] 01b_setup_metadata: PASS or BLOCKED
  - If BLOCKED: skip metadata update tests (TC-140+), run data update tests only

---

## Required Evidence

- [ ] Updated record field values (before/after)
- [ ] Updated component validation scores
- [ ] Any error messages verbatim

---

## Data Update Tests

> These tests require only Phase 1a. They are always runnable.

### TC-120 — Update Account fields

**Command:** `/insert-data` — update 5 Accounts:

```
Operation: update
Records: the 5 CirraTest_Acct_ records from TC-011
Change: set Industry = "Healthcare" for all 5
```

**Expected:**

- 5 records updated successfully
  **Verify:** `/query-data` — `SELECT Id, Name, Industry FROM Account WHERE Name LIKE 'CirraTest_Acct_%'`
- All 5 show Industry = Healthcare
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field                      | Value |
| -------------------------- | ----- |
| Status                     |       |
| Records updated            |       |
| Verification query correct |       |
| Notes                      |       |

---

### TC-121 — Bulk update (200 records)

**Command:** `/insert-data` — update 200 Accounts:

```
Operation: update
Records: the 200 CirraTest_Bulk_ records from TC-018
Change: set Description = "Bulk updated by CirraTest"
```

**Expected:**

- 200 records updated (may be batched)
  **Verify:** `/query-data` —

```sql
SELECT COUNT() FROM Account
WHERE Name LIKE 'CirraTest_Bulk_%' AND Description = 'Bulk updated by CirraTest'
```

- Returns 200
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field              | Value |
| ------------------ | ----- |
| Status             |       |
| Count after update |       |
| Notes              |       |

---

### TC-122 — Upsert with custom external ID

**Command:** `/insert-data` — upsert 5 Account records:

```
Operation: upsert
externalIdField: <custom ExternalId__c field>
Records: 3 existing CirraTest_Acct_ records (update) + 2 new (insert)
```

**Expected:**

- If org has a custom ExternalId\_\_c field on Account: 5 records upserted (3 updated, 2 inserted)
- If no custom external ID field exists: validator warns and aborts with a clear message

**Known limitation:** Standard fields (Name, Id) are not valid upsert keys in
Salesforce REST API. A custom external ID field is a prerequisite for this test.

**SKIP condition:** Skip and mark SKIP if no custom external ID field is
available on Account. Do not attempt with standard fields.

**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field                  | Value |
| ---------------------- | ----- |
| Status                 |       |
| External ID field used |       |
| Records upserted       |       |
| Notes                  |       |

---

### TC-123 — Delete records

**Command:** `/insert-data` — delete 3 Lead records:

```
Operation: delete
Records: CirraTest_Lead_01, CirraTest_Lead_02, CirraTest_Lead_03 (by Id)
```

**Expected:** 3 records deleted (moved to Recycle Bin)
**Verify:** `/query-data` — `SELECT COUNT() FROM Lead WHERE LastName LIKE 'CirraTest_Lead_%'`

- Returns 2 (CirraTest_Lead_04 and CirraTest_Lead_05 remain)
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field           | Value |
| --------------- | ----- |
| Status          |       |
| Records deleted |       |
| Remaining count |       |
| Notes           |       |

---

### TC-124 — Validate update operation (pre-flight)

**Command:** `/validate-data` — validate an update operation without executing:

```json
{
  "tool": "sobject_dml",
  "params": {
    "sObject": "Account",
    "operation": "update",
    "records": [{ "Id": "<any CirraTest Account Id>", "Industry": "Finance" }]
  }
}
```

**Expected:** Validator returns clean report. Do NOT execute.
**On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field    | Value |
| -------- | ----- |
| Status   |       |
| Errors   |       |
| Warnings |       |
| Notes    |       |

---

## Metadata Update Tests

> These tests require Phase 1b. If 01b is BLOCKED, mark all tests below as
> BLOCKED.

### TC-140 — Update Apex service class

**Command:** `/update-apex CirraTest_AccountService` — add a second method:

```
Add a method: public static Integer countActiveAccounts()
It should return the count of Accounts with Industry != null
```

**Expected:**

- Existing class fetched from org
- Method added preserving existing code and ApexDoc
- Validation score reported
- Updated class deployed via `tooling_api_dml` update
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field            | Value |
| ---------------- | ----- |
| Status           |       |
| Validation score |       |
| Deployed         |       |
| Notes            |       |

---

### TC-141 — Update Apex trigger (add event)

**Command:** `/update-apex CirraTest_AccountTrigger` — add after delete handling:

```
Add after delete event handling
Purpose: Log a debug message when an Account is deleted
```

**Expected:**

- Trigger updated to include `after delete` in its event list
- Handler class updated with the new event handling logic
- Both redeployed
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field             | Value |
| ----------------- | ----- |
| Status            |       |
| Trigger updated   |       |
| Handler updated   |       |
| Validation scores |       |
| Notes             |       |

---

### TC-145 — Update record-triggered Flow

**Command:** `/update-flow CirraTest_Account_Create_Task` — modify the flow:

```
Add a Decision element: only create the Task if the Account's Industry is not null
```

**Expected:**

- Flow XML fetched from org
- Decision element added before the Create Records element
- Fault paths preserved
- Validation score reported
- Flow redeployed via `metadata_update`
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field            | Value |
| ---------------- | ----- |
| Status           |       |
| Validation score |       |
| Deployed         |       |
| Notes            |       |

---

### TC-150 — Update LWC (add feature)

**Command:** `/update-lwc cirraTestDashboard` — add pagination:

```
Add pagination: show 10 Accounts per page with Previous/Next buttons
```

**Expected:**

- Bundle fetched from org
- JS updated with pagination logic
- HTML updated with pagination controls
- CSS updated if needed
- Validation scores reported per file
- Bundle redeployed via `metadata_update`
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field      | Value |
| ---------- | ----- |
| Status     |       |
| HTML score |       |
| CSS score  |       |
| JS score   |       |
| Deployed   |       |
| Notes      |       |

---

## Phase 3 Summary

### Data Tests

| TC     | Description                  | Status |
| ------ | ---------------------------- | ------ |
| TC-120 | Update Account fields        |        |
| TC-121 | Bulk update 200 records      |        |
| TC-122 | Upsert with external ID      |        |
| TC-123 | Delete records               |        |
| TC-124 | Validate update (pre-flight) |        |

### Metadata Tests

| TC     | Description                  | Status |
| ------ | ---------------------------- | ------ |
| TC-140 | Update Apex service class    |        |
| TC-141 | Update Apex trigger          |        |
| TC-145 | Update record-triggered Flow |        |
| TC-150 | Update LWC                   |        |
