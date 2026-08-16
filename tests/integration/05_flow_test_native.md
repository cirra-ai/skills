# Phase 5 — Native Flow Test (`FlowTest`) End-to-End

**Time estimate:** ~5 minutes
**Purpose:** Verify the full native Flow Test lifecycle through the Cirra AI MCP
server — create, metadata read-back, Tooling read-back, asynchronous run, result
interpretation, and delete — and confirm that the platform behaviours the
`sf-flow` skill documents still hold.

This phase is **self-contained**. It creates every artifact it needs, asserts on
them, and deletes them. It leaves no residue in the org and depends on no other
phase.

---

## Scope and rationale

Native Flow Tests (`FlowTest`) are declarative tests attached to
**record-triggered flows only** (`RecordBeforeSave` / `RecordAfterSave`). They
are a Metadata API artifact that executes on the **Apex** async test
infrastructure. That split is the source of most of the surprises below, and it
is why this phase asserts on **two** result objects rather than one.

Three things this phase is specifically designed to catch:

1. `metadata_create` silently accepting a `FlowTest` whose assertion is wrong —
   creation never evaluates assertions, so a create-only test proves very little.
2. A regression in which `Error` (the test could not execute) becomes
   indistinguishable from `Fail` (the assertion evaluated and was false).
3. A regression in the read-back shape that breaks read → re-deploy round-trips.

---

## Prerequisites

- [ ] A Salesforce connection is selected and `cirra_ai_init` reports
      `capabilities.canUseMetadataApi: true`
- [ ] The org is on **API version 65.0 or later** (flow test support minimum)
- [ ] A **record-triggered** flow exists with a deterministic, assertable branch

### Parameters

Set these once; every step below refers to them.

| Parameter  | Value used in the reference run                                           |
| ---------- | ------------------------------------------------------------------------- |
| `{ORG}`    | your selected org connection — reference run used a Cirra AI SDO demo org |
| `{FLOW}`   | `SDO_Change_Request_Set_Priority_Based_on_Impact`                         |
| `{OBJECT}` | `ChangeRequest`                                                           |
| `{BRANCH}` | `Impact = High` → `Priority = High`                                       |
| `{PREFIX}` | `Cirra_Probe_` — every artifact this phase creates carries it             |

**Substituting a different flow:** pick a before-save flow whose branch is
unconditional in the org (no gate custom permission, no org-default toggle that
could be off), and populate `{OBJECT}`'s commonly-required fields in the
triggering record — see TC-505 for why.

If the reference flow is gated by a toggle such as
`xDO_Tool_ProcessAutomation__c`, confirm the org default is `true` before
treating a `Fail` as a real regression.

---

## Pre-flight — clean slate

**Command:** `metadata_list(type="FlowTest")`

**Expected:** No records carrying `{PREFIX}`. `metadata_list` does return
`FlowTest` records — with `fullName`, `id`, `manageableState` and audit fields —
when any exist, so an empty result here means an empty org rather than a blind
spot in the listing.

If any `{PREFIX}` records exist, a prior run of this phase aborted; delete them
before continuing:

```
metadata_delete(type="FlowTest", fullNames=["Cirra_Probe_..."])
```

Do **not** delete `FlowTest` records that lack `{PREFIX}` — those belong to the org.

---

## Tests

### TC-501 — Create (`metadata_create`, three variants in one call)

**Command:**

