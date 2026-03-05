---
name: cirra-ai-sf-flow
metadata:
  version: 1.1.0
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

# Create/deploy Flow as structured metadata (NOT raw XML — unlike ApexClass,
# Flow metadata_create does not accept XML in a "content" field)
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "apiVersion": "65.0",
        "label": "Auto Lead Assignment",
        "processType": "AutoLaunchedFlow",
        "status": "Draft",
        # ... remaining Flow structure as JSON properties ...
    }],
    sf_user="your-username"
)
```

**For Review** — validate an existing flow from the org or a local file before modifying:

- `/validate-flow <FlowApiName>` — fetch and validate a single flow from the org
- `/validate-flow All` — full org audit sorted by score

**Validation (STRICT MODE)**:

- **BLOCK** (CRITICAL — deployment denied): DML in loops, SOQL in loops, recursive after-update without entry conditions
- **WARN** (score deduction): Missing required fields, API <65.0, element ordering, missing fault paths, unused vars, naming violations, non-zero coords

**New v2.0.0 Validations**:

- `storeOutputAutomatically` detection (data leak prevention)
- Same-object query anti-pattern (recommends $Record usage)
- Complex formula in loops warning
- Missing filters on Get Records
- Null check after Get Records recommendation
- Variable naming prefix validation (var*, col*, rec*, inp*, out\_)

### Schema Validation (Structural)

Before deployment, validate the generated Flow against known structural
requirements. This applies to **both XML and JSON** output formats.

> **Why not a full XSD?** Salesforce publishes a metadata XSD/WSDL, but public
> copies (e.g., [forcedotcom/idecore](https://github.com/forcedotcom/idecore/blob/master/com.salesforce.ide.api/schema/metadata.xsd))
> are stuck at API v39.0 and miss modern flow elements. The only reliable
> source is the org-specific WSDL (Setup > API > Generate Metadata WSDL),
> which is impractical to fetch at skill runtime. The structural checks below
> cover the issues that most commonly cause deployment failures.

#### Tier 1 — Built-in structural checks (always run)

These checks work on both XML and JSON representations and require no external
tools. Run them before every `metadata_create` or `metadata_update` call.

| Check                      | Applies to | What to validate                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| -------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Required top-level fields  | XML + JSON | `apiVersion`, `label`, `processType`, `status`, `start` must be present                                                                                                                                                                                                                                                                                                                                                                                            |
| Valid `processType` enum   | XML + JSON | Must be one of: `AutoLaunchedFlow`, `Screen`, `RecordTriggeredFlow`, `ScheduleTriggeredFlow`, `PlatformEvent`, `Workflow`, `CustomEvent`, `ActionPlan`, `CartAsyncFlow`, `CheckoutFlow`, `ContactRequestFlow`, `FieldServiceMobile`, `FieldServiceWeb`, `FSCLending`, `IndividualObject`, `InvocableProcess`, `Journey`, `LoginFlow`, `ManagedContentFlow`, `OrchestrationFlow`, `Orchestrator`, `SurveyEnrich`, `TransactionSecurityFlow`, `UserProvisioningFlow` |
| Valid `status` enum        | XML + JSON | Must be `Draft`, `Active`, `Obsolete`, or `InvalidDraft`                                                                                                                                                                                                                                                                                                                                                                                                           |
| `apiVersion` range         | XML + JSON | Must be a valid decimal (e.g., `65.0`). Warn if < 55.0, block if absent                                                                                                                                                                                                                                                                                                                                                                                            |
| Element type grouping      | XML only   | All elements of the same type (e.g., all `<assignments>`) must be contiguous — no scattering                                                                                                                                                                                                                                                                                                                                                                       |
| Alphabetical root ordering | XML only   | Root-level element types must follow alphabetical order (see XML Element Ordering section)                                                                                                                                                                                                                                                                                                                                                                         |
| Connector integrity        | XML + JSON | Every `connector.targetReference` and `faultConnector.targetReference` must reference an element that exists in the flow                                                                                                                                                                                                                                                                                                                                           |
| No orphaned elements       | XML + JSON | Every non-start element must be reachable from `start` via connector chain                                                                                                                                                                                                                                                                                                                                                                                         |
| Variable type validity     | XML + JSON | `dataType` must be one of: `String`, `Number`, `Currency`, `Boolean`, `Date`, `DateTime`, `Picklist`, `Multipicklist`, `SObject`, `Apex`                                                                                                                                                                                                                                                                                                                           |
| DML fault paths            | XML + JSON | All `recordCreates`, `recordUpdates`, `recordDeletes` must have a `faultConnector`                                                                                                                                                                                                                                                                                                                                                                                 |

#### Tier 2 — Org-validated schema (when `sf` CLI is available)

When the Salesforce CLI is available and authenticated (see `cirra-ai-sf-audit`
environment detection pattern), use a **dry-run deployment** to validate against
the org's actual metadata schema at its current API version:

```bash
# Write the flow to a temporary sfdx project structure
mkdir -p /tmp/flow-validate/force-app/main/default/flows
cp <flow-file>.flow-meta.xml /tmp/flow-validate/force-app/main/default/flows/

