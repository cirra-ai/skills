---
name: update-apex
description: Fetch an existing Apex class or trigger from the org, apply requested changes, validate with 150-point scoring, and redeploy via the Cirra AI MCP Server.
---

Fetch, modify, validate, and redeploy an existing Apex class or trigger.

## Parsing the request

The argument should be a class or trigger name: `/update-apex MyClass do X` or `/update-apex AccountTrigger add after update handling`

If no name is given, ask the user which class or trigger to update and what changes are needed.

## Workflow

### 1. Fetch the current implementation

First try `ApexClass`. If not found, try `ApexTrigger`.

**Try class first**:
```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<Name>'",
  fields=["Id", "Name", "Body", "ApiVersion"]
)
```

**If not found, try trigger**:
```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="Name = '<Name>'",
  fields=["Id", "Name", "TableEnumOrId", "Body", "ApiVersion"]
)
```

If neither is found, suggest `/create-apex` instead.

### 2. Read and understand

Review the existing code before making any changes. Understand:

- What the class/trigger currently does
- Existing patterns and conventions in use
- What the requested change affects

For triggers, also check whether related handler/action classes need updating.

### 3. Apply changes

Modify the code following sf-apex skill guidelines. Preserve:

- Existing ApexDoc comments (update where relevant)
- Existing test coverage patterns
- Naming conventions already in use

For triggers: keep logic out of the trigger body — route to handler or TAF action classes instead.

### 4. Validate before deploying

Write the updated code to a temp file and validate:

```bash
# For a class:
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/<Name>.cls"

# For a trigger:
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/<Name>.trigger"
```

Fix any CRITICAL or HIGH issues before proceeding. The pre-deployment hook will also validate automatically when `tooling_api_dml` is called.

### 5. Deploy

#### Updated class
```
tooling_api_dml(
  operation="update",
  sObject="ApexClass",
  record={
    "Id": "<classId>",
    "Name": "<ClassName>",
    "Body": "<updated body>",
    "Status": "Active"
  }
)
```

#### Updated trigger
```
tooling_api_dml(
  operation="update",
  sObject="ApexTrigger",
  record={
    "Id": "<triggerId>",
    "Name": "<TriggerName>",
    "TableEnumOrId": "<ObjectApiName>",
    "Body": "<updated body>",
    "Status": "Active"
  }
)
```

If related handler/action classes were also modified, deploy each of those as separate `ApexClass` updates.

### 6. Report

Summarise the changes made and show the final validation score.
