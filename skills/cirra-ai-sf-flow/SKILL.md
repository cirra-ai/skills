---
name: cirra-ai-sf-flow
metadata:
  version: 1.2.0
description: >
  Creates and validates Salesforce flows with 110-point scoring and Winter '26
  best practices using Cirra AI MCP Server. Use when building record-triggered flows,
  screen flows, autolaunched flows, scheduled flows, or reviewing existing flow performance.
---

# cirra-ai-sf-flow: Salesforce Flow Creation and Validation (Cirra AI)

Expert Salesforce Flow Builder with deep knowledge of best practices, bulkification, and Winter '26 (API 65.0) metadata. Create production-ready, performant, secure, and maintainable flows using Cirra AI MCP Server for deployment.

## 📋 Quick Reference: Validation and Deployment

**Flow Creation & Deployment Workflow:**

```
1. Call cirra_ai_init (REQUIRED - one per session)
2. Generate Flow metadata (JSON object — NOT XML)
3. Deploy via metadata_create tool (Cirra AI MCP Server)
4. Retrieve existing flows via metadata_read or metadata_list (Cirra AI MCP Server)
5. Query Flow metadata via tooling_api_query for FlowDefinition
6. Describe objects/fields via sobject_describe before flow creation
```

**Scoring**: 110 points across 6 categories. Minimum 88 (80%) for deployment.

---

## Core Responsibilities

1. **Flow Generation**: Create well-structured Flow metadata (JSON) from requirements
2. **Strict Validation**: Enforce best practices with comprehensive checks and scoring
3. **Cirra AI Integration**: Deploy via metadata_create, retrieve via metadata_read/metadata_list
4. **Testing Guidance**: Provide type-specific testing checklists and verification steps

---

## ⚠️ CRITICAL: Cirra AI MCP Server Setup

**BEFORE using any Cirra AI tools:**

```python
cirra_ai_init()
```

Call with no parameters — uses the default org. If a default is configured, confirm with the user before proceeding. If no default is configured, ask for the Salesforce user/alias.

This initializes your Salesforce org connection. It must be called once per session before using any of these Cirra AI tools:

- `metadata_create` (deploy flows)
- `metadata_read` (retrieve flows)
- `metadata_list` (list existing flows)
- `tooling_api_query` (query FlowDefinition)
- `sobject_describe` (verify objects/fields)
- `soql_query` (query org data)

---

## ⚠️ CRITICAL: Orchestration Order

**cirra-ai-sf-metadata → cirra-ai-sf-flow → cirra-ai-sf-data** (you are here: cirra-ai-sf-flow with Cirra AI)

⚠️ Flow references custom object/fields? Create with cirra-ai-sf-metadata FIRST. Deploy objects BEFORE flows.

```
1. cirra-ai-sf-metadata  → Create objects/fields (local)
2. cirra-ai-sf-flow      ◀── YOU ARE HERE (create flow, deploy via Cirra AI)
3. cirra-ai-sf-data      → Create test data (remote - objects must exist!)
```

See `references/orchestration.md` for extended orchestration patterns including Agentforce.

---

## 🔑 Key Insights

| Insight                  | Details                                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Before vs After Save** | Before-Save: same-record updates (no DML), validation. After-Save: related records, emails, callouts                                                                                                               |
| **Test with 251**        | Batch boundary at 200. Test 251+ records for governor limits, N+1 patterns, bulk safety                                                                                                                            |
| **$Record context**      | Single-record, NOT a collection. Platform handles batching. Never loop over $Record                                                                                                                                |
| **$Record traversal**    | `$Record` supports relationship traversal: `{!$Record.Contact__r.FirstName}`, `{!$Record.Account__r.Name}`. Do NOT use Get Records for data already available through `$Record` lookups — this wastes a SOQL query |
| **Transform vs Loop**    | Transform: data mapping/shaping (30-50% faster). Loop: per-record decisions, counters, varying logic. See `references/transform-vs-loop-guide.md`                                                                  |

---

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
| Flow Type | Template File |
|-----------|---------------|
| Screen | `screen-flow-template.xml` |
| Record-Triggered | `record-triggered-*.xml` |
| Platform Event | `platform-event-flow-template.xml` |
| Autolaunched | `autolaunched-flow-template.xml` |
| Scheduled | `scheduled-flow-template.xml` |
| Wait Elements | `wait-template.xml` |

**Element Pattern Templates** (`assets/elements/`):
| Element | Template | Purpose |
|---------|----------|---------|
| Loop | `loop-pattern.xml` | Complete loop with nextValueConnector/noMoreValuesConnector |
| Get Records | `get-records-pattern.xml` | All recordLookups options (filters, sort, limit) |
| Delete Records | `record-delete-pattern.xml` | Filter-based and reference-based delete patterns |

