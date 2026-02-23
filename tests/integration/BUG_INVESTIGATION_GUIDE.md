# Bug Investigation Guide

**Purpose:** When a test fails unexpectedly, use this guide to reach a diagnosis
in 2–3 steps. This is the only place where plugin internals (file paths, hook
configurations, script details) should be examined.

> **Reminder:** The main test phases treat skills as black boxes. Only open this
> guide when a test produces an unexpected result.

---

## Hook / Subprocess Errors

**Symptom:** Error message containing `PreToolUse hook error` or
`python3: can't open file '...'` or `subprocess` errors when calling
`/create-apex`, `/create-flow`, `/create-lwc`, or their update variants.

### Decision Tree

```
1. Note the full path in the error message.
   └─ Path example: /home/user/.claude/plugins/.../hooks/scripts/pre-mcp-validate.py

2. Check whether that path exists:
   $ ls <path from error>

   ├─ NOT FOUND
   │  └─ Verdict: PACKAGING BUG (wrong path in hooks.json)
   │     Action: File a bug. Mark all metadata tests as BLOCKED.
   │     Do NOT attempt workarounds.
   │
   └─ FOUND
      └─ Check if it's executable:
         $ python3 <path> --help   (or any no-op invocation)

         ├─ "Permission denied" or "Read-only file system"
         │  └─ Try: chmod +x <path>
         │     ├─ chmod succeeds → retry the original test
         │     └─ chmod fails (read-only filesystem)
         │        └─ Verdict: ENVIRONMENT BUG (sandbox restrictions)
         │           Action: Mark all metadata tests as BLOCKED.
         │
         └─ Script runs but errors (ImportError, SyntaxError, etc.)
            └─ Verdict: SCRIPT BUG
               Action: Record the full traceback. File a bug.
               Mark all metadata tests as BLOCKED.
```

### What NOT to Attempt

These approaches require capabilities not available in the Claude sandbox:

- PATH shims or symlinks to redirect script execution
- `usercustomize.py` or `sitecustomize.py` hacks
- FUSE mounts or filesystem overlays
- Direct HTTP calls to bypass the MCP server
- Modifying `hooks.json` to point to a different script path

If the hook is broken, the correct action is to **mark metadata tests as
BLOCKED** and continue with data-only tests.

---

## MCP Connectivity Errors

**Symptom:** `cirra_ai_init()` fails, times out, or returns an error instead of
org information.

### Decision Tree

```
1. Is the MCP server URL configured?
   Check: .mcp.json should contain "url": "https://mcp.cirra.ai/mcp"
   ├─ Missing or malformed → Fix .mcp.json and retry
   └─ Present → continue

2. Does the MCP server respond?
   Try: call any MCP tool (e.g., cirra_ai_init)
   ├─ Timeout → Network issue or server down
   │  Action: Retry once after 30 seconds. If still failing, STOP.
   │  Verdict: INFRASTRUCTURE (MCP server unreachable)
   └─ Error response → Read the error message
      ├─ "Authentication" / "credentials" → Org credentials issue
      │  Action: Verify sf_user value and org access. File a bug if correct.
      └─ Other error → Record verbatim and file a bug
```

---

## INVALID_FIELD Errors on DML

**Symptom:** `INVALID_FIELD: No such column 'X' on sobject of type Y` when
running `/insert-data` or during update/upsert operations.

### Decision Tree

```
1. Identify the field name (X) and object (Y) from the error.

2. Run sobject_describe for Y:
   sobject_describe(sObject="Y")
   Confirm X appears in the field list.

   ├─ X is ABSENT from field list
   │  └─ Verdict: TEST DATA ERROR
   │     The field doesn't exist on this object in this org.
   │     Action: Remove X from the record payload and retry.
   │     If X was part of the test spec, update the test to note this
   │     field is org-specific.
   │
   └─ X is PRESENT in field list
      └─ Check if X is writable:
         Look at createable/updateable properties from sobject_describe.

         ├─ NOT writable (createable=false or updateable=false)
         │  └─ Verdict: FIELD RESTRICTION
         │     The field exists but cannot be set via DML in this org
         │     (profile restriction, formula, auto-number, etc.)
         │     Action: Remove X from payload. Record as known limitation.
         │
         └─ IS writable
            └─ Check field type vs. value provided:
               ├─ Type mismatch (e.g., string for a number field)
               │  └─ Fix the value type and retry
               ├─ Restricted picklist value not in picklist
               │  └─ Use a valid picklist value and retry
               └─ Other
                  └─ Verdict: BUG — record full error and file it
```

