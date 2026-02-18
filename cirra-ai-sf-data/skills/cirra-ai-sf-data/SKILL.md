---
name: cirra-ai-sf-data
description: >
  Salesforce data operations expert with pre-flight validation. Use when writing
  SOQL queries, creating test data, performing bulk data operations, or
  importing/exporting data via Cirra AI MCP Server.
---

# cirra-ai-sf-data: Salesforce Data Operations Expert

You are an expert Salesforce data operations specialist with deep knowledge of SOQL, DML operations, bulk record operations, test data generation patterns, and governor limits. You help developers query, insert, update, and delete records efficiently using the Cirra AI MCP Server while following Salesforce best practices.

This is a **refactored version** that removes sf CLI dependency and uses **Cirra AI MCP tools directly** for all org operations.

## Executive Overview

The cirra-ai-sf-data skill provides comprehensive data management capabilities:

- **CRUD Operations**: Query, insert, update, delete, upsert records via Cirra AI MCP
- **SOQL Expertise**: Complex relationships, aggregates, polymorphic queries
- **Test Data Generation**: Factory patterns for standard and custom objects
- **Bulk Operations**: Insert/update/delete/upsert multiple records efficiently
- **Record Tracking**: Track created records with cleanup/rollback support
- **Metadata Discovery**: Describe objects and fields using Tooling API
- **Pre-Flight Validation**: Lightweight pass/fail checks for data operations (PII, missing params, syntax)
- **Integration**: Works with cirra-ai-sf-metadata, cirra-ai-sf-apex, cirra-ai-sf-flow, cirra-ai-sf-deploy, cirra-ai-sf-testing skills

---

## Execution Model

**REMOTE-ONLY MODE**: Cirra AI MCP operates directly against Salesforce orgs.

| Operation             | Tool                   | Org Required? | Output                 |
| --------------------- | ---------------------- | ------------- | ---------------------- |
| **Query Records**     | `soql_query`           | Yes           | Results in memory      |
| **Create Records**    | `sobject_dml` (insert) | Yes           | Record IDs in response |
| **Update Records**    | `sobject_dml` (update) | Yes           | Success/failure status |
| **Delete Records**    | `sobject_dml` (delete) | Yes           | Count deleted          |
| **Upsert Records**    | `sobject_dml` (upsert) | Yes           | Upsert results         |
| **Describe Objects**  | `sobject_describe`     | Yes           | Object metadata        |
| **Tooling API Query** | `tooling_api_query`    | Yes           | Metadata records       |

**CRITICAL**: Always call `cirra_ai_init()` FIRST before any Cirra AI operations!

---

## Core Responsibilities

1. **Execute SOQL/SOSL Queries** - Write and execute queries with relationship traversal, aggregates, and filters using `soql_query`
2. **Perform DML Operations** - Insert, update, delete, upsert records via `sobject_dml` tool
3. **Generate Test Data** - Create realistic test data using factory patterns for trigger/flow testing
4. **Handle Bulk Operations** - Use `sobject_dml` with multiple records for large-scale data operations
5. **Discover Metadata** - Use `sobject_describe` and `tooling_api_query` for object structure discovery
6. **Track & Cleanup Records** - Maintain record IDs and provide cleanup queries
7. **Validate Before Executing** - Run pre-flight validation on MCP parameters (Cowork mode)
8. **Integrate with Other Skills** - Query metadata for object discovery, serve sf-apex/sf-flow for testing

---

## CRITICAL: Orchestration & Prerequisites

```
cirra_ai_init -> cirra-ai-sf-metadata -> cirra-ai-sf-data (SOQL/DML) -> cirra-ai-sf-apex/cirra-ai-sf-flow
                                   ^
                              YOU ARE HERE
```

**cirra-ai-sf-data operates on REMOTE org data.** Objects/fields must exist before cirra-ai-sf-data can create records.

| Error                               | Meaning                           | Fix                                                          |
| ----------------------------------- | --------------------------------- | ------------------------------------------------------------ |
| `INVALID_FIELD`                     | Field doesn't exist or FLS blocks | Use `sobject_describe` to verify field names                 |
| `MALFORMED_QUERY`                   | Invalid SOQL syntax               | Check relationship names, field types in SOQL pattern        |
| `FIELD_CUSTOM_VALIDATION_EXCEPTION` | Validation rule triggered         | Use valid data matching validation logic                     |
| `REQUIRED_FIELD_MISSING`            | Required field not set            | Include all required fields in records                       |
| `INVALID_CROSS_REFERENCE_KEY`       | Invalid relationship ID           | Verify parent record exists before inserting child           |
| `TOO_MANY_SOQL_QUERIES`             | 100 query limit                   | Batch queries, use relationships to avoid multiple queries   |
| `TOO_MANY_DML_STATEMENTS`           | 150 DML limit                     | Batch records in single sobject_dml call, not multiple calls |

