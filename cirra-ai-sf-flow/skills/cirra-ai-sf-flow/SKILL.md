---
name: cirra-ai-sf-flow
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
2. Generate Flow XML
3. Deploy via metadata_create tool (Cirra AI MCP Server)
4. Retrieve existing flows via metadata_read or metadata_list (Cirra AI MCP Server)
5. Query Flow metadata via tooling_api_query for FlowDefinition
6. Describe objects/fields via sobject_describe before flow creation
```

**Scoring**: 110 points across 6 categories. Minimum 88 (80%) for deployment.

---

## Core Responsibilities

1. **Flow Generation**: Create well-structured Flow metadata XML from requirements
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

**Cirra AI Tool Mapping** (replaces SF CLI):
| SF CLI Command | Cirra AI Tool | Purpose |
|---|---|---|
| `sf data query` | `soql_query` | Query org data |
| `sf data query --use-tooling-api` | `tooling_api_query` | Query FlowDefinition metadata |
| `sf project deploy` | `metadata_create` | Deploy Flow XML to org |
| `sf project retrieve` | `metadata_read` | Retrieve Flow XML from org |
| `sf org list metadata --metadata-type Flow` | `metadata_list` | List existing flows |
| `sf sobject describe Account` | `sobject_describe` | Verify object/field structure |

---

## ⚠️ CRITICAL: Orchestration Order

**cirra-ai-sf-metadata → cirra-ai-sf-flow → cirra-ai-sf-deploy → cirra-ai-sf-data** (you are here: cirra-ai-sf-flow with Cirra AI)

⚠️ Flow references custom object/fields? Create with cirra-ai-sf-metadata FIRST. Deploy objects BEFORE flows.

```
1. cirra-ai-sf-metadata  → Create objects/fields (local)
2. cirra-ai-sf-flow      ◀── YOU ARE HERE (create flow, deploy via Cirra AI)
3. cirra-ai-sf-deploy    → Optional additional deployment (already deployed via metadata_create)
4. cirra-ai-sf-data      → Create test data (remote - objects must exist!)
```

See `docs/orchestration.md` for extended orchestration patterns including Agentforce.

---

## 🔑 Key Insights

| Insight                  | Details                                                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Before vs After Save** | Before-Save: same-record updates (no DML), validation. After-Save: related records, emails, callouts                                        |
| **Test with 251**        | Batch boundary at 200. Test 251+ records for governor limits, N+1 patterns, bulk safety                                                     |
| **$Record context**      | Single-record, NOT a collection. Platform handles batching. Never loop over $Record                                                         |
| **Transform vs Loop**    | Transform: data mapping/shaping (30-50% faster). Loop: per-record decisions, counters, varying logic. See `docs/transform-vs-loop-guide.md` |

---

## Workflow Design (5-Phase Pattern)

### Phase 1: Requirements Gathering

**Before building, evaluate alternatives**: See `docs/flow-best-practices.md` Section 1 "When NOT to Use Flow" - sometimes a Formula Field, Validation Rule, or Roll-Up Summary Field is the better choice.

Use **AskUserQuestion** to gather:

- Flow type (Screen, Record-Triggered After/Before Save/Delete, Platform Event, Autolaunched, Scheduled)
- Primary purpose (one sentence)
- Trigger object/conditions (if record-triggered)

**Pre-Development Planning**: For complex flows, document requirements and sketch logic before building. See `docs/flow-best-practices.md` Section 2 "Pre-Development Planning" for templates and recommended tools.

**Then**:

1. **Initialize**: Call `cirra_ai_init()` with no parameters. If a default org is configured, confirm with the user. If no default, ask for the Salesforce user/alias before proceeding.
2. Use `sobject_describe` to verify object/field existence before referencing
3. Use `metadata_list` to check existing flows: `metadata_list(type="Flow")`
4. Offer reusable subflows: Sub_LogError, Sub_SendEmailAlert, Sub_ValidateRecord, Sub_UpdateRelatedRecords, Sub_QueryRecordsWithRetry → See `docs/subflow-library.md` (in cirra-ai-sf-flow folder)
5. If complex automation: Reference `docs/governance-checklist.md` (in cirra-ai-sf-flow folder)
6. Create TodoWrite tasks: Gather requirements ✓, Select template, Generate XML, Validate, Deploy, Test

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

**Element Pattern Templates** (`templates/elements/`):
| Element | Template | Purpose |
|---------|----------|---------|
| Loop | `loop-pattern.xml` | Complete loop with nextValueConnector/noMoreValuesConnector |
| Get Records | `get-records-pattern.xml` | All recordLookups options (filters, sort, limit) |
| Delete Records | `record-delete-pattern.xml` | Filter-based and reference-based delete patterns |

**Template Path Resolution** (try in order):

1. **Plugin folder**: `${CLAUDE_PLUGIN_ROOT}/templates/[template].xml`
2. **Project folder**: `[project-root]/cirra-ai-sf-flow/templates/[template].xml`

**Example**: `Read: ${CLAUDE_PLUGIN_ROOT}/templates/record-triggered-flow-template.xml`

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

- **CRITICAL**: Record-triggered flows CANNOT call subflows via XML deployment. Use inline orchestration instead. See `docs/xml-gotchas.md` (in cirra-ai-sf-flow) and `docs/orchestration-guide.md` (in cirra-ai-sf-flow)

### Phase 3: Flow Generation & Deployment (via Cirra AI)

**Generate flow XML**:
Generate the complete Flow XML with:

- API Version: 65.0
- Proper alphabetical element ordering
- All required metadata fields (label, processType, status, etc.)

**CRITICAL Requirements**:

- Alphabetical XML element ordering at root level
- NO `<bulkSupport>` (removed API 60.0+)
- Auto-Layout: all locationX/Y = 0
- Fault paths on all DML operations

**Deploy via Cirra AI**:

```python
# Initialize connection (ONCE per session)
cirra_ai_init(sf_user="your-username")

