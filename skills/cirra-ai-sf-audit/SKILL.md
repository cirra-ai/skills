---
name: cirra-ai-sf-audit
description: >
  Run a full Salesforce org audit across Apex, Flows, LWC, Permissions, and
  Metadata. Scores all components against quality rubrics and generates Word,
  Excel, and HTML reports. Use when asked to audit a Salesforce org, review org
  health, score org quality, run an org health check, audit permissions,
  review the data model, or audit apex flows and lwc.
metadata:
  version: 1.1.0
---

# cirra-ai-sf-audit: Salesforce Org Audit

Run a complete Salesforce org audit. Follow these phases in order.

**Scoring**: Use the rubrics from the `cirra-ai-sf-apex`, `cirra-ai-sf-flow`,
`cirra-ai-sf-lwc`, `cirra-ai-sf-permissions`, and `cirra-ai-sf-metadata` skills,
which should be loaded in your context alongside this skill.
Do not invent your own criteria.

## Prerequisites

Call `cirra_ai_init()` first if not already done this session.

## Phase 1 — Count components

Query how many components exist so the user knows the scope:

```
tooling_api_query: ApexClass WHERE NamespacePrefix = null → COUNT
tooling_api_query: FlowDefinition WHERE ActiveVersionId != null AND NamespacePrefix = null → COUNT
tooling_api_query: LightningComponentBundle WHERE NamespacePrefix = null → COUNT
soql_query: PermissionSet WHERE IsOwnedByProfile = false AND NamespacePrefix = null → COUNT
soql_query: PermissionSetGroup → COUNT
tooling_api_query: CustomObject WHERE NamespacePrefix = null → COUNT
```

Tell the user: "Found X Apex classes, Y active Flows, Z LWC components, N Permission Sets, M Permission Set Groups, and P custom objects. Starting audit..."

## Phase 2 — Collect and score Apex

Paginate Apex class metadata in batches of 200 using an Id cursor:

1. Fetch `Id`, `Name`, `LengthWithoutComments`, `ApiVersion` for each batch via `tooling_api_query`
2. Fetch `Body` for each class individually (one at a time to avoid size limits)
3. Write each class body to `./audit_output/intermediate/apex/<ClassName>.cls` before scoring
4. Score using the 150-point rubric from the `cirra-ai-sf-apex` skill
5. Track: class name, score, issues found

## Phase 3 — Collect and score Flows

Paginate Flow metadata in batches of 200 using an Id cursor, then fetch XML in batches:

1. Fetch `Id`, `DeveloperName`, `MasterLabel`, `ActiveVersionId` for all flows via `tooling_api_query`
2. Fetch Flow XML via `metadata_read` in batches — start with 25 flows per call. If the response
   is too large or an error is thrown, halve the batch size and retry.
3. Write each flow XML to `./audit_output/intermediate/flows/<DeveloperName>.flow-meta.xml`
4. Score using the 110-point rubric from the `cirra-ai-sf-flow` skill
5. Track: flow name, score, issues found

## Phase 4 — Collect and score LWC

Paginate LWC bundle metadata in batches of 200 using an Id cursor:

1. Fetch `Id`, `DeveloperName`, `MasterLabel`, `ApiVersion` for each batch via `tooling_api_query`
   on `LightningComponentBundle`
2. Fetch each component's source files via `metadata_read` (type `LightningComponentBundle`,
   one component at a time)
3. Write each component to `./audit_output/intermediate/lwc/<DeveloperName>/` before scoring
4. Score using the rubric from the `cirra-ai-sf-lwc` skill
5. Track: component name, score, issues found

## Phase 5 — Audit Permissions

Use the `cirra-ai-sf-permissions` skill's security audit approach to evaluate the org's
permission model. This phase does not score individual Permission Sets on a numeric rubric;
instead it produces a security findings report.

### 5a. Inventory Permission Sets and Groups

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

### 5b. Detect overly broad permissions

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

### 5c. Count assignments per Permission Set

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

### 5d. Check PSG health

Flag any Permission Set Groups with `Status = 'Outdated'`.

### 5e. Classify findings

For each finding, assign a severity:

| Severity | Examples                                                       |
| -------- | -------------------------------------------------------------- |
| CRITICAL | Non-admin PS with ModifyAllData; orphaned PS with broad access |
| HIGH     | PS with ViewAllData on sensitive objects; outdated PSGs        |
| MEDIUM   | Overlapping PS that should be consolidated into PSGs           |
| LOW      | Missing descriptions on Permission Sets                        |

