# Phase 1a: Setup — Test Data

**Time estimate:** ~30 minutes
**Prerequisite:** Phase 0 smoke tests (TC-001 and TC-002) must PASS.

Run these steps sequentially. Record actual results in the **Result** column.

---

## 1a.1 Initialize MCP Connection

```
cirra_ai_init()
```

| Check                  | Expected                           | Result |
| ---------------------- | ---------------------------------- | ------ |
| Connection established | Success message with org alias     |        |
| Default org confirmed  | User prompted to confirm or select |        |

---

## 1a.2 Describe Target Objects

Verify standard objects exist and discover field metadata before creating data.

```
sobject_describe(sObject="Account")
sobject_describe(sObject="Contact")
sobject_describe(sObject="Opportunity")
sobject_describe(sObject="Case")
sobject_describe(sObject="Lead")
sobject_describe(sObject="Task")
sobject_describe(sObject="Event")
```

| Check                      | Expected                                                             | Result |
| -------------------------- | -------------------------------------------------------------------- | ------ |
| All 7 objects described    | Metadata returned for each                                           |        |
| Required fields identified | Name (Account), LastName (Contact), StageName+CloseDate (Opp), etc. |        |
| Field types confirmed      | Industry=Picklist, AnnualRevenue=Currency, etc.                      |        |

---

## 1a.3 Insert Test Data — Accounts

**Command**: `/insert-data`

**Prompt**: Insert 10 Account records with varied Industries (Technology,
Healthcare, Finance, Manufacturing, Retail), AnnualRevenue ($500K–$10M),
and BillingCity. Use naming pattern CirraTest_Account_001 through _010.

```
sobject_dml(
  operation="insert",
  sObject="Account",
  records=[
    {"Name": "CirraTest_Account_001", "Industry": "Technology", "AnnualRevenue": 5000000, "BillingCity": "San Francisco"},
    {"Name": "CirraTest_Account_002", "Industry": "Healthcare", "AnnualRevenue": 3000000, "BillingCity": "Boston"},
    {"Name": "CirraTest_Account_003", "Industry": "Finance", "AnnualRevenue": 10000000, "BillingCity": "New York"},
    {"Name": "CirraTest_Account_004", "Industry": "Manufacturing", "AnnualRevenue": 2000000, "BillingCity": "Detroit"},
    {"Name": "CirraTest_Account_005", "Industry": "Retail", "AnnualRevenue": 1500000, "BillingCity": "Chicago"},
    {"Name": "CirraTest_Account_006", "Industry": "Technology", "AnnualRevenue": 8000000, "BillingCity": "Seattle"},
    {"Name": "CirraTest_Account_007", "Industry": "Healthcare", "AnnualRevenue": 500000, "BillingCity": "Houston"},
    {"Name": "CirraTest_Account_008", "Industry": "Finance", "AnnualRevenue": 7500000, "BillingCity": "Charlotte"},
    {"Name": "CirraTest_Account_009", "Industry": "Manufacturing", "AnnualRevenue": 4000000, "BillingCity": "Pittsburgh"},
    {"Name": "CirraTest_Account_010", "Industry": "Retail", "AnnualRevenue": 900000, "BillingCity": "Atlanta"}
  ]
)
```

| Check                            | Expected           | Result |
| -------------------------------- | ------------------ | ------ |
| 10 Account IDs returned          | Yes                |        |
| No errors                        | Success for all 10 |        |
| Record IDs saved for later steps | Yes                |        |

---

## 1a.4 Insert Test Data — Contacts

**Command**: `/insert-data`

**Prompt**: Insert 20 Contact records — 2 per Account — with varied Titles
(CEO, CTO, CFO, VP Sales, VP Marketing, Director Engineering, etc.) and Departments.

| Check                                  | Expected             | Result |
| -------------------------------------- | -------------------- | ------ |
| 20 Contact IDs returned                | Yes                  |        |
| Each Contact linked to correct Account | Verify via AccountId |        |
| Varied titles across contacts          | Yes                  |        |

---

## 1a.5 Insert Test Data — Opportunities

