# Apex MCP Integration Test Protocol

Live integration test for Apex deployment via Cirra AI MCP Server.
Run interactively in a Claude Code or Codex session with MCP access and the `cirra-ai-sf-apex` skill active.

## Purpose

Validate that an LLM can:

1. Apply the Apex skill workflow
2. Deploy Apex artifacts to a real org
3. Verify outcomes in the org
4. Catch and handle negative cases

## Prerequisites

- Cirra AI MCP Server connected to a Salesforce sandbox
- `cirra_ai_init()` called in the session
- Apex skill active (so `pre-mcp-validate.py` hook is active)

## LLM Prompt You Can Reuse

Use this prompt in a fresh session:

```text
Use the cirra-ai-sf-apex skill and run the full Apex MCP integration protocol at:
skills/cirra-ai-sf-apex/tests/test_apex_mcp_integration.md

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

## Step 2: Deploy Valid Apex Class via metadata_create

Deploy:

```python
metadata_create(
    type="ApexClass",
    metadata=[{
        "fullName": "TEST_AccountService_Valid",
        "body": "public with sharing class TEST_AccountService_Valid { public static Integer process(List<Account> records) { if (records == null) return 0; Integer countProcessed = 0; for (Account a : records) { if (a.Name != null) { a.Name = a.Name.trim(); countProcessed++; } } return countProcessed; } }"
    }]
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
metadata_create(
    type="ApexClass",
    metadata=[{
        "fullName": "TEST_Bad_DmlInLoop",
        "body": "public with sharing class TEST_Bad_DmlInLoop { public static void run(List<Account> accounts) { for (Account a : accounts) { update a; } } }"
    }]
)
```

Expected:

- Pre-MCP validator denies deployment (CRITICAL bulkification issue)
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
metadata_create(
    type="ApexClass",
    metadata=[{
        "fullName": "TEST_MissingSharing",
        "body": "public class TEST_MissingSharing { public static void run() { System.debug('x'); } }"
    }]
)
```

Expected:

- Deployment is allowed (warning/advisory path)
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
