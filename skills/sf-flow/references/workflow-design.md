## Workflow Design (5-Phase Pattern)

### Phase 1: Requirements Gathering

**Before building, evaluate alternatives**: See `references/flow-best-practices.md` Section 1 "When NOT to Use Flow" - sometimes a Formula Field, Validation Rule, or Roll-Up Summary Field is the better choice.

If the request is underspecified, ask concise follow-up questions to gather:

- Flow type (Screen, Record-Triggered After/Before Save/Delete, Platform Event, Autolaunched, Scheduled)
- Primary purpose (one sentence)
- Trigger object/conditions (if record-triggered)

**Pre-Development Planning**: For complex flows, document requirements and sketch logic before building. See `references/flow-best-practices.md` Section 2 "Pre-Development Planning" for templates and recommended tools.

**Then**:

1. **Initialize**: Call `cirra_ai_init()` with no parameters. If a default org is configured, confirm with the user. If no default, ask for the Salesforce user/alias before proceeding.
2. Use `sobject_describe` to verify object/field existence before referencing
3. Use `metadata_list` to check existing flows: `metadata_list(type="Flow")`
4. Offer reusable subflows: Sub_LogError, Sub_SendEmailAlert, Sub_ValidateRecord, Sub_UpdateRelatedRecords, Sub_QueryRecordsWithRetry → See `references/subflow-library.md`
5. If complex automation: Reference `references/governance-checklist.md`
6. Keep an internal checklist: Gather requirements, select template, generate flow metadata (JSON), validate, deploy, test

### Phase 2: Flow Design & Template Selection

**Select template**:

| Flow Type        | Template File                      |
| ---------------- | ---------------------------------- |
| Screen           | `screen-flow-template.xml`         |
| Record-Triggered | `record-triggered-*.xml`           |
| Platform Event   | `platform-event-flow-template.xml` |
| Autolaunched     | `autolaunched-flow-template.xml`   |
| Scheduled        | `scheduled-flow-template.xml`      |
| Wait Elements    | `wait-template.xml`                |

**Element Pattern Templates** (`assets/elements/`):

| Element        | Template                    | Purpose                                                     |
| -------------- | --------------------------- | ----------------------------------------------------------- |
| Loop           | `loop-pattern.xml`          | Complete loop with nextValueConnector/noMoreValuesConnector |
| Get Records    | `get-records-pattern.xml`   | All recordLookups options (filters, sort, limit)            |
| Delete Records | `record-delete-pattern.xml` | Filter-based and reference-based delete patterns            |

**JSON Deployment Reference** (`assets/json-deployment-reference.md`):
Covers XML-to-JSON translation, property placement rules, start patterns for all flow types, entry conditions (filterFormula vs filters), value reference patterns, and element JSON examples. **For `metadata_create` deployments, this reference alone is usually sufficient** — the XML templates are optional structural references for complex or unfamiliar flow types.

**Template Path Resolution** (try in order):

1. Resolve paths relative to the skill root under `assets/[template]`
2. For element snippets, resolve paths under `assets/elements/[template]`

**When to read XML templates**: Only when dealing with complex or unfamiliar element patterns (e.g., wait elements, advanced screen flows). For standard record-triggered, autolaunched, and scheduled flows, the JSON deployment reference has all the patterns needed.

**Example**: `Read: assets/record-triggered-after-save.xml`

**Naming Convention** (Recommended Prefixes):

| Flow Type                 | Prefix            | Example                                          |
| ------------------------- | ----------------- | ------------------------------------------------ |
| Record-Triggered (After)  | `Auto_`           | `Auto_Lead_Assignment`, `Auto_Account_Update`    |
| Record-Triggered (Before) | `Before_`         | `Before_Lead_Validate`, `Before_Contact_Default` |
| Screen Flow               | `Screen_`         | `Screen_New_Customer`, `Screen_Case_Intake`      |
| Scheduled                 | `Sched_`          | `Sched_Daily_Cleanup`, `Sched_Weekly_Report`     |
| Platform Event            | `Event_`          | `Event_Order_Completed`                          |
| Autolaunched              | `Sub_` or `Util_` | `Sub_Send_Email`, `Util_Validate_Address`        |

