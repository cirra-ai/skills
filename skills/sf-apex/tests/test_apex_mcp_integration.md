# Apex MCP Integration Test Protocol

Live integration test for Apex deployment via Cirra AI MCP Server.
Run interactively in a Claude Code or Codex session with MCP access and the `sf-apex` skill active.

## Test Summary (Last Run: 2026-03-07)

| #   | Test                                        | Result | Details                                           |
| --- | ------------------------------------------- | ------ | ------------------------------------------------- |
| 1   | Clean pre-existing test artifacts           | PASS   | No TEST\_\* classes or triggers found             |
| 2   | Deploy valid Apex class via tooling_api_dml | PASS   | Created successfully, 150/150                     |
| 3   | Deploy valid trigger via tooling_api_dml    | PASS   | Created, status Active                            |
| 4   | DML-in-loop class blocked by validator      | PASS   | Validator detects CRITICAL (140/150), hook denies |
| 5   | Missing sharing class allowed with advisory | PASS   | Validator warns (145/150), deploy allowed         |

## Prerequisites

- Cirra AI MCP Server connected to a Salesforce sandbox
- `cirra_ai_init()` called in the session
- Apex skill active (so `pre-mcp-validate.py` hook is active)

## LLM Prompt You Can Reuse

Use this prompt in a fresh session:

```text
Use the sf-apex skill and run the full Apex MCP integration protocol at:
skills/sf-apex/tests/test_apex_mcp_integration.md

Requirements:
- Execute each step against my connected sandbox org
- Show each MCP call and summarize the result
- Verify expected outcomes after each deployment via tooling_api_query
- Do not skip negative test cases
- Do not auto-cleanup without asking me first
```

## Step 1: Clean Slate

Query for test artifacts:

```python
tooling_api_query(
    sObject="ApexClass",
    fields=["Id", "Name"],
    whereClause="Name LIKE 'TEST_%'"
)

tooling_api_query(
    sObject="ApexTrigger",
    fields=["Id", "Name", "TableEnumOrId"],
    whereClause="Name LIKE 'TEST_%'"
)
```

Expected: 0 records, or delete found records before proceeding.

## Step 2: Deploy Valid Apex Class via tooling_api_dml

> **Note**: Apex classes must be deployed via `tooling_api_dml`, not `metadata_create`.
> The Metadata API does not support the `body` field for ApexClass — it returns
> `"Element body invalid at this location in type ApexClass"`.

Deploy:

```python
tooling_api_dml(
    operation="insert",
    sObject="ApexClass",
    record={
        "Name": "TEST_AccountService_Valid",
        "Body": "public with sharing class TEST_AccountService_Valid { public static Integer process(List<Account> records) { if (records == null) return 0; Integer countProcessed = 0; for (Account a : records) { if (a.Name != null) { a.Name = a.Name.trim(); countProcessed++; } } return countProcessed; } }",
        "Status": "Active"
    }
)
```

Expected:

- Tool call succeeds
- No blocking from pre-MCP validator

Verify:

```python
tooling_api_query(
    sObject="ApexClass",
    fields=["Id", "Name", "ApiVersion"],
    whereClause="Name = 'TEST_AccountService_Valid'"
)
```

Expected: 1 record found.

## Step 3: Deploy Valid Trigger via tooling_api_dml

Deploy:

```python
tooling_api_dml(
    operation="insert",
    sObject="ApexTrigger",
    record={
        "Name": "TEST_AccountTrigger_Valid",
        "TableEnumOrId": "Account",
        "Body": "trigger TEST_AccountTrigger_Valid on Account (before insert) { for (Account a : Trigger.new) { if (String.isBlank(a.Name)) { a.Name = 'Test Account'; } } }",
        "Status": "Active",
        "ApiVersion": "65.0"
    }
)
```

Expected:

- Tool call succeeds
- Pre-MCP validator allows deployment

Verify:

```python
tooling_api_query(
    sObject="ApexTrigger",
    fields=["Id", "Name", "TableEnumOrId", "ApiVersion", "Status"],
    whereClause="Name = 'TEST_AccountTrigger_Valid'"
)
```

Expected: 1 record found, status active.

## Step 4: Negative Test — DML In Loop Must Be Blocked

Attempt to deploy:

```python
tooling_api_dml(
    operation="insert",
    sObject="ApexClass",
    record={
        "Name": "TEST_Bad_DmlInLoop",
        "Body": "public with sharing class TEST_Bad_DmlInLoop { public static void run(List<Account> accounts) { for (Account a : accounts) { update a; } } }",
        "Status": "Active"
    }
)
```

Expected:

- Pre-MCP validator denies deployment (CRITICAL bulkification issue, score 140/150)
- No class record is created

Verify:

```python
tooling_api_query(
    sObject="ApexClass",
    fields=["Id", "Name"],
    whereClause="Name = 'TEST_Bad_DmlInLoop'"
)
```

Expected: 0 records.

## Step 5: Advisory Test — Missing Sharing (Warning Path)

Deploy:

```python
tooling_api_dml(
    operation="insert",
    sObject="ApexClass",
    record={
        "Name": "TEST_MissingSharing",
        "Body": "public class TEST_MissingSharing { public static void run() { System.debug('x'); } }",
        "Status": "Active"
    }
)
```

Expected:

- Deployment is allowed (warning/advisory path, score 145/150)
- Class exists in org after deployment

Verify:

```python
tooling_api_query(
    sObject="ApexClass",
    fields=["Id", "Name"],
    whereClause="Name = 'TEST_MissingSharing'"
)
```

Expected: 1 record found.

## Step 6: Cleanup (Optional, Ask First)

Delete test artifacts only with user approval:

```python
# Query IDs first, then delete with tooling_api_dml(operation="delete", ...)
tooling_api_query(sObject="ApexClass", fields=["Id", "Name"], whereClause="Name LIKE 'TEST_%'")
tooling_api_query(sObject="ApexTrigger", fields=["Id", "Name"], whereClause="Name LIKE 'TEST_%'")
```

Expected cleanup target:

- `TEST_AccountService_Valid`
- `TEST_AccountTrigger_Valid`
- `TEST_MissingSharing`

(`TEST_Bad_DmlInLoop` should never exist if blocking works correctly.)

## Pass Criteria

- Positive deploys succeed and are queryable in org
- Critical negative case is blocked before deploy
- Advisory warning case is allowed
- LLM reports each result and matches expected behavior

## Key Insights from Testing

1. **Apex requires Tooling API, not Metadata API**: `metadata_create` does not support the `body` field for `ApexClass`. Always use `tooling_api_dml` with `insert` for new Apex classes and triggers.
2. **Validator `full_name` extraction**: The `tooling_api_dml` record uses `Name` (not `FullName`). The validator must check `Name` first when extracting the class/trigger name.
3. **Plugins must stay in sync**: The `plugins/` directory contains a copy of the validator scripts. If `skills/` is updated but `plugins/` is not rebuilt, the deployed hook uses stale code. This caused the DML-in-loop check to fail silently in prior runs.
