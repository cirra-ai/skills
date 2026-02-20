---
name: create-apex
description: Generate a new Salesforce Apex class or trigger from requirements. Guides through type selection, generates production-ready code with 150-point scoring, and deploys via the Cirra AI MCP Server.
---

Create a new Apex class or trigger following 2025 best practices.

## Workflow

### 1. Gather requirements

Use AskUserQuestion to collect:

- **Type**: Trigger, Service, Selector, Batch, Queueable, Test, or other
- **Primary purpose**: one sentence description
- **Target object(s)**: which Salesforce objects are involved
- **Special requirements**: async, scheduled, invocable, aura-enabled, etc.

If the type is **Trigger**, also ask:
- Which trigger events are needed (before insert, after update, etc.)
- Whether the Trigger Actions Framework (TAF) is installed in the org

### 2. Check for existing Apex

Before generating, confirm nothing already exists with that name.

**For a class**:
```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<ClassName>'",
  fields=["Name", "ApiVersion"]
)
```

**For a trigger**:
```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="Name = '<TriggerName>'",
  fields=["Name", "TableEnumOrId", "ApiVersion"]
)
```

If either already exists, suggest `/update-apex <Name>` instead.

### 3. Generate

#### For a trigger

Follow the **MANDATORY DELIVERABLES** rule from the sf-apex skill: never put logic directly in the trigger body.

**Check TAF installation** (if unknown):
```
tooling_api_query(
  sObject="InstalledSubscriberPackage",
  whereClause="Name = 'Trigger Actions Framework'"
)
```

- **TAF installed** → generate a thin TAF trigger (`new MetadataTriggerHandler().run()`) + one or more `TA_Object_Purpose` action classes
- **TAF not installed** → generate a thin trigger that delegates to an `ObjectTriggerHandler` class

Also generate a corresponding test class covering the trigger and its handler/action.

#### For a class

Create the class and its test class following the sf-apex skill guidelines:

- Proper naming conventions (PascalCase, type suffix where applicable)
- ApexDoc comments on all public methods
- Bulkification patterns (no SOQL/DML in loops)
- Corresponding test class with 90%+ coverage patterns

### 4. Validate before deploying

Write the generated code to a temp file and validate:

```bash
# For a class:
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/<ClassName>.cls"

# For a trigger:
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/<TriggerName>.trigger"
```

Fix any CRITICAL or HIGH issues before proceeding. The pre-deployment hook will also validate automatically when `tooling_api_dml` is called.

### 5. Deploy

#### Trigger

**Deploy the handler/action class(es) first** — the trigger body references them and Salesforce will reject the trigger if they don't exist yet:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "<HandlerOrActionClassName>",
    "Body": "<class body>",
    "Status": "Active",
    "ApiVersion": "65.0"
  }
)
```

Then deploy the trigger:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexTrigger",
  record={
    "Name": "<ObjectName>Trigger",
    "TableEnumOrId": "<ObjectApiName>",
    "Body": "<trigger body>",
    "Status": "Active",
    "ApiVersion": "65.0"
  }
)
```

> **Note (TAF only)**: For TAF triggers (`new MetadataTriggerHandler().run()`), deploy order between the trigger and action classes does not matter because `MetadataTriggerHandler` comes from the installed package and is already present in the org.

#### Class
```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "<ClassName>",
    "Body": "<class body>",
    "Status": "Active",
    "ApiVersion": "65.0"
  }
)
```

Deploy the test class separately.

### 6. Report

Show the final validation score and deployment status. For TAF triggers, remind the user that a `Trigger_Action__mdt` custom metadata record must be created for each action class to activate it.
