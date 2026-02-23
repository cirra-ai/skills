# Phase 1b — Metadata Setup

**Purpose:** Create Apex classes, Flows, and Lightning Web Components using the
`/create-apex`, `/create-flow`, and `/create-lwc` commands. This phase exercises
the full metadata deployment pipeline including pre-deployment validation hooks.

---

## Prerequisites

- [ ] 00_smoke_test: TC-001 PASS (MCP connectivity)
- [ ] 00_smoke_test: TC-003 PASS (metadata path — no hook/subprocess errors)
- [ ] Org confirmed connected

> **If TC-003 returned a hook/subprocess error:** This entire phase is BLOCKED.
> Mark all tests below as BLOCKED, record the error from TC-003, and skip to
> Phase 2 (data-only tests).

---

## Required Evidence

- [ ] Deployment confirmation (success/failure) for each component
- [ ] Validation scores from the pre-deployment hook
- [ ] Any error messages verbatim

---

## Apex Tests

### TC-050 — Create a service class

**Command:** `/create-apex` —

```
Type: Service class
Name: CirraTest_AccountService
Purpose: Service class with a method that returns a greeting string for an Account name
Target object: Account
```

**Expected:**

- Class generated with proper ApexDoc, naming conventions
- Pre-deployment validation runs and returns a score (out of 150)
- Class deployed via `tooling_api_dml` insert on ApexClass
- A corresponding test class (`CirraTest_AccountServiceTest`) is also generated and deployed
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field               | Value |
| ------------------- | ----- |
| Status              |       |
| Validation score    |       |
| Class deployed      |       |
| Test class deployed |       |
| Notes               |       |

---

### TC-051 — Create a trigger (non-TAF)

**Command:** `/create-apex` —

```
Type: Trigger
Name: CirraTest_AccountTrigger
Target object: Account
Events: before insert, before update
Purpose: Set Description to "Processed by CirraTest" on insert/update
TAF installed: No (use handler pattern)
```

**Expected:**

- Thin trigger generated that delegates to a handler class (`CirraTest_AccountTriggerHandler`)
- Handler class deployed first, then trigger
- Pre-deployment validation runs for both
- A test class covering the trigger is generated and deployed
  **Known limitation:** If TAF is installed in the org, the command may suggest TAF
  pattern instead. Accept either pattern — the test verifies deployment works.
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field                  | Value |
| ---------------------- | ----- |
| Status                 |       |
| Handler class deployed |       |
| Trigger deployed       |       |
| Test class deployed    |       |
| Validation scores      |       |
| Notes                  |       |

---

### TC-052 — Create a batch class

**Command:** `/create-apex` —

```
Type: Batch
Name: CirraTest_AccountBatch
Purpose: Batch job that updates Account Description to include "Batch processed"
Target object: Account
Special requirements: Schedulable
```

**Expected:**

- Batch class implementing `Database.Batchable<SObject>` and `Schedulable`
- Pre-deployment validation runs
- Class deployed via `tooling_api_dml`
- Test class generated and deployed
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field               | Value |
| ------------------- | ----- |
| Status              |       |
| Validation score    |       |
| Deployed            |       |
| Test class deployed |       |
| Notes               |       |

---

## Flow Tests

### TC-055 — Create a record-triggered flow

**Command:** `/create-flow` —

```
Type: Record-Triggered Flow
Trigger object: Account
Trigger event: After save (create)
Purpose: When a new Account is created, create a default Task assigned to the owner
Flow API name: CirraTest_Account_Create_Task
```

**Expected:**

- Flow XML generated with fault paths, proper element labels
- Pre-deployment validation runs and returns a score (out of 110)
- Flow deployed via `metadata_create`
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field            | Value |
| ---------------- | ----- |
| Status           |       |
| Validation score |       |
| Deployed         |       |
| Notes            |       |

---

### TC-056 — Create a screen flow

**Command:** `/create-flow` —

```
Type: Screen Flow
Purpose: Simple intake form that collects a Case Subject and Description, then creates a Case
Flow API name: CirraTest_Case_Intake_Screen
```

**Expected:**

- Screen flow XML with input screen, Create Records element, and confirmation screen
- Fault paths on DML elements
- Flow deployed successfully
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field            | Value |
| ---------------- | ----- |
| Status           |       |
| Validation score |       |
| Deployed         |       |
| Notes            |       |

---

## LWC Tests

### TC-060 — Create a basic LWC

**Command:** `/create-lwc` —

```
Component name: cirraTestDashboard
Purpose: Display a list of Account names with a search filter
Target placement: App Page
Data source: Apex @wire
Target object: Account
```

**Expected:**

- 4-file bundle generated (html, js, css, js-meta.xml)
- SLDS 2 styling hooks used (no hardcoded colors)
- Pre-deployment validation runs and returns per-file scores (out of 165 each)
- Bundle deployed via `metadata_create` on LightningComponentBundle
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

### TC-061 — Create an LWC for Record Page

**Command:** `/create-lwc` —

```
Component name: cirraTestContactCard
Purpose: Show Contact details with phone and email in a card layout
Target placement: Record Page
Data source: Lightning Data Service (LDS)
Target object: Contact
```

**Expected:**

- Bundle uses `lightning-record-view-form` or similar LDS pattern
- `js-meta.xml` has `lightning__RecordPage` target
- Deployed successfully
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field             | Value |
| ----------------- | ----- |
| Status            |       |
| Validation scores |       |
| Deployed          |       |
| Notes             |       |

---

## Phase 1b Summary

| TC     | Description           | Status |
| ------ | --------------------- | ------ |
| TC-050 | Service class         |        |
| TC-051 | Trigger (non-TAF)     |        |
| TC-052 | Batch class           |        |
| TC-055 | Record-triggered flow |        |
| TC-056 | Screen flow           |        |
| TC-060 | Basic LWC (App Page)  |        |
| TC-061 | LWC for Record Page   |        |

**Components deployed:** **\_** Apex classes/triggers, **\_** Flows, **\_** LWC bundles