# Dry-run deploy — validates schema + dependencies without saving
sf project deploy validate \
  --source-dir /tmp/flow-validate/force-app/main/default/flows \
  --target-org <org> \
  --json
```

This validates:

- Full XML structure against the org's current metadata XSD
- Field and object references exist in the target org
- API version compatibility
- Dependency resolution (referenced Apex classes, subflows, etc.)

For **JSON payloads** (used with `metadata_create`), there is no equivalent
offline schema. Tier 1 checks cover structural validity; the MCP
`metadata_create` call itself acts as the authoritative JSON validator — if
the Metadata API rejects it, the error message identifies the invalid property.

**Error handling**: If `sf project deploy validate` fails:

- Parse the `--json` output for `componentFailures`
- Map each failure to the corresponding Tier 1 check category
- Report failures alongside the 110-point score

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
cirra_ai_init()
```

2. **Deploy Flow XML**:

> **Automatic validation**: A skill-scoped PreToolUse hook runs `pre-mcp-validate.py` before every `metadata_create`, `metadata_update`, and `tooling_api_dml` call while this skill is active. It blocks deployment for CRITICAL/HIGH issues (DML in loops, missing fault paths) and warns when score is below 80% (88/110).

```python
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "apiVersion": "65.0",
        "label": "Auto Lead Assignment",
        "processType": "AutoLaunchedFlow",
        "status": "Draft",
        # ... Flow structure as JSON (NOT raw XML) ...
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
metadata_create(type="Flow", metadata=[{"fullName": "Flow_Name", "apiVersion": "65.0", "label": "Flow Name", "processType": "AutoLaunchedFlow", "status": "Draft", ...}])
```

> **API version**: Always specify `"apiVersion": "65.0"` (or current) explicitly. If omitted, `metadata_create` defaults to API v49.0, which lacks modern flow features.
>
> **InvalidDraft status**: Salesforce auto-classifies a Flow as `InvalidDraft` (not `Draft`) when it has `status: Draft` but no trigger configuration (no `start` element with `triggerType`, or no `processType` that implies auto-launch). This is expected Salesforce behavior — the flow becomes `Draft` once a valid trigger or entry condition is added.

### Update a flow

> **Version behavior**: A new version is only created when the **latest version is Active**. If the latest version is already a **Draft**, the update **replaces it in-place** with no version history preserved. Always check the latest version status first with `tooling_api_query` on FlowDefinition.

1. Check current status: `tooling_api_query(sObject="FlowDefinition", fields=["DeveloperName","LatestVersion.Status","LatestVersion.VersionNumber"], whereClause="DeveloperName='Flow_Name'")`
2. Retrieve current metadata: `metadata_read(type="Flow", fullNames=["Flow_Name"])`
3. Apply changes to the metadata object
4. Deploy: `metadata_update(type="Flow", metadata=[{...}], upsert=True)`
   - **Do NOT change the `fullName`** — version numbers are managed automatically
   - In production: deploy as `status: Draft` and ask user to activate manually if you get an error
   - If latest version is Draft, warn the user that the update will overwrite the existing Draft

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
# Deploy flow as structured metadata (NOT raw XML in "content")
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Auto_Lead_Assignment",
        "apiVersion": "65.0",
        "label": "Auto Lead Assignment",
        "processType": "AutoLaunchedFlow",
        "status": "Draft",
        # ... remaining Flow properties as JSON ...
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

| From Skill              | To cirra-ai-sf-flow | When                                 |
| ----------------------- | ------------------- | ------------------------------------ |
| cirra-ai-sf-apex        | → cirra-ai-sf-flow  | "Create Flow wrapper for Apex logic" |
| cirra-ai-sf-integration | → cirra-ai-sf-flow  | "Create HTTP Callout Flow"           |

| From cirra-ai-sf-flow | To Skill               | When                                                |
| --------------------- | ---------------------- | --------------------------------------------------- |
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

| Resource              | Location                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| LWC Integration Guide | [docs/lwc-integration-guide.md](docs/lwc-integration-guide.md)                                      |
| LWC Component Setup   | [cirra-ai-sf-lwc/docs/flow-integration-guide.md](../cirra-ai-sf-lwc/docs/flow-integration-guide.md) |
| Triangle Architecture | [docs/triangle-pattern.md](docs/triangle-pattern.md)                                                |

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

| Resource                    | Location                                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| Apex Action Template        | `templates/apex-action-template.xml`                                                      |
| Apex @InvocableMethod Guide | [cirra-ai-sf-apex/docs/flow-integration.md](../cirra-ai-sf-apex/docs/flow-integration.md) |
| Triangle Architecture       | [docs/triangle-pattern.md](docs/triangle-pattern.md)                                      |

### ⚠️ Flows for Agentforce

**When creating Flows for Agentforce agents:**

- cirra-ai-sf-flow (this skill) creates the validated Flow XML
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

**Validation hook**: Scope-limited to this skill — `pre-mcp-validate.py` only fires while cirra-ai-sf-flow is active; use `/validate-flow` for on-demand checks.
