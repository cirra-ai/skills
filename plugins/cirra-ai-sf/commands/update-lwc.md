---
name: update-lwc
description: Fetch an existing Lightning Web Component from the org, apply requested changes, validate with 165-point SLDS 2 scoring, and redeploy via the Cirra AI MCP Server.
---

Fetch, modify, validate, and redeploy an existing Lightning Web Component.

## Parsing the request

The argument should be a component name: `/update-lwc accountDashboard add a search filter` or `/update-lwc contactCard fix dark mode colors`.

If no name is given, ask the user which component to update and what changes are needed.

## Workflow

### 1. Fetch the current bundle

```
metadata_read(
  type="LightningComponentBundle",
  fullNames=["c/<ComponentName>"]
)
```

If not found, suggest `/create-lwc` instead.

### 2. Read and understand

Review the existing files before making any changes. Understand:

- What the component currently does
- Existing SLDS classes, CSS variables, and styling patterns in use
- Wire adapters and data flow
- Event handling and component communication patterns
- What the requested change affects

### 3. Apply changes

Modify the relevant file(s) following cirra-ai-sf-lwc skill guidelines:

- Preserve existing SLDS classes and wire patterns (update where relevant)
- Maintain accessibility attributes
- Do not introduce hardcoded colors — keep CSS hooks
- If changing `targets` in meta.xml, verify all existing placements remain valid

### 4. Validate before deploying

Write the modified file(s) to a temp directory and validate:

```bash
# Locate the validator
VALIDATOR=$(find ~/.claude/plugins -name "validate_slds.py" 2>/dev/null | grep cirra-ai-sf-lwc | head -1)

# Validate each modified file (skip unchanged ones)
python3 "$VALIDATOR" "/tmp/<ComponentName>/<componentName>.html"
python3 "$VALIDATOR" "/tmp/<ComponentName>/<componentName>.css"
python3 "$VALIDATOR" "/tmp/<ComponentName>/<componentName>.js"
```

Fix any CRITICAL issues before proceeding.

### 5. Deploy

```
metadata_update(
  type="LightningComponentBundle",
  metadata=[{
    "fullName": "c/<ComponentName>",
    "html": "<updated html>",
    "css": "<updated css>",
    "js": "<updated js>",
    "meta": "<updated meta.xml>"
  }]
)
```

### 6. Report

Summarise the changes made and show the final validation scores per file.
