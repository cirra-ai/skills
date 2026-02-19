---
name: validate-data
description: Run pre-flight validation on a Salesforce data operation before executing it. Accepts a tool name and JSON parameters, or a local JSON file. Catches structural errors and PII before hitting the org.
---

Validate a Salesforce data operation using the two-tier MCP validator and return a report.

## Parsing the request

| Input after `/validate-data` | Interpretation |
|---|---|
| `path/to/operation.json` | Local JSON file containing `{"tool": "...", "params": {...}}` |
| `soql_query SELECT Id FROM Account` | Inline SOQL — validate query parameters |
| `sobject_dml insert Account 50 records` | Describe the operation — build params and validate |
| *(no argument)* | Ask the user what to validate |

## Validation script

The validator is at `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/mcp_validator_cli.py`. Locate it with:

```bash
# $CLAUDE_PLUGIN_ROOT is set by Claude Code when the plugin is active.
# If not set, find the script:
find ~/.claude/plugins -name "mcp_validator_cli.py" 2>/dev/null | grep cirra-ai-sf-data | head -1
```

## Workflow

### Local JSON file

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/mcp_validator_cli.py" --format report operation.json
```

### Inline or described operation

1. Construct the operation JSON:

```json
{
  "tool": "sobject_dml",
  "params": {
    "sObject": "Account",
    "operation": "insert",
    "records": [
      {"Name": "Test Account 1", "Industry": "Technology"}
    ],
    "sf_user": "prod"
  }
}
```

2. Write to a temp file:
```
Write /tmp/validate_op.json  ← the JSON above
```

3. Validate:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/mcp_validator_cli.py" --format report /tmp/validate_op.json
```

4. Delete the temp file after validation.

## Tier 1: Data operations (soql_query, sobject_dml)

Simple pass/fail. Catches:

| Check | Severity |
|---|---|
| Missing `sObject` or `sf_user` | Error |
| Invalid DML `operation` | Error |
| Empty records array | Error |
| Update/delete missing `Id` | Error |
| Upsert missing `externalIdField` | Error |
| PII in record values | Warning |
| Inconsistent field names across records | Warning |
| SOQL syntax issues (`==`, unbalanced parens, double quotes) | Warning |

## Tier 2: Code deployment (metadata_create, metadata_update, tooling_api_dml)

Full scoring when the payload contains Apex or Flow metadata. Delegates to:

| Metadata Type | Validator | Max Score |
|---|---|---|
| ApexClass / ApexTrigger | ApexValidator | 150 |
| Flow / FlowDefinition | EnhancedFlowValidator | 110 |
| Other | (skipped) | — |
