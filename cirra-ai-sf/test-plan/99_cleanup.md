# Phase 99 — Cleanup

**Purpose:** Remove all test data and metadata created during the test run.
This phase is safe to run at any point — including after partial failures.

---

## Design Principles

1. **Pattern-based:** All queries use `LIKE 'CirraTest_%'` — no hardcoded IDs
2. **Idempotent:** Deleting zero matches is safe — queries that match nothing
   return empty results, and DML on an empty list is a no-op
3. **Dependency-ordered:** Children are deleted before parents to avoid
   relationship constraint errors
4. **Soft delete:** All deletes go to the Salesforce Recycle Bin by default

---

## Prerequisites

- [ ] MCP connectivity confirmed (TC-001 passed at some point)
- [ ] This phase can run regardless of which other phases completed

---

## Step 1 — Delete Data Records

Delete in dependency order: Activities → Children → Parents.

> **Note:** Each query below may return 0 records if that object type was never
> created or was already cleaned up. This is expected and safe.

### 1.1 — Delete Tasks

**Command:** `/query-data` then `/insert-data` (delete operation):

```sql
SELECT Id FROM Task WHERE Subject LIKE 'CirraTest_%'
```

Then delete all returned IDs.

**Expected:** 0–5 records deleted (or 0 if Tasks were never created)

---

### 1.2 — Delete Events

```sql
SELECT Id FROM Event WHERE Subject LIKE 'CirraTest_%'
```

Then delete all returned IDs.

**Expected:** 0–3 records deleted

---

### 1.3 — Delete Cases

```sql
SELECT Id FROM Case WHERE Subject LIKE 'CirraTest_%'
```

Then delete all returned IDs.

**Expected:** 0–5 records deleted

---

### 1.4 — Delete Opportunities

```sql
SELECT Id FROM Opportunity WHERE Name LIKE 'CirraTest_%'
```

Then delete all returned IDs.

**Expected:** 0–10 records deleted

---

### 1.5 — Delete Contacts

```sql
SELECT Id FROM Contact WHERE LastName LIKE 'CirraTest_%'
```

Then delete all returned IDs.

**Expected:** 0–10 records deleted

---

### 1.6 — Delete Leads

```sql
SELECT Id FROM Lead WHERE LastName LIKE 'CirraTest_%'
```

Then delete all returned IDs.

**Expected:** 0–5 records deleted

---

### 1.7 — Delete Accounts

Delete Accounts last — they are parents of Contacts, Opportunities, and Cases.

```sql
SELECT Id FROM Account
WHERE Name LIKE 'CirraTest_%'
```

Then delete all returned IDs.

**Expected:** 0–206 records deleted (5 named + 200 bulk + 1 smoke test)

---

### 1.8 — Verify data cleanup

**Command:** `/query-data` — run each count query:

```sql
SELECT COUNT() FROM Account WHERE Name LIKE 'CirraTest_%'
SELECT COUNT() FROM Contact WHERE LastName LIKE 'CirraTest_%'
SELECT COUNT() FROM Opportunity WHERE Name LIKE 'CirraTest_%'
SELECT COUNT() FROM Case WHERE Subject LIKE 'CirraTest_%'
SELECT COUNT() FROM Lead WHERE LastName LIKE 'CirraTest_%'
SELECT COUNT() FROM Task WHERE Subject LIKE 'CirraTest_%'
SELECT COUNT() FROM Event WHERE Subject LIKE 'CirraTest_%'
```

**Expected:** All counts return 0

---

## Step 2 — Delete Metadata (only if Phase 1b ran)

> If Phase 1b was BLOCKED, skip this step entirely. There is nothing to clean up.

### 2.1 — Delete Apex Classes and Triggers

Query for CirraTest\_ Apex components:

```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name LIKE 'CirraTest_%'",
  fields=["Id", "Name"]
)
```

For each returned class, delete:

```
tooling_api_dml(
  operation="delete",
  sObject="ApexClass",
  record={"Id": "<classId>"}
)
```

Then delete the trigger:

```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="Name LIKE 'CirraTest_%'",
  fields=["Id", "Name"]
)
```

Delete each returned trigger the same way.

**Expected components to find:**

- CirraTest_AccountService (class)
- CirraTest_AccountServiceTest (class)
- CirraTest_AccountTriggerHandler (class)
- CirraTest_AccountTrigger (trigger)
- CirraTest_AccountBatch (class)
- CirraTest_AccountBatchTest (class)
- CirraTest_SmokeCheck (class, from smoke test)
- Associated test classes

> **Note:** Delete test classes first, then handler classes, then triggers.
> Salesforce may reject deleting a class that is referenced by a trigger.

---

### 2.2 — Delete Flows

```
metadata_list(type="Flow")
```

For each Flow with API name matching `CirraTest_%`:

```
metadata_delete(
  type="Flow",
  fullNames=["<FlowApiName>"]
)
```

**Expected flows to find:**

- CirraTest_Account_Create_Task
- CirraTest_Case_Intake_Screen

---

### 2.3 — Delete LWC Components

```
tooling_api_query(
  sObject="LightningComponentBundle",
  whereClause="DeveloperName LIKE 'cirraTest%'",
  fields=["Id", "DeveloperName"]
)
```

For each returned component:

```
metadata_delete(
  type="LightningComponentBundle",
  fullNames=["c/<DeveloperName>"]
)
```

**Expected components to find:**

- cirraTestDashboard
- cirraTestContactCard

---

### 2.4 — Verify metadata cleanup

Re-run the queries from 2.1–2.3 to confirm all CirraTest\_ metadata is gone.

**Expected:** All queries return 0 results.

---

## Step 3 — Clean up local files

Delete any local files created during the audit phase:

```bash
rm -rf ./audit_output/
```

---

## Cleanup Summary

| Category       | Records/Components Deleted | Verified Clean |
| -------------- | -------------------------- | -------------- |
| Tasks          |                            |                |
| Events         |                            |                |
| Cases          |                            |                |
| Opportunities  |                            |                |
| Contacts       |                            |                |
| Leads          |                            |                |
| Accounts       |                            |                |
| Apex Classes   |                            |                |
| Apex Triggers  |                            |                |
| Flows          |                            |                |
| LWC Components |                            |                |
| Local files    |                            |                |