```
metadata_create(type="FlowTest", metadata=[
  {
    "fullName": "Cirra_Probe_CR_Priority_Pass",
    "label": "Cirra Probe - CR Priority Pass",
    "description": "E2E probe. Safe to delete.",
    "flowApiName": "{FLOW}",
    "testType": "WithAssertion",
    "testPoints": [
      {"elementApiName": "Start", "parameters": [
        {"leftValueReference": "$Record", "type": "InputTriggeringRecordInitial",
         "value": {"sobjectValue": "{\"Impact\":\"High\",\"Subject\":\"Router upgrade\"}"}}]},
      {"elementApiName": "Finish", "assertions": [
        {"conditions": [
          {"leftValueReference": "$Record.Priority", "operator": "EqualTo",
           "rightValue": {"stringValue": "High"}}],
         "errorMessage": "Priority should be High when Impact is High"}]}
    ]
  },
  {
    "fullName": "Cirra_Probe_CR_Priority_Fail",
    "label": "Cirra Probe - CR Priority Fail",
    "description": "E2E probe: deliberately wrong assertion. Safe to delete.",
    "flowApiName": "{FLOW}",
    "testType": "WithAssertion",
    "testPoints": [
      {"elementApiName": "Start", "parameters": [
        {"leftValueReference": "$Record", "type": "InputTriggeringRecordInitial",
         "value": {"sobjectValue": "{\"Impact\":\"High\",\"Subject\":\"Router upgrade\"}"}}]},
      {"elementApiName": "Finish", "assertions": [
        {"conditions": [
          {"leftValueReference": "$Record.Priority", "operator": "EqualTo",
           "rightValue": {"stringValue": "Low"}}],
         "errorMessage": "Deliberately wrong: asserts Priority is Low"}]}
    ]
  },
  {
    "fullName": "Cirra_Probe_CR_Priority_Sparse",
    "label": "Cirra Probe - CR Priority Sparse",
    "description": "E2E probe: sparse triggering record. Safe to delete.",
    "flowApiName": "{FLOW}",
    "testType": "WithAssertion",
    "testPoints": [
      {"elementApiName": "Start", "parameters": [
        {"leftValueReference": "$Record", "type": "InputTriggeringRecordInitial",
         "value": {"sobjectValue": "{\"Impact\":\"High\"}"}}]},
      {"elementApiName": "Finish", "assertions": [
        {"conditions": [
          {"leftValueReference": "$Record.Priority", "operator": "EqualTo",
           "rightValue": {"stringValue": "High"}}],
         "errorMessage": "Priority should be High when Impact is High"}]}
    ]
  }
])
```

**Expected:**

- `successCount: 3`, `errorCount: 0`
- **All three succeed, including the one with the deliberately wrong assertion.**
  This is the point of the variant: creation does not evaluate assertions. If
  `Cirra_Probe_CR_Priority_Fail` is rejected at create time, that is a _change in
  platform behaviour_, not a pass.

**Result:**

| Field                            | Value |
| -------------------------------- | ----- |
| Status                           |       |
| successCount / errorCount        |       |
| Wrong-assertion variant accepted |       |
| Notes                            |       |

---

### TC-502 — Metadata read-back shape (`metadata_read`)

**Command:**

```
metadata_read(type="FlowTest", fullNames=[
  "Cirra_Probe_CR_Priority_Pass",
  "Cirra_Probe_CR_Priority_Fail",
  "Cirra_Probe_CR_Priority_Sparse"])
```

**Expected — three shape assertions:**

1. All three read back with `flowApiName`, `testType`, `label`, `description` intact.
2. **Single-element arrays collapse to bare objects.** `parameters`,
   `assertions` and `conditions` each read back as `{…}`, not `[{…}]`. This is
   standard Metadata API XML→JSON behaviour, not data loss.
3. **`isUseMockOutput` is injected on every test point as the string `"false"`**,
   not a boolean, and was not present in the create payload.

Any consumer that iterates these fields must normalize to an array first.

**Result:**

| Field                             | Value |
| --------------------------------- | ----- |
| Status                            |       |
| Arrays collapsed to objects       |       |
| `isUseMockOutput` present, string |       |
| Any field lost in read-back       |       |
| Notes                             |       |

---

### TC-503 — Tooling read-back (`tooling_api_query`)

**Command:**

```
tooling_api_query(sObject="FlowTest",
  fields=["Id","DeveloperName","MasterLabel","TestType"],
  whereClause="DeveloperName LIKE 'Cirra_Probe_%'")
```

**Expected:**

- Exactly 3 records
- IDs carry the `320` key prefix
- Field-name mapping holds: `DeveloperName` ↔ `fullName`,
  `MasterLabel` ↔ `label`, `TestType` ↔ `testType`

**Result:**

| Field               | Value |
| ------------------- | ----- |
| Status              |       |
| Records returned    |       |
| Key prefix is `320` |       |
| Notes               |       |

---

### TC-504 — Run (`run_tests`)

**Command:**

```
run_tests(tests=[{
  "className": "FlowTesting.{FLOW}",
  "testMethods": [
    "Cirra_Probe_CR_Priority_Pass",
    "Cirra_Probe_CR_Priority_Fail",
    "Cirra_Probe_CR_Priority_Sparse"]
}], skipCodeCoverage="true")
```

Notes on the call shape:

- `className` **must** carry the `FlowTesting.` prefix. A bare flow name is
  rejected with `INVALID_INPUT`.