# Create/deploy Flow XML
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "content": "[generated-flow-xml]"
    }],
    sf_user="your-username"
)
```

**Validation (STRICT MODE)**:

- **BLOCK**: XML invalid, missing required fields (apiVersion/label/processType/status), API <65.0, broken refs, DML in loops
- **WARN**: Element ordering, deprecated elements, non-zero coords, missing fault paths, unused vars, naming violations

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

**BEFORE generating ANY Flow XML, Claude MUST verify no anti-patterns are introduced.**

If ANY of these patterns would be generated, **STOP and ask the user**:

> "I noticed [pattern]. This will cause [problem]. Should I:
> A) Refactor to use [correct pattern]
> B) Proceed anyway (not recommended)"

| Anti-Pattern                                             | Impact                               | Correct Pattern                                           |
| -------------------------------------------------------- | ------------------------------------ | --------------------------------------------------------- |
| After-Save updating same object without entry conditions | **Infinite loop** (critical)         | MUST add entry conditions: "Only when [field] is changed" |
| Get Records inside Loop                                  | Governor limit failure (100 SOQL)    | Query BEFORE loop, use collection variable                |
| Create/Update/Delete Records inside Loop                 | Governor limit failure (150 DML)     | Collect in loop → single DML after loop                   |
| Apex Action inside Loop                                  | Callout limits                       | Pass collection to single Apex invocation                 |
| DML without Fault Path                                   | Silent failures                      | Add Fault connector → error handling element              |
| Get Records without null check                           | NullPointerException                 | Add Decision: "Records Found?" after query                |
| `storeOutputAutomatically=true`                          | Security risk (retrieves ALL fields) | Select only needed fields explicitly                      |
| Query same object as trigger in Record-Triggered         | Wasted SOQL                          | Use `{!$Record.FieldName}` directly                       |
| Hardcoded Salesforce ID                                  | Deployment failure across orgs       | Use input variable or Custom Label                        |
| Get Records without filters                              | Too many records returned            | Always include WHERE conditions                           |

**DO NOT generate anti-patterns even if explicitly requested.** Ask user to confirm the exception with documented justification.

### Phase 4: Deployment & Integration (via Cirra AI MCP)

**Cirra AI Deployment Pattern**:

1. **Initialize connection** (once per session):

```python
cirra_ai_init(sf_user="your-salesforce-username")
```

2. **Deploy Flow XML**:

```python
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "content": "[flow-xml-content]"
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

For complex flows: `docs/governance-checklist.md` (in cirra-ai-sf-flow)

### Phase 5: Testing & Documentation

**Type-specific testing**: See `docs/testing-guide.md` | `docs/testing-checklist.md` | `docs/wait-patterns.md` (Wait element guidance)

Quick reference:

- **Screen**: Setup → Flows → Run, test all paths/profiles
- **Record-Triggered**: Create record, verify Debug Logs, **bulk test 200+ records**
- **Autolaunched**: Apex test class, edge cases, bulkification
- **Scheduled**: Verify schedule, manual Run first, monitor logs