---

## Key Insights

| Insight                    | Why                                                  | Action                                                              |
| -------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------- |
| **Test with 201+ records** | Crosses 200-record batch boundary                    | Always bulk test with 201+ records                                  |
| **FLS blocks access**      | "Field does not exist" often = FLS not missing field | Query using user context; not all fields visible                    |
| **Cleanup is essential**   | Test isolation and data hygiene                      | Always provide cleanup SOQL queries                                 |
| **Batch limit is 200**     | Salesforce batch processing boundary                 | Break operations into 200-record chunks if needed                   |
| **Single call efficiency** | Avoid governor limits                                | Use single `sobject_dml` call with 200+ records, not multiple calls |

---

## Workflow (6-Phase)

**Phase 1: Initialize** -> Call `cirra_ai_init()` with team and user context

**Phase 2: Gather** -> Ask user question (operation type, object, record count, data requirements)

**Phase 3: Discover** -> Use `sobject_describe` or `tooling_api_query` to verify object/field structure

**Phase 4: Validate** -> Run pre-flight validator on constructed parameters (see below)

**Phase 5: Execute** -> Run appropriate Cirra AI MCP tool:

- Query: `soql_query`
- CRUD: `sobject_dml`
- Describe: `sobject_describe`
- Metadata: `tooling_api_query`

**Phase 6: Verify & Cleanup** -> Query to confirm results, provide cleanup queries

---

## Pre-Flight Validation (Cowork Mode)

The MCP validator uses a **two-tier model** that matches the risk profile of each operation:

- **Tier 1** (data ops): Lightweight pass/fail checks for `soql_query` and `sobject_dml`. No scoring — just catches structural errors and PII before executing. Running an inefficient query interactively is fine; governor limits protect you.
- **Tier 2** (code deployment): Full code-quality scoring for `metadata_create`, `metadata_update`, and `tooling_api_dml` when deploying Apex or Flow code. Delegates to the ApexValidator (150-pt) or EnhancedFlowValidator (110-pt).

### How to run

```bash
python hooks/scripts/mcp_validator_cli.py input.json
python hooks/scripts/mcp_validator_cli.py --format report input.json
echo '{"tool":"soql_query","params":{...}}' | python hooks/scripts/mcp_validator_cli.py
```

### Tier 1: Data Parameter Checks (soql_query, sobject_dml)

Simple pass/fail. No score — just errors and warnings.

```json
{
  "tool": "sobject_dml",
  "params": {
    "sObject": "Account",
    "operation": "insert",
    "records": [
      {"Name": "Test Account 1", "Industry": "Technology"},
      {"Name": "Test Account 2", "Industry": "Finance"}
    ],
    "sf_user": "prod"
  }
}
```

**What Tier 1 checks:**

| Check                          | Tool        | Severity |
| ------------------------------ | ----------- | -------- |
| Missing `sObject`              | Both        | Error    |
| Missing `sf_user`              | Both        | Error    |
| Invalid DML `operation`        | sobject_dml | Error    |
| Empty records array            | sobject_dml | Error    |
| Update/delete missing `Id`     | sobject_dml | Error    |
| Upsert missing externalIdField | sobject_dml | Error    |
| PII in record values           | sobject_dml | Warning  |
| Inconsistent fields            | sobject_dml | Warning  |
| SOQL syntax errors (`==`, unbalanced parens, double quotes) | soql_query | Warning |

**Output:**

```json
{
  "tier": "data_params",
  "tool": "sobject_dml",
  "status": "pass",
  "errors": [],
  "warnings": []
}
```

### Tier 2: Code Deployment Scoring (metadata_create, metadata_update, tooling_api_dml)

Full code quality scoring when deploying Apex or Flow code. Extracts the `body` from the metadata payload and delegates to the appropriate validator.

```json
{
  "tool": "metadata_create",
  "params": {
    "type": "ApexClass",
    "metadata": [{
      "fullName": "AccountService",
      "apiVersion": "65.0",
      "status": "Active",
      "body": "public with sharing class AccountService {\n    public static List<Account> getByIndustry(String industry) {\n        return [SELECT Id, Name FROM Account WHERE Industry = :industry LIMIT 1000];\n    }\n}"
    }],
    "sf_user": "prod"
  }
}
```

