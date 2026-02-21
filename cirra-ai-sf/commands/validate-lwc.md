---
name: validate-lwc
description: Validate a Lightning Web Component with 165-point SLDS 2 scoring. Accepts a component name (fetched from org), a local file path, a comma-separated list of component names, or --all for org-wide audit.
---

Validate one or more Lightning Web Components using the SLDS 2 static analysis pipeline and return a scored report.

## Parsing the request

| Input after `/validate-lwc`                                            | Interpretation                                   |
| ---------------------------------------------------------------------- | ------------------------------------------------ |
| `accountDashboard`                                                     | Component name — fetch bundle from org, validate |
| `force-app/.../accountDashboard.html` (ends `.html`, `.css`, or `.js`) | Local file — validate directly                   |
| `accountDashboard,contactCard`                                         | Comma-separated list — bulk fetch, validate each |
| `--all`                                                                | All LightningComponentBundle records in the org  |
| _(no argument)_                                                        | Ask the user what to validate                    |

## Validation script

```bash
# $CLAUDE_PLUGIN_ROOT is set by Claude Code when the plugin is active.
# If not set, find the script:
VALIDATOR=$(find ~/.claude/plugins -name "validate_slds.py" 2>/dev/null | grep cirra-ai-sf-lwc | head -1)
```

## Workflow

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

### --all

1. List all deployed components:

```
metadata_list(type="LightningComponentBundle")
```

2. Fetch and validate each component bundle in batches of 10.

**Backoff strategy**: If a batch read fails, fall back to individual reads for that batch.

3. Validate each bundle (write → validate → delete).
4. Show the summary table sorted by combined score ascending.
5. Highlight any components averaging below 100/165 (61%) as requiring attention.