**Format**: `[Prefix]_Object_Action` using PascalCase (e.g., `Auto_Lead_Priority_Assignment`)

**Screen Flow Button Config** (CRITICAL):

| Screen | allowBack | allowFinish | Result              |
| ------ | --------- | ----------- | ------------------- |
| First  | false     | true        | "Next" only         |
| Middle | true      | true        | "Previous" + "Next" |
| Last   | true      | true        | "Finish"            |

Rule: `allowFinish="true"` required on all screens. Connector present → "Next", absent → "Finish".

**Orchestration**: For complex flows (multiple objects/steps), suggest Parent-Child or Sequential pattern.

- **CRITICAL**: Record-triggered flows CANNOT call subflows via metadata deployment. Use inline orchestration instead. See `references/xml-gotchas.md` and `references/orchestration-guide.md`

### Phase 3: Flow Generation & Deployment (via Cirra AI)

> **Two deployment formats — know which to use:**
>
> | Path                                     | Format          | When                              |
> | ---------------------------------------- | --------------- | --------------------------------- |
> | `metadata_create` / `metadata_update`    | **JSON object** | Deploying via Cirra AI MCP Server |
> | Writing `.flow-meta.xml` to `force-app/` | **XML**         | Source-controlled project files   |
>
> **CRITICAL**: Do NOT pass XML strings to `metadata_create`. It requires a structured
> JSON object — use the format reference and examples below. The XML templates in
> `assets/` are the correct reference when writing local `.flow-meta.xml` files.

**Generate flow metadata**:
Construct the complete Flow metadata as a JSON object with:

- API Version: 65.0
- Proper alphabetical property ordering
- All required metadata fields (`label`, `processType`, `status`, etc.)

**CRITICAL Requirements**:

- Alphabetical property ordering at root level
- NO `bulkSupport` property (removed API 60.0+)
- Auto-Layout: all `locationX`/`locationY` = 0
- Fault paths on all DML operations

#### JSON Format Reference

> **Read `assets/json-deployment-reference.md` for the complete reference** — it covers
> XML-to-JSON translation, start patterns for all flow types, entry conditions,
> value references, and element JSON examples.

**Essential rules** (always apply):

1. **Format**: `metadata_create` requires a JSON object, NOT XML. The XML templates
   in `assets/` show structure; translate using the reference above.
2. **Property placement**: `triggerType`, `recordTriggerType`, `object`, `schedule`,
   `filters`/`filterFormula`/`filterLogic` belong ONLY inside `start`, never at top level.
3. **Value wrappers**: `{"stringValue": "text"}`, `{"booleanValue": true}`,
   `{"numberValue": 100}`, `{"elementReference": "var_Name"}`.
4. **Merge fields**: `stringValue` supports `{!$Record.Name}` syntax — no need for
   formula variables for simple string interpolation.
5. **Entry conditions**: Use `filterFormula` for compound/negated conditions
   (`AND()`, `OR()`, `NOT()`). Use `filters` array for simple field comparisons.
6. **Shell template**: Start from the Flow Shell Template below (Lesson 9) for the
   complete JSON boilerplate with all element arrays.

**Pre-Deployment: Check Prerequisites** (REQUIRED for flows referencing custom fields/objects):

Before deploying a flow, verify that all referenced custom fields and objects exist
in the target org. Flows referencing missing fields will deploy but become
`InvalidDraft` and cannot be activated.

```python
# Check if custom field exists before deploying flow that references it
sobject_describe(sObject="Lead")
# Verify TEST_Priority__c (or any custom field) appears in the field list
# If missing: create the field FIRST via sobject_field_create, then deploy the flow
```

**Deploy via Cirra AI**:

```python
# Initialize connection (ONCE per session)
cirra_ai_init(sf_user="your-username")

# Create/deploy Flow — pass a JSON object, NOT XML
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "label": "Auto Lead Assignment",
        "apiVersion": 65,
        "description": "Assigns new leads to the appropriate queue based on region",
        "environments": ["Default"],
        "processMetadataValues": [
            {"name": "BuilderType", "value": {"stringValue": "LightningFlowBuilder"}},
            {"name": "CanvasMode", "value": {"stringValue": "AUTO_LAYOUT_CANVAS"}}
        ],
        "processType": "AutoLaunchedFlow",
        "start": {
            "locationX": 0, "locationY": 0,
            "object": "Lead",
            "recordTriggerType": "Create",
            "triggerType": "RecordAfterSave",
            "connector": {"targetReference": "Check_Region"}
        },
        "decisions": [...],
        "recordUpdates": [...],
        "status": "Draft"
    }],
    sf_user="your-username"
)
```