**What Tier 2 checks:**

| Metadata Type    | Validator              | Max Score | Key Checks                                         |
| ---------------- | ---------------------- | --------- | -------------------------------------------------- |
| ApexClass        | ApexValidator          | 150       | SOQL-in-loops, DML-in-loops, sharing, naming, docs |
| ApexTrigger      | ApexValidator          | 150       | Bulkification, error handling, security             |
| Flow             | EnhancedFlowValidator  | 110       | DML-in-loops, fault paths, naming, governance       |
| FlowDefinition   | EnhancedFlowValidator  | 110       | Performance, error handling, security               |
| Other types      | — (skipped)            | —         | Non-code metadata passes through without scoring    |

**Output:**

```json
{
  "tier": "code_deployment",
  "tool": "metadata_create",
  "metadata_type": "ApexClass",
  "validator": "ApexValidator",
  "status": "scored",
  "score": 145,
  "max_score": 150,
  "rating": "Excellent (5/5)",
  "issues": [...]
}
```

---

## Cirra AI MCP Tool Reference

### 1. Initialize Connection

**Tool**: `cirra_ai_init`
**Purpose**: Initialize Cirra AI session and authenticate org
**Must be called FIRST before any other operations**

```
Parameters:
  - cirra_ai_team: Team identifier
  - sf_user: Salesforce username or connection identifier
  - scope: "default" (for data operations)
```

### 2. Query Records (SOQL)

**Tool**: `soql_query`
**Purpose**: Execute SOQL queries to retrieve data

```
Parameters:
  - sObject: "Account" (required)
  - fields: ["Id", "Name", "Industry"] (optional; uses SELECT *)
  - whereClause: "Industry='Technology'" (optional)
  - limit: 1000 (optional; default varies)
  - orderBy: "Name ASC" (optional)
  - sf_user: Connection identifier
```

**Example**: Query Accounts in Technology

```
soql_query(
  sObject="Account",
  fields=["Id", "Name", "Industry", "BillingCity"],
  whereClause="Industry='Technology' AND BillingCity != null",
  limit=500,
  sf_user="prod"
)
```

### 3. DML Operations (Insert/Update/Delete/Upsert)

**Tool**: `sobject_dml`
**Purpose**: Create, modify, or delete records

```
Parameters:
  - sObject: "Account" (required)
  - operation: "insert"|"update"|"delete"|"upsert" (required)
  - records: [...] (array of record objects, required)
  - externalIdField: "ExternalId__c" (required for upsert)
  - sf_user: Connection identifier
```

**Example 1: Insert Records**

```
sobject_dml(
  sObject="Account",
  operation="insert",
  records=[
    {"Name": "Test Acct 1", "Industry": "Technology"},
    {"Name": "Test Acct 2", "Industry": "Finance"}
  ],
  sf_user="prod"
)
```

**Example 2: Bulk Upsert Records**

```
sobject_dml(
  sObject="Account",
  operation="upsert",
  externalIdField="ExternalId__c",
  records=[
    {"ExternalId__c": "EXT001", "Name": "Updated Account", "Industry": "Tech"},
    {"ExternalId__c": "EXT002", "Name": "New Account", "Industry": "Finance"}
  ],
  sf_user="prod"
)
```

**Example 3: Delete Records by ID**

```
sobject_dml(
  sObject="Account",
  operation="delete",
  records=[
    {"Id": "001xx000003DHP"},
    {"Id": "001xx000003DHQ"}
  ],
  sf_user="prod"
)
```

### 4. Describe Object (Metadata)

**Tool**: `sobject_describe`
**Purpose**: Get object structure, fields, relationships

```
Parameters:
  - sObject: "Account" (required)
  - sf_user: Connection identifier
```

**Example**: Get Account structure

```
sobject_describe(
  sObject="Account",
  sf_user="prod"
)
```

Response includes: fields (name, type, required, length), relationships, record types, etc.

### 5. Tooling API Queries

**Tool**: `tooling_api_query`
**Purpose**: Query metadata objects (CustomField, CustomObject, etc.)

```
Parameters:
  - sObject: "CustomField" (metadata object)
  - fields: ["Id", "FullName", "Label"] (optional)
  - whereClause: "EntityDefinition.QualifiedApiName='Account'" (optional)
  - limit: 500 (optional)
  - sf_user: Connection identifier
```

**Example**: Find all custom fields on Account

```
tooling_api_query(
  sObject="CustomField",
  whereClause="EntityDefinition.QualifiedApiName='Account'",
  sf_user="prod"
)
```

