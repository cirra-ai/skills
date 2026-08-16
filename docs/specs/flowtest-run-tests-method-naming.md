# Backend + skill correction: Flow Test `run_tests` method naming

**Status:** Ready for `cloud-app` updates (skill docs shipped in [#141](https://github.com/cirra-ai/skills/pull/141))  
**Date:** 2026-08-09 (skill-ship note updated 2026-08-16)  
**Repos:** `cirra-ai/cloud-app` (`run_tests` MCP tool); skill text lives in `skills/sf-flow` via #141  
**Verified against:** Integration Test Org (Cirra int-test sandbox)  
**Harness left in org (CirraTest\*):** flow `CirraTest_Before_Lead_Set_Rating_Hot` + three `FlowTest` records

This documents a **live mismatch** between (a) Salesforce Tooling docs / prior Cirra skill text / MCP tool schema, and (b) what the org actually accepts for Flow Test method names. The `{flowTestApiName}` naming is now documented in `sf-flow` 2.5.1 (#141); remaining work is cloud-app schema/behavior.

---

## 1. Bug

### Symptom

`run_tests` with the documented compound method name returns a job that finishes as **`ApexTestRunResult.Status = Failed`** with **`MethodsCompleted = 0`** — the Flow Test never runs:

```json
{
  "tests": [
    {
      "className": "FlowTesting.CirraTest_Before_Lead_Set_Rating_Hot",
      "testMethods": ["CirraTest_Before_Lead_Set_Rating_Hot_CirraTest_Lead_Rating_Hot_When_Tech"]
    }
  ],
  "skipCodeCoverage": "true"
}
```

### Control that works

Same class, method = **FlowTest API name only**:

```json
{
  "tests": [
    {
      "className": "FlowTesting.CirraTest_Before_Lead_Set_Rating_Hot",
      "testMethods": ["CirraTest_Lead_Rating_Hot_When_Tech"]
    }
  ],
  "skipCodeCoverage": "true"
}
```

Result: `ApexTestRunResult.Status = Completed`, `ApexTestResult.Outcome = Pass`, `FlowTestResult.Result = Pass`.

Omitting `testMethods` (run every method on the synthetic class) also works.

### Where the wrong name is / was documented

| Surface                                                            | Status                                                                                  |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| `run_tests` MCP tool schema (`testMethods` / `tests` descriptions) | **Still wrong** — `'{flowApiName}_{flowTestApiName}'` (BE-1)                            |
| `skills/sf-flow`                                                   | **Fixed in #141** (2.5.1) — documents bare `{flowTestApiName}`                          |
| Salesforce Tooling async runner docs (narrative)                   | Still shows examples shaped like `FlowName_UpdateRecordFlowTest`; trust live MethodName |

Live `ApexTestResult.MethodName` for a successful run is the **FlowTest developer name alone** (e.g. `CirraTest_Lead_Rating_Hot_When_Tech`), not the compound form.

---

## 2. Verified end-to-end matrix (int-test)

Harness:

- Active before-save Flow: `CirraTest_Before_Lead_Set_Rating_Hot` (sets `Lead.Rating = Hot` when `Industry = Technology`)
- FlowTests:
  - `CirraTest_Lead_Rating_Hot_When_Tech` (assert Hot) → **Pass**
  - `CirraTest_Lead_Rating_Hot_Pass2` (assert Hot) → **Pass**
  - `CirraTest_Lead_Rating_Wrong_Assert` (assert Cold) → **Fail**

| Call                                                              | Result                                                                         |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `metadata_create(type="FlowTest", …)`                             | Success; Tooling Id prefix `320`                                               |
| `metadata_read` round-trip                                        | Single-element arrays collapse to objects; `isUseMockOutput: "false"` (string) |
| `className=FlowTesting.{flow}`, `testMethods=[{flowTestApiName}]` | Runs; Pass/Fail as asserted                                                    |
| `testMethods=[{flowApiName}_{flowTestApiName}]`                   | Job `Failed`, `MethodsCompleted=0`                                             |
| omit `testMethods`                                                | Runs all discovered FlowTests for that flow                                    |
| `testLevel=RunLocalTests`, `category=["Flow"]`                    | Org-wide Flow tests run                                                        |

### Secondary observations (not the primary bug)

1. **Discovery lag after create.** A brand-new `FlowTest` can be absent from class-wide / named runs for ~1–2 minutes even though Tooling `FlowTest` already returns the row. Retry after a short wait; do not assume create failure.
2. **`ApexTestResult.Message` empty on Fail.** On intentional assertion failures, `Outcome`/`FlowTestResult.Result` were `Fail`, but `Message` was absent/null in MCP responses. Do not rely on `Message` for the FlowTest `errorMessage` until re-verified; prefer `Outcome` + `FlowTestResult`.
3. **Job Id length.** `run_tests` returns a 15-char `jobId`; Tooling stores 18-char `AsyncApexJobId`. Prefix match works for `WHERE AsyncApexJobId = '707…'`, but prefer the 18-char value from `ApexTestRunResult` when querying `ApexTestResult`.
4. **No `ApexClass` row.** Confirmed: no Tooling `ApexClass` with `NamespacePrefix = FlowTesting` for the harness — synthetic addressing only.

---

## 3. Required behavior

### 3.1 Contract agents should use (skills)

```text
className   = FlowTesting.{flowApiName}
testMethods = [ {flowTestApiName}, ... ]   // NOT {flowApiName}_{flowTestApiName}
```

Example (corrected):

```
run_tests(tests=[{
  "className": "FlowTesting.SDO_Change_Request_Set_Priority_Based_on_Impact",
  "testMethods": ["Test_CR_Priority_High"]
}], skipCodeCoverage="true")
```

Poll:

1. `ApexTestRunResult` by `AsyncApexJobId` until `Completed` / `Failed` / `Aborted`
2. `ApexTestResult` for `Outcome` / `MethodName` (MethodName = FlowTest API name)
3. `FlowTestResult` for `Result` / `FlowTestId` / `FlowVersionNumber`

### 3.2 Contract `run_tests` MCP should advertise (cloud-app)

Tool descriptions must say Flow Test methods are **`{flowTestApiName}`**, matching live `ApexTestResult.MethodName`.

---

## 4. Backend changes (`cloud-app`)

### BE-1 — Fix `run_tests` tool schema copy (required, trivial)

Update JSON Schema / tool description strings that currently claim:

- `FlowTesting.{flowApiName}` + `'{flowApiName}_{flowTestApiName}'`

to:

- `className`: `FlowTesting.{flowApiName}`
- `testMethods`: `{flowTestApiName}` (FlowTest developer name / metadata `fullName`)

Also update any internal prompt snippets or OpenAPI examples that repeat the compound form.

### BE-2 — Optional normalize compound → FlowTest name (recommended)

If `className` matches `FlowTesting.{flowApiName}` (optional namespace: `FlowTesting.{ns}.{flowApiName}`) and a `testMethods` entry equals `{flowApiName}_{suffix}` where `suffix` is a known FlowTest for that flow, rewrite to `suffix` before calling Salesforce.

Safer variant without Tooling lookup: if method starts with `{flowApiName}_`, strip that prefix once and send the remainder. Log a warning when rewriting so agents can correct.

Acceptance: the previously failing compound call becomes a successful enqueue that produces `ApexTestResult` rows.

### BE-3 — Surface “method not found / not run” clearly (recommended)

Today a bad method name yields `ApexTestRunResult.Status=Failed` with `MethodsCompleted=0` and **no** `ApexTestResult` rows — agents cannot tell “wrong name” from “org outage”.

After `run_tests` returns `jobId`, either:

- document that agents must treat `Status=Failed` + `MethodsCompleted=0` as “nothing ran (bad class/method name or discovery lag)”, and/or
- have the MCP helper poll once and, when that pattern is seen, return a structured error:

```json
{
  "success": false,
  "errorCode": "FLOW_TEST_METHOD_NOT_RUN",
  "message": "No Flow Test methods completed. For FlowTests use testMethods=[{flowTestApiName}] under className=FlowTesting.{flowApiName}. Compound {flowApiName}_{flowTestApiName} is not accepted by this org.",
  "jobId": "707…"
}
```

(If the product keeps `run_tests` fire-and-forget, put this guidance only in the tool description — still update the schema per BE-1.)

### BE-4 — Assertion message on Fail (investigate)

Confirm whether Salesforce populates `ApexTestResult.Message` for Flow Test failures with the FlowTest assertion `errorMessage`. If the platform does and Cirra strips null/empty fields, keep stripping but document that Flow fails often have empty `Message`. If Cirra drops non-null values, fix that. Prefer linking `FlowTestResult` in any enriched response.

### BE-5 — Out of scope

- Creating/activating Flows or FlowTests (already works via `metadata_*`)
- Synchronous runner (`runTestsSynchronous`) unless product wants it later
- JSON Patch nested-add (`docs/specs/json-patch-named-path-nested-add.md`) — separate ticket

---

## 5. Skills changes (`skills/sf-flow`) — done in #141

Shipped in [#141](https://github.com/cirra-ai/skills/pull/141) (`sf-flow` 2.5.1). Do **not** re-land a competing `SKILL.md` edit from this specs PR. #141 also went further than the early draft of this doc on:

- sparse `$Record` inputs → `FlowTestResult.Result: Error` (not a silent Pass)
- `category=["Flow"]` does **not** reliably filter to Flow-only runs
- `ApexTestRunResult` counters can be unreliable; prefer per-result objects
- `FlowTestResult.Result` uses `Error` vs `Fail` distinctions

This PR keeps only the BE-facing specs. Further skill tweaks belong in follow-up skill PRs, not here.

---

## 6. Test plan

### BE unit / contract

| ID     | Case                                                                                           | Expect |
| ------ | ---------------------------------------------------------------------------------------------- | ------ |
| BE-RT1 | Schema / description mentions `{flowTestApiName}` only                                         | Pass   |
| BE-RT2 | (If BE-2) compound method rewritten to FlowTest name before HTTP call                          | Pass   |
| BE-RT3 | (If BE-3) Failed job with 0 completed methods returns `FLOW_TEST_METHOD_NOT_RUN` or equivalent | Pass   |

### Live int-test harness (already green once; re-run after BE deploy)

| ID     | Case                                                  | Expect                                                              |
| ------ | ----------------------------------------------------- | ------------------------------------------------------------------- |
| LV-RT1 | `testMethods=["CirraTest_Lead_Rating_Hot_When_Tech"]` | Pass                                                                |
| LV-RT2 | `testMethods=["CirraTest_Lead_Rating_Wrong_Assert"]`  | Fail assertion (`Outcome=Fail` / `FlowTestResult.Result` Fail)      |
| LV-RT3 | compound `{flow}_{test}`                              | After BE-2: runs; without BE-2: still Failed/0 completed (document) |
| LV-RT4 | omit `testMethods`                                    | All three CirraTest methods appear                                  |
| LV-RT5 | `testLevel=RunLocalTests`, `category=["Flow"]`        | May still enqueue Apex; do not treat as Flow-only (see #141)        |

---

## 7. Suggested rollout

1. **skills:** done — `sf-flow` 2.5.1 via #141.
2. **cloud-app:** BE-1 immediately (stops new agents from copying the wrong name from the MCP schema).
3. **cloud-app:** BE-2 / BE-3 as follow-ups for resilience.
4. Re-run LV-RT1…RT5 on int-test after deploy; delete CirraTest harness when no longer needed.
