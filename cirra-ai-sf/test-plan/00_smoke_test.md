# Phase 0 — Smoke Tests

**Time estimate:** ~2 minutes
**Purpose:** Verify the three core paths (MCP connectivity, data DML, metadata
deployment) are functional before running the full suite.

---

## Prerequisites

- [ ] Org credentials configured (e.g., `admin@demo2.cirra.ai.dev`)
- [ ] cirra-ai-sf plugin is loaded (MCP tools available)

---

## Smoke Test Gate

```
All three smoke tests must return "success" or a validation result
(not a hook/subprocess error) before proceeding to Phase 1.

If any smoke test returns a hook/subprocess error → STOP, file Bug,
mark all metadata tests as BLOCKED, and proceed with data-only tests (01a).
```

---

## Tests

### TC-001 — MCP connectivity

**Command:** Call `cirra_ai_init()` via the MCP server.
**Expected:**

- Returns the connected org name and username
- No connection errors or timeouts
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § MCP Connectivity Errors

**Result:**

| Field             | Value |
| ----------------- | ----- |
| Status            |       |
| Org name returned |       |
| Username returned |       |
| Notes             |       |

---

### TC-002 — Data path (insert + query)

**Command:** `/insert-data` — insert 1 Account with Name = `CirraTest_Smoke`
**Expected:**

- Record inserted successfully, record ID returned
- No hook errors or subprocess errors
  **Verify:** `/query-data` — `SELECT Id, Name FROM Account WHERE Name = 'CirraTest_Smoke' LIMIT 1`
- Returns exactly 1 record with the matching Name
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § INVALID_FIELD Errors on DML

**Result:**

| Field                | Value |
| -------------------- | ----- |
| Status               |       |
| Record ID            |       |
| Query returned match |       |
| Notes                |       |

---

### TC-003 — Metadata path (create Apex)

**Command:** `/create-apex` — create a trivial Apex class:

```
Class name: CirraTest_SmokeCheck
Type: Service class
Purpose: Return a hardcoded string "smoke-ok"
```

The class body should be approximately:

```apex
public with sharing class CirraTest_SmokeCheck {
    public static String check() {
        return 'smoke-ok';
    }
}
```

**Expected:**

- Class created successfully via `tooling_api_dml`, OR
- Clear validation error from the pre-deployment hook (still counts as PASS — the hook is functional)
- **NOT** a hook subprocess error (e.g., `python3: can't open file '...'`)
  **On unexpected failure:** See BUG_INVESTIGATION_GUIDE.md § Hook / Subprocess Errors

**Result:**

| Field                 | Value |
| --------------------- | ----- |
| Status                |       |
| Deployed successfully |       |
| Validation score      |       |
| Error (if any)        |       |
| Notes                 |       |

---

## Gate Decision

| TC-001 | TC-002 | TC-003                  | Decision                                                                  |
| ------ | ------ | ----------------------- | ------------------------------------------------------------------------- |
| PASS   | PASS   | PASS                    | Proceed to 01a + 01b                                                      |
| PASS   | PASS   | FAIL (hook error)       | Proceed to 01a only. Mark 01b, metadata tests in 02/03, and 04 as BLOCKED |
| PASS   | PASS   | FAIL (validation error) | Investigate validation issue, but data path is clear. Proceed to 01a      |
| PASS   | FAIL   | any                     | Investigate data path. MCP may be misconfigured. Do not proceed           |
| FAIL   | any    | any                     | MCP not reachable. Do not proceed. File connectivity bug                  |

Record the gate decision here before continuing:

**Gate decision:** **********************\_\_\_**********************
**Blocked phases (if any):** ****************\_\_\_\_****************
