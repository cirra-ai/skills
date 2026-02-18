---
name: update
description: Fetch an existing Salesforce Flow from the org, apply requested changes, validate with 110-point scoring, and redeploy via the Cirra AI MCP Server.
---

Fetch, modify, validate, and redeploy an existing Salesforce Flow.

## Parsing the request

The argument should be a flow API name: `/update Auto_Lead_Assignment do X`

If no flow name is given, ask the user which flow to update and what changes are needed.

## Workflow

### 1. Fetch the current implementation

```
metadata_read(
  type="Flow",
  fullNames=["<FlowApiName>"],
  sf_user="<sf_user>"
)
```

If the flow is not found, suggest `/create` instead.

### 2. Read and understand

Review the existing flow XML before making any changes. Understand:

- Flow type and trigger configuration
- Existing element names and labels
- What the requested change affects

### 3. Apply changes

Modify the flow following sf-flow skill guidelines. Preserve:

- Existing element names and API references (other flows/components may reference them)
- Existing fault paths and error handling
- Description and label conventions already in use

### 4. Validate before deploying

Write the updated XML to a temp file and validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_flow_cli.py" "/tmp/<FlowApiName>.flow-meta.xml"
```

Fix any CRITICAL or HIGH issues before proceeding. The pre-deployment hook will also validate automatically when `metadata_update` is called.

### 5. Deploy

```
metadata_update(
  type="Flow",
  metadata=[{"fullName": "<FlowApiName>", "body": "<updated XML>"}]
)
```

### 6. Report

Summarise the changes made and show the final validation score.
