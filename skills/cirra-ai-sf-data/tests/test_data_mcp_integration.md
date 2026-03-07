# Data MCP Integration Test Protocol

Live integration test for SOQL queries and DML operations via Cirra AI MCP Server.
Run interactively in a Claude Code session with MCP access.

## Test Summary (Last Run: _not yet run_)

| #   | Test                                             | Result  | Details |
| --- | ------------------------------------------------ | ------- | ------- |
| 1   | Clean pre-existing test artifacts                | PENDING |         |
| 2   | Describe Account object                          | PENDING |         |
| 3   | Insert 5 test accounts                           | PENDING |         |
| 4   | Query inserted accounts (basic)                  | PENDING |         |
| 5   | Query with WHERE + ORDER BY + LIMIT              | PENDING |         |
| 6   | Query with relationship (child-to-parent)        | PENDING |         |
| 7   | Query with aggregate (COUNT, GROUP BY)           | PENDING |         |
| 8   | Update records by Id                             | PENDING |         |
| 9   | Verify update                                    | PENDING |         |
| 10  | Create external ID field for upsert              | PENDING |         |
| 11  | Upsert records (insert + update in one call)     | PENDING |         |
| 12  | Verify upsert results                            | PENDING |         |
| 13  | Insert with missing required field (negative)    | PENDING |         |
| 14  | Insert with invalid field name (negative)        | PENDING |         |
| 15  | Query with malformed SOQL (negative)             | PENDING |         |
| 16  | Pre-flight validator catches missing sObject      | PENDING |         |
| 17  | Pre-flight validator catches PII                 | PENDING |         |
| 18  | Pre-flight validator catches invalid DML op      | PENDING |         |
| 19  | Bulk insert 201 records (batch boundary)         | PENDING |         |
| 20  | Query bulk records with pagination               | PENDING |         |
| 21  | Delete bulk records                              | PENDING |         |
| 22  | Cleanup — remove all test artifacts              | PENDING |         |

## Prerequisites

- Cirra AI MCP Server connected to a Salesforce sandbox
- `cirra_ai_init()` called in current session

## Step 1: Clean Slate — Remove Pre-Existing Test Artifacts

```
soql_query(sObject="Account", fields=["Id"],
    whereClause="Name LIKE 'DATATEST_%'")
# Expected: 0 records (or delete any found via sobject_dml delete)

tooling_api_query(sObject="CustomField", fields=["Id", "DeveloperName", "TableEnumOrId"],
    whereClause="DeveloperName = 'DATATEST_ExtId' AND TableEnumOrId = 'Account'")
# Expected: 0 records (or delete via metadata_delete)
```

## Step 2: Describe Account Object

Verify we can read object metadata before inserting records.

```
sobject_describe(sObject="Account")
```

Expected:
- Returns field list including Name, Industry, BillingCity, AnnualRevenue
- Response includes field types, required flags, and relationship metadata

## Step 3: Insert 5 Test Accounts

```
sobject_dml(
    sObject="Account",
    operation="insert",
    records=[
        {"Name": "DATATEST_Account_001", "Industry": "Technology", "BillingCity": "San Francisco", "AnnualRevenue": 1000000},
        {"Name": "DATATEST_Account_002", "Industry": "Healthcare", "BillingCity": "New York", "AnnualRevenue": 2500000},
        {"Name": "DATATEST_Account_003", "Industry": "Finance", "BillingCity": "Chicago", "AnnualRevenue": 5000000},
        {"Name": "DATATEST_Account_004", "Industry": "Technology", "BillingCity": "Seattle", "AnnualRevenue": 750000},
        {"Name": "DATATEST_Account_005", "Industry": "Healthcare", "BillingCity": "Boston", "AnnualRevenue": 3000000}
    ]
)
```

Expected: `success: true`, 5 record IDs returned. Save IDs for later steps.

## Step 4: Query Inserted Accounts (Basic)

```
soql_query(
    sObject="Account",
    fields=["Id", "Name", "Industry", "BillingCity", "AnnualRevenue"],
    whereClause="Name LIKE 'DATATEST_%'"
)
```

Expected: 5 records returned with correct field values.

## Step 5: Query with WHERE + ORDER BY + LIMIT

```
soql_query(
    sObject="Account",
    fields=["Id", "Name", "AnnualRevenue"],
    whereClause="Name LIKE 'DATATEST_%' AND AnnualRevenue > 1000000",
    orderBy="AnnualRevenue DESC",
    limit=3
)
```