- `skipCodeCoverage` is a **string**, not a boolean, on this endpoint.
- The response `testCount` counts **classes**, not methods. A `testCount: 1` for
  three methods is correct, not a truncation.

**Expected:** a `jobId` beginning `707`. Then poll:

```
tooling_api_query(sObject="ApexTestRunResult",
  fields=["Id","AsyncApexJobId","Status","MethodsEnqueued","MethodsCompleted","MethodsFailed"],
  whereClause="AsyncApexJobId = '{jobId}'")
```

`Status` is `Queued` / `Preparing` / `Processing` while running; `Completed`,
`Failed` or `Aborted` once finished. Three flow tests finish within seconds.

Use this query **only** to tell "finished" from "still running". Take every
verdict from TC-505.

**Result:**

| Field                                   | Value |
| --------------------------------------- | ----- |
| Status                                  |       |
| jobId                                   |       |
| Run Status                              |       |
| MethodsEnqueued / Completed / Failed    |       |
| Polls needed to reach a terminal Status |       |
| Notes                                   |       |

---

### TC-505 — Result interpretation (the load-bearing assertion)

**Command — per-test Apex outcome:**

```
tooling_api_query(sObject="ApexTestResult",
  fields=["Id","MethodName","Outcome","Message","StackTrace"],
  whereClause="AsyncApexJobId = '{jobId}'")
```

**Command — flow-specific result:**

```
tooling_api_query(sObject="FlowTestResult",
  fields=["Id","FlowTestId","FlowDefinitionId","FlowVersionNumber","Result","TestStartDateTime","TestEndDateTime","ApexTestResultId"],
  whereClause="ApexTestResultId IN ('{apexTestResultIds}')")
```

**Expected — the two objects must disagree, and that disagreement is the assertion:**

| Probe     | `ApexTestResult.Outcome` | `FlowTestResult.Result` | Meaning                           |
| --------- | ------------------------ | ----------------------- | --------------------------------- |
| `_Pass`   | `Pass`                   | `Pass`                  | Assertion evaluated and held      |
| `_Fail`   | `Fail`                   | `Fail`                  | Assertion evaluated and was false |
| `_Sparse` | `Fail`                   | **`Error`**             | Test could not execute at all     |

**`ApexTestResult.Outcome` collapses `Error` into `Fail`.** Only
`FlowTestResult.Result` separates "your assertion is wrong" from "your test never
ran." Any tooling that reports flow-test verdicts from `ApexTestResult` alone
will mislabel a broken test as a failing one.

- `_Pass` returning `Pass` proves assertions are genuinely evaluated at run time,
  which TC-501 could not prove.
- `_Sparse` differing from `_Pass` **only** in the triggering record proves the
  cause is record sparseness, not the assertion. If `_Sparse` returns `Pass`, the
  platform has become more tolerant — note it, do not treat it as a failure of
  this phase.
- `Message` was empty on both failures in the reference run. Do not depend on the
  `errorMessage` surfacing there.

**Result:**

| Probe     | `Outcome` | `Result` | Matches expectation |
| --------- | --------- | -------- | ------------------- |
| `_Pass`   |           |          |                     |
| `_Fail`   |           |          |                     |
| `_Sparse` |           |          |                     |

| Field                           | Value |
| ------------------------------- | ----- |
| Error distinguishable from Fail |       |
| `Message` populated on failures |       |
| Notes                           |       |

---

### TC-506 — Test-method naming form

Two naming forms are in circulation. The `run_tests` **tool description** documents
`{flowApiName}_{flowTestApiName}`; the `sf-flow` skill documents the bare
`{flowTestApiName}` and warns the prefixed form fails with
`Could not run tests on class null`.

This test settles which is true in the org under test.

**Command:**

```
run_tests(tests=[{
  "className": "FlowTesting.{FLOW}",
  "testMethods": ["{FLOW}_Cirra_Probe_CR_Priority_Pass"]
}], skipCodeCoverage="true")
```

Then query `ApexTestResult` for the returned `jobId`.

**Expected:** In the reference run **both forms resolved and ran**. The prefixed
form executed and reported back under the bare name
(`MethodName: Cirra_Probe_CR_Priority_Pass`), i.e. the platform normalizes.

- Both forms run → record it; the skill's warning needs softening.
- Prefixed form yields `Could not run tests on class null` and
  `MethodsEnqueued: 0` → the skill's warning is correct for this org; record the
  org and API version, since the reference run contradicts it.