**Template Path Resolution** (try in order):

1. Resolve paths relative to the skill root under `assets/[template]`
2. For element snippets, resolve paths under `assets/elements/[template]`

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
| Screen | allowBack | allowFinish | Result |
|--------|-----------|-------------|--------|
| First | false | true | "Next" only |
| Middle | true | true | "Previous" + "Next" |
| Last | true | true | "Finish" |

Rule: `allowFinish="true"` required on all screens. Connector present → "Next", absent → "Finish".

**Orchestration**: For complex flows (multiple objects/steps), suggest Parent-Child or Sequential pattern.

- **CRITICAL**: Record-triggered flows CANNOT call subflows via metadata deployment. Use inline orchestration instead. See `references/xml-gotchas.md` and `references/orchestration-guide.md`

### Phase 3: Flow Generation & Deployment (via Cirra AI)

> **CRITICAL: `metadata_create` requires JSON, NOT XML**
>
> The XML templates in `assets/` are for **structural reference only** — to understand
> element ordering and schema. Do NOT pass XML strings as a `content` property to
> `metadata_create`. Always construct a **structured JSON object** matching the examples
> in the instructions returned by `cirra_ai_init` and `metadata_create`.
>
> The authoritative format examples are in the `metadata_create` tool instructions
> (returned at runtime via the Cirra AI MCP Server). Those take precedence over the
> static XML asset templates in this skill.

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
        "processType": "AutoLaunchedFlow",
        "status": "Draft",
        "environments": ["Default"],
        "processMetadataValues": [
            {"name": "BuilderType", "value": {"stringValue": "LightningFlowBuilder"}},
            {"name": "CanvasMode", "value": {"stringValue": "AUTO_LAYOUT_CANVAS"}}
        ],
        "start": {
            "locationX": 0,
            "locationY": 0,
            "object": "Lead",
            "recordTriggerType": "Create",
            "triggerType": "RecordAfterSave",
            "connector": {"targetReference": "First_Element_Name"}
        }
        # ... remaining flow elements as JSON properties
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

| Cause                            | Symptom                                                        | Fix                                                           |
| -------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------- |
| Missing `triggerType` in `start` | Scheduled flow with `schedule` but no `triggerType: Scheduled` | Add `triggerType: "Scheduled"` to start element               |
| Missing custom field             | Flow references `Custom_Field__c` that doesn't exist           | Create field via `sobject_field_create` first, then redeploy  |
| Deprecated `bulkSupport`         | API 60.0+ flow includes `bulkSupport`                          | Remove the `bulkSupport` property                             |
| Missing `recordTriggerType`      | Record-triggered flow without `recordTriggerType`              | Add `recordTriggerType: "Create"` (or Update/CreateAndUpdate) |

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

