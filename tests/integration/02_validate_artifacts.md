# Phase 2: Validate — Verify All Artifacts

Run after Phase 1 completes. Each step validates artifacts created in Phase 1
using the `/validate-*` and `/query-data` commands.

---

## 2.1 Validate Data — Pre-flight Insert Validation

**Command**: `/validate-data`

**Prompt**: Validate a pre-flight check on this insert operation JSON:

```json
{
  "tool": "sobject_dml",
  "params": {
    "operation": "insert",
    "sObject": "Account",
    "records": [{ "Name": "Validation_Test", "Industry": "Technology", "AnnualRevenue": 5000000 }]
  }
}
```

| Check                        | Expected                                            | Result |
| ---------------------------- | --------------------------------------------------- | ------ |
| Validator runs without error | Yes                                                 |        |
| Tier 1 checks pass           | sObject present, operation valid, records non-empty |        |
| No PII detected              | Yes                                                 |        |
| Output format is report      | Yes                                                 |        |

---

## 2.2 Validate Data — SOQL Syntax Check

**Command**: `/validate-data`

**Prompt**: Validate pre-flight check on this SOQL query:

```json
{
  "tool": "soql_query",
  "params": {
    "query": "SELECT Id, Name, Industry FROM Account WHERE Name LIKE 'CirraTest_%' ORDER BY Name ASC LIMIT 100"
  }
}
```

| Check                      | Expected | Result |
| -------------------------- | -------- | ------ |
| SOQL syntax valid          | Yes      |        |
| No injection warnings      | Yes      |        |
| sf_user or sObject present | Yes      |        |

---

## 2.3 Validate Data — PII Detection

**Command**: `/validate-data`

**Prompt**: Validate pre-flight check on this insert that contains PII-like data:

```json
{
  "tool": "sobject_dml",
  "params": {
    "operation": "insert",
    "sObject": "Contact",
    "records": [
      {
        "LastName": "Smith",
        "Email": "john.smith@gmail.com",
        "Phone": "555-123-4567",
        "Description": "SSN: 123-45-6789"
      }
    ]
  }
}
```

| Check                           | Expected                            | Result |
| ------------------------------- | ----------------------------------- | ------ |
| PII warning raised              | SSN pattern detected in Description |        |
| Warning severity (not blocking) | Warning, not Error                  |        |

---

## 2.4 Query Data — Basic Account Query

**Command**: `/query-data`

**Prompt**: Query all Accounts where Name starts with 'CirraTest*Account*'. Show
Id, Name, Industry, AnnualRevenue, BillingCity.

```
soql_query(query="SELECT Id, Name, Industry, AnnualRevenue, BillingCity FROM Account WHERE Name LIKE 'CirraTest_Account_%' ORDER BY Name ASC")
```

| Check                            | Expected                                               | Result |
| -------------------------------- | ------------------------------------------------------ | ------ |
| Returns 10 records               | Yes                                                    |        |
| Industries match inserted values | Technology, Healthcare, Finance, Manufacturing, Retail |        |
| Revenue matches inserted values  | $500K–$10M range                                       |        |
| BillingCity populated            | Yes                                                    |        |

---

## 2.5 Query Data — Parent-to-Child (Subquery)

**Command**: `/query-data`

**Prompt**: Query Accounts with their related Contacts using a subquery.

```
soql_query(query="SELECT Id, Name, (SELECT Id, FirstName, LastName, Title FROM Contacts) FROM Account WHERE Name LIKE 'CirraTest_Account_%' ORDER BY Name ASC")
```

| Check                              | Expected                   | Result |
| ---------------------------------- | -------------------------- | ------ |
| 10 Account records returned        | Yes                        |        |
| Each Account has 2 Contacts nested | Yes                        |        |
| Contact fields populated           | FirstName, LastName, Title |        |

---

## 2.6 Query Data — Child-to-Parent (Dot Notation)

**Command**: `/query-data`

**Prompt**: Query Contacts with their parent Account name.

```
soql_query(query="SELECT Id, FirstName, LastName, Title, Account.Name, Account.Industry FROM Contact WHERE Account.Name LIKE 'CirraTest_Account_%' ORDER BY Account.Name, LastName")
```

| Check                          | Expected | Result |
| ------------------------------ | -------- | ------ |
| 20 Contact records returned    | Yes      |        |
| Account.Name populated on each | Yes      |        |
| Account.Industry populated     | Yes      |        |

---

## 2.7 Query Data — Aggregate (GROUP BY)

**Command**: `/query-data`

**Prompt**: Get Account count and total AnnualRevenue grouped by Industry.

