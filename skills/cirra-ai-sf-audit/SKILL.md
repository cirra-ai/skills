---
name: cirra-ai-sf-audit
description: >
  Run a comprehensive Salesforce org audit. Inventories and scores Apex classes,
  Apex triggers, Flows, Process Builders, Workflow Rules, LWC components, custom
  objects and fields, validation rules, Profiles, and Permission Sets. Generates
  Word, Excel, and HTML reports. Use when asked to audit a Salesforce org, review
  org health, generate an org inventory, run an org health check, audit
  permissions, review the data model, or audit apex flows and lwc.
metadata:
  version: 1.2.0
---

# cirra-ai-sf-audit: Salesforce Org Audit

Run a comprehensive Salesforce org audit that inventories and evaluates all
major metadata categories. The goal is a **complete overview** of the org — not
just security scoring — covering code quality, automation health, data model
design, and the permission model. Follow these phases in order.

**Scoring**: Where a numeric rubric exists, use the rubric from the corresponding
domain skill (`cirra-ai-sf-apex`, `cirra-ai-sf-flow`, `cirra-ai-sf-lwc`,
`cirra-ai-sf-metadata`). These skills should be loaded in your context alongside
this skill. Do not invent your own criteria.

For categories without a numeric rubric (Triggers, Workflow Rules, Process
Builders, Profiles, Validation Rules), produce an inventory with qualitative
findings and severity classifications instead.

## Prerequisites

Call `cirra_ai_init()` first if not already done this session.

## Phase 1 — Inventory the org

Query component counts across every category so the user knows the full scope:

```
tooling_api_query: ApexClass WHERE NamespacePrefix = null → COUNT
tooling_api_query: ApexTrigger WHERE NamespacePrefix = null → COUNT
tooling_api_query: FlowDefinition WHERE ActiveVersionId != null AND NamespacePrefix = null → COUNT
tooling_api_query: LightningComponentBundle WHERE NamespacePrefix = null → COUNT
tooling_api_query: CustomObject WHERE NamespacePrefix = null → COUNT
tooling_api_query: ValidationRule WHERE NamespacePrefix = null → COUNT
tooling_api_query: WorkflowRule WHERE NamespacePrefix = null → COUNT
soql_query: PermissionSet WHERE IsOwnedByProfile = false AND NamespacePrefix = null → COUNT
soql_query: PermissionSetGroup → COUNT
soql_query: Profile → COUNT
```

Tell the user the full inventory, for example:
"Found X Apex classes, T triggers, Y active Flows, Z LWC components, P custom objects, V validation rules, W workflow rules, N Permission Sets, M Permission Set Groups, and Q Profiles. Starting audit..."

## Phase 2 — Collect and score Apex classes

Paginate Apex class metadata in batches of 200 using an Id cursor:

1. Fetch `Id`, `Name`, `LengthWithoutComments`, `ApiVersion` for each batch via `tooling_api_query`
2. Fetch `Body` for each class individually (one at a time to avoid size limits)
3. Write each class body to `./audit_output/intermediate/apex/<ClassName>.cls` before scoring
4. Score using the 150-point rubric from the `cirra-ai-sf-apex` skill
5. Track: class name, score, issues found

## Phase 3 — Collect and review Apex triggers

Paginate Apex triggers in batches of 200 using an Id cursor:

1. Fetch `Id`, `Name`, `TableEnumOrId`, `ApiVersion`, `Status` via `tooling_api_query` on `ApexTrigger`
2. Fetch `Body` for each trigger individually
3. Write each trigger body to `./audit_output/intermediate/triggers/<TriggerName>.trigger`

Score triggers using the `cirra-ai-sf-apex` skill's rubric where applicable (bulkification,
security, error handling). Additionally flag these trigger-specific issues:

| Finding                                                                                    | Severity |
| ------------------------------------------------------------------------------------------ | -------- |
| Logic inside the trigger body instead of a handler class                                   | HIGH     |
| No bulkification (iterating `Trigger.new` with SOQL/DML inside)                            | CRITICAL |
| Trigger on the same object for the same event as another trigger (order-of-execution risk) | HIGH     |
| Missing `before`/`after` context checks                                                    | MEDIUM   |
| Outdated API version (< 55.0)                                                              | LOW      |

Track: trigger name, object, events, score/findings

## Phase 4 — Collect and score Flows (including Process Builders)

Paginate Flow metadata in batches of 200 using an Id cursor, then fetch XML in batches:

1. Fetch `Id`, `DeveloperName`, `MasterLabel`, `ActiveVersionId`, `ProcessType`
   for all active flows via `tooling_api_query` on `FlowDefinition`
