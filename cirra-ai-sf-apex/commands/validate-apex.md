---
name: validate-apex
description: Validate Salesforce Apex code with 150-point scoring. Accepts a class or trigger name (fetched from org), a local file path, a comma-separated list of names, or --all for org-wide audit of both classes and triggers.
---

Validate one or more Apex classes or triggers using the 150-point static analysis pipeline and return a scored report.

## Parsing the request

| Input after `/validate-apex` | Interpretation |
|---|---|
| `MyClass` | Class or trigger name — fetch body from org, validate |
| `<path>/MyClass.cls` (ends `.cls`) | Local class file — validate directly |
| `<path>/MyTrigger.trigger` (ends `.trigger`) | Local trigger file — validate directly |
| `MyClass,AccountTrigger,OtherClass` | Comma-separated list — bulk fetch, validate each |
| `--all` | All ApexClass **and** ApexTrigger records in the org |
| *(no argument)* | Ask the user what to validate |

## Validation script

The validation script is at `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py`. Locate it with:

```bash
# $CLAUDE_PLUGIN_ROOT is set by Claude Code when the plugin is active.
# If not set, find the script:
find ~/.claude/plugins -name "validate_apex_cli.py" 2>/dev/null | grep cirra-ai-sf-apex | head -1
```

## Workflow

### Local file

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "<file_path>"
```

### Class or trigger name (fetch from org)

1. Try to fetch as a class first:
```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<Name>'",
  fields=["Name", "Body"]
)
```

If no result, try as a trigger:
```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="Name = '<Name>'",
  fields=["Name", "Body"]
)
```

If neither returns a result, tell the user the name was not found in the org.

2. Write the body to a temp file using the appropriate extension:
```
Write /tmp/validate_<Name>.cls    ← for a class
Write /tmp/validate_<Name>.trigger  ← for a trigger
```

3. Validate:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/validate_<Name>.cls"
# or
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/validate_<Name>.trigger"
```

4. Delete the temp file after validation.

### Comma-separated list

Each name may be a class or a trigger. Fetch all in a single query per sObject type, then merge the results.

**Fetch all as classes**:
```
tooling_api_query(
  sObject="ApexClass",
  fields=["Name", "Body"],
  whereClause="Name IN ('Name1', 'Name2', 'Name3')"
)
```

**Fetch any remaining names as triggers** (names not matched above):
```
tooling_api_query(
  sObject="ApexTrigger",
  fields=["Name", "Body"],
  whereClause="Name IN ('Name1', 'Name2', 'Name3')"
)
```

**Fallback**: If either bulk fetch fails (timeout or size error), fall back to individual queries per name using the class-or-trigger lookup above.

Validate each body (write → validate → delete), using `.cls` for classes and `.trigger` for triggers. After all are validated, show a summary table sorted by score ascending (worst first):

| Name | Type | Score | % | Status |
|---|---|---|---|---|
| WeakClass | Class | 58/150 | 39% | ❌ Below threshold |
| AccountTrigger | Trigger | 102/150 | 68% | ✅ Pass |
| MyClass | Class | 125/150 | 83% | ✅ Pass |

### --all

1. Fetch all class names and all trigger names in parallel:
```
tooling_api_query(sObject="ApexClass", fields=["Name"], limit=500)
tooling_api_query(sObject="ApexTrigger", fields=["Name"], limit=200)
```

2. Fetch bodies in batches of 50 (large bodies can make bigger batches fail):
```
tooling_api_query(
  sObject="ApexClass",
  fields=["Name", "Body"],
  whereClause="Name IN (<50 names>)"
)
```

Repeat with `ApexTrigger` for trigger names.

**Backoff strategy**: If a batch of 50 fails (timeout or response size error), retry with 20 names, then 10, then fall back to individual queries for that batch.

3. Validate each body (write → validate → delete), using `.cls` or `.trigger` extension as appropriate.
4. Show the summary table (classes and triggers together) sorted by score ascending.
5. Highlight any below 100/150 (67%) as requiring attention.
