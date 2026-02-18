---
name: update
description: Fetch an existing Apex class from the org, apply requested changes, validate with 150-point scoring, and redeploy via the Cirra AI MCP Server.
---

Fetch, modify, validate, and redeploy an existing Apex class.

## Parsing the request

The argument should be a class name: `/update MyClass do X`

If no class name is given, ask the user which class to update and what changes are needed.

## Workflow

### 1. Fetch the current implementation

```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<ClassName>'",
  fields=["Name", "Body", "ApiVersion"]
)
```

If the class is not found, suggest `/create` instead.

### 2. Read and understand

Review the existing code before making any changes. Understand:

- What the class currently does
- Existing patterns and conventions in use
- What the requested change affects

### 3. Apply changes

Modify the class following sf-apex skill guidelines. Preserve:

- Existing ApexDoc comments (update where relevant)
- Existing test coverage patterns
- Naming conventions already in use

### 4. Validate before deploying

Write the updated code to a temp file and validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/<ClassName>.cls"
```

Fix any CRITICAL or HIGH issues before proceeding. The pre-deployment hook will also validate automatically when `metadata_update` is called.

### 5. Deploy

```
metadata_update(
  type="ApexClass",
  metadata=[{"fullName": "<ClassName>", "body": "<updated body>"}]
)
```

### 6. Report

Summarise the changes made and show the final validation score.