2. Separate results by `ProcessType`:
   - **Flow** (`AutoLaunchedFlow`, `Screen`, `RecordTriggeredFlow`, etc.) — score in this phase
   - **Process Builder** (`Workflow`) — inventory in Phase 4b
3. Fetch Flow XML via `metadata_read` in batches — start with 25 flows per call. If the response
   is too large or an error is thrown, halve the batch size and retry.
4. Write each flow XML to `./audit_output/intermediate/flows/<DeveloperName>.flow-meta.xml`
5. Score Flows using the 110-point rubric from the `cirra-ai-sf-flow` skill
6. Track: flow name, process type, score, issues found

### 4b. Process Builders

Process Builders are legacy automation (`ProcessType = 'Workflow'`). Do not score them against
the Flow rubric. Instead, produce an inventory and flag:

| Finding                                                    | Severity |
| ---------------------------------------------------------- | -------- |
| Active Process Builder exists (should be migrated to Flow) | HIGH     |
| Process Builder with > 10 criteria nodes (complexity risk) | MEDIUM   |
| Process Builder invoking Apex actions                      | MEDIUM   |
| Multiple Process Builders on the same object               | HIGH     |

Write inventory to `./audit_output/intermediate/process_builders/inventory.md`.
Track: name, object, criteria node count, actions summary, migration priority

## Phase 5 — Collect and score LWC

Paginate LWC bundle metadata in batches of 200 using an Id cursor:

1. Fetch `Id`, `DeveloperName`, `MasterLabel`, `ApiVersion` for each batch via `tooling_api_query`
   on `LightningComponentBundle`
2. Fetch each component's source files via `metadata_read` (type `LightningComponentBundle`,
   one component at a time)
3. Write each component to `./audit_output/intermediate/lwc/<DeveloperName>/` before scoring
4. Score using the rubric from the `cirra-ai-sf-lwc` skill
5. Track: component name, score, issues found

## Phase 6 — Audit Profiles and Permissions

Use the `cirra-ai-sf-permissions` skill's approach to evaluate the org's
permission model. This phase produces both a complete inventory and a security
findings report.

### 6a. Inventory Profiles

```
soql_query(
  sObject="Profile",
  fields=["Id", "Name", "UserType"]
)
```

For each non-standard Profile, query key permissions:

```
soql_query(
  sObject="PermissionSet",
  fields=["Name", "PermissionsModifyAllData", "PermissionsViewAllData",
          "PermissionsManageUsers", "PermissionsAuthorApex"],
  whereClause="IsOwnedByProfile = true AND Profile.Name = '<ProfileName>'"
)
```

Write to `./audit_output/intermediate/permissions/profiles.md`.
Flag:

- Custom Profiles with ModifyAllData or ViewAllData (should use Permission Sets instead)
- Profiles with overly broad object CRUD (violates least-privilege)
- Profiles assigned to active users vs inactive users

### 6b. Inventory Permission Sets and Groups

```
soql_query(
  sObject="PermissionSet",
  fields=["Id", "Name", "Label", "Description", "IsOwnedByProfile"],
  whereClause="IsOwnedByProfile = false AND NamespacePrefix = null AND Type != 'Group'"
)

soql_query(
  sObject="PermissionSetGroup",
  fields=["Id", "DeveloperName", "MasterLabel", "Status", "Description"]
)

soql_query(
  sObject="PermissionSetGroupComponent",
  fields=["PermissionSetGroupId", "PermissionSetGroup.DeveloperName",
          "PermissionSetId", "PermissionSet.Name"]
)
```

Write the hierarchy to `./audit_output/intermediate/permissions/hierarchy.md`.

### 6c. Detect overly broad permissions

Query for high-risk system permissions per the `cirra-ai-sf-permissions` skill:

```
soql_query(
  sObject="PermissionSet",
  fields=["Name", "Label", "PermissionsModifyAllData", "PermissionsViewAllData",
          "PermissionsManageUsers", "PermissionsAuthorApex"],
  whereClause="IsOwnedByProfile = false AND (PermissionsModifyAllData = true
               OR PermissionsViewAllData = true OR PermissionsManageUsers = true
               OR PermissionsAuthorApex = true)"
)
```

### 6d. Count assignments per Permission Set

```
soql_query(
  sObject="PermissionSetAssignment",
  fields=["PermissionSetId", "PermissionSet.Name"],
  whereClause="PermissionSet.IsOwnedByProfile = false"
)
```

Group by `PermissionSetId` to find:

- Orphaned Permission Sets (0 assignments)
- Overly popular Permission Sets (assigned to >50% of users)

### 6e. Check PSG health

Flag any Permission Set Groups with `Status = 'Outdated'`.

### 6f. Classify findings

For each finding, assign a severity:

