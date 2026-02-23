---
name: create-lwc
description: Generate a new Lightning Web Component from requirements. Guides through the PICKLES design process, generates a production-ready bundle with 165-point SLDS 2 scoring, and deploys via the Cirra AI MCP Server.
---

Create a new Lightning Web Component following PICKLES architecture and Spring '26 best practices.

## Workflow

### 1. Gather requirements

Use AskUserQuestion to collect:

- **Component purpose**: one sentence description
- **Target placement**: App Page, Record Page, Home Page, or Flow Screen
- **Data source**: Lightning Data Service (LDS), Apex @wire, GraphQL, or none
- **Target object(s)** (if data-driven): which Salesforce objects
- **Special requirements**: dark mode, accessibility, LMS events, TypeScript, Agentforce discoverability, etc.

### 2. Check for existing component

Before generating, confirm nothing already exists with that name.

```
tooling_api_query(
  sObject="LightningComponentBundle",
  whereClause="DeveloperName = '<ComponentName>'",
  fields=["DeveloperName", "ApiVersion"]
)
```

If it already exists, suggest `/update-lwc <ComponentName>` instead.

### 3. Generate the bundle

Apply the PICKLES framework from the cirra-ai-sf-lwc skill. Generate all four files:

#### `<componentName>.html`

- SLDS 2 markup with `lightning-*` base components
- No hardcoded colors — use CSS styling hooks (`--slds-g-*` variables)
- Accessibility: ARIA labels/roles, keyboard navigation, `lwc:if` instead of ternary

#### `<componentName>.js`

- `@wire` decorators for data fetching (LDS or Apex)
- `@api` for parent→child props, `CustomEvent` for child→parent
- Error state handling for wire adapters
- No `@track` on primitives (unnecessary in modern LWC)

#### `<componentName>.css`

- CSS styling hooks only — no hardcoded hex or RGB values
- Dark mode ready via `--slds-g-*` variable fallbacks

#### `<componentName>.js-meta.xml`

- Correct `targets` for the intended placement
- `targetConfigs` with typed properties where applicable
- `isExposed: true` for App Builder drag-and-drop

### 4. Validate before deploying

Write each file to a temp directory and validate:

```bash
# Locate the validator
VALIDATOR=$(find ~/.claude/plugins -name "validate_slds.py" 2>/dev/null | grep cirra-ai-sf-lwc | head -1)
# Or if CLAUDE_PLUGIN_ROOT is set:
# VALIDATOR="${CLAUDE_PLUGIN_ROOT}/skills/cirra-ai-sf-lwc/scripts/validate_slds.py"

python3 "$VALIDATOR" "/tmp/<componentName>/<componentName>.html"
python3 "$VALIDATOR" "/tmp/<componentName>/<componentName>.css"
python3 "$VALIDATOR" "/tmp/<componentName>/<componentName>.js"
```

Fix any CRITICAL issues before proceeding. Advisory warnings can be noted in the report.

### 5. Deploy

```
metadata_create(
  type="LightningComponentBundle",
  metadata=[{
    "fullName": "c/<componentName>",
    "html": "<html content>",
    "css": "<css content>",
    "js": "<js content>",
    "meta": "<meta.xml content>"
  }]
)
```

### 6. Report

Show the per-file validation scores and deployment status. If the component exposes `lightning__agentforce` capability, remind the user to add an agent action in Setup to make it discoverable.