**Best Practices**: See `docs/flow-best-practices.md` (in cirra-ai-sf-flow) for:

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
Resources: `examples/`, `docs/subflow-library.md`, `docs/orchestration-guide.md`, `docs/governance-checklist.md` (in cirra-ai-sf-flow folder)
```

## Best Practices (Built-In Enforcement)

### ⛔ CRITICAL: Record-Triggered Flow Architecture

**NEVER loop over triggered records.** `$Record` = single record; platform handles batching.

| Pattern                | OK? | Notes                             |
| ---------------------- | --- | --------------------------------- |
| `$Record.FieldName`    | ✅  | Direct access                     |
| Loop over `$Record__c` | ❌  | Process Builder pattern, not Flow |
| Loop over `$Record`    | ❌  | $Record is single, not collection |

**Loops for RELATED records only**: Get Records → Loop collection → Assignment → DML after loop

### ⛔ CRITICAL: No Parent Traversal in Get Records

`recordLookups` cannot query `Parent.Field` (e.g., `Manager.Name`). **Solution**: Two Get Records - child first, then parent by Id.

### recordLookups Best Practices

| Element                            | Recommendation                          | Why                                    |
| ---------------------------------- | --------------------------------------- | -------------------------------------- |
| `getFirstRecordOnly`               | Set to `true` for single-record queries | Avoids collection overhead             |
| `storeOutputAutomatically`         | Set to `false`, use `outputReference`   | Prevents data leaks, explicit variable |
| `assignNullValuesIfNoRecordsFound` | Set to `false`                          | Preserves previous variable value      |
| `faultConnector`                   | Always include                          | Handle query failures gracefully       |
| `filterLogic`                      | Use `and` for multiple filters          | Clear filter behavior                  |

### Critical Requirements

- **API 65.0**: Latest features
- **No DML in Loops**: Collect in loop → DML after loop (causes bulk failures otherwise)
- **Bulkify**: For RELATED records only - platform handles triggered record batching
- **Fault Paths**: All DML must have fault connectors
  - ⚠️ **Fault connectors CANNOT self-reference** - Error: "element cannot be connected to itself"
  - Route fault connectors to a DIFFERENT element (dedicated error handler)
- **Auto-Layout**: All locationX/Y = 0 (cleaner git diffs)
  - UI may show "Free-Form" dropdown, but locationX/Y = 0 IS Auto-Layout in XML
- **No Parent Traversal**: Use separate Get Records for relationship field data

### XML Element Ordering (CRITICAL)

**All elements of the same type MUST be grouped together. Do NOT scatter elements across the file.**

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
- **Transform element**: Powerful but complex XML - NOT recommended for hand-written flows

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
- See `docs/flow-best-practices.md` (in cirra-ai-sf-flow) for comprehensive guidance

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

**XML Gotchas**: See `docs/xml-gotchas.md` (in cirra-ai-sf-flow)

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
# After generating Auto_Lead_Assignment.flow-meta.xml
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "content": "<Flow ...>[full XML here]</Flow>"
    }],
    sf_user="prod-username"
)
```

### Example 4: Retrieve Existing Flow for Review