| Severity | Examples                                                                                    |
| -------- | ------------------------------------------------------------------------------------------- |
| CRITICAL | Non-admin PS with ModifyAllData; orphaned PS with broad access                              |
| HIGH     | PS with ViewAllData on sensitive objects; outdated PSGs; custom Profiles with ModifyAllData |
| MEDIUM   | Overlapping PS that should be consolidated into PSGs                                        |
| LOW      | Missing descriptions on Permission Sets; unused Profiles                                    |

Track: finding description, severity, affected Profile/PS/PSG

## Phase 7 — Audit Metadata (Data Model & Validation Rules)

Use the `cirra-ai-sf-metadata` skill's 120-point rubric to evaluate custom objects
and fields. Additionally inventory and evaluate validation rules.

### 7a. Inventory custom objects

```
tooling_api_query(
  sObject="CustomObject",
  fields=["Id", "DeveloperName", "Description", "NamespacePrefix"],
  whereClause="NamespacePrefix = null"
)
```

### 7b. For each custom object, describe its structure

```
sobject_describe(sObject="<ObjectApiName>")
```

Write a summary to `./audit_output/intermediate/metadata/<ObjectApiName>.md` with:

- Field count (standard vs custom)
- Relationship count (Lookup vs Master-Detail)
- Validation rule count
- Record type count

### 7c. Score against the 120-point metadata rubric

Evaluate each custom object using the six categories from the `cirra-ai-sf-metadata` skill:

| Category           | Points | What to Check                                                   |
| ------------------ | ------ | --------------------------------------------------------------- |
| Structure & Format | 20     | Valid metadata structure, API version >= 65.0                   |
| Naming Conventions | 20     | PascalCase API names, meaningful labels, `__c` suffix           |
| Data Integrity     | 20     | Required fields have defaults/validation, appropriate precision |
| Security & FLS     | 20     | Sensitive fields flagged, sharing model appropriate             |
| Documentation      | 20     | Descriptions present, help text on user-facing fields           |
| Best Practices     | 20     | Permission Sets over Profiles, no hardcoded IDs                 |

Track: object name, score, issues found

### 7d. Inventory and evaluate Validation Rules

```
tooling_api_query(
  sObject="ValidationRule",
  fields=["Id", "EntityDefinition.QualifiedApiName", "ValidationName",
          "Active", "Description", "ErrorMessage"],
  whereClause="NamespacePrefix = null"
)
```

Write to `./audit_output/intermediate/metadata/validation_rules.md`.
Flag:

| Finding                                                                    | Severity |
| -------------------------------------------------------------------------- | -------- |
| Active validation rule with no description                                 | MEDIUM   |
| Validation rule with no bypass mechanism (`$Permission` or custom setting) | MEDIUM   |
| Validation rule with hardcoded Record IDs in formula                       | HIGH     |
| Inactive validation rules (cleanup candidates)                             | LOW      |
| Object with > 20 active validation rules (complexity risk)                 | MEDIUM   |

Track: rule name, object, active status, findings

### 7e. Cross-object analysis

Beyond per-object scoring, check for org-wide data model issues:

- Objects with no relationships (orphaned objects)
- Missing descriptions on custom objects
- Outdated API versions (< 55.0)
- Objects with > 100 custom fields (complexity risk)
- Validation rules without bypass mechanisms (aggregate from 7d)

## Phase 8 — Inventory Workflow Rules

Workflow Rules are legacy automation. Inventory them and recommend migration.

```
tooling_api_query(
  sObject="WorkflowRule",
  fields=["Id", "Name", "TableEnumOrId"],
  whereClause="NamespacePrefix = null"
)
```

For richer detail, also fetch via metadata:

```
metadata_read(type="WorkflowRule", fullNames=["<ObjectName>.<RuleName>", ...])
```

Write to `./audit_output/intermediate/workflow_rules/inventory.md` with:

- Rule name, object, active status
- Actions summary (field updates, email alerts, outbound messages, tasks)
- Criteria formula (if retrievable)

Flag:

| Finding                                                                                            | Severity |
| -------------------------------------------------------------------------------------------------- | -------- |
| Active Workflow Rule exists (should be migrated to Flow)                                           | HIGH     |
| Workflow Rule with field updates that could conflict with Process Builders or Flows on same object | CRITICAL |
| Workflow Rule with outbound messages (integration dependency — migrate carefully)                  | MEDIUM   |
| Multiple automation types on the same object (Workflow + Flow + Process Builder)                   | CRITICAL |

Track: rule name, object, action types, migration priority

## Phase 9 — Generate reports

Produce three report files in `./audit_output/` (create the directory if needed).
Never scatter files into the working directory root.