```
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

**BEFORE generating ANY Flow metadata, Claude MUST verify no anti-patterns are introduced.**

If ANY of these patterns would be generated, **STOP and ask the user**:

> "I noticed [pattern]. This will cause [problem]. Should I:
> A) Refactor to use [correct pattern]
> B) Proceed anyway (not recommended)"

| Anti-Pattern                                                            | Impact                               | Correct Pattern                                                                                                                    |
| ----------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| After-Save updating same object without entry conditions                | **Infinite loop** (critical)         | MUST add entry conditions: "Only when [field] is changed"                                                                          |
| Get Records inside Loop                                                 | Governor limit failure (100 SOQL)    | Query BEFORE loop, use collection variable                                                                                         |
| Create/Update/Delete Records inside Loop                                | Governor limit failure (150 DML)     | Collect in loop → single DML after loop                                                                                            |
| Apex Action inside Loop                                                 | Callout limits                       | Pass collection to single Apex invocation                                                                                          |
| DML without Fault Path                                                  | Silent failures                      | Add Fault connector → error handling element                                                                                       |
| Get Records without null check                                          | NullPointerException                 | Add Decision: "Records Found?" after query                                                                                         |
| `storeOutputAutomatically=true` in system-mode flow with sensitive data | Security risk (retrieves ALL fields) | Use explicit field selection only when flow runs in system mode AND queries objects with sensitive fields (SSN, credit card, etc.) |
| Query same object as trigger in Record-Triggered                        | Wasted SOQL                          | Use `{!$Record.FieldName}` directly                                                                                                |
| Get Records for data available via `$Record` lookup                     | Wasted SOQL                          | Use `{!$Record.Lookup__r.Field}` — traversal works up to 5 levels                                                                  |
| Hardcoded Salesforce ID                                                 | Deployment failure across orgs       | Use input variable or Custom Label                                                                                                 |
| Get Records without filters                                             | Too many records returned            | Always include WHERE conditions                                                                                                    |

**DO NOT generate anti-patterns even if explicitly requested.** Ask user to confirm the exception with documented justification.

### Phase 4: Deployment & Integration (via Cirra AI MCP)

**Cirra AI Deployment Pattern**:

1. **Initialize connection** (once per session):

```python
cirra_ai_init()
```

2. **Deploy Flow metadata** (JSON, not XML):

> **Automatic validation**: A skill-scoped PreToolUse hook runs `pre-mcp-validate.py` before every `metadata_create`, `metadata_update`, and `tooling_api_dml` call while this skill is active. It blocks deployment for CRITICAL/HIGH issues (DML in loops, missing fault paths) and warns when score is below 80% (88/110).

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

3. **Retrieve existing flows** (to review or modify):

```python
metadata_read(
    type="Flow",
    fullNames=["Auto_Lead_Assignment"],
    sf_user="your-salesforce-username"
)
```

4. **List all flows** (for reference):

```python
metadata_list(
    type="Flow",
    sf_user="your-salesforce-username"
)
```

5. **Query Flow metadata** (Tooling API):

```python
tooling_api_query(
    sObject="FlowDefinition",
    fields=["Id", "ApiName", "Description"],
    whereClause="Status = 'Active'",
    sf_user="your-salesforce-username"
)
```

6. **Verify object/fields before flow creation**:

```python
sobject_describe(
    sObject="Account",
    sf_user="your-salesforce-username"
)
```

**For Agentforce Flows**: Variable names must match Agent Script input/output names exactly.

For complex flows: `references/governance-checklist.md`

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

## Best Practices (Built-In Enforcement)

### ⛔ CRITICAL: Record-Triggered Flow Architecture

**NEVER loop over triggered records.** `$Record` = single record; platform handles batching.

| Pattern                          | OK? | Notes                                                     |
| -------------------------------- | --- | --------------------------------------------------------- |
| `$Record.FieldName`              | ✅  | Direct field access                                       |
| `$Record.Lookup__r.FieldName`    | ✅  | Relationship traversal — NO Get Records needed            |
| `$Record.Account__r.Owner.Name`  | ✅  | Multi-level traversal (up to 5 levels)                    |
| Get Records for `$Record` lookup | ❌  | Wastes SOQL — use `$Record.Relationship__r.Field` instead |
| Loop over `$Record__c`           | ❌  | Process Builder pattern, not Flow                         |
| Loop over `$Record`              | ❌  | $Record is single, not collection                         |

**`$Record` relationship traversal**: In record-triggered flows, `$Record` provides access to related records through lookup/master-detail fields WITHOUT a Get Records element. Use `{!$Record.Contact__r.FirstName}` instead of querying Contact separately. Only use Get Records when you need related records that are NOT accessible through `$Record` lookups (e.g., child records, or records with no relationship to the trigger object).

**Loops for RELATED records only**: Get Records → Loop collection → Assignment → DML after loop

### ⛔ CRITICAL: No Parent Traversal in Get Records

`recordLookups` cannot query `Parent.Field` (e.g., `Manager.Name`). **Solution**: Two Get Records - child first, then parent by Id.

### recordLookups Best Practices

| Element                            | Recommendation                          | Why                                                                                                                                                    |
| ---------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `getFirstRecordOnly`               | Set to `true` for single-record queries | Avoids collection overhead                                                                                                                             |
| `storeOutputAutomatically`         | Set to `true` (default)                 | Simpler, modern approach — auto-stores all fields. Only set to `false` with explicit field selection when handling sensitive data in system-mode flows |
| `assignNullValuesIfNoRecordsFound` | Set to `false`                          | Preserves previous variable value                                                                                                                      |
| `faultConnector`                   | Always include                          | Handle query failures gracefully                                                                                                                       |
| `filterLogic`                      | Use `and` for multiple filters          | Clear filter behavior                                                                                                                                  |

### Critical Requirements

- **API 65.0**: Latest features
- **No DML in Loops**: Collect in loop → DML after loop (causes bulk failures otherwise)
- **Bulkify**: For RELATED records only - platform handles triggered record batching
- **Fault Paths**: All DML must have fault connectors
  - ⚠️ **Fault connectors CANNOT self-reference** - Error: "element cannot be connected to itself"
  - Route fault connectors to a DIFFERENT element (dedicated error handler)
- **Auto-Layout**: All locationX/Y = 0 (cleaner git diffs)
  - UI may show "Free-Form" dropdown, but locationX/Y = 0 IS Auto-Layout in metadata
- **No Parent Traversal**: Use separate Get Records for relationship field data

### Property Ordering (CRITICAL)

**All properties of the same type MUST be grouped together. Do NOT scatter them across the object.**

Complete alphabetical order:

```
apiVersion → assignments → constants → decisions → description → environments →
formulas → interviewLabel → label → loops → processMetadataValues → processType →
recordCreates → recordDeletes → recordLookups → recordUpdates → runInMode →
screens → start → status → subflows → textTemplates → variables → waits
```

**Common Mistake**: Adding an assignment near related logic (e.g., after a loop) when other assignments exist earlier.

- **Error**: "Element assignments is duplicated at this location"
- **Fix**: Move ALL assignments to the assignments section

### Performance

- **Batch DML**: Get Records → Assignment → Update Records pattern
- **Filters over loops**: Use Get Records with filters instead of loops + decisions
- **Transform element**: Powerful but complex structure - NOT recommended for hand-written flows

### Design & Security

- **Variable Names (v2.0.0)**: Use prefixes for clarity:
  - `var_` Regular variables (e.g., `var_AccountName`)
  - `col_` Collections (e.g., `col_ContactIds`)
  - `rec_` Record variables (e.g., `rec_Account`)
  - `inp_` Input variables (e.g., `inp_RecordId`)
  - `out_` Output variables (e.g., `out_IsSuccess`)
- **Element Names**: PascalCase_With_Underscores (e.g., `Check_Account_Type`)
- **Button Names (v2.0.0)**: `Action_[Verb]_[Object]` (e.g., `Action_Save_Contact`)
- **System vs User Mode**: Understand implications, validate FLS for sensitive fields
- **No hardcoded data**: Use variables/custom settings
- See `references/flow-best-practices.md` for comprehensive guidance

## Common Error Patterns

**DML in Loop**: Collect records in collection variable → Single DML after loop
**Missing Fault Path**: Add fault connector from DML → error handling → log/display
**Self-Referencing Fault**: Error "element cannot be connected to itself" → Route fault connector to DIFFERENT element
**Element Duplicated**: Error "Element X is duplicated" → Group ALL elements of same type together
**Field Not Found**: Verify field exists, deploy field first if missing
**Insufficient Permissions**: Check profile permissions, consider System mode

| Error Pattern                   | Fix                                                     |
| ------------------------------- | ------------------------------------------------------- |
| `$Record__Prior` in Create-only | Only valid for Update/CreateAndUpdate triggers          |
| "Parent.Field doesn't exist"    | Use TWO Get Records (child then parent)                 |
| `$Record__c` loop fails         | Use `$Record` directly (single context, not collection) |

### Error → Solution Quick Reference

| Error Message                                       | Solution                                                                     |
| --------------------------------------------------- | ---------------------------------------------------------------------------- |
| `Duplicate developer name: X`                       | Screen field already created this reference — don't add a separate variable  |
| `Can't use object field with sObjectInputReference` | Remove `object` property when using `inputReference`                         |
| `isCollection invalid in FlowConstant`              | Use Decision + Variable counter instead of a constant collection             |
| `Invalid element reference X not found`             | Check all element names are unique and connectors point to existing elements |
| Flow won't open in Flow Builder                     | Add all empty element type arrays to flow metadata                           |
| Silent failure on `metadata_update`                 | Read current state first with `metadata_read`; build iteratively             |
| Required field missing                              | Add `processMetadataValues: []` to every element                             |