**Result:**

| Field                      | Value |
| -------------------------- | ----- |
| Status                     |       |
| Prefixed form resolved     |       |
| `MethodName` reported back |       |
| Notes                      |       |

---

### TC-507 — Read → re-deploy round-trip

Confirms the TC-502 read-back shape is _cosmetic_, not lossy: the collapsed-array
output must be redeployable **verbatim**.

**Command:** Take the `metadata_read` output for `Cirra_Probe_CR_Priority_Pass`
exactly as returned — collapsed objects, injected `isUseMockOutput: "false"`,
reordered keys, all of it — change only `fullName` and `label`, and create it:

```
metadata_create(type="FlowTest", metadata=[{
  "fullName": "Cirra_Probe_RT_Copy",
  "label": "Cirra Probe - Roundtrip Copy",
  "description": "Round-trip probe. Safe to delete.",
  "flowApiName": "{FLOW}",
  "testPoints": [
    {"elementApiName": "Start", "isUseMockOutput": "false",
     "parameters": {"leftValueReference": "$Record", "type": "InputTriggeringRecordInitial",
       "value": {"sobjectValue": "{\"Impact\":\"High\",\"Subject\":\"Router upgrade\"}"}}},
    {"assertions": {"conditions": {"leftValueReference": "$Record.Priority",
       "operator": "EqualTo", "rightValue": {"stringValue": "High"}},
      "errorMessage": "Priority should be High when Impact is High"},
     "elementApiName": "Finish", "isUseMockOutput": "false"}
  ],
  "testType": "WithAssertion"
}])
```

Then **run the copy** — acceptance alone is not enough; it must behave identically:

```
run_tests(tests=[{"className": "FlowTesting.{FLOW}",
  "testMethods": ["Cirra_Probe_RT_Copy"]}], skipCodeCoverage="true")
```

**Expected:**

- Create succeeds. Bare objects are accepted where arrays were sent; the injected
  string `"false"` is accepted as-is.
- The copy runs and returns `Pass` — semantically identical to its source.

A failure here upgrades the TC-502 read-back shape from a cosmetic quirk to a
**round-trip defect**, and any read-modify-write helper built on `metadata_read`
must be audited.

**Result:**

| Field                       | Value |
| --------------------------- | ----- |
| Status                      |       |
| Copy created from read-back |       |
| Copy `Outcome` when run     |       |
| Notes                       |       |

---

### TC-508 — `metadata_update` and JSON Patch pointer depth

TC-507 proves whole-object read-modify-write is safe. This test probes the
**targeted** update path, where the TC-502 collapse stops being cosmetic: a JSON
Patch pointer must match the server-side shape, and that shape depends on how many
siblings a node happens to have.

**Command — create a probe, then patch one assertion value:**

```
metadata_create(type="FlowTest", metadata=[{
  "fullName": "Cirra_Probe_Gap_Check",
  "label": "Cirra Probe - Gap Check",
  "description": "Update probe. Safe to delete.",
  "flowApiName": "{FLOW}",
  "testType": "WithAssertion",
  "testPoints": [
    {"elementApiName": "Start", "parameters": [
      {"leftValueReference": "$Record", "type": "InputTriggeringRecordInitial",
       "value": {"sobjectValue": "{\"Impact\":\"High\",\"Subject\":\"Router upgrade\"}"}}]},
    {"elementApiName": "Finish", "assertions": [
      {"conditions": [
        {"leftValueReference": "$Record.Priority", "operator": "EqualTo",
         "rightValue": {"stringValue": "High"}}],
       "errorMessage": "Priority should be High when Impact is High"}]}
  ]
}])

metadata_update(type="FlowTest", fullName="Cirra_Probe_Gap_Check", patch=[
  {"op": "replace",
   "path": "/testPoints/1/assertions/conditions/rightValue/stringValue",
   "value": "Low"}])
```

Then run it and read the outcome.

**Expected:**

- The patch succeeds, and the pointer above has **no array index** on
  `assertions` or `conditions` — it addresses the _collapsed_ shape. With more
  than one condition the same logical target requires `/conditions/0/…`.
- The updated test now returns `Outcome: Fail` — proving the patch changed
  behaviour, not just the stored payload. An update that returns `success: true`
  without changing the verdict is a silent-write regression and is the main thing
  this test exists to catch.