### Word report (`Salesforce_Org_Audit_Report.docx`)

- **Executive summary**: org name, date, complete component inventory across all categories
- **Apex classes section**: scores ranked lowest to highest, top issues per class
- **Apex triggers section**: inventory with findings per trigger
- **Flows section**: scores ranked lowest to highest, top issues per flow
- **Process Builders section**: inventory with migration priorities
- **LWC section**: scores ranked lowest to highest, top issues per component
- **Profiles & Permissions section**: profile inventory, PS/PSG hierarchy, findings by severity
- **Data Model section**: object scores ranked lowest to highest, field/relationship summary per object
- **Validation Rules section**: inventory with findings
- **Workflow Rules section**: inventory with migration priorities
- **Automation overlap analysis**: objects with multiple automation types (Workflow + PB + Flow + Trigger)
- **Recommendations**: top 10 highest-impact improvements across all domains

### Excel report (`Salesforce_Org_Audit_Scores.xlsx`)

- Sheet 1 — Apex Classes: columns Name, Score, Category Breakdown, Top Issues
- Sheet 2 — Apex Triggers: columns Name, Object, Events, Findings, Severity
- Sheet 3 — Flows: columns Name, Process Type, Score, Top Issues
- Sheet 4 — Process Builders: columns Name, Object, Criteria Count, Actions, Migration Priority
- Sheet 5 — LWC: columns Name, Score, Category Breakdown, Top Issues
- Sheet 6 — Profiles: columns Name, UserType, Key Permissions, Findings
- Sheet 7 — Permission Sets: columns Name, Label, Assignments, Findings, Severity
- Sheet 8 — Custom Objects: columns Name, Score, Field Count, Relationship Count, Top Issues
- Sheet 9 — Validation Rules: columns Name, Object, Active, Findings, Severity
- Sheet 10 — Workflow Rules: columns Name, Object, Action Types, Migration Priority
- Sheet 11 — Summary: overall health score, component counts per category, finding counts by severity, automation overlap matrix

### HTML report (`Salesforce_Org_Audit_Report.html`)

- Same content as Word, formatted for browser viewing
- Include a score distribution chart if possible
- For each Apex class, link to its source file in `intermediate/apex/<ClassName>.cls`
- For each trigger, link to its source in `intermediate/triggers/<TriggerName>.trigger`
- For each LWC component, link to its directory in `intermediate/lwc/<DeveloperName>/`
- For permissions, include a collapsible hierarchy tree
- For metadata, link to each object summary in `intermediate/metadata/<ObjectApiName>.md`
- Automation overlap matrix: a table showing which objects have which automation types active

## Phase 10 — Summarise

Tell the user:

- **Org inventory**: total counts for every category (Apex classes, triggers, Flows, Process Builders, LWC, custom objects, validation rules, workflow rules, Profiles, Permission Sets, PSGs)
- **Overall org health score**: weighted average across scored domains (Apex, Flows, LWC, Metadata)
- **Components needing attention**: count scoring below 70, broken down by domain
- **Permissions findings**: count by severity (CRITICAL / HIGH / MEDIUM / LOW)
- **Legacy automation**: count of active Workflow Rules and Process Builders that should be migrated
- **Automation overlap warnings**: objects with multiple automation types active
- **Top 3 most common issues per domain**
- **Where report files were saved**

## Routing reference

When the user asks about a specific domain during or after the audit:

| Request                             | Skill                     |
| ----------------------------------- | ------------------------- |
| Fix or review an Apex class/trigger | `cirra-ai-sf-apex`        |
| Fix or review a Flow                | `cirra-ai-sf-flow`        |
| Fix or review an LWC component      | `cirra-ai-sf-lwc`         |
| Fix a permission or Profile issue   | `cirra-ai-sf-permissions` |
| Fix a metadata / data model issue   | `cirra-ai-sf-metadata`    |
| Query or update data                | `cirra-ai-sf-data`        |
| Visualize architecture or hierarchy | `cirra-ai-sf-diagram`     |

## Build order (when fixing issues)

If the audit reveals work to be done, recommend this deployment order:

1. **Metadata** — fix data model issues first (objects, fields, validation rules)
2. **Permissions** — update Profiles, Permission Sets, and PSGs after metadata is corrected
3. **Apex + Flows + LWC** — deploy in parallel if independent; Apex before Flows/LWC if they invoke Apex
4. **Legacy migration** — migrate Workflow Rules and Process Builders to Flows
5. **Data** — load test data and verify with SOQL after code is deployed

---

## Dependencies

### Cirra AI MCP Server tools

#### Required

- cirra_ai_init
- tooling_api_query
- metadata_read
- soql_query
- sobject_describe

#### Optional

- metadata_create
- metadata_update