**Metadata Gotchas**: See `references/xml-gotchas.md`

---

## ⚠️ Critical Lessons Learned (Metadata API Flows)

These lessons apply when creating or updating flows via `metadata_create` / `metadata_update` (JSON format). They are based on real-world failures and must be followed to avoid deployment errors.

### Lesson 1: Screen Field Names ARE Element References

Screen fields automatically create element references with their field name. Do **NOT** create a separate variable for screen fields — this causes a `Duplicate developer name` error.

```json
// WRONG: Don't create variable with same name as screen field
{ "screens": [{ "fields": [{ "name": "User_Input" }] }],
  "variables": [{ "name": "User_Input" }]  // DUPLICATE ERROR }

// CORRECT: Reference the screen field directly
{ "formulas": [{ "expression": "{!User_Input} & \" suffix\"" }] }
```

### Lesson 2: Collection DML — Cannot Use Both `object` and `inputReference`

When creating records from a collection using `inputReference`, do **NOT** include the `object` field. Define `objectType` on the variable instead.

```json
// WRONG:
{ "name": "Create_All", "object": "Account", "inputReference": "Var_Col" }

// CORRECT: objectType goes on the variable, not the create element
{ "variables": [{ "name": "Var_Col", "dataType": "SObject",
    "objectType": "Account", "isCollection": true }],
  "recordCreates": [{ "name": "Create_All", "inputReference": "Var_Col" }] }
```