**Implication to record:** a generic patch-path builder that always emits an index
(or never does) works on one arity and fails on the other, and a wrong pointer
surfaces as a patch error rather than a wrong value. Read the current shape before
constructing a patch, or send the whole object via `metadata`.

**Result:**

| Field                                 | Value |
| ------------------------------------- | ----- |
| Status                                |       |
| Patch accepted against collapsed path |       |
| `Outcome` after update                |       |
| Notes                                 |       |

---

## Cleanup — mandatory

```
metadata_delete(type="FlowTest", fullNames=[
  "Cirra_Probe_CR_Priority_Pass",
  "Cirra_Probe_CR_Priority_Fail",
  "Cirra_Probe_CR_Priority_Sparse",
  "Cirra_Probe_RT_Copy",
  "Cirra_Probe_Gap_Check"])
```

Then confirm the org is clean:

```
metadata_list(type="FlowTest")
```

**Expected:** no records carrying `{PREFIX}`.

`metadata_delete` caps at **10 fullNames per call**. Deleting a `FlowTest` does
not affect the flow or its versions.

**Result:**

| Field                   | Value |
| ----------------------- | ----- |
| All probes deleted      |       |
| Org clean after cleanup |       |
| Residue left (if any)   |       |

---

## Gate Decision

| TC-501 | TC-502/503 | TC-504/505 | TC-507/508 | Decision                                                                                                           |
| ------ | ---------- | ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------ |
| PASS   | PASS       | PASS       | PASS       | `FlowTest` lifecycle fully functional. No action                                                                   |
| PASS   | PASS       | PASS       | FAIL       | Write path defect — round-trip lossy or patch silently no-op. File against the MCP server; audit read-modify-write |
| PASS   | PASS       | FAIL       | any        | Run or result-interpretation regression. Record which of the three probes diverged                                 |
| PASS   | FAIL       | any        | any        | Read-back shape changed. Update any consumer that parses `FlowTest`                                                |
| FAIL   | —          | —          | —          | `metadata_create` no longer accepts `FlowTest`. Blocking; file immediately                                         |

**Gate decision:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Org / API version tested:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Date run:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

## Reference run — baseline for regression comparison

Recorded so a future run can tell "the platform changed" from "this script is wrong."

| Item                      | Observation                                                         |
| ------------------------- | ------------------------------------------------------------------- |
| Org                       | Cirra AI SDO demo org — production instance, API 65.0+              |
| Flow                      | `{FLOW}`, active version **2**                                      |
| TC-501 create             | 3/3 succeeded, including the wrong-assertion variant                |
| TC-502 read-back          | Arrays collapsed; `isUseMockOutput: "false"` injected as a string   |
| TC-503 tooling            | 3 records, `320` key prefix                                         |
| TC-504 run                | `Completed`, enqueued 3 / completed 3 / failed 2 — counters correct |
| TC-505 verdicts           | `Pass`→Pass/Pass · `Fail`→Fail/Fail · `Sparse`→Fail/**Error**       |
| TC-505 `Message`          | Empty on both failures                                              |
| TC-506 prefixed name form | **Resolved and ran**; reported back under the bare name             |
| TC-507 round-trip         | Created from read-back verbatim, ran, `Pass`                        |
| TC-508 patch update       | Patch applied against the collapsed path; verdict flipped to `Fail` |
| Cleanup                   | Clean — `metadata_list` returned zero `FlowTest` records            |

### Behaviours that were checked and did _not_ occur

Recorded because each has been reported at some point, and a future run seeing one
of them should treat it as new information rather than a known quirk. Single org,
single date — absence here is not proof they cannot happen.

1. **`ApexTestRunResult` counters were accurate**, not unreliable — `Completed`
   with 3 enqueued / 3 completed / 2 failed, matching the per-test results
   exactly. Taking the verdict from TC-505 is still correct, but because
   `ApexTestResult.Outcome` collapses `Error` into `Fail`, not because the
   roll-up counters lie.
2. **Both method-name forms resolved.** The bare `{flowTestApiName}` and the
   prefixed `{flowApiName}_{flowTestApiName}` each ran; results reported back
   under the bare name either way. No `Could not run tests on class null`.
3. **Freshly created tests were immediately runnable.** Every probe ran seconds
   after creation, including in the same session as its `metadata_create`. No
   resolution delay observed.

If a future run hits 2 or 3, capture the timing between create and run — a
transient post-create resolution delay would explain both, and would look like a
naming problem from the outside.