Expected:
- 3 records returned (out of 4 matching the WHERE)
- Ordered by AnnualRevenue descending: Finance (5M), Healthcare Boston (3M), Healthcare NY (2.5M)

## Step 6: Query with Relationship (Child-to-Parent)

First, insert a Contact linked to one of the test accounts:

```
sobject_dml(
    sObject="Contact",
    operation="insert",
    records=[
        {"FirstName": "DATATEST", "LastName": "Contact_001", "AccountId": "<DATATEST_Account_001 Id>", "Email": "datatest@example.com"}
    ]
)
```

Then query with relationship traversal:

```
soql_query(
    sObject="Contact",
    fields=["Id", "FirstName", "LastName", "Account.Name", "Account.Industry"],
    whereClause="LastName = 'Contact_001' AND FirstName = 'DATATEST'"
)
```

Expected: 1 record with `Account.Name = "DATATEST_Account_001"` and `Account.Industry = "Technology"`.

## Step 7: Query with Aggregate (COUNT, GROUP BY)

```
soql_query(
    sObject="Account",
    fields=["Industry", "COUNT(Id)"],
    whereClause="Name LIKE 'DATATEST_%'",
    groupBy="Industry"
)
```

Expected: 3 groups — Technology (2), Healthcare (2), Finance (1).

## Step 8: Update Records by Id

Update two accounts' BillingCity:

```
sobject_dml(
    sObject="Account",
    operation="update",
    records=[
        {"Id": "<DATATEST_Account_001 Id>", "BillingCity": "Oakland"},
        {"Id": "<DATATEST_Account_002 Id>", "BillingCity": "Brooklyn"}
    ]
)
```

Expected: `success: true`, 2 records updated.

## Step 9: Verify Update

```
soql_query(
    sObject="Account",
    fields=["Id", "Name", "BillingCity"],
    whereClause="Name IN ('DATATEST_Account_001', 'DATATEST_Account_002')"
)
```

Expected: Account_001 BillingCity = "Oakland", Account_002 BillingCity = "Brooklyn".

## Step 10: Create External ID Field for Upsert

```
sobject_field_create(
    sObject="Account",
    fieldName="DATATEST_ExtId__c",
    fieldType="Text",
    label="DATATEST External Id",
    description="Test external ID field for data integration tests. Safe to delete.",
    defaultFLS="Editable",
    properties={"length": 50, "externalId": true, "unique": true}
)
```

Expected: Field created successfully.

## Step 11: Upsert Records (Insert + Update in One Call)

```
sobject_dml(
    sObject="Account",
    operation="upsert",
    externalIdField="DATATEST_ExtId__c",
    records=[
        {"DATATEST_ExtId__c": "EXT-001", "Name": "DATATEST_Upsert_New", "Industry": "Energy"},
        {"DATATEST_ExtId__c": "EXT-002", "Name": "DATATEST_Upsert_New_2", "Industry": "Retail"}
    ]
)
```

Expected: 2 records created (new external IDs).

Then upsert again with one existing and one new:

```
sobject_dml(
    sObject="Account",
    operation="upsert",
    externalIdField="DATATEST_ExtId__c",
    records=[
        {"DATATEST_ExtId__c": "EXT-001", "Name": "DATATEST_Upsert_Updated", "Industry": "Energy"},
        {"DATATEST_ExtId__c": "EXT-003", "Name": "DATATEST_Upsert_New_3", "Industry": "Media"}
    ]
)
```

Expected: EXT-001 updated (name changed), EXT-003 created.

## Step 12: Verify Upsert Results

```
soql_query(
    sObject="Account",
    fields=["Id", "Name", "DATATEST_ExtId__c", "Industry"],
    whereClause="DATATEST_ExtId__c != null",
    orderBy="DATATEST_ExtId__c ASC"
)
```

Expected:
- EXT-001: Name = "DATATEST_Upsert_Updated", Industry = "Energy"
- EXT-002: Name = "DATATEST_Upsert_New_2", Industry = "Retail"
- EXT-003: Name = "DATATEST_Upsert_New_3", Industry = "Media"

## Step 13: Insert with Missing Required Field (Negative)

```
sobject_dml(
    sObject="Account",
    operation="insert",
    records=[
        {"Industry": "Technology"}
    ]
)
```

Expected: API error — `REQUIRED_FIELD_MISSING` (Account.Name is required).

## Step 14: Insert with Invalid Field Name (Negative)

```
sobject_dml(
    sObject="Account",
    operation="insert",
    records=[
        {"Name": "DATATEST_Bad_Field", "NonExistentField__c": "value"}
    ]
)
```