---

## Upsert External ID Errors

**Symptom:** Upsert fails with `INVALID_FIELD` or `INVALID_TYPE` related to the
external ID field.

### Decision Tree

```
1. What field was used as externalIdField?

   ├─ Standard field (Name, Id, etc.)
   │  └─ Verdict: EXPECTED FAILURE
   │     Standard fields are NOT valid upsert keys in Salesforce REST API.
   │     Action: Mark test as SKIP. A custom external ID field
   │     (e.g., ExternalId__c with External ID = true) is required.
   │
   └─ Custom field (ending in __c)
      └─ Run sobject_describe and check if the field has
         externalId=true in its properties.

         ├─ externalId=false
         │  └─ Verdict: FIELD CONFIG ERROR
         │     The field exists but is not marked as an External ID.
         │     Action: Mark as SKIP or ask admin to enable External ID
         │     on the field.
         │
         └─ externalId=true
            └─ Check if all records have a value for this field.
               ├─ Some records missing the external ID value
               │  └─ Add the value and retry
               └─ All present → Verdict: BUG. File it.
```

---

## Validation Script Errors

**Symptom:** `/validate-apex`, `/validate-flow`, or `/validate-lwc` returns an
error instead of a score.

### Decision Tree

```
1. Is the error a hook/subprocess error?
   ├─ YES → Follow "Hook / Subprocess Errors" above
   └─ NO → continue

2. Is the error "not found in the org"?
   ├─ YES → The component name is wrong or wasn't deployed
   │  Action: Verify the component exists:
   │  - For Apex: tooling_api_query(sObject="ApexClass", whereClause="Name = '...'")
   │  - For Flow: metadata_list(type="Flow")
   │  - For LWC: tooling_api_query(sObject="LightningComponentBundle", ...)
   │  If not found, the deployment in Phase 1b likely failed. Mark as BLOCKED.
   └─ NO → continue

3. Is it a Python error (ImportError, ModuleNotFoundError)?
   ├─ YES → Verdict: PACKAGING BUG (missing dependency)
   │  Action: Record the full traceback. File a bug.
   └─ NO → Record the full error and file a bug.
```

---

## Metadata Deployment Errors

**Symptom:** `metadata_create` or `tooling_api_dml` returns an error when
deploying Apex, Flow, or LWC.

### Decision Tree

```
1. Read the error message from the MCP response.

   ├─ "duplicate value found" or "already exists"
   │  └─ Verdict: DUPLICATE
   │     The component was already deployed (possibly from a previous run).
   │     Action: Use the update command instead, or clean up first with
   │     99_cleanup.md and retry.
   │
   ├─ "Compile Error" or "Unexpected token"
   │  └─ Verdict: CODE GENERATION BUG
   │     The generated code has a syntax error.
   │     Action: Record the error. File a bug against the create command.
   │
   ├─ "insufficient access" or "permission"
   │  └─ Verdict: ORG PERMISSION
   │     The connected user doesn't have deploy permissions.
   │     Action: Mark as BLOCKED. Requires admin access.
   │
   └─ Other error
      └─ Record verbatim and file a bug.
```

---

## Audit Errors

**Symptom:** `/audit-org` fails or produces incomplete results.

### Decision Tree

```
1. At what phase did the audit fail?

   ├─ Phase 1 (counting components)
   │  └─ Likely an MCP connectivity issue.
   │     Follow "MCP Connectivity Errors" above.
   │
   ├─ Phase 2/3/4 (fetching and scoring)
   │  └─ Check for timeout errors:
   │     ├─ Timeout on large batches → Expected for large orgs
   │     │  The audit should retry with smaller batch sizes.
   │     │  If it doesn't, file a bug.
   │     └─ Other error → Record and file a bug.
   │
   └─ Phase 5 (report generation)
      └─ Check for file system errors:
         ├─ "Permission denied" writing to ./audit_output/
         │  └─ Try creating the directory manually and retry
         └─ Other → Record and file a bug.
```

---

## Filing a Bug

When filing a bug, include:

1. **Test case ID** (e.g., TC-050)
2. **Error message** — verbatim, not paraphrased
3. **Command used** — the exact skill command and arguments
4. **Expected vs actual** — what should have happened vs what did
5. **Environment** — org username, date, session context
6. **Investigation verdict** — which decision tree was followed and what
   conclusion was reached