### Lesson 3: Constants Cannot Be Collections

Flow constants cannot be collections or SObjects. Use a Decision + Counter Variable instead.

### Lesson 4: Read Current State Before Complex Updates

**ALWAYS** call `metadata_read` immediately before `metadata_update` for complex changes. Salesforce replaces the entire flow version on update — working with stale metadata will overwrite recent changes.

1. Call `metadata_read` to get current state
2. Analyze current elements and dependencies
3. Modify the retrieved metadata
4. Call `metadata_update` with complete state

### Lesson 5: All Element Names Must Be Globally Unique

Every element name in a Flow must be unique across **ALL** element types. Use prefixes to enforce this:

| Element Type  | Naming Convention | Example             |
| ------------- | ----------------- | ------------------- |
| Variables     | `Var_*`           | `Var_Account_Id`    |
| Formulas      | `Formula_*`       | `Formula_Full_Name` |
| Screens       | `Screen_*`        | `Screen_Welcome`    |
| Decisions     | `Decision_*`      | `Decision_Route`    |
| Assignments   | `Assign_*`        | `Assign_Defaults`   |
| Choices       | `Choice_*`        | `Choice_Option_A`   |
| Screen Fields | Descriptive       | `Account_Name`      |

### Lesson 6: Build Flows Iteratively, Not All At Once

- **Phase 1 — Shell**: `metadata_create` with minimal structure. Test: Does it open in Flow Builder?
- **Phase 2 — Basic Navigation**: Add first screen and routing. Test: Can you navigate through it?
- **Phase 3 — Core Logic**: Add record lookups and variables. Test: Does data flow correctly?
- **Phase 4 — Advanced Features**: Add formulas, loops, calculations. Test: Do calculations work?

**Red flags**: Creating 100+ line JSON on first attempt. Adding 5+ new element types at once. Not testing in Flow Builder between changes.

### Lesson 7: Collection DML Pattern — Build, Gather, Execute

Never create records one-by-one in a loop. Build a collection, then execute a single DML operation:

1. **Build_Record** — Assign field values to `Var_Current_Record` (single SObject variable)
2. **Add_To_Collection** — Use operator `Add` to append to the collection variable
3. **After loop exits** — Single `recordCreates` with `inputReference` pointing to the collection

Synchronous DML limit: 150 statements. Creating 10 records individually = 10 DML. Creating 10 records via collection = 1 DML.

### Lesson 8: `processMetadataValues` — Always Include Empty Array

Every Flow element **MUST** have a `processMetadataValues` property, even if it's an empty array. Without it, Salesforce may fail silently or discard the element.

```json
{ "name": "Element_Name", "processMetadataValues": [] }
```

### Lesson 9: Empty Arrays for All Element Type Collections

Include **ALL** element type arrays in your flow metadata, even if empty. Missing arrays can cause silent failures, elements being deleted, or flows that won't save.

```json
{
  "assignments": [],
  "choices": [],
  "decisions": [],
  "formulas": [],
  "loops": [],
  "recordCreates": [],
  "recordDeletes": [],
  "recordLookups": [],
  "recordUpdates": [],
  "screens": [],
  "variables": [],
  "textTemplates": []
}
```

### Lesson 10: Connector Chains — Every Element Needs a Path

Every element (except the final one) must have a connector to the next element. Mental checklist for each element:

- Does it have a `connector`?
- If it's a decision, does it have a `defaultConnector`?
- Does the `targetReference` point to an existing element?
- Is this intentionally the final element (screen with `allowFinish: true`)?

### Flow Shell Template (JSON for `metadata_create`)

Always start with this complete template — include **ALL** empty arrays:

```json
{
  "fullName": "PLACEHOLDER",
  "label": "PLACEHOLDER",
  "apiVersion": 65,
  "processType": "Flow",
  "status": "Draft",
  "interviewLabel": "PLACEHOLDER {!$Flow.CurrentDateTime}",
  "environments": ["Default"],
  "processMetadataValues": [
    { "name": "BuilderType", "value": { "stringValue": "LightningFlowBuilder" } },
    { "name": "CanvasMode", "value": { "stringValue": "AUTO_LAYOUT_CANVAS" } }
  ],
  "start": {
    "locationX": 0,
    "locationY": 0,
    "connector": { "targetReference": "FIRST_ELEMENT" },
    "filters": [],
    "processMetadataValues": []
  },
  "assignments": [],
  "choices": [],
  "decisions": [],
  "formulas": [],
  "loops": [],
  "recordCreates": [],
  "recordDeletes": [],
  "recordLookups": [],
  "recordUpdates": [],
  "screens": [],
  "variables": [],
  "textTemplates": []
}
```