Expected: API error — `INVALID_FIELD` or similar.

## Step 15: Query with Malformed SOQL (Negative)

```
soql_query(
    sObject="Account",
    fields=["Id", "Name"],
    whereClause="Name == 'test'"
)
```

Expected: API error — `MALFORMED_QUERY` (SOQL uses `=`, not `==`).

**Key insight**: The pre-flight validator (`MCPDataValidator`) catches `==` as a WARNING
before the call reaches the org, preventing wasted API calls.

## Step 16: Pre-Flight Validator — Missing sObject

Run locally (no org call needed):

```python
from mcp_validator import MCPDataValidator
result = MCPDataValidator().validate({
    "tool": "soql_query",
    "params": {"orderBy": "", "groupBy": ""}
})
```

Expected: `status: "fail"`, error message includes "sObject".

## Step 17: Pre-Flight Validator — PII Detection

```python
from mcp_validator import MCPDataValidator
result = MCPDataValidator().validate({
    "tool": "sobject_dml",
    "params": {
        "sObject": "Contact",
        "operation": "insert",
        "records": [
            {"LastName": "Test", "SSN__c": "123-45-6789"}
        ]
    }
})
```

Expected: `status: "pass"` (PII is a warning, not a blocking error), but warnings include "SSN pattern detected".

**Key insight**: PII detection warns before data reaches the org, giving the user a chance to
use synthetic data instead.

## Step 18: Pre-Flight Validator — Invalid DML Operation

```python
from mcp_validator import MCPDataValidator
result = MCPDataValidator().validate({
    "tool": "sobject_dml",
    "params": {
        "sObject": "Account",
        "operation": "merge",
        "records": [{"Name": "Test"}]
    }
})
```

Expected: `status: "fail"`, error message includes "operation" and lists valid operations.

## Step 19: Bulk Insert 201 Records (Batch Boundary)

Generate 201 accounts to cross the 200-record batch boundary:

```
sobject_dml(
    sObject="Account",
    operation="insert",
    records=[
        {"Name": "DATATEST_Bulk_001", "Industry": "Technology"},
        {"Name": "DATATEST_Bulk_002", "Industry": "Technology"},
        ... (201 records total)
    ]
)
```

Expected: `success: true`, 201 record IDs returned. Salesforce processes these in
two batches (200 + 1) internally.

## Step 20: Query Bulk Records with Pagination

```
soql_query(
    sObject="Account",
    fields=["Id", "Name"],
    whereClause="Name LIKE 'DATATEST_Bulk_%'",
    orderBy="Name ASC",
    limit=50
)
```

Expected: First 50 records returned, ordered alphabetically.

Then query the count:

```
soql_query(
    sObject="Account",
    fields=["COUNT(Id)"],
    whereClause="Name LIKE 'DATATEST_Bulk_%'"
)
```

Expected: COUNT = 201.

## Step 21: Delete Bulk Records

```
# First query all IDs
soql_query(
    sObject="Account",
    fields=["Id"],
    whereClause="Name LIKE 'DATATEST_Bulk_%'"
)

# Then delete (may need batching if > 200)
sobject_dml(
    sObject="Account",
    operation="delete",
    records=[{"Id": "<id1>"}, {"Id": "<id2>"}, ...]
)
```

Expected: All 201 records deleted successfully.

## Step 22: Cleanup — Remove All Test Artifacts

Delete test records and the test field. Offer to the user, don't auto-clean.

```
# Delete test contacts first (child records)
soql_query(sObject="Contact", fields=["Id"],
    whereClause="FirstName = 'DATATEST'")
sobject_dml(sObject="Contact", operation="delete",
    records=[{"Id": "<contact ids>"}])

# Delete upsert test accounts
soql_query(sObject="Account", fields=["Id"],
    whereClause="DATATEST_ExtId__c != null")
sobject_dml(sObject="Account", operation="delete",
    records=[{"Id": "<upsert account ids>"}])

# Delete remaining test accounts
soql_query(sObject="Account", fields=["Id"],
    whereClause="Name LIKE 'DATATEST_%'")
sobject_dml(sObject="Account", operation="delete",
    records=[{"Id": "<account ids>"}])

# Delete test external ID field
metadata_delete(type="CustomField", fullNames=["Account.DATATEST_ExtId__c"])
```

## Error Handling Observations

Document any unexpected behaviors found during testing:

| Observation | Expected | Actual | Notes |
| ----------- | -------- | ------ | ----- |
|             |          |        |       |

## Key Insights from Testing

Document findings that should inform the skill's documentation or validator:

1. _To be filled after running tests_