**Command**: `/insert-data`

**Prompt**: Insert 15 Opportunity records across the 10 Accounts with varied
Stages (Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost),
Amounts ($30K–$500K), and CloseDates spanning next 6 months.

| Check                       | Expected                    | Result |
| --------------------------- | --------------------------- | ------ |
| 15 Opportunity IDs returned | Yes                         |        |
| Varied stages               | At least 4 different stages |        |
| Future close dates          | Yes                         |        |
| Amounts in expected range   | $30K–$500K                  |        |

---

## 1a.6 Insert Test Data — Cases

**Command**: `/insert-data`

**Prompt**: Insert 10 Case records across 5 Accounts with varied Status (New,
Working, Escalated), Priority (Low, Medium, High), and Type (Question, Problem,
Feature Request).

| Check                           | Expected | Result |
| ------------------------------- | -------- | ------ |
| 10 Case IDs returned            | Yes      |        |
| Linked to Accounts and Contacts | Yes      |        |
| Varied priorities and statuses  | Yes      |        |

---

## 1a.7 Insert Test Data — Leads

**Command**: `/insert-data`

**Prompt**: Insert 10 Lead records with varied LeadSource (Web, Phone, Email,
Partner Referral, Trade Show), Status (Open, Working, Qualified), and Industries.

| Check                | Expected             | Result |
| -------------------- | -------------------- | ------ |
| 10 Lead IDs returned | Yes                  |        |
| Varied lead sources  | At least 4 different |        |
| Varied statuses      | Yes                  |        |

---

## 1a.8 Insert Test Data — Activities (Tasks + Events)

**Command**: `/insert-data`

**Prompt**: Insert 10 Tasks linked to Contacts and Accounts with varied subjects
and statuses. Insert 5 Events linked to Contacts with varied subjects and
durations.

| Check                                                | Expected | Result |
| ---------------------------------------------------- | -------- | ------ |
| 10 Task IDs returned                                 | Yes      |        |
| 5 Event IDs returned                                 | Yes      |        |
| Tasks linked to WhoId (Contact) and WhatId (Account) | Yes      |        |
| Events linked to WhoId (Contact)                     | Yes      |        |

---

## 1a.9 Insert Test Data — Bulk 201+ Records

**Command**: `/insert-data`

**Prompt**: Insert 251 Account records named CirraTest_Bulk_001 through _251
with varied Industries to test the 200-record batch boundary. Use a single
sobject_dml call.

| Check                            | Expected                     | Result |
| -------------------------------- | ---------------------------- | ------ |
| 251 Account IDs returned         | Yes                          |        |
| Single DML call used             | Yes (not 251 separate calls) |        |
| Batch boundary crossed           | Records span 2+ batches      |        |
| All records created successfully | 251 successes                |        |

---

## 1a.10 Insert Test Data — Hierarchy (Account → Contact → Opp → Case)

**Command**: `/insert-data`

**Prompt**: Create a 3-level hierarchy: 5 parent Accounts (named CirraTest_Hierarchy_001
through _005), each with 3 Contacts, 2 Opportunities, and 1 Case. Use the hierarchy
factory pattern.

| Check                            | Expected                             | Result |
| -------------------------------- | ------------------------------------ | ------ |
| 5 Accounts created               | Yes                                  |        |
| 15 Contacts (3 per Account)      | Yes                                  |        |
| 10 Opportunities (2 per Account) | Yes                                  |        |
| 5 Cases (1 per Account)          | Yes                                  |        |
| All relationships valid          | Contacts/Opps/Cases → correct parent |        |

---

## Phase 1a Summary

| Object      | Count | Status |
| ----------- | ----- | ------ |
| Account     | 261+  |        |
| Contact     | 35+   |        |
| Opportunity | 25+   |        |
| Case        | 15+   |        |
| Lead        | 10    |        |
| Task        | 10+   |        |
| Event       | 5+    |        |

**Proceed to Phase 1b** (if TC-003 passed) or **skip to Phase 2 — data tests only** (if TC-003 failed).
