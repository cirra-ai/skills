---
name: sf-lwc
plugin: cirra-ai-sf
argument-hint: '[create|update|validate] {ComponentName} ...'
metadata:
  version: 2.0.3
description: >
  Lightning Web Components development with PICKLES architecture methodology, component
  scaffolding, wire service patterns, event handling, Apex integration, GraphQL support,
  and Jest test generation. Powered by Cirra AI MCP Server for seamless metadata deployment.
  Usage: /sf-lwc [create|update|validate] {ComponentName} ...
---

# Salesforce Lightning Web Components

Expert frontend engineer specializing in Lightning Web Components for Salesforce. Generate production-ready LWC components using the **PICKLES Framework** for architecture, with proper data binding, Apex/GraphQL integration, event handling, SLDS 2 styling, and comprehensive Jest tests. Deploy components directly via **Cirra AI MCP Server** for seamless org integration.

## Dispatch

Parse `$ARGUMENTS` to determine which workflow to run:

| First argument or intent            | Workflow                               |
| ----------------------------------- | -------------------------------------- |
| `create`, new component request     | [Create LWC](#create-lwc-workflow)     |
| `update`, modify existing component | [Update LWC](#update-lwc-workflow)     |
| `validate`, review, score           | [Validate LWC](#validate-lwc-workflow) |
| _(no argument or unclear)_          | Ask the user (see below)               |

When the operation is missing or unclear, **you MUST use `AskUserQuestion`** before proceeding:

```
AskUserQuestion(question="What would you like to do?\n\n1. **Create** — scaffold a new Lightning Web Component\n2. **Update** — fetch, modify, validate, and redeploy\n3. **Validate** — score an existing LWC")
```

Do NOT guess the operation or default to one. Wait for the user's answer.

## Execution modes

This skill supports four execution modes — see
`references/execution-modes.md` for detection logic and full details,
and `references/mcp-pagination.md` for handling large MCP responses.

All LWC operations go through MCP tools regardless of mode. The mode
determines whether local tooling (filesystem, Jest, code execution) is
available for post-processing and how large query results are retrieved.

---

## Source encoding rules (read this before any deploy/update)

Salesforce uses two different APIs for LWC source code, and they expect different encodings. Mixing them up produces errors like `XML parse error: Content is not allowed in prolog.: Source` or `Compilation` failures.

| API path                                                                           | Field                               | Encoding                         |
| ---------------------------------------------------------------------------------- | ----------------------------------- | -------------------------------- |
| Metadata API — `metadata_create` / `metadata_update` on `LightningComponentBundle` | `lwcResources.lwcResource[].source` | **Base64-encoded**               |
| Tooling API — `tooling_api_dml` on `LightningComponentResource`                    | `Source`                            | **Plain text** (NOT Base64)      |
| Tooling API — `tooling_api_query` on `LightningComponentResource`                  | `Source` (returned)                 | **Plain text** (already decoded) |

When falling back from `metadata_update` to per-file Tooling API edits (see [Tooling API fallback](#tooling-api-fallback--per-file-edits)), do not re-encode. The `Source` you read with `tooling_api_query` is the same plain text you write back with `tooling_api_dml`.

---

## Create LWC Workflow

Create a new Lightning Web Component following PICKLES architecture and Spring '26 best practices.

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

If it already exists, suggest `update <ComponentName>` instead.

### 3. Generate the bundle

Apply the PICKLES framework from the sf-lwc skill. Generate all four files:

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
VALIDATOR=$(find ~/.claude/plugins -name "validate_slds.py" 2>/dev/null | grep sf-lwc | head -1)
# Or if CLAUDE_PLUGIN_ROOT is set:
# VALIDATOR="${CLAUDE_PLUGIN_ROOT}/skills/sf-lwc/scripts/validate_slds.py"

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
    "fullName": "<componentName>",
    "apiVersion": "66.0",
    "isExposed": true,
    "masterLabel": "<Component Label>",
    "lwcResources": {
      "lwcResource": [
        {"filePath": "lwc/<componentName>/<componentName>.js", "source": "<Base64-encoded JS>"},
        {"filePath": "lwc/<componentName>/<componentName>.html", "source": "<Base64-encoded HTML>"},
        {"filePath": "lwc/<componentName>/<componentName>.css", "source": "<Base64-encoded CSS>"}
      ]
    }
  }]
)
```

### 6. Report

Show the per-file validation scores and deployment status. If the component exposes `lightning__agentforce` capability, remind the user to add an agent action in Setup to make it discoverable.

---

## Update LWC Workflow

Fetch, modify, validate, and redeploy an existing Lightning Web Component.

### Parsing the request

The argument should be a component name followed by the requested changes: `update accountDashboard add a search filter` or `update contactCard fix dark mode colors`.

If no name is given, ask the user which component to update and what changes are needed.

### 1. Fetch the current bundle

```
metadata_read(
  type="LightningComponentBundle",
  fullNames=["c/<ComponentName>"]
)
```

If not found, suggest `create <ComponentName>` instead.

### 2. Read and understand

Review the existing files before making any changes. Understand:

- What the component currently does
- Existing SLDS classes, CSS variables, and styling patterns in use
- Wire adapters and data flow
- Event handling and component communication patterns
- What the requested change affects

### 3. Apply changes

Modify the relevant file(s) following sf-lwc skill guidelines:

- Preserve existing SLDS classes and wire patterns (update where relevant)
- Maintain accessibility attributes
- Do not introduce hardcoded colors — keep CSS hooks
- If changing `targets` in meta.xml, verify all existing placements remain valid

### 4. Validate before deploying

Write the modified file(s) to a temp directory and validate:

```bash
# Locate the validator
VALIDATOR=$(find ~/.claude/plugins -name "validate_slds.py" 2>/dev/null | grep sf-lwc | head -1)

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
    "fullName": "<ComponentName>",
    "apiVersion": "66.0",
    "isExposed": true,
    "masterLabel": "<Component Label>",
    "lwcResources": {
      "lwcResource": [
        {"filePath": "lwc/<ComponentName>/<ComponentName>.js", "source": "<Base64-encoded JS>"},
        {"filePath": "lwc/<ComponentName>/<ComponentName>.html", "source": "<Base64-encoded HTML>"},
        {"filePath": "lwc/<ComponentName>/<ComponentName>.css", "source": "<Base64-encoded CSS>"}
      ]
    }
  }]
)
```

> **If `metadata_update` reports a partial failure** (e.g. `had partial failures: All 1 operations failed`), do NOT retry the bundle-level call with the same payload. Switch to the [Tooling API fallback](#tooling-api-fallback--per-file-edits) and update one resource at a time with plain-text `Source`. Re-running `metadata_update` with the same content will reproduce the same failure.

### 6. Report

Summarise the changes made and show the final validation scores per file.

---

## Tooling API fallback — per-file edits

See [Tooling API Fallback](references/tooling-api-fallback.md) when Metadata API bundle deploy is unavailable.

## Validate LWC Workflow

Validate one or more Lightning Web Components using the SLDS 2 static analysis pipeline and return a scored report.

### Parsing the request

| Input after `validate`                                                 | Interpretation                                   |
| ---------------------------------------------------------------------- | ------------------------------------------------ |
| `accountDashboard`                                                     | Component name — fetch bundle from org, validate |
| `force-app/.../accountDashboard.html` (ends `.html`, `.css`, or `.js`) | Local file — validate directly                   |
| `accountDashboard,contactCard`                                         | Comma-separated list — bulk fetch, validate each |
| `All`                                                                  | All LightningComponentBundle records in the org  |
| _(no argument)_                                                        | Ask the user what to validate                    |

### Validation script

```bash
# $CLAUDE_PLUGIN_ROOT is set by Claude Code. Other hosts: see references/execution-modes.md.
# If not set, find the script:
VALIDATOR=$(find ~/.claude/plugins -name "validate_slds.py" 2>/dev/null | grep sf-lwc | head -1)
```

### Local file

```bash
python3 "$VALIDATOR" "<file_path>"
```

### Component name (fetch from org)

1. Fetch the component bundle:

```
metadata_read(
  type="LightningComponentBundle",
  fullNames=["c/<ComponentName>"]
)
```

If not found, tell the user the component was not found in the org.

2. Write the bundle files to a temp directory:

```
Write /tmp/validate_<ComponentName>/<componentName>.html
Write /tmp/validate_<ComponentName>/<componentName>.css
Write /tmp/validate_<ComponentName>/<componentName>.js
```

3. Validate each file:

```bash
python3 "$VALIDATOR" "/tmp/validate_<ComponentName>/<componentName>.html"
python3 "$VALIDATOR" "/tmp/validate_<ComponentName>/<componentName>.css"
python3 "$VALIDATOR" "/tmp/validate_<ComponentName>/<componentName>.js"
```

4. Delete the temp directory after validation.

5. Aggregate scores: sum the per-file scores and show a combined report with per-category breakdown.

### Comma-separated list

Fetch all bundles in individual `metadata_read` calls (LightningComponentBundle doesn't support bulk reads reliably):

```
metadata_read(type="LightningComponentBundle", fullNames=["c/<Name1>"])
metadata_read(type="LightningComponentBundle", fullNames=["c/<Name2>"])
```

Validate each bundle (write → validate → delete). After all are validated, show a summary table sorted by score ascending (worst first):

| Component     | HTML    | CSS     | JS      | Combined | Status             |
| ------------- | ------- | ------- | ------- | -------- | ------------------ |
| weakDashboard | 45/165  | 60/165  | 55/165  | avg 53%  | ❌ Below threshold |
| accountCard   | 140/165 | 155/165 | 148/165 | avg 90%  | ✅ Pass            |

### All

1. List all deployed components. Prefer the lightweight Tooling API query — `metadata_list` exceeds the per-call response cap in larger orgs and returns only a paginated preview:

```
tooling_api_query(
  sObject="LightningComponentBundle",
  fields=["Id", "DeveloperName", "MasterLabel", "ApiVersion"],
  whereClause="NamespacePrefix = null"
)
```

2. Fetch and validate each component bundle in batches of 10.

**Backoff strategy**: If a batch read fails, fall back to individual reads for that batch.

3. Validate each bundle (write → validate → delete).
4. Show the summary table sorted by combined score ascending.
5. Highlight any components averaging below 100/165 (61%) as requiring attention.

---

## Core Responsibilities

1. **Component Scaffolding**: Generate complete LWC bundles (JS, HTML, CSS, meta.xml)
2. **PICKLES Architecture**: Apply structured design methodology for robust components
3. **Wire Service Patterns**: Implement @wire decorators for data fetching (Apex & GraphQL)
4. **Apex/GraphQL Integration**: Connect LWC to backend with @AuraEnabled and GraphQL
5. **Event Handling**: Component communication (CustomEvent, LMS, pubsub)
6. **Lifecycle Management**: Proper use of connectedCallback, renderedCallback, etc.
7. **Jest Testing**: Generate comprehensive unit tests with advanced patterns
8. **Accessibility**: WCAG compliance with ARIA attributes, focus management
9. **Dark Mode**: SLDS 2 compliant styling with global styling hooks
10. **Performance**: Lazy loading, virtual scrolling, debouncing, efficient rendering
11. **Cirra AI Deployment**: Deploy via metadata_create with validation

---

## Cirra AI MCP Integration

See [MCP Integration](references/mcp-integration.md) for init, deploy, and Tooling API patterns.

## Fast Path (Simple Requests)

For simple, self-contained components (static display, single-field input, basic wrapper, quick prototype), bypass the full PICKLES design methodology and 165-point scoring while still performing initialization and mandatory checks, then generate + deploy:

1. Call `cirra_ai_init()` (always required)
2. Generate the LWC bundle (JS, HTML, CSS, meta.xml)
3. Run basic checks (accessibility attributes, no hardcoded colors)
4. Deploy via `metadata_create`
5. Verify deployment

**Use the fast path when**: the request is explicit, the component is self-contained with no complex data binding, and there are no ambiguous requirements.

**Use the full PICKLES workflow when**: the component involves Apex/GraphQL integration, complex state management, cross-component communication, or underspecified requirements.

---

## PICKLES Framework (Architecture Methodology)

See [PICKLES Framework](references/pickles-framework.md).

## Key Component Patterns

See [Component Patterns](references/component-patterns.md).

## SLDS 2 Validation (165-Point Scoring)

See [SLDS Validation](references/slds-validation.md).

## Dark Mode Readiness

See [Dark Mode Readiness](references/dark-mode.md).

## Jest Testing

See [Jest Testing](references/jest-testing.md).

## Accessibility

See [Accessibility](references/accessibility.md).

## Metadata Configuration

See [Metadata Configuration](references/metadata-configuration.md).

## Deployment via Cirra AI

See [Deployment](references/deployment.md).

## Code Generation Examples

See [Code Generation Examples](references/code-generation-examples.md).

## Flow Screen Integration

See [Flow Screen Integration](references/flow-screen-integration.md).

## Advanced Features

See [Advanced Features](references/advanced-features.md).

## Cross-Skill Integration

| Skill       | Use Case                                                       |
| ----------- | -------------------------------------------------------------- |
| sf-apex     | Generate Apex controllers (`@AuraEnabled`, `@InvocableMethod`) |
| sf-flow     | Embed components in Flow Screens, pass data to/from Flow       |
| sf-data     | SOQL queries and test data for component development           |
| sf-metadata | Create LWC message channels                                    |

---

## Limitations & Workarounds

| Feature                     | CLI Support                                           | MCP Support                              | Workaround                                      |
| --------------------------- | ----------------------------------------------------- | ---------------------------------------- | ----------------------------------------------- |
| Local file scaffolding      | `sf lightning generate component`                     | ❌ Not available                         | Generate code as strings, write via Edit        |
| Automatic file sync         | `force-app/main/default/lwc/`                         | ❌ Not available                         | Generate as strings, deploy via metadata_create |
| LWC Jest runner             | `sf lightning lwc test run`                           | ❌ Not available                         | Run `npm run test` locally                      |
| Component metadata deploy   | `sf project deploy start -m LightningComponentBundle` | ✅ `metadata_create` / `metadata_update` | Full support via MCP                            |
| Component metadata retrieve | `sf project retrieve`                                 | ✅ `metadata_read`                       | Full support via MCP                            |
| List deployed components    | `sf metadata list`                                    | ✅ `metadata_list`                       | Full support via MCP                            |

---

## Dependencies

**Required**:

- Cirra AI MCP Server connection (via `cirra_ai_init`)
- Target org with LWC support (API 45.0+)

**For Testing**:

- Node.js 18+
- Jest (`@salesforce/sfdx-lwc-jest`)

**For SLDS Validation**:

- `@salesforce-ux/slds-linter` (optional)

---

## Additional Resources

See [Additional Resources](references/additional-resources.md).

## License

See [LICENSE](LICENSE)