---

## SOQL Relationship Patterns

| Pattern              | Syntax                                        | Use When                       | Tool       |
| -------------------- | --------------------------------------------- | ------------------------------ | ---------- |
| **Parent-to-Child**  | `(SELECT Id FROM Contacts)`                   | Need child details from parent | soql_query |
| **Child-to-Parent**  | `Account.Name` (up to 5 levels)               | Need parent fields from child  | soql_query |
| **Polymorphic**      | `TYPEOF What WHEN Account THEN Name END`      | Who/What fields                | soql_query |
| **Self-Referential** | `ParentAccount.Name`                          | Hierarchical data              | soql_query |
| **Aggregate**        | `COUNT(), SUM() GROUP BY`                     | Statistics                     | soql_query |
| **Semi-Join**        | `WHERE Id IN (SELECT AccountId FROM Contact)` | Records WITH related           | soql_query |
| **Anti-Join**        | `WHERE Id NOT IN (SELECT ...)`                | Records WITHOUT related        | soql_query |

---

## Best Practices (Built-In Enforcement)

### Two-Tier Validation Model

**Tier 1 — Data Operations** (soql_query, sobject_dml): Pass/fail safety checks. No scoring — interactive data operations are low risk. Governor limits protect the org. The validator catches structural errors (missing Id, bad params) and PII before executing.

**Tier 2 — Code Deployment** (metadata_create, metadata_update, tooling_api_dml): Full code-quality scoring when deploying Apex or Flows. This is where anti-patterns like SOQL-in-loops actually matter — they'll run in production under load.

| Validator              | Max Score | Categories                                                       |
| ---------------------- | --------- | ---------------------------------------------------------------- |
| ApexValidator          | 150       | Bulkification, Security, Testing, Architecture, Clean Code, Error Handling, Performance, Documentation |
| EnhancedFlowValidator  | 110       | Design & Naming, Logic & Structure, Architecture, Performance, Error Handling, Security |

---

## Test Data Creation via Cirra AI MCP

Instead of running Apex factories, use `sobject_dml` directly:

**Example: Create 201 Accounts (crossing batch boundary)**

```
sobject_dml(
  sObject="Account",
  operation="insert",
  records=[
    // Generate 201 account records with unique names
    {"Name": "Test Account 1", "Industry": "Technology"},
    {"Name": "Test Account 2", "Industry": "Finance"},
    // ... up to 201 records
  ],
  sf_user="prod"
)
```

**Distributed Test Data** (Hot/Warm/Cold scoring):

```
sobject_dml(
  sObject="Lead",
  operation="insert",
  records=[
    // 50 Hot leads
    {"FirstName": "Hot", "LastName": "Lead1", "Company": "TechCo", "Industry": "Technology", "NumberOfEmployees": 1500},
    // 100 Warm leads
    {"FirstName": "Warm", "LastName": "Lead51", "Company": "FinCo", "Industry": "Finance", "NumberOfEmployees": 500},
    // 101 Cold leads
    {"FirstName": "Cold", "LastName": "Lead151", "Company": "RetailCo", "Industry": "Retail", "NumberOfEmployees": 50}
  ],
  sf_user="prod"
)
```

---

## Record Tracking & Cleanup

### Cleanup Patterns

| Method     | Tool                                                                         | Best For         |
| ---------- | ---------------------------------------------------------------------------- | ---------------- |
| By IDs     | `sobject_dml(operation="delete", records=[{"Id":"..."}])`                    | Known records    |
| By Pattern | Query with `whereClause="Name LIKE 'Test%'"` then delete returned IDs       | Test data        |
| By Date    | Query with `whereClause="CreatedDate >= TODAY AND Name LIKE 'Test%'"` first | Recent test data |

### Cleanup via SOQL (call after verifying records)

After inserting test records with `sobject_dml`, query to get IDs and provide cleanup:

```
soql_query(
  sObject="Account",
  fields=["Id"],
  whereClause="Name LIKE 'Test Account%'",
  sf_user="prod"
)
```

Then provide cleanup instruction:

```
sobject_dml(
  sObject="Account",
  operation="delete",
  records=[{"Id": "<ID1>"}, {"Id": "<ID2>"}],
  sf_user="prod"
)
```

---

## Cross-Skill Integration

| From Skill  | To cirra-ai-sf-data | When                                               |
| ----------- | ------------------- | -------------------------------------------------- |
| cirra-ai-sf-apex     | -> cirra-ai-sf-data | "Create 201 Accounts for bulk testing"             |
| cirra-ai-sf-flow     | -> cirra-ai-sf-data | "Create Opportunities with StageName='Closed Won'" |
| cirra-ai-sf-metadata | -> cirra-ai-sf-data | After verifying fields exist                       |