Track: finding description, severity, affected Permission Set(s)

## Phase 6 — Audit Metadata (Data Model)

Use the `cirra-ai-sf-metadata` skill's 120-point rubric to evaluate custom objects
and fields.

### 6a. Inventory custom objects

```
tooling_api_query(
  sObject="CustomObject",
  fields=["Id", "DeveloperName", "Description", "NamespacePrefix"],
  whereClause="NamespacePrefix = null"
)
```

### 6b. For each custom object, describe its structure

```
sobject_describe(sObject="<ObjectApiName>")
```

Write a summary to `./audit_output/intermediate/metadata/<ObjectApiName>.md` with:

- Field count (standard vs custom)
- Relationship count (Lookup vs Master-Detail)
- Validation rule count
- Record type count

### 6c. Score against the 120-point metadata rubric

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

### 6d. Cross-object analysis

Beyond per-object scoring, check for org-wide data model issues:

- Objects with no relationships (orphaned objects)
- Missing descriptions on custom objects
- Outdated API versions (< 55.0)
- Objects with > 100 custom fields (complexity risk)
- Validation rules without bypass mechanisms

## Phase 7 — Generate reports

Produce three report files in `./audit_output/` (create the directory if needed).
Never scatter files into the working directory root.

### Word report (`Salesforce_Org_Audit_Report.docx`)

- Executive summary: org name, date, total components audited across all domains
- Apex section: scores ranked lowest to highest, top issues per class
- Flow section: same structure
- LWC section: same structure
- Permissions section: findings ranked by severity, hierarchy overview, orphaned PS list
- Metadata section: object scores ranked lowest to highest, cross-object findings
- Recommendations: top 5 highest-impact improvements across all domains

### Excel report (`Salesforce_Org_Audit_Scores.xlsx`)

- Sheet 1 — Apex: columns Name, Score, Category Breakdown, Top Issues
- Sheet 2 — Flows: same structure
- Sheet 3 — LWC: same structure
- Sheet 4 — Permissions: columns Finding, Severity, Affected PS/PSG, Recommendation
- Sheet 5 — Metadata: columns Object Name, Score, Category Breakdown, Top Issues
- Sheet 6 — Summary: overall health score, component counts per domain, finding counts by severity

### HTML report (`Salesforce_Org_Audit_Report.html`)

- Same content as Word, formatted for browser viewing
- Include a score distribution chart if possible
- For each Apex class, link to its source file in `intermediate/apex/<ClassName>.cls`
- For each LWC component, link to its directory in `intermediate/lwc/<DeveloperName>/`
- For permissions, include a collapsible hierarchy tree
- For metadata, link to each object summary in `intermediate/metadata/<ObjectApiName>.md`

## Phase 8 — Summarise

Tell the user:

- Overall org health score (weighted average across scored domains: Apex, Flows, LWC, Metadata)
- Number of components scoring below 70 (needs attention), broken down by domain
- Permissions finding count by severity (CRITICAL / HIGH / MEDIUM / LOW)
- Top 3 most common issues per domain
- Where report files were saved

## Routing reference

When the user asks about a specific domain during or after the audit:

| Request                             | Skill                     |
| ----------------------------------- | ------------------------- |
| Fix or review an Apex class         | `cirra-ai-sf-apex`        |
| Fix or review a Flow                | `cirra-ai-sf-flow`        |
| Fix or review an LWC component      | `cirra-ai-sf-lwc`         |
| Fix a permission issue              | `cirra-ai-sf-permissions` |
| Fix a metadata / data model issue   | `cirra-ai-sf-metadata`    |
| Query or update data                | `cirra-ai-sf-data`        |
| Visualize architecture or hierarchy | `cirra-ai-sf-diagram`     |

## Build order (when fixing issues)

If the audit reveals work to be done, recommend this deployment order:

1. **Metadata** — fix data model issues first (objects, fields, validation rules)
2. **Permissions** — update Permission Sets / PSGs after metadata is corrected
3. **Apex + Flows + LWC** — deploy in parallel if independent; Apex before Flows/LWC if they invoke Apex
4. **Data** — load test data and verify with SOQL after code is deployed

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
