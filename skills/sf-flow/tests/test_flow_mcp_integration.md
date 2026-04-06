# Flow MCP Integration Test Protocol

Live integration test for flow deployment via Cirra AI MCP Server.
Run interactively in a coding session with MCP access.

## Test Summary (Last Run: 2026-03-07)

| #   | Test                                                                       | Result | Details                                                                                   |
| --- | -------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------- |
| 1   | Clean pre-existing test artifacts                                          | PASS   | No TEST\_\* flows or fields found                                                         |
| 2   | Create TEST_Priority\_\_c on Lead                                          | PASS   | `sobject_field_create` succeeded                                                          |
| 3   | Deploy 5 valid flows (before-save, after-save, screen, scheduled, complex) | PASS   | All 5 returned `success: true` (with locationX/Y fix)                                     |
| 4   | Deploy 1 invalid flow (scheduled, missing triggerType)                     | PASS   | API rejected with serialization error or returned InvalidDraft (deploy blocked or broken) |
| 5   | Query flow status via Tooling API                                          | PASS   | 5 valid flows = Draft (invalid flow: not created or InvalidDraft)                         |
| 6   | Verify all valid flows are Draft                                           | PASS   | All 5 flows confirmed Draft                                                               |
| 7   | Deploy flow with missing custom field (TEST_Invalid\_\_c)                  | PASS   | API accepted, Status = InvalidDraft                                                       |

## Key Insights from Testing

1. **All flow elements require `locationX` and `locationY`**: The Metadata API rejects flows with `FIELD_INTEGRITY_EXCEPTION: Required field is missing: locationX`. Every element (start, assignments, screens, recordCreates) needs canvas coordinates.
2. **Empty `assignmentItems` not allowed**: An assignment with `assignmentItems: []` fails with `Required field is missing: assignmentItems`. Use a variable assignment placeholder instead.
3. **Missing triggerType (API 62.0+)**: A scheduled flow without `triggerType: "Scheduled"` is rejected by the API with a serialization error — the flow record is never created. Confirmed in integration tests.
4. **Missing triggerType (earlier APIs)**: In earlier API versions the same invalid flow may instead be created with `Status: "InvalidDraft"` rather than being rejected outright. Both outcomes mean the flow is non-functional.

## Prerequisites

- Cirra AI MCP Server connected to a Salesforce sandbox
- `cirra_ai_init()` called in current session

## Step 1: Clean Slate — Remove Pre-Existing Test Artifacts

```
tooling_api_query(sObject="Flow", fields=["Id", "Definition.DeveloperName", "Status"],
    whereClause="Definition.DeveloperName LIKE 'TEST_%'")
# Expected: 0 records (or delete any found)

tooling_api_query(sObject="CustomField", fields=["Id", "DeveloperName", "TableEnumOrId"],
    whereClause="DeveloperName = 'TEST_Priority' AND TableEnumOrId = 'Lead'")
# Expected: 0 records (or delete via metadata_delete)
```

## Step 2: Create Prerequisites

```
sobject_field_create(
    sObject="Lead",
    fieldName="TEST_Priority__c",
    fieldType="Text",
    label="TEST Priority",
    description="Test field for flow integration tests. Safe to delete.",
    inlineHelpText="Used by flow integration tests only.",
    defaultFLS="Editable",
    properties={"length": 50}
)
```

## Step 3: Deploy Valid Flows

Deploy all 5 valid test flows via `metadata_create(type="Flow", metadata=[...])`:

- **TEST_Before_Lead_Priority_Assignment** — before-save on Lead, references TEST_Priority\_\_c
- **TEST_Auto_Opportunity_Follow_Up_Task** — after-save on Opportunity
- **TEST_Screen_New_Case_Intake** — screen flow for Case creation
- **TEST_Sched_Daily_Stale_Opportunity_Cleanup** — scheduled with triggerType=Scheduled
- **TEST_Auto_Account_Address_Sync_And_Task** — complex multi-object after-save

Expected: All 5 return `success: true`.

## Step 4: Deploy Invalid Flow (Negative Test)

Deploy `TEST_Sched_Missing_Trigger_Type` — a scheduled flow WITHOUT `triggerType: Scheduled`.

Expected: One of two outcomes depending on API version:

- **API 62.0+**: The flow is rejected outright with a serialization error (flow NOT created, no record in Tooling API).
- **Earlier API versions**: The flow may be created with `Status: "InvalidDraft"` rather than being rejected.

Either outcome is acceptable. The important assertion is that the flow is NOT deployable/active.

## Step 5: Verify Flow Status (Post-Deploy Check)

```
tooling_api_query(
    sObject="Flow",
    fields=["Id", "Definition.DeveloperName", "VersionNumber", "Status"],
    whereClause="Definition.DeveloperName LIKE 'TEST_%'"
)
```

Expected results:

- 5 flows with `Status: "Draft"` (valid)
- `TEST_Sched_Missing_Trigger_Type`: either 0 records (rejected outright on API 62.0+) or 1 record with `Status: "InvalidDraft"` (earlier APIs). Either outcome confirms the flow is non-functional.

## Step 6: Deploy Flow With Missing Custom Field (Negative Test)

Deploy `TEST_Before_Lead_Missing_Field` — references `TEST_Invalid__c` which does NOT exist on Lead.

```
metadata_create(type="Flow", metadata=[{
    "fullName": "TEST_Before_Lead_Missing_Field",
    ...
    "start": { "object": "Lead", "triggerType": "RecordBeforeSave", ... },
    # assignments reference $Record.TEST_Invalid__c
}])
```

Expected: API returns `success: true` (it accepts the flow), but:

```
tooling_api_query(sObject="Flow", fields=["Id", "Definition.DeveloperName", "Status"],
    whereClause="Definition.DeveloperName = 'TEST_Before_Lead_Missing_Field'")
```

Result: `Status: "InvalidDraft"` — the field doesn't exist so the flow is broken.

**Key insight**: The `check_deploy_readiness()` function with `org_fields` parameter
catches this BEFORE deploying by promoting the custom field warning to an ERROR:

```python
# Pre-deploy check: get actual fields from org
fields = sobject_describe(sObject="Lead")  # get field list
result = check_deploy_readiness("flow.xml", org_fields=field_names)
# result["ready"] == False, issues include "missing_custom_fields" ERROR
```

Clean up after test: `metadata_delete(type="Flow", fullNames=["TEST_Before_Lead_Missing_Field"])`

## Cleanup (Optional — Run After Review)

Delete test flows and the test field. Offer to the user, don't auto-clean.

```
# Delete test flows (deactivate first if active)
metadata_delete(type="Flow", fullNames=[
    "TEST_Before_Lead_Priority_Assignment",
    "TEST_Auto_Opportunity_Follow_Up_Task",
    "TEST_Screen_New_Case_Intake",
    "TEST_Sched_Daily_Stale_Opportunity_Cleanup",
    "TEST_Auto_Account_Address_Sync_And_Task"
])

# Delete test field
metadata_delete(type="CustomField", fullNames=["Lead.TEST_Priority__c"])
```