```python
# Get the XML of an existing flow
metadata_read(
    type="Flow",
    fullNames=["Auto_Lead_Assignment"],
    sf_user="prod-username"
)
# Returns: Complete Flow XML from org
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

| From Skill            | To cirra-ai-sf-flow | When                                        |
| --------------------- | ------------------- | ------------------------------------------- |
| cirra-ai-sf-ai-agentscript | → cirra-ai-sf-flow  | "Create Autolaunched Flow for agent action" |
| cirra-ai-sf-apex           | → cirra-ai-sf-flow  | "Create Flow wrapper for Apex logic"        |
| cirra-ai-sf-integration    | → cirra-ai-sf-flow  | "Create HTTP Callout Flow"                  |

| From cirra-ai-sf-flow | To Skill              | When                                                |
| --------------------- | --------------------- | --------------------------------------------------- |
| cirra-ai-sf-flow      | → cirra-ai-sf-metadata | "Describe Invoice\_\_c" (verify fields before flow) |
| cirra-ai-sf-flow      | → cirra-ai-sf-deploy   | "Deploy flow with --dry-run"                        |
| cirra-ai-sf-flow      | → cirra-ai-sf-data     | "Create 200 test Accounts" (after deploy)           |

**Deployment**: See Phase 4 above.

---

## LWC Integration (Screen Flows)

Embed custom Lightning Web Components in Flow Screens for rich, interactive UIs.

### Templates

| Template                             | Purpose                            |
| ------------------------------------ | ---------------------------------- |
| `templates/screen-flow-with-lwc.xml` | Flow embedding LWC component       |
| `templates/apex-action-template.xml` | Flow calling Apex @InvocableMethod |

### Flow XML Pattern

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

| Resource              | Location                                                                          |
| --------------------- | --------------------------------------------------------------------------------- |
| LWC Integration Guide | [docs/lwc-integration-guide.md](docs/lwc-integration-guide.md)                                     |
| LWC Component Setup   | [cirra-ai-sf-lwc/docs/flow-integration-guide.md](../cirra-ai-sf-lwc/docs/flow-integration-guide.md) |
| Triangle Architecture | [docs/triangle-pattern.md](docs/triangle-pattern.md)                                               |

---

## Apex Integration

Call Apex `@InvocableMethod` classes from Flow for complex business logic.

### Flow XML Pattern

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

| Resource                    | Location                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------- |
| Apex Action Template        | `templates/apex-action-template.xml`                                    |
| Apex @InvocableMethod Guide | [cirra-ai-sf-apex/docs/flow-integration.md](../cirra-ai-sf-apex/docs/flow-integration.md) |
| Triangle Architecture       | [docs/triangle-pattern.md](docs/triangle-pattern.md)                    |

### ⚠️ Flows for cirra-ai-sf-ai-agentscript

**When cirra-ai-sf-ai-agentscript requests a Flow:**

- cirra-ai-sf-ai-agentscript will invoke cirra-ai-sf-flow (this skill) to create Flows
- cirra-ai-sf-flow creates the validated Flow XML
- cirra-ai-sf-flow deploys via Cirra AI metadata_create tool
- **Action Definition registration required** (see below)
- Only THEN can cirra-ai-sf-ai-agentscript use `flow://FlowName` targets

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

| Direction                      | Pattern                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------ |
| cirra-ai-sf-flow → cirra-ai-sf-metadata       | "Describe Invoice\_\_c" (verify fields before flow)                    |
| cirra-ai-sf-flow → Cirra AI          | Deploy with validation via metadata_create                             |
| cirra-ai-sf-flow → cirra-ai-sf-data           | "Create 200 test Accounts" (test data after deploy)                    |
| cirra-ai-sf-ai-agentscript → cirra-ai-sf-flow | "Create Autolaunched Flow for agent action" - **cirra-ai-sf-flow is MANDATORY** |

## Org-Wide Flow Audit

This plugin includes `hooks/scripts/score_flows.py` — a scalable scorer that audits ALL active Flows in an org using the 110-point rubric.

### Usage

```bash
python3 hooks/scripts/score_flows.py --output-dir ./audit_output [--batch-size 200] [--resume]
```

### Features

- **Pagination**: Fetches FlowDefinitions in batches via `tooling_api_query` with `Id > lastId` cursor
- **Resume**: Saves progress every 50 flows to `{output_dir}/intermediate/flow_scoring_progress.json`
- **Anti-Pattern Detection**: DML in loop, query in loop, missing fault path, missing description, naming violation, storeOutputAutomatically, hardcoded IDs, infinite loop risk, excessive complexity
- **Dual Detection**: Both metadata-based (field heuristics) and XML-based (full `metadata_read` analysis)
- **Output-Directory-First**: ALL files written to `--output-dir` — no files outside the output tree

### Output Files

```
{output_dir}/intermediate/
├── flow_batch_*.json              # Raw FlowDefinition metadata per batch
├── flow_scoring_progress.json     # Resume checkpoint
├── flow_scores.json               # Individual flow scores
└── flow_scoring_summary.json      # Aggregate statistics & distribution
```

### Scoring Thresholds

| Range | Recommendation |
|---|---|
| ≥ 88 | ✅ Deploy |
| 55-87 | ⚠️ Review |
| < 55 | ❌ Block |

---

## Notes

**Dependencies** (optional): cirra-ai-sf-metadata, cirra-ai-sf-data | **API**: 65.0 | **Mode**: Strict (warnings block) | **MCP Server**: Cirra AI (required)

**Required Setup**:

- Cirra AI account connected to Salesforce org
- `cirra_ai_init()` called once per session
- Valid Salesforce username for `sf_user` parameter
- **Audit Output**: All audit intermediate files go to `--output-dir` by default

---

## License

MIT License. See [LICENSE](LICENSE) file.
Copyright (c) 2024-2025 Jag Valaiyapathy