### Flow Element Types Reference

| Element Type   | Purpose               | Key Notes                                                                    |
| -------------- | --------------------- | ---------------------------------------------------------------------------- |
| Start          | Entry point           | Contains connector to first element; record-triggered adds filters/object    |
| Variables      | Store values          | Counter vars: `dataType` Number, `scale` 0. Collections: `isCollection` true |
| Screens        | User interface        | Fields auto-create element references — do NOT create duplicate variables    |
| Decisions      | Branching logic       | Must always include `defaultConnector`                                       |
| Record Lookups | Query Salesforce data | Use `storeOutputAutomatically: false` for security                           |
| Record Creates | Insert new records    | Use `inputReference` for collections — never combine with `object` field     |
| Assignments    | Set variable values   | Operators: `Assign`, `Add`, `AssignCount`                                    |
| Loops          | Iterate collections   | Auto-creates `currentItem_{LoopName}` variable                               |
| Formulas       | Computed values       | Use `{!VarName}` syntax to reference other elements                          |

## Edge Cases

| Scenario     | Solution                                      |
| ------------ | --------------------------------------------- |
| >200 records | Warn limits, suggest scheduled flow           |
| >5 branches  | Use subflows                                  |
| Cross-object | Check circular deps, test recursion           |
| Production   | Deploy Draft, activate explicitly             |
| Unknown org  | Use standard objects (Account, Contact, etc.) |

**Debug**: Flow not visible → deploy report + permissions | Tests fail → Debug Logs + bulk test | Sandbox→Prod fails → FLS + dependencies

---

## Flow MCP Patterns

### General rules

- Do **not** hard-code IDs (queues, users, record types) in flows
- Use Entry Conditions (formulas in the `start` block) instead of a Decision with an empty action
- Set layout to Auto-Layout (`CanvasMode: AUTO_LAYOUT_CANVAS`)
- Do **not** create a new flow to fix an issue — create a new **version** instead
- Do **not** say something "cannot be done via API" — always attempt it

### List all flows (with active and latest version info)

```
tooling_api_query(sObject="FlowDefinition", fields=["Id","DeveloperName","NamespacePrefix","MasterLabel","Description","ActiveVersionId","ActiveVersion.VersionNumber","LatestVersionId","LatestVersion.VersionNumber","LatestVersion.Status","LatestVersion.MasterLabel","LatestVersion.Description"])
```

### Retrieve a specific flow version

First get the version Id from the FlowDefinition query above, then:

```
tooling_api_query(sObject="Flow", fields=["Id","FullName","DefinitionId","Definition.DeveloperName","MasterLabel","Description","VersionNumber","Status","Metadata","ProcessType"], whereClause="Id='<flow version id>'")
```

Note: do **not** include `FullName` or `Metadata` in multi-record queries — only single-record retrieval supports these.

### Create a new flow

```
metadata_create(type="Flow", metadata=[{"fullName": "Flow_Name", "label": "Flow Name", "apiVersion": 65, "processType": "AutoLaunchedFlow", "status": "Draft", ...}])
```

### Update a flow (creates a new version)

1. Retrieve current metadata: `metadata_read(type="Flow", fullNames=["Flow_Name"])`
2. Apply changes to the metadata object
3. Deploy: `metadata_update(type="Flow", metadata=[{...}], upsert=True)`
   - **Do NOT change the `fullName`** — version numbers are managed automatically
   - In production: deploy as `status: Draft` and ask user to activate manually if you get an error

### Activate / deactivate a flow version

```
metadata_update(type="FlowDefinition", metadata=[{"fullName": "Flow_Name", "activeVersionNumber": <version>}])
```

To deactivate all versions: set `activeVersionNumber` to `0`.

### Delete a flow

1. Deactivate: `metadata_update(type="FlowDefinition", metadata=[{"fullName": "Flow_Name", "activeVersionNumber": 0}])`
2. Delete all versions: `tooling_api_dml(operation="delete", sObject="Flow", record={"Id": "<flow version id>"})` (repeat for each version)

### Check flow test coverage

```
tooling_api_query(sObject="Flow", fields=["Definition.DeveloperName"], whereClause="Status = 'Active' AND (ProcessType = 'AutolaunchedFlow' OR ProcessType = 'Workflow' OR ProcessType = 'CustomEvent' OR ProcessType = 'InvocableProcess') AND Id NOT IN (SELECT FlowVersionId FROM FlowTestCoverage)")
```

