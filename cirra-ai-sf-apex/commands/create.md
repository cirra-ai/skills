---
name: create
description: Generate a new Salesforce Apex class from requirements. Guides through class type selection, generates production-ready code with 150-point scoring, and deploys via the Cirra AI MCP Server.
---

Create a new Apex class following 2025 best practices.

## Workflow

### 1. Gather requirements

Use AskUserQuestion to collect:

- **Class type**: Service, Selector, Trigger Handler, Batch, Queueable, Test, or other
- **Primary purpose**: one sentence description
- **Target object(s)**: which Salesforce objects are involved
- **Special requirements**: async, scheduled, invocable, aura-enabled, etc.

### 2. Check for existing class

Before generating, confirm the class doesn't already exist:

```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<ClassName>'",
  fields=["Name", "ApiVersion"]
)
```

If it exists, suggest `/update <ClassName>` instead.

### 3. Generate

Create the class and its test class following the sf-apex skill guidelines:

- Proper naming conventions (PascalCase, type suffix where applicable)
- ApexDoc comments on all public methods
- Bulkification patterns (no SOQL/DML in loops)
- Corresponding test class with 90%+ coverage patterns

### 4. Validate before deploying

Write the generated code to a temp file and validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/<ClassName>.cls"
```

Fix any CRITICAL or HIGH issues before proceeding. The pre-deployment hook will also validate automatically when `metadata_create` is called.

### 5. Deploy

```
metadata_create(
  type="ApexClass",
  metadata=[{"fullName": "<ClassName>", "body": "<class body>"}]
)
```

Deploy the test class separately if generated.

### 6. Report

Show the final validation score and deployment status.
