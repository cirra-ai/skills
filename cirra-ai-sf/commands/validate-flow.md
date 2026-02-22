---
name: validate-flow
description: Validate a Salesforce Flow with 110-point scoring. Accepts a flow API name (fetched from org), a local file path, a comma-separated list of flow names, or All for org-wide audit.
---

Validate one or more Flows using the 110-point static analysis pipeline and return a scored report.

## Parsing the request

| Input after `/validate-flow`                                                         | Interpretation                                   |
| ------------------------------------------------------------------------------------ | ------------------------------------------------ |
| `Auto_Lead_Assignment`                                                               | Flow API name — fetch XML from org, validate     |
| `force-app/.../Auto_Lead_Assignment.flow-meta.xml` (ends `.flow-meta.xml` or `.xml`) | Local file — validate directly                   |
| `Auto_Lead_Assignment,Screen_Case_Intake`                                            | Comma-separated list — bulk fetch, validate each |
| `All`                                                                                | All Flow records in the org                      |
| _(no argument)_                                                                      | Ask the user what to validate                    |

## Validation script

The validation script is at `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_flow_cli.py`. Locate it with:

```bash
# $CLAUDE_PLUGIN_ROOT is set by Claude Code when the plugin is active.
# If not set, find the script:
find ~/.claude/plugins -name "validate_flow_cli.py" 2>/dev/null | grep cirra-ai-sf-flow | head -1
```

## Workflow

### Local file

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_flow_cli.py" "<file_path>"
```

### Flow API name (fetch from org)

1. Fetch the Flow XML:

```
metadata_read(
  type="Flow",
  fullNames=["<FlowApiName>"],
  sf_user="<sf_user>"
)
```

2. Write the XML content to a temp file:

```
Write /tmp/validate_<FlowApiName>.flow-meta.xml  ← the flow XML
```

3. Validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_flow_cli.py" "/tmp/validate_<FlowApiName>.flow-meta.xml"
```

4. Delete the temp file after validation.

### Comma-separated list

Fetch all flow XML bodies in a single call:

```
metadata_read(
  type="Flow",
  fullNames=["Flow1", "Flow2", "Flow3"],
  sf_user="<sf_user>"
)
```

**Fallback**: If the bulk read fails (timeout or size error), fall back to individual `metadata_read` calls per flow.

Validate each flow body (write → validate → delete). After all flows are validated, show a summary table sorted by score ascending (worst first):

| Flow                        | Score  | %   | Status             |
| --------------------------- | ------ | --- | ------------------ |
| Before_Opportunity_Validate | 72/110 | 65% | ❌ Below threshold |
| Auto_Lead_Assignment        | 98/110 | 89% | ✅ Pass            |

### All

1. Fetch all flow names:

```
metadata_list(type="Flow", sf_user="<sf_user>")
```

2. Fetch flow XML in batches of 20 (large flows can make bigger batches fail):

```
metadata_read(
  type="Flow",
  fullNames=["Flow1", ..., "Flow20"],
  sf_user="<sf_user>"
)
```

**Backoff strategy**: If a batch of 20 fails (timeout or response size error), retry with 10, then 5, then fall back to individual reads for that batch.

3. Validate each flow (write → validate → delete).
4. Show the summary table sorted by score ascending.
5. Highlight any below 88/110 (80%) as requiring attention.