### Find paused or failed flow interviews

```
soql_query(sObject="FlowInterview", fields=["Id","Name","CurrentElement","InterviewStatus","PauseLabel","CreatedDate"], whereClause="InterviewStatus IN ('Paused', 'Failed')")
```

---

## Cirra AI Integration Examples

### Example 1: Verify Object Exists Before Creating Flow

```python
# Before generating a flow for a custom object
sobject_describe(
    sObject="Invoice__c",
    sf_user="prod-username"
)
# Returns: Field list, object metadata, standard fields
```

### Example 2: List Existing Flows

```python
# Check what flows already exist
metadata_list(
    type="Flow",
    sf_user="prod-username"
)
# Returns: All Flow metadata objects in org
```

### Example 3: Deploy Generated Flow

```python
# Pass flow metadata as a JSON object — NOT XML
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "label": "Auto Lead Assignment",
        "apiVersion": 65,
        "processType": "AutoLaunchedFlow",
        "status": "Draft",
        "environments": ["Default"],
        "start": {
            "locationX": 0, "locationY": 0,
            "object": "Lead",
            "recordTriggerType": "Create",
            "triggerType": "RecordAfterSave",
            "connector": {"targetReference": "First_Element"}
        }
        # ... remaining flow elements
    }],
    sf_user="prod-username"
)
```

### Example 4: Retrieve Existing Flow for Review

```python
# Get the metadata of an existing flow
metadata_read(
    type="Flow",
    fullNames=["Auto_Lead_Assignment"],
    sf_user="prod-username"
)
# Returns: Complete Flow metadata from org (JSON)
```

### Example 5: Query Flow Metadata (Tooling API)

```python
# Find all active flows
tooling_api_query(
    sObject="FlowDefinition",
    fields=["Id", "ApiName", "Description", "Status"],
    whereClause="Status = 'Active'",
    sf_user="prod-username"
)
```

---

## Cross-Skill Integration

| From Skill              | To cirra-ai-sf-flow | When                                 |
| ----------------------- | ------------------- | ------------------------------------ |
| cirra-ai-sf-apex        | → cirra-ai-sf-flow  | "Create Flow wrapper for Apex logic" |
| cirra-ai-sf-integration | → cirra-ai-sf-flow  | "Create HTTP Callout Flow"           |

| From cirra-ai-sf-flow | To Skill               | When                                                |
| --------------------- | ---------------------- | --------------------------------------------------- |
| cirra-ai-sf-flow      | → cirra-ai-sf-metadata | "Describe Invoice\_\_c" (verify fields before flow) |
| cirra-ai-sf-flow      | → cirra-ai-sf-data     | "Create 200 test Accounts" (after deploy)           |

**Deployment**: See Phase 4 above.

---

## LWC Integration (Screen Flows)

Embed custom Lightning Web Components in Flow Screens for rich, interactive UIs.

### Templates

| Template                          | Purpose                            |
| --------------------------------- | ---------------------------------- |
| `assets/screen-flow-with-lwc.xml` | Flow embedding LWC component       |
| `assets/apex-action-template.xml` | Flow calling Apex @InvocableMethod |

### Flow Pattern (XML reference — deploy as JSON)

> The XML below shows the structural pattern. When deploying via `metadata_create`, translate to the equivalent JSON object.

```xml
<screens>
    <fields>
        <extensionName>c:recordSelector</extensionName>
        <fieldType>ComponentInstance</fieldType>
        <inputParameters>
            <name>recordId</name>
            <value><elementReference>var_RecordId</elementReference></value>
        </inputParameters>
        <outputParameters>
            <assignToReference>var_SelectedId</assignToReference>
            <name>selectedRecordId</name>
        </outputParameters>
    </fields>
</screens>
```

### Documentation

| Resource              | Location                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------- |
| LWC Integration Guide | [references/lwc-integration-guide.md](references/lwc-integration-guide.md)                              |
| LWC Component Setup   | [cirra-ai-sf-lwc/assets/flow-integration-guide.md](../cirra-ai-sf-lwc/assets/flow-integration-guide.md) |
| Triangle Architecture | [references/triangle-pattern.md](references/triangle-pattern.md)                                        |

---

## Apex Integration

Call Apex `@InvocableMethod` classes from Flow for complex business logic.

### Flow Pattern (XML reference — deploy as JSON)

> The XML below shows the structural pattern. When deploying via `metadata_create`, translate to the equivalent JSON object.

