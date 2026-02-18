---
name: validate-apex
description: Validate Salesforce Apex code with 150-point scoring. Accepts a class name (fetched from org), a local file path, a comma-separated list of class names, or --all for org-wide audit.
---

Validate one or more Apex classes using the 150-point static analysis pipeline and return a scored report.

## Parsing the request

| Input after `/validate-apex` | Interpretation |
|---|---|
| `MyClass` | Class name — fetch body from org, validate |
| `force-app/.../MyClass.cls` (ends `.cls` or `.trigger`) | Local file — validate directly |
| `MyClass,OtherClass,ThirdClass` | Comma-separated list — validate each in sequence |
| `--all` | All ApexClass records in the org |
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

### Class name (fetch from org)

1. Fetch the class body:
```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<ClassName>'",
  fields=["Name", "Body"]
)
```

2. Write the body to a temp file:
```
Write /tmp/validate_<ClassName>.cls  ← the class body
```

3. Validate:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate_apex_cli.py" "/tmp/validate_<ClassName>.cls"
```

4. Delete the temp file after validation.

### Comma-separated list

Validate each class using the class name workflow above. After all classes are validated, show a summary table sorted by score ascending (worst first):

| Class | Score | % | Status |
|---|---|---|---|
| WeakClass | 58/150 | 39% | ❌ Below threshold |
| MyClass | 125/150 | 83% | ✅ Pass |

### --all

1. Fetch all class names:
```
tooling_api_query(sObject="ApexClass", fields=["Name"], limit=200)
```

2. Validate each using the class name workflow.
3. Show the summary table sorted by score ascending.
4. Highlight any below 100/150 (67%) as requiring attention.

## Disabling validation

To disable automatic pre-deployment validation for a project, create a file named `.no-apex-validation` in the project root. The hook will silently skip. Remove the file to re-enable.

This command always runs validation regardless of that flag.
