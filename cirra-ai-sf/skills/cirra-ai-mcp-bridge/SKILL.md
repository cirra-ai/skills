---
name: cirra-ai-mcp-bridge
metadata:
  version: 1.0.0
description: >
  MCPorter bridge for Cirra AI MCP Server. Use when native MCP tools (mcp__*)
  are unavailable, such as in web sessions. Routes Cirra AI tool calls through
  MCPorter via Bash, preserving the same tool interface and parameters.
---

# cirra-ai-mcp-bridge: MCPorter Bridge for Web Sessions

When native MCP tools are not available (typically in web sessions), use MCPorter
to call the Cirra AI MCP Server via the Bash tool. This skill maps every Cirra AI
MCP tool to its MCPorter bridge equivalent.

## When to Use This Skill

Use this bridge **only when** native MCP tools (`mcp__plugin_cirra-ai-sf_cirra-ai__*`)
are unavailable. In CLI and desktop sessions, always prefer native MCP.

## Bridge Script

All calls go through the wrapper script:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" <tool_name> '<json_params>'
```

The script:

- Discovers the Cirra AI MCP server from the plugin's `.mcp.json`
- Converts JSON parameters to MCPorter call syntax
- Returns JSON results from the MCP server

## Authentication

The bridge script automatically selects the right auth mode:

| `CIRRA_AI_TOKEN` env var | Auth mode | Browser needed? |
| --- | --- | --- |
| Set | Bearer token via header | No |
| Not set | MCPorter OAuth flow | Yes |

### Recommended: Token-based auth (web sessions)

Set `CIRRA_AI_TOKEN` with a valid Cirra AI API token before starting a session.
The bridge script picks it up automatically — no browser, no OAuth flow:

```bash
export CIRRA_AI_TOKEN="your-cirra-ai-token"
```

The token is passed as a `Bearer` header to `https://mcp.cirra.ai/mcp` via
a separate config file (`scripts/mcporter-token.mcp.json`). The plugin's
main `.mcp.json` (used by native MCP in CLI/desktop) is not modified.

### Fallback: OAuth (CLI or environments with browser access)

If `CIRRA_AI_TOKEN` is not set, MCPorter falls back to its standard OAuth flow:
it launches a browser, completes the OAuth handshake, and caches tokens under
`~/.mcporter/cirra-ai/`.

> **Note**: Headless MCP authentication is [an open discussion](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/298)
> at the MCP spec level. If you need OAuth in a headless environment,
> authenticate locally with `npx mcporter auth cirra-ai` and copy
> `~/.mcporter/cirra-ai/` to the target machine. This is unofficial.

## Tool Reference

### 1. Initialize Connection

**Native MCP**: `cirra_ai_init()`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" cirra_ai_init '{}'
```

Must be called first before any other operations. Returns the default org
configuration.

### 2. SOQL Query

**Native MCP**: `soql_query(sObject, fields, whereClause, limit, orderBy, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" soql_query '{
  "sObject": "Account",
  "fields": ["Id", "Name", "Industry"],
  "whereClause": "Industry = '\''Technology'\''",
  "limit": 100,
  "sf_user": "prod"
}'
```

### 3. DML Operations (Insert/Update/Delete/Upsert)

**Native MCP**: `sobject_dml(sObject, operation, records, externalIdField, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" sobject_dml '{
  "sObject": "Account",
  "operation": "insert",
  "records": [
    {"Name": "Test Account 1", "Industry": "Technology"},
    {"Name": "Test Account 2", "Industry": "Finance"}
  ],
  "sf_user": "prod"
}'
```

For upsert, include `"externalIdField": "ExternalId__c"`.

### 4. Describe Object

**Native MCP**: `sobject_describe(sObject, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" sobject_describe '{
  "sObject": "Account",
  "sf_user": "prod"
}'
```

### 5. Tooling API Query

**Native MCP**: `tooling_api_query(sObject, fields, whereClause, limit, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" tooling_api_query '{
  "sObject": "ApexClass",
  "fields": ["Id", "Name", "ApiVersion"],
  "whereClause": "NamespacePrefix = null",
  "limit": 200,
  "sf_user": "prod"
}'
```

### 6. Tooling API DML

**Native MCP**: `tooling_api_dml(operation, sObject, record, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" tooling_api_dml '{
  "operation": "insert",
  "sObject": "ApexClass",
  "record": {
    "Name": "MyService",
    "Body": "public with sharing class MyService { }",
    "Status": "Active",
    "ApiVersion": "65.0"
  },
  "sf_user": "prod"
}'
```

### 7. Metadata Read

**Native MCP**: `metadata_read(type, fullNames, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" metadata_read '{
  "type": "Flow",
  "fullNames": ["My_Flow"],
  "sf_user": "prod"
}'
```

### 8. Metadata Create

**Native MCP**: `metadata_create(type, metadata, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" metadata_create '{
  "type": "CustomObject",
  "metadata": [
    {
      "fullName": "Inspection__c",
      "label": "Inspection",
      "pluralLabel": "Inspections",
      "deploymentStatus": "Deployed",
      "sharingModel": "ReadWrite",
      "nameField": {
        "label": "Inspection Name",
        "type": "Text"
      }
    }
  ],
  "sf_user": "prod"
}'
```

### 9. Metadata Update

**Native MCP**: `metadata_update(type, metadata, sf_user)`
**MCPorter bridge**:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" metadata_update '{
  "type": "CustomObject",
  "metadata": [
    {
      "fullName": "Inspection__c",
      "label": "Inspection Updated"
    }
  ],
  "sf_user": "prod"
}'
```

## Error Handling

MCPorter returns JSON responses. Check for error fields:

```bash
RESULT=$("${CLAUDE_PLUGIN_ROOT}/scripts/mcporter-bridge.sh" soql_query '{"sObject":"Account","fields":["Id"],"sf_user":"prod"}')
echo "$RESULT"
```

Common errors:

| Error | Cause | Fix |
| --- | --- | --- |
| `mcporter: command not found` | Not installed | `npm install -g mcporter` |
| `OAuth token expired` | Cached token stale | Delete `~/.mcporter/cirra-ai/` and re-auth |
| `Connection refused` | Server unreachable | Check network; verify `https://mcp.cirra.ai/mcp` is accessible |
| `INVALID_FIELD` | Field does not exist | Use `sobject_describe` to verify field names first |

## Pre-Flight Validation

The plugin's validation scripts work the same way regardless of transport.
Run validation before executing operations:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/mcp_validator_cli.py" --format report /tmp/operation.json
```

## Limitations

- **First-call latency**: MCPorter via `npx` has cold-start overhead. Install
  globally (`npm install -g mcporter`) to avoid this.
- **Token management**: When using `CIRRA_AI_TOKEN`, you are responsible for
  token rotation and expiry. If calls start failing with auth errors, refresh
  the token.
- **No tool auto-discovery**: Claude does not automatically see MCPorter tools.
  Use this skill's reference to know which tools are available.
- **OAuth timeout**: If using OAuth fallback, browser handshakes have a 60s
  default. Override with `--oauth-timeout <ms>` or
  `export MCPORTER_OAUTH_TIMEOUT_MS=<ms>`.