**Post-Deployment: Verify Flow Status** (REQUIRED after every metadata_create for Flow):

After deploying a flow, immediately query its status via the Tooling API to
detect `InvalidDraft`. This catches issues the Metadata API accepts silently.

```python
# Check flow status after deployment
tooling_api_query(
    sObject="Flow",
    fields=["Id", "Definition.DeveloperName", "VersionNumber", "Status"],
    whereClause="Definition.DeveloperName = 'Auto_Lead_Assignment'"
)
# Expected: Status = "Draft"
# If Status = "InvalidDraft":
#   1. Check for missing triggerType (scheduled flows need triggerType=Scheduled)
#   2. Check for missing custom field references (sobject_describe to verify)
#   3. Fix the issue and redeploy via metadata_update
```

**Common InvalidDraft Causes and Fixes**:

| Cause                                    | Symptom                                                        | Fix                                                                                              |
| ---------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Missing `triggerType` in `start`         | Scheduled flow with `schedule` but no `triggerType: Scheduled` | Add `triggerType: "Scheduled"` to start element                                                  |
| Missing custom field                     | Flow references `Custom_Field__c` that doesn't exist           | Create field via `sobject_field_create` first, then redeploy                                     |
| Deprecated `bulkSupport`                 | API 60.0+ flow includes `bulkSupport`                          | Remove the `bulkSupport` property                                                                |
| Missing `recordTriggerType`              | Record-triggered flow without `recordTriggerType`              | Add `recordTriggerType: "Create"` (or Update/CreateAndUpdate)                                    |
| Missing `locationX`/`locationY` on start | `Required field is missing: locationX` on create               | Always include `"locationX": 0, "locationY": 0` on the start element, even for auto-layout flows |

**For Review** — validate an existing flow from the org or a local file before modifying:

- `python scripts/validate_flow_cli.py <FlowApiName>` — fetch and validate a single flow from the org
- `python scripts/validate_flow_cli.py All` — full org audit sorted by score

**Validation (STRICT MODE)**:

- **BLOCK**: Invalid structure, missing required fields (apiVersion/label/processType/status), API <65.0, broken refs, DML in loops
- **WARN**: Property ordering, deprecated properties, non-zero coords, missing fault paths, unused vars, naming violations

**New v2.0.0 Validations**:

- `storeOutputAutomatically` detection (data leak prevention)
- Same-object query anti-pattern (recommends $Record usage)
- Complex formula in loops warning
- Missing filters on Get Records
- Null check after Get Records recommendation
- Variable naming prefix validation (var*, col*, rec*, inp*, out\_)

**Validation Report Format** (6-Category Scoring 0-110):

```text
Score: 92/110 ⭐⭐⭐⭐ Very Good
├─ Design & Naming: 18/20 (90%)
├─ Logic & Structure: 20/20 (100%)
├─ Architecture: 12/15 (80%)
├─ Performance & Bulk Safety: 20/20 (100%)
├─ Error Handling: 15/20 (75%)
└─ Security: 15/15 (100%)
```

**Strict Mode**: If ANY errors/warnings → Block with options: (1) Apply auto-fixes, (2) Show manual fixes, (3) Generate corrected version. **DO NOT PROCEED** until 100% clean.

### ⛔ GENERATION GUARDRAILS (MANDATORY)

**BEFORE generating ANY Flow metadata, VERIFY no anti-patterns are introduced.**

If ANY of these patterns would be generated, **STOP and ask the user**:

> "I noticed [pattern]. This will cause [problem]. Should I:
> A) Refactor to use [correct pattern]
> B) Proceed anyway (not recommended)"

