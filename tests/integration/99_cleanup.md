# Cleanup — Remove All Test Artifacts

Run after all phases complete (or at any point to reset the org). Follows
proper dependency order: children before parents, code after data.

---

## Step 1: Delete Test Data (Dependency Order)

Delete in this order to respect lookup/master-detail relationships:

### 1a. Delete Events

```
soql_query(query="SELECT Id FROM Event WHERE Subject LIKE 'CirraTest_%'")
sobject_dml(operation="delete", sObject="Event", records=[...ids...])
```

### 1b. Delete Tasks

```
soql_query(query="SELECT Id FROM Task WHERE Subject LIKE 'CirraTest_%'")
sobject_dml(operation="delete", sObject="Task", records=[...ids...])
```

### 1c. Delete Cases

```
soql_query(query="SELECT Id FROM Case WHERE Subject LIKE 'CirraTest_%'")
sobject_dml(operation="delete", sObject="Case", records=[...ids...])
```

### 1d. Delete Opportunities

```
soql_query(query="SELECT Id FROM Opportunity WHERE Name LIKE 'CirraTest_%'")
sobject_dml(operation="delete", sObject="Opportunity", records=[...ids...])
```

### 1e. Delete Contacts

```
soql_query(query="SELECT Id FROM Contact WHERE LastName LIKE 'CirraTest_%' OR Account.Name LIKE 'CirraTest_%'")
sobject_dml(operation="delete", sObject="Contact", records=[...ids...])
```

### 1f. Delete Leads

```
soql_query(query="SELECT Id FROM Lead WHERE LastName LIKE 'CirraTest_%' OR Company LIKE 'CirraTest_%'")
sobject_dml(operation="delete", sObject="Lead", records=[...ids...])
```

### 1g. Delete Accounts (parents last)

```
soql_query(query="SELECT Id FROM Account WHERE Name LIKE 'CirraTest_%'")
sobject_dml(operation="delete", sObject="Account", records=[...ids...])
```

| Check                     | Expected                            | Result |
| ------------------------- | ----------------------------------- | ------ |
| All Events deleted        | 0 remaining with CirraTest\_ prefix |        |
| All Tasks deleted         | 0 remaining                         |        |
| All Cases deleted         | 0 remaining                         |        |
| All Opportunities deleted | 0 remaining                         |        |
| All Contacts deleted      | 0 remaining                         |        |
| All Leads deleted         | 0 remaining                         |        |
| All Accounts deleted      | 0 remaining (including 251 bulk)    |        |

---

## Step 2: Delete Bulk Test Data

The 251 bulk-insert records use a different prefix.

```
soql_query(query="SELECT Id FROM Account WHERE Name LIKE 'CirraTest_Bulk_%'")
sobject_dml(operation="delete", sObject="Account", records=[...ids...])
```

```
soql_query(query="SELECT Id FROM Account WHERE Name LIKE 'CirraTest_Hierarchy_%'")
sobject_dml(operation="delete", sObject="Account", records=[...ids...])
```

```
soql_query(query="SELECT Id FROM Account WHERE Name LIKE 'CirraTest_Upsert_%'")
sobject_dml(operation="delete", sObject="Account", records=[...ids...])
```

| Check                      | Expected    | Result |
| -------------------------- | ----------- | ------ |
| Bulk accounts deleted      | 251 removed |        |
| Hierarchy accounts deleted | 5 removed   |        |
| Upsert accounts deleted    | 2 removed   |        |

---

## Step 3: Delete Flows

Delete flows before Apex since flows may reference Apex invocable methods.

```
metadata_delete(type="Flow", fullNames=[
  "CirraTest_Account_Before_Save",
  "CirraTest_Opp_After_Save_Task",
  "CirraTest_Case_Intake_Screen",
  "CirraTest_VIP_Contact_Tasks",
  "CirraTest_Stale_Opp_Cleanup",
  "CirraTest_Order_Event_Handler"
])
```

| Check               | Expected                      | Result |
| ------------------- | ----------------------------- | ------ |
| All 6 flows deleted | No CirraTest\_\* flows remain |        |

### Verify

```
metadata_list(type="Flow")
```

Filter for CirraTest\_ — expect zero results.

---

## Step 4: Delete LWC Components

