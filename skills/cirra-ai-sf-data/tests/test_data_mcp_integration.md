# Data MCP Integration Test Protocol

Live integration test for SOQL queries and DML operations via Cirra AI MCP Server.
Run interactively in a Claude Code session with MCP access.

## Test Summary (Last Run: 2026-03-06, org: admin@demo2.cirra.ai.dev)

| #   | Test                                          | Result | Details                                              |
| --- | --------------------------------------------- | ------ | ---------------------------------------------------- |
| 1   | Clean pre-existing test artifacts             | PASS   | 0 pre-existing records                               |
| 2   | Describe Account object                       | PASS   | Name, Industry, BillingCity, AnnualRevenue confirmed |
| 3   | Insert 5 test accounts                        | PASS   | 5/5 created                                          |
| 4   | Query inserted accounts (basic)               | PASS   | 5 records with correct values                        |
| 5   | Query with WHERE + ORDER BY + LIMIT           | PASS   | 3 records, correct order (5M, 3M, 2.5M)              |
| 6   | Query with relationship (child-to-parent)     | PASS   | Account.Name = DATATEST_Account_001                  |
| 7   | Query with aggregate (COUNT, GROUP BY)        | PASS   | Tech(2), Healthcare(2), Finance(1)                   |
| 8   | Update records by Id                          | PASS   | 2/2 updated                                          |
| 9   | Verify update                                 | PASS   | Oakland, Brooklyn confirmed                          |
| 10  | Create external ID field for upsert           | PASS   | DATATEST_ExtId\_\_c created                          |
| 11  | Upsert records (insert + update in one call)  | PASS   | 2 created, then 1 updated + 1 created                |
| 12  | Verify upsert results                         | PASS   | EXT-001 updated, EXT-002/003 present                 |
| 13  | Insert with missing required field (negative) | PASS   | REQUIRED_FIELD_MISSING returned                      |
| 14  | Insert with invalid field name (negative)     | PASS   | INVALID_FIELD returned                               |
| 15  | Query with malformed SOQL (negative)          | PASS   | MALFORMED_QUERY returned                             |
| 16  | Pre-flight validator catches missing sObject  | PASS   | Offline validation only (see note)                   |
| 17  | Pre-flight validator catches PII              | PASS   | Offline validation only (see note)                   |
| 18  | Pre-flight validator catches invalid DML op   | PASS   | Offline validation only (see note)                   |
| 19  | Bulk insert 201 records (batch boundary)      | PASS   | Split into 200+1 batches (see Key Insights)          |
| 20  | Query bulk records with pagination            | PASS   | 50 returned with LIMIT 50, COUNT=201                 |
| 21  | Delete bulk records                           | PASS   | 200+1 deleted in 2 batches                           |
| 22  | Cleanup — remove all test artifacts           | PASS   | 0 records remain, custom field deleted               |

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

Generate 201 accounts to cross the 200-record batch boundary.

**Important**: The MCP server enforces a **200-record limit per `sobject_dml` call**.
Attempting to send 201 records in a single call returns `EXCEEDED_ID_LIMIT`.
You MUST split into multiple batches of <= 200 records each.

```
# Batch 1: records 1-200
sobject_dml(
    sObject="Account",
    operation="insert",
    records=[
        {"Name": "DATATEST_Bulk_001", "Industry": "Technology"},
        ... (200 records)
    ]
)

# Batch 2: record 201
sobject_dml(
    sObject="Account",
    operation="insert",
    records=[
        {"Name": "DATATEST_Bulk_201", "Industry": "Technology"}
    ]
)
```

Expected: `success: true` for both batches, 201 total record IDs returned.

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

Delete also requires batching at 200 records. Use `recordIds` (not `records`) for delete.
Use `Id > '<last_id>'` pagination to fetch all IDs.

```
# Batch 1: query first 200 IDs
soql_query(sObject="Account", fields=["Id"],
    whereClause="Name LIKE 'DATATEST_Bulk_%'",
    orderBy="Id ASC", limit=200)

# Delete batch 1 (use recordIds parameter)
sobject_dml(sObject="Account", operation="delete",
    recordIds=["<id1>", "<id2>", ...])

# Batch 2: query remaining IDs
soql_query(sObject="Account", fields=["Id"],
    whereClause="Name LIKE 'DATATEST_Bulk_%'")

# Delete batch 2
sobject_dml(sObject="Account", operation="delete",
    recordIds=["<remaining ids>"])
```

Expected: All 201 records deleted successfully across 2 batches.

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

| Observation                | Expected                             | Actual                    | Notes                                             |
| -------------------------- | ------------------------------------ | ------------------------- | ------------------------------------------------- |
| 201-record insert          | Single call succeeds                 | `EXCEEDED_ID_LIMIT` error | MCP server enforces 200-record max per call       |
| Delete uses `recordIds`    | `records` param with `{"Id": "..."}` | `recordIds` string array  | Different param than insert/update                |
| `soql_query` default limit | Unlimited                            | 100 records               | Must set explicit `limit` or paginate with `Id >` |
| Aggregate queries          | `groupBy` as param                   | Works correctly           | COUNT + GROUP BY returns expected groups          |
| `==` in WHERE clause       | MALFORMED_QUERY                      | MALFORMED_QUERY           | Correctly rejected by Salesforce API              |

## Key Insights from Testing

1. **200-record MCP limit**: `sobject_dml` rejects calls with > 200 records (`EXCEEDED_ID_LIMIT`). Always batch at 200. This applies to insert, update, and delete.
2. **Delete uses `recordIds`**: The `delete` operation uses a `recordIds` string array parameter, not the `records` object array used by insert/update/upsert.
3. **Query pagination**: `soql_query` defaults to 100 records. For bulk queries, use `orderBy="Id ASC"` + `Id > '<last_id>'` pattern to paginate.
4. **Upsert requires `externalIdField`**: Both the MCP validator and the API enforce this. The field must exist and be marked as External ID.
5. **Pre-flight validators are offline-only**: Steps 16-18 test Python validators that run locally before MCP calls. They catch structural errors and PII without consuming API calls.
6. **Relationship queries work**: Child-to-parent dot notation (e.g., `Account.Name` on Contact) works correctly via `soql_query`.
7. **Error messages are clear**: Salesforce returns specific error codes (`REQUIRED_FIELD_MISSING`, `INVALID_FIELD`, `MALFORMED_QUERY`) that can be surfaced directly to users.
