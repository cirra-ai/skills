---
name: insert
description: Insert, update, upsert, or delete Salesforce records via DML. Accepts an object name and operation details. Runs pre-flight validation before executing and provides cleanup queries.
---

Perform a DML operation (insert, update, upsert, or delete) against a Salesforce org.

## Parsing the request

The argument should describe the operation: `/insert 50 test Accounts in Technology industry`

If no argument is given, ask the user:
- Which object
- Which DML operation (insert, update, upsert, delete)
- What records or criteria

## Workflow

### 1. Gather requirements

Use AskUserQuestion to collect any missing information:

- **Object**: which Salesforce object
- **Operation**: insert | update | upsert | delete
- **Record count / data**: how many records and what field values
- **External ID field**: required for upsert operations

### 2. Discover object structure

Verify field names and required fields:

```
sobject_describe(
  sObject="<ObjectName>",
  sf_user="<sf_user>"
)
```

### 3. Run pre-flight validation

Before executing, validate the operation parameters:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/mcp_validator_cli.py" --format report input.json
```

Where `input.json` contains:
```json
{
  "tool": "sobject_dml",
  "params": {
    "sObject": "<Object>",
    "operation": "<operation>",
    "records": [...],
    "sf_user": "<sf_user>"
  }
}
```

Fix any errors before proceeding. Warnings are advisory.

### 4. Execute

```
sobject_dml(
  sObject="<ObjectName>",
  operation="insert|update|upsert|delete",
  records=[...],
  sf_user="<sf_user>"
)
```

For upsert, include `externalIdField="<FieldName__c>"`.

**Batch sizing**: Keep records arrays under 200 per call. For larger operations, split into 200-record batches — each batch counts as one DML statement.

### 5. Verify and provide cleanup

After a successful insert, provide a cleanup query so test records can be removed later:

```
soql_query(
  sObject="<ObjectName>",
  fields=["Id"],
  whereClause="Name LIKE 'Test%' AND CreatedDate = TODAY",
  sf_user="<sf_user>"
)
```

### 6. Report

Show: operation type, object, record count, success/failure, and cleanup instructions.