| Anti-Pattern                                                            | Impact                                                                                                                                                                                                                                   | Correct Pattern                                                                                                                     |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| After-Save updating same object without entry conditions                | **Infinite loop** (critical)                                                                                                                                                                                                             | MUST add entry conditions: "Only when [field] is changed"                                                                           |
| Get Records inside Loop                                                 | Governor limit failure (100 SOQL)                                                                                                                                                                                                        | Query BEFORE loop, use collection variable                                                                                          |
| Create/Update/Delete Records inside Loop                                | Governor limit failure (150 DML)                                                                                                                                                                                                         | Collect in loop → single DML after loop                                                                                             |
| Apex Action inside Loop                                                 | Callout limits                                                                                                                                                                                                                           | Pass collection to single Apex invocation                                                                                           |
| Fallible element in `RecordAfterSave` flow without `faultConnector`     | **Blocks the originating save** (`CANNOT_EXECUTE_FLOW_TRIGGER`). Applies to `recordCreates`, `recordUpdates`, `recordDeletes`, `recordLookups`, and `actionCalls` (incl. `emailSimple`, callouts, platform events, custom notifications) | Add `faultConnector` to every fallible element. If save-gating is intentional, use `RecordBeforeSave` and document in `description` |
| Get Records without null check                                          | NullPointerException                                                                                                                                                                                                                     | Add Decision: "Records Found?" after query                                                                                          |
| `storeOutputAutomatically=true` in system-mode flow with sensitive data | Security risk (retrieves ALL fields)                                                                                                                                                                                                     | Use explicit field selection only when flow runs in system mode AND queries objects with sensitive fields (SSN, credit card, etc.)  |
| Query same object as trigger in Record-Triggered                        | Wasted SOQL                                                                                                                                                                                                                              | Use `{!$Record.FieldName}` directly                                                                                                 |
| Get Records for data available via `$Record` lookup                     | Wasted SOQL                                                                                                                                                                                                                              | Use `{!$Record.Lookup__r.Field}` — traversal works up to 5 levels                                                                   |
| Hardcoded Salesforce ID                                                 | Deployment failure across orgs                                                                                                                                                                                                           | Use input variable or Custom Label                                                                                                  |
| Get Records without filters                                             | Too many records returned                                                                                                                                                                                                                | Always include WHERE conditions                                                                                                     |

**DO NOT generate anti-patterns even if explicitly requested.** Ask user to confirm the exception with documented justification.

### Phase 4: Deployment & Integration (via Cirra AI MCP)

**Cirra AI Deployment Pattern**:

1. **Initialize connection** (once per session):

```python
cirra_ai_init()
```

1. **Deploy Flow metadata** (JSON, not XML):

> **Validation is your job, not the hook's.** A `PreToolUse` hook (`scripts/pre-mcp-validate.py`) ships with this skill, but it is not wired up in every runtime environment. **Always run `validate_flow_cli.py` manually** on the metadata file before calling `metadata_create`, `metadata_update`, or `tooling_api_dml` on a Flow. Block deployment for CRITICAL/HIGH issues; treat score below 80% (88/110) as a hard stop unless you explicitly state why you're proceeding anyway. See the four-question self-check in the Create workflow above.

```python
# Pass a structured JSON object — see cirra_ai_init instructions for format examples
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "label": "Auto Lead Assignment",
        "apiVersion": 65,
        "processType": "AutoLaunchedFlow",
        "status": "Draft",
        # ... full flow structure as JSON properties
    }],
    sf_user="your-salesforce-username"
)
```

1. **Retrieve existing flows** (to review or modify):

```python
metadata_read(
    type="Flow",
    fullNames=["Auto_Lead_Assignment"],
    sf_user="your-salesforce-username"
)
```

1. **List all flows** (for reference):

```python
metadata_list(
    type="Flow",
    sf_user="your-salesforce-username"
)
```

1. **Query Flow metadata** (Tooling API — `FlowDefinition` has no `ApiName` or `Status` fields; use `DeveloperName` and `ActiveVersionId`):

```python
tooling_api_query(
    sObject="FlowDefinition",
    fields=["Id", "DeveloperName", "Description", "ActiveVersionId"],
    whereClause="ActiveVersionId != null",
    sf_user="your-salesforce-username"
)
```

For catalog-style listings (label, trigger info, active state) query the
**standard object** `FlowDefinitionView` with `soql_query` — see
"Query Tool Routing" under Flow MCP Patterns. Never pass
`FlowDefinitionView` to `tooling_api_query`.