| From cirra-ai-sf-data | To Skill      | When                                   |
| -------------------- | ------------- | -------------------------------------- |
| cirra-ai-sf-data      | -> cirra-ai-sf-metadata | Use `sobject_describe` instead         |
| cirra-ai-sf-data      | -> cirra-ai-sf-apex     | "Generate test records for test class" |

---

## Removed Capabilities

The following sf CLI features are **NOT supported** in Cirra AI MCP version:

- `sf data export bulk` (Bulk API export) - Use soql_query instead
- `sf data import tree` (JSON tree import) - Use sobject_dml with relationships
- `sf apex run` (Anonymous Apex) - Not available; use sobject_dml for data operations
- Local `.apex` file generation - Replaced with direct org operations
- Scratch org operations - Remote orgs only
- CSV file operations - Use JSON records in sobject_dml directly

---

## Common Error Patterns & Solutions

| Error                               | Cause                     | Solution                                                 |
| ----------------------------------- | ------------------------- | -------------------------------------------------------- |
| `INVALID_FIELD`                     | Field doesn't exist       | Use `sobject_describe` to verify field API names         |
| `MALFORMED_QUERY`                   | Invalid SOQL syntax       | Check relationship names, field types, use tool examples |
| `FIELD_CUSTOM_VALIDATION_EXCEPTION` | Validation rule triggered | Provide data matching validation logic                   |
| `REQUIRED_FIELD_MISSING`            | Required field not set    | Include all required fields in records array             |
| `INVALID_CROSS_REFERENCE_KEY`       | Invalid relationship ID   | Verify parent record exists; query first                 |
| `TOO_MANY_SOQL_QUERIES`             | 100 query limit           | Combine queries using relationships                      |
| `TOO_MANY_DML_STATEMENTS`           | 150 DML limit             | Use single `sobject_dml` call with array of 200+ records |
| `cirra_ai_init not called`          | Session not initialized   | Always call `cirra_ai_init()` FIRST                      |

---

## Governor Limits

Reference [Salesforce Governor Limits](https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_apexgov.htm) for current limits.

**Key limits**: SOQL 100/200 (sync/async) | DML 150 | Records 10K | Bulk API 10M records/day

**Cirra AI Optimization**: Single `sobject_dml` calls with 200+ records count as ONE DML statement toward limit.

---

## Completion Format

### Data Operations (Tier 1)

```
Data Operation Complete: [Operation Type]
  Object: [ObjectName] | Records: [Count]
  Target Org: [org identifier]

  Pre-flight: [PASS/FAIL — errors/warnings count]

  Record Summary:
  - Created/Updated/Deleted: [count] records
  Record IDs: [first 5 IDs...]

  Cleanup Query:
  - soql_query(sObject="[Object]", fields=["Id"], whereClause="Name LIKE 'Test%'")
  - Then: sobject_dml(operation="delete", records=[...])
```

### Code Deployment (Tier 2)

```
Code Deployment Validated: [metadata_type]
  Full Name: [class/flow name]
  Validator: [ApexValidator | EnhancedFlowValidator]
  Score: [score]/[max] — [rating]

  Issues: [count] ([critical count] critical)
  [list critical issues if any]

  Next Steps:
  1. Fix critical issues (if any)
  2. Deploy via metadata_create / metadata_update
  3. Verify in org
```

---

## Dependencies

- **Cirra AI MCP Server** (required): All data operations use Cirra AI tools
  - Initialize with: `cirra_ai_init(team, user)`
  - Tools: soql_query, sobject_dml, sobject_describe, tooling_api_query

- **sf-metadata** (optional): Query object/field structure
  - Or use `sobject_describe` and `tooling_api_query` directly

- **Python 3.8+** (for validation): Required to run mcp_validator_cli.py in Cowork mode

---

## Notes

- **API Version**: Operations use org's default API version (recommend 62.0+)
- **Bulk Operations**: Single `sobject_dml` call with 200+ records optimizes DML limits
- **User Context**: Queries respect user's field-level security
- **Test Isolation**: Track created record IDs for cleanup
- **Sensitive Data**: Never include real PII in test data
- **Remote Org Only**: No local scratch org support; all operations target remote orgs
- **Validation**: Run `mcp_validator_cli.py` before executing operations in Cowork mode (Tier 1 for data ops, Tier 2 for code deployment)
