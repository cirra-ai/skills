---
name: create
description: Generate a new Salesforce Flow from requirements. Guides through flow type selection, generates production-ready XML with 110-point scoring, and deploys via the Cirra AI MCP Server.
---

Create a new Flow following Winter '26 best practices.

## Workflow

### 1. Gather requirements

Use AskUserQuestion to collect:

- **Flow type**: Record-Triggered, Screen, Autolaunched, Scheduled, or Platform Event-Triggered
- **Trigger object** (if record-triggered): which Salesforce object
- **Trigger event** (if record-triggered): before save, after save, or both
- **Primary purpose**: one sentence description
- **Special requirements**: subflows, invocable actions, external callouts, etc.

### 2. Check for existing flow

Before generating, confirm the flow doesn't already exist:

```
metadata_list(
  type="Flow",
  sf_user="<sf_user>"
)
```

If it exists, suggest `/update <FlowApiName>` instead.

### 3. Generate

Create the flow XML following the sf-flow skill guidelines:

- Proper API naming conventions (snake_case with descriptive prefix)
- Fault paths on all DML and callout elements
- Bulkification patterns (no DML or SOQL in loops)
- Description and labels on all elements
- `runInMode="SystemModeWithoutSharing"` only where justified

### 4. Validate before deploying

Write the generated XML to a temp file and validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_flow_cli.py" "/tmp/<FlowApiName>.flow-meta.xml"
```

Fix any CRITICAL or HIGH issues before proceeding. The pre-deployment hook will also validate automatically when `metadata_create` is called.

### 5. Deploy

```
metadata_create(
  type="Flow",
  metadata=[{"fullName": "<FlowApiName>", "body": "<flow XML>"}]
)
```

### 6. Report

Show the final validation score and deployment status.