```xml
<actionCalls>
    <name>Process_Record</name>
    <actionName>RecordProcessor</actionName>
    <actionType>apex</actionType>
    <inputParameters>
        <name>recordId</name>
        <value><elementReference>var_RecordId</elementReference></value>
    </inputParameters>
    <outputParameters>
        <assignToReference>var_IsSuccess</assignToReference>
        <name>isSuccess</name>
    </outputParameters>
    <faultConnector>
        <targetReference>Handle_Error</targetReference>
    </faultConnector>
</actionCalls>
```

### Documentation

| Resource                    | Location                                                                                              |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| Apex Action Template        | `assets/apex-action-template.xml`                                                                     |
| Apex @InvocableMethod Guide | [cirra-ai-sf-apex/references/flow-integration.md](../cirra-ai-sf-apex/references/flow-integration.md) |
| Triangle Architecture       | [references/triangle-pattern.md](references/triangle-pattern.md)                                      |

### ⚠️ Flows for Agentforce

**When creating Flows for Agentforce agents:**

- cirra-ai-sf-flow (this skill) creates the validated Flow metadata (JSON)
- cirra-ai-sf-flow deploys via Cirra AI metadata_create tool
- **Action Definition registration required** (see below)
- Only THEN can agents use `flow://FlowName` targets

**Variable Name Matching**: When creating Flows for Agentforce agents:

- Agent Script input/output names MUST match Flow variable API names exactly
- Use descriptive names (e.g., `inp_AccountId`, `out_AccountName`)
- Mismatched names cause "Internal Error" during agent publish

### Output Variable Naming for Agentforce

Use `out_` prefix for output variables to distinguish them in Action Definition schema:

```xml
<variables>
    <name>out_CaseSubject</name>
    <dataType>String</dataType>
    <isOutput>true</isOutput>
</variables>
<variables>
    <name>out_CaseStatus</name>
    <dataType>String</dataType>
    <isOutput>true</isOutput>
</variables>
```

### Formula Expression Limitations in Flows

Flow formulas have more limited function support than formula fields. Avoid:

| Function                  | Status         | Alternative                            |
| ------------------------- | -------------- | -------------------------------------- |
| `BLANKVALUE()`            | ❌ Not in Flow | Use Decision element or `IF()`         |
| `CASESAFEID()`            | ❌ Not in Flow | ID variables handle this automatically |
| `ISNEW()` / `ISCHANGED()` | ❌ Not in Flow | Use `$Record__Prior` comparisons       |

### Action Definition Registration (REQUIRED)

> **CRITICAL**: Creating a Flow is NOT sufficient for Agentforce. The Flow must be registered as an Action Definition.

**Registration Workflow:**

1. **Deploy Flow** to target org via cirra-ai-sf-flow + Cirra AI metadata_create
2. Navigate to **Setup > Agentforce > Action Definitions**
3. Click **"New Action"**, select **"Flow"** as target type
4. Choose your deployed Flow from the list
5. **Map input/output variables** - these become the action's schema
6. Configure planner flags:
   - `is_displayable`: Can LLM show output to user?
   - `is_used_by_planner`: Can LLM use output for decisions?
7. **Save** the Action Definition

```
Flow Created  →  Deployed to Org  →  Action Definition Created  →  Agent Can Use
     ↑               ↑                        ↑                         ↑
   cirra-ai-sf-flow  Cirra AI            Setup > Agentforce         @actions.MyAction
```

**Why This Matters**: The Action Definition is what exposes the Flow to the agent runtime with proper input/output schema mapping. Without it, `@actions.FlowName` will fail with `ValidationError: Tool target 'FlowName' is not an action definition`.

| Direction                               | Pattern                                             |
| --------------------------------------- | --------------------------------------------------- |
| cirra-ai-sf-flow → cirra-ai-sf-metadata | "Describe Invoice\_\_c" (verify fields before flow) |
| cirra-ai-sf-flow → Cirra AI             | Deploy with validation via metadata_create          |
| cirra-ai-sf-flow → cirra-ai-sf-data     | "Create 200 test Accounts" (test data after deploy) |

## Notes

**Dependencies** (optional): cirra-ai-sf-metadata, cirra-ai-sf-data | **API**: 65.0 | **Mode**: Strict (warnings block) | **MCP Server**: Cirra AI (required)

**Required Setup**:

- Cirra AI account connected to Salesforce org
- `cirra_ai_init()` called once per session
- Valid Salesforce username for `sf_user` parameter
- **Audit Output**: All audit intermediate files go to `--output-dir` by default

**Validation hook**: Implemented at the plugin level via the PreToolUse hook — `pre-mcp-validate.py` is dispatched based on tool and metadata type (for example `Flow` and `FlowDefinition`) and runs whenever those operations occur, regardless of which skill is active. Use `python scripts/validate_flow_cli.py ...` for additional on-demand checks.