```
soql_query(query="SELECT Industry, COUNT(Id) numAccounts, SUM(AnnualRevenue) totalRevenue FROM Account WHERE Name LIKE 'CirraTest_Account_%' GROUP BY Industry ORDER BY COUNT(Id) DESC")
```

| Check                         | Expected                                               | Result |
| ----------------------------- | ------------------------------------------------------ | ------ |
| 5 industry groups returned    | Technology, Healthcare, Finance, Manufacturing, Retail |        |
| Counts match (2 per industry) | Yes                                                    |        |
| Revenue sums correct          | Yes                                                    |        |

---

## 2.8 Query Data — Semi-Join (Accounts WITH Opportunities)

**Command**: `/query-data`

```
soql_query(query="SELECT Id, Name FROM Account WHERE Id IN (SELECT AccountId FROM Opportunity WHERE StageName = 'Closed Won') AND Name LIKE 'CirraTest_%'")
```

| Check                                      | Expected | Result |
| ------------------------------------------ | -------- | ------ |
| Returns only Accounts with Closed Won Opps | Yes      |        |
| No Accounts without Closed Won             | Correct  |        |

---

## 2.9 Query Data — Anti-Join (Accounts WITHOUT Cases)

**Command**: `/query-data`

```
soql_query(query="SELECT Id, Name FROM Account WHERE Id NOT IN (SELECT AccountId FROM Case WHERE AccountId != null) AND Name LIKE 'CirraTest_Account_%'")
```

| Check                               | Expected                 | Result |
| ----------------------------------- | ------------------------ | ------ |
| Returns only Accounts without Cases | Yes                      |        |
| Count matches expected              | 5 Accounts without Cases |        |

---

## 2.10 Query Data — Polymorphic (Task Who/What)

**Command**: `/query-data`

```
soql_query(query="SELECT Id, Subject, Who.Name, What.Name, TYPEOF Who WHEN Contact THEN FirstName, LastName, Email WHEN Lead THEN Name, Company END FROM Task WHERE Subject LIKE 'CirraTest_%' LIMIT 20")
```

| Check                                  | Expected | Result |
| -------------------------------------- | -------- | ------ |
| Tasks returned with polymorphic fields | Yes      |        |
| Who resolves to Contact or Lead        | Yes      |        |
| What resolves to Account               | Yes      |        |

---

## 2.11 Query Data — Bulk Records Verification

**Command**: `/query-data`

```
soql_query(query="SELECT COUNT(Id) total FROM Account WHERE Name LIKE 'CirraTest_Bulk_%'")
```

| Check       | Expected | Result |
| ----------- | -------- | ------ |
| Count = 251 | Yes      |        |

---

## 2.12 Query Data — Hierarchy Verification

**Command**: `/query-data`

**Prompt**: Verify the 3-level hierarchy by querying Accounts with their
Contacts, Opportunities, and Cases.

```
soql_query(query="SELECT Name, (SELECT Name, Title FROM Contacts), (SELECT Name, StageName FROM Opportunities), (SELECT Subject, Status FROM Cases) FROM Account WHERE Name LIKE 'CirraTest_Hierarchy_%' ORDER BY Name")
```

| Check                       | Expected | Result |
| --------------------------- | -------- | ------ |
| 5 parent Accounts           | Yes      |        |
| 3 Contacts per Account      | Yes      |        |
| 2 Opportunities per Account | Yes      |        |
| 1 Case per Account          | Yes      |        |

---

## 2.13 Validate Apex — Single Class

**Command**: `/validate-apex CirraTest_AccountService`

| Check                      | Expected              | Result |
| -------------------------- | --------------------- | ------ |
| Class fetched from org     | Via tooling_api_query |        |
| 150-point scoring returned | Yes                   |        |
| Bulkification score        | >= 20/25              |        |
| Security score             | >= 20/25              |        |
| Testing score              | >= 20/25              |        |
| Architecture score         | >= 15/20              |        |
| Clean Code score           | >= 15/20              |        |
| Error Handling score       | >= 10/15              |        |
| Performance score          | >= 7/10               |        |
| Documentation score        | >= 7/10               |        |
| Overall score              | >= 90/150             |        |
| No CRITICAL issues         | Yes                   |        |

---

## 2.14 Validate Apex — Comma-Separated List

**Command**: `/validate-apex CirraTest_AccountService,CirraTest_AccountSelector,CirraTest_AccountRevenueBatch`