1. **Verify object/fields before flow creation**:

```python
sobject_describe(
    sObject="Account",
    sf_user="your-salesforce-username"
)
```

**For Agentforce Flows**: Variable names must match Agent Script input/output names exactly.

For complex flows: `references/governance-checklist.md`

### Deleting a Flow Version (Recovering Stuck Versions)

If `tooling_api_dml` delete on a `Flow` version returns `DEPENDENCY_EXISTS`
referencing a `FlowInterview`, query and delete the blocking interviews first:

```python
# Find blocking interviews for the flow version
soql_query(
    sObject="FlowInterview",
    fields=["Id", "Name", "InterviewStatus", "FlowVersionViewId"],
    whereClause="FlowVersionViewId = '<flow_version_id_truncated_to_15>'"
)

# Delete failed/errored interviews from prior runs
sobject_dml(
    operation="delete",
    sObject="FlowInterview",
    recordIds=["<interview_id_1>", "<interview_id_2>"]
)

# Now retry the Flow version delete
tooling_api_dml(
    operation="delete",
    sObject="Flow",
    recordId="<flow_version_id>"
)
```

`FlowInterview` records with `InterviewStatus = 'Error'` (failed runs) are
the most common blockers. They persist even after the flow is deactivated,
and Salesforce will not let you delete a Flow version while any interview
references it.

This commonly happens in demo/dev orgs that have run the flow with
intentionally-failing inputs (e.g. unverified email domain causing
fault-path runs). It does not typically happen in production.

### Phase 5a: Failure-Mode Review (REQUIRED before declaring done)

Before declaring a flow complete, walk through this checklist. Each question
maps to a concrete metadata pattern; if the answer reveals an unhandled case,
fix it before activation.

1. **What happens if an external action fails?** (email server down, callout
   timeout, platform event subscriber rejecting, custom notification fails
   to deliver.) → `faultConnector` on every `actionCalls` element.

2. **What happens if a referenced record doesn't exist or the user lacks
   access?** → null check on every `recordLookups`, plus `faultConnector`.

3. **What happens if the flow re-fires on the same record?** Edits, rollups,
   trigger order can re-fire your flow on records it already processed. →
   Idempotency guard: dedup flag (`*_Notified__c`, `*_Processed__c`) checked
   in entry conditions, OR `ISCHANGED()` guard on the field that drives the
   action.

4. **What happens under bulk DML (200+ records in one transaction)?** →
   No DML in loops; no SOQL in loops; `$Record` is the single record context,
   not a collection.

5. **What happens if a downstream flow this one triggers also fails?** →
   Decide if cascade-blocking is OK; if not, route to side-effect pattern.

6. **Which category is this flow?** Side-effect or save-gating? Is the
   `description` clear about the intent so the next maintainer knows?

This checklist takes 60 seconds and catches the failure modes the validator
can't see (intent, idempotency design, downstream cascading).

### Phase 5: Testing & Documentation

**Type-specific testing**: See `references/testing-guide.md` | `references/testing-checklist.md` | `references/wait-patterns.md` (Wait element guidance)

Quick reference:

- **Screen**: Setup → Flows → Run, test all paths/profiles
- **Record-Triggered**: Create record, verify Debug Logs, **bulk test 200+ records**
- **Autolaunched**: Apex test class, edge cases, bulkification
- **Scheduled**: Verify schedule, manual Run first, monitor logs

**Best Practices**: See `references/flow-best-practices.md` for:

- Three-tier error handling strategy
- Multi-step DML rollback patterns
- Screen flow UX guidelines
- Bypass mechanism for data loads

**Security**: Test with multiple profiles. System mode requires security review.

**Completion Summary**:

```
✓ Flow Creation & Deployment Complete: [FlowName]
  Type: [type] | API: 65.0 | Status: [Draft/Active]
  Deployed via: Cirra AI MCP Server (metadata_create)
  Validation: PASSED (Score: XX/110)
  Org: [target-org-username]

  Navigate: Setup → Process Automation → Flows → "[FlowName]"

Next Steps: Test (unit, bulk, security), Review docs, Activate if Draft, Monitor logs
Resources: `assets/`, `references/subflow-library.md`, `references/orchestration-guide.md`, `references/governance-checklist.md`
```