```
metadata_delete(type="LightningComponentBundle", fullNames=[
  "c/cirraTestAccountDashboard",
  "c/cirraTestAccountForm",
  "c/cirraTestRecordSelector",
  "c/cirraTestConfirmModal",
  "c/cirraTestContactList"
])
```

| Check                    | Expected                         | Result |
| ------------------------ | -------------------------------- | ------ |
| All 5 components deleted | No cirraTest\* components remain |        |

### Verify

```
tooling_api_query(sObject="LightningComponentBundle", whereClause="DeveloperName LIKE 'cirraTest%'")
```

Expect zero results.

---

## Step 5: Delete Apex Classes and Triggers

Delete test classes first (they reference main classes), then main classes,
then triggers.

### 5a. Delete Test Classes

```
tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'CirraTest_%Test'")
```

For each: `tooling_api_dml(operation="delete", sObject="ApexClass", records=[{"Id": "..."}])`

### 5b. Delete Main Classes

```
tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'CirraTest_%' OR Name LIKE 'TA_CirraTest_%'")
```

For each: `tooling_api_dml(operation="delete", sObject="ApexClass", records=[{"Id": "..."}])`

### 5c. Delete Triggers

```
tooling_api_query(sObject="ApexTrigger", whereClause="Name LIKE 'CirraTest_%'")
```

For each: `tooling_api_dml(operation="delete", sObject="ApexTrigger", records=[{"Id": "..."}])`

| Check                    | Expected    | Result |
| ------------------------ | ----------- | ------ |
| All test classes deleted | 0 remaining |        |
| All main classes deleted | 0 remaining |        |
| All triggers deleted     | 0 remaining |        |

### Verify

```
tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'CirraTest_%' OR Name LIKE 'TA_CirraTest_%'")
tooling_api_query(sObject="ApexTrigger", whereClause="Name LIKE 'CirraTest_%'")
```

Both expect zero results.

---

## Step 6: Clean Up Audit Output

```bash
rm -rf ./audit_output/
```

| Check                          | Expected | Result |
| ------------------------------ | -------- | ------ |
| audit_output directory removed | Yes      |        |

---

## Step 7: Final Verification

Run a comprehensive check that nothing CirraTest\_\* remains.

```
soql_query(query="SELECT COUNT(Id) FROM Account WHERE Name LIKE 'CirraTest_%'")
soql_query(query="SELECT COUNT(Id) FROM Contact WHERE LastName LIKE 'CirraTest_%'")
soql_query(query="SELECT COUNT(Id) FROM Opportunity WHERE Name LIKE 'CirraTest_%'")
soql_query(query="SELECT COUNT(Id) FROM Case WHERE Subject LIKE 'CirraTest_%'")
soql_query(query="SELECT COUNT(Id) FROM Lead WHERE LastName LIKE 'CirraTest_%'")
soql_query(query="SELECT COUNT(Id) FROM Task WHERE Subject LIKE 'CirraTest_%'")
soql_query(query="SELECT COUNT(Id) FROM Event WHERE Subject LIKE 'CirraTest_%'")
tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'CirraTest_%' OR Name LIKE 'TA_CirraTest_%'")
tooling_api_query(sObject="ApexTrigger", whereClause="Name LIKE 'CirraTest_%'")
metadata_list(type="Flow")  -- filter for CirraTest_
tooling_api_query(sObject="LightningComponentBundle", whereClause="DeveloperName LIKE 'cirraTest%'")
```

| Object      | Expected Count | Actual Count | Clean? |
| ----------- | -------------- | ------------ | ------ |
| Account     | 0              |              |        |
| Contact     | 0              |              |        |
| Opportunity | 0              |              |        |
| Case        | 0              |              |        |
| Lead        | 0              |              |        |
| Task        | 0              |              |        |
| Event       | 0              |              |        |
| ApexClass   | 0              |              |        |
| ApexTrigger | 0              |              |        |
| Flow        | 0              |              |        |
| LWC         | 0              |              |        |

---

## Cleanup Summary

| Category                | Items Removed                                                 |
| ----------------------- | ------------------------------------------------------------- |
| Data records            | ~400+ (Accounts, Contacts, Opps, Cases, Leads, Tasks, Events) |
| Apex classes + triggers | ~11                                                           |
| Flows                   | 6                                                             |
| LWC components          | 5                                                             |
| Audit output files      | 3 reports + intermediates                                     |
| **Total artifacts**     | **~425+**                                                     |