| Check                                   | Expected                     | Result |
| --------------------------------------- | ---------------------------- | ------ |
| 3 classes fetched                       | Yes                          |        |
| Summary table generated                 | Name, Type, Score, % columns |        |
| Sorted by score ascending (worst first) | Yes                          |        |
| All scores >= 90/150                    | Yes                          |        |

---

## 2.15 Validate Apex — All Classes (--all)

**Command**: `/validate-apex --all`

| Check                             | Expected            | Result |
| --------------------------------- | ------------------- | ------ |
| All CirraTest\_\* classes fetched | At least 10 classes |        |
| Summary table generated           | Yes                 |        |
| Any below 100/150 (67%) flagged   | Highlighted         |        |
| Execution completes               | No timeout or error |        |

---

## 2.16 Validate Flow — Single Flow

**Command**: `/validate-flow CirraTest_Account_Before_Save`

| Check                           | Expected          | Result |
| ------------------------------- | ----------------- | ------ |
| Flow XML fetched from org       | Via metadata_read |        |
| 110-point scoring returned      | Yes               |        |
| Design & Naming score           | >= 15/20          |        |
| Logic & Structure score         | >= 15/20          |        |
| Architecture score              | >= 12/15          |        |
| Performance & Bulk Safety score | >= 15/20          |        |
| Error Handling score            | >= 15/20          |        |
| Security score                  | >= 12/15          |        |
| Overall score                   | >= 88/110         |        |
| No BLOCK issues                 | Yes               |        |

---

## 2.17 Validate Flow — Comma-Separated List

**Command**: `/validate-flow CirraTest_Account_Before_Save,CirraTest_Opp_After_Save_Task,CirraTest_Case_Intake_Screen`

| Check                     | Expected               | Result |
| ------------------------- | ---------------------- | ------ |
| 3 flows fetched           | Yes                    |        |
| Summary table generated   | Flow, Score, % columns |        |
| Sorted by score ascending | Yes                    |        |
| All scores >= 88/110      | Yes                    |        |

---

## 2.18 Validate Flow — All Flows (--all)

**Command**: `/validate-flow --all`

| Check                           | Expected         | Result |
| ------------------------------- | ---------------- | ------ |
| All CirraTest\_\* flows fetched | At least 6 flows |        |
| Summary table generated         | Yes              |        |
| Any below 88/110 (80%) flagged  | Highlighted      |        |
| Execution completes             | No timeout       |        |

---

## 2.19 Validate LWC — Single Component

**Command**: `/validate-lwc cirraTestAccountDashboard`

| Check                             | Expected                       | Result |
| --------------------------------- | ------------------------------ | ------ |
| Component bundle fetched from org | Via metadata_read              |        |
| Per-file scores returned          | .html, .js, .css, .js-meta.xml |        |
| SLDS class usage score            | >= 20/25                       |        |
| Accessibility score               | >= 20/25                       |        |
| Dark mode score                   | >= 20/25                       |        |
| SLDS migration score              | >= 15/20                       |        |
| Styling hooks score               | >= 15/20                       |        |
| Component structure score         | >= 10/15                       |        |
| Performance score                 | >= 7/10                        |        |
| PICKLES compliance score          | >= 20/25                       |        |
| Overall score                     | >= 100/165                     |        |

---

## 2.20 Validate LWC — Comma-Separated List

**Command**: `/validate-lwc cirraTestAccountDashboard,cirraTestAccountForm,cirraTestConfirmModal`

| Check                     | Expected                    | Result |
| ------------------------- | --------------------------- | ------ |
| 3 components fetched      | Yes                         |        |
| Summary table generated   | Component, Score, % columns |        |
| Sorted by score ascending | Yes                         |        |
| All scores >= 100/165     | Yes                         |        |

---

## 2.21 Validate LWC — All Components (--all)

**Command**: `/validate-lwc --all`

| Check                              | Expected    | Result |
| ---------------------------------- | ----------- | ------ |
| All cirraTest\* components fetched | At least 5  |        |
| Summary table generated            | Yes         |        |
| Any below 100/165 (61%) flagged    | Highlighted |        |
| Execution completes                | No timeout  |        |

---

## Phase 2 Summary

| Validation Type             | Count                        | Expected All Pass        |
| --------------------------- | ---------------------------- | ------------------------ |
| Data pre-flight validations | 3                            | Yes                      |
| SOQL queries executed       | 9                            | All return expected data |
| Apex validations            | 3 runs (single + list + all) | All >= 90/150            |
| Flow validations            | 3 runs (single + list + all) | All >= 88/110            |
| LWC validations             | 3 runs (single + list + all) | All >= 100/165           |
