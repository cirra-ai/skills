---
name: cirra-ai-sf-audit
description: >
  Run a full Salesforce org audit across Apex, Flows, LWC, Permissions, and
  Metadata. Scores all components against quality rubrics and generates Word,
  Excel, and HTML reports. Use when asked to audit a Salesforce org, review org
  health, score org quality, run an org health check, audit permissions,
  review the data model, or audit apex flows and lwc.
metadata:
  version: 1.2.0
---


# cirra-ai-sf-audit: Salesforce Org Audit

Run a complete Salesforce org audit. Follow these phases in order.

**Scoring**: Use the rubrics from the `cirra-ai-sf-apex`, `cirra-ai-sf-flow`,
`cirra-ai-sf-lwc`, `cirra-ai-sf-permissions`, and `cirra-ai-sf-metadata` skills,
which should be loaded in your context alongside this skill.
Do not invent your own criteria.

## Prerequisites

Call `cirra_ai_init()` first if not already done this session.

## Execution mode (critical)

Choose execution mode up front:

### Local mode (CLI-first, recommended when `sf` is available)

Use MCP for initialization and targeted checks, but do bulk extraction with Salesforce CLI
and write outputs to disk directly.

- Keep using `cirra_ai_init()` to confirm org context.
- Confirm local auth with `sf org list --json`.
- Use `--target-org <alias-or-username>` consistently.
- Prefer file outputs in `./audit_output/*.json` for large datasets.

### Cloud mode (MCP-only, no local CLI/browser)

Run entirely with MCP tools and enforce strict pagination/chunking.

- Always query in batches with `orderBy="Id"` and `Id > '<lastId>'`.
- For large results, reduce `limit` and iterate until complete.
- Persist each batch to `./audit_output/intermediate/` as you go.
- Explicitly report any unavoidable MCP/tooling limits in final summary.

## Known MCP limitations and required workarounds

1. `soql_query` / `tooling_api_query` may truncate large responses in chat context.
   Workaround: cursor pagination (`Id` ordering + `Id > lastId`) with small limits.
2. Tooling query of `Flow` including `Metadata`/`FullName` is effectively single-row.
   Workaround: query active Flow IDs first, then fetch one Flow row per `Id`.
3. Large relationship-heavy queries (PermissionSet/PSG datasets) may exceed response limits.
   Workaround: split queries by `Id` cursor windows and materialize per-batch files.
4. Some object filters differ across APIs (SOQL vs Tooling).
   Workaround: validate fields/operators first; fallback to broader query + local filtering.

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

### Local mode optimization

You may run the same count queries via CLI for speed:

```bash
sf data query --use-tooling-api --query "SELECT COUNT(Id) total FROM ApexClass WHERE NamespacePrefix = null" --target-org <org>
sf data query --use-tooling-api --query "SELECT COUNT(Id) total FROM FlowDefinition WHERE ActiveVersionId != null AND NamespacePrefix = null" --target-org <org>
...
```

## Phase 2 — Collect and score Apex

Paginate Apex class metadata in batches using an Id cursor:

1. Fetch `Id`, `Name`, `LengthWithoutComments`, `ApiVersion` for each batch
2. Fetch `Body` for each class (batch if local CLI, one-at-a-time if MCP constrained)
3. Write each class body to `./audit_output/intermediate/apex/<ClassName>.cls` before scoring
4. Score using the 150-point rubric from the `cirra-ai-sf-apex` skill
5. Track: class name, score, issues found

### Local mode (CLI-first)

Prefer one bulk export:

```bash
sf data query --use-tooling-api --query \
"SELECT Id, Name, LengthWithoutComments, ApiVersion, Body FROM ApexClass WHERE NamespacePrefix = null ORDER BY Id" \
--target-org <org> --json > audit_output/apex_classes.json
```

### Cloud mode (MCP-only)

- Query metadata in pages (`limit` 100-200).
- If body payload is too large, fetch `Body` per class id.
- Persist each page to `audit_output/intermediate/apex_batches/`.

## Phase 3 — Collect and score Flows

Paginate flow definitions, then fetch active flow metadata safely:

1. Fetch `Id`, `DeveloperName`, `MasterLabel`, `ActiveVersionId` for all active flows.
2. Fetch flow metadata using one of:
   - Local: Tooling API query per `ActiveVersionId` to file, parallelized.
   - Cloud: per-flow MCP retrieval (single row per Flow Id when `Metadata` is requested).
3. Write each flow XML to `./audit_output/intermediate/flows/<DeveloperName>.flow-meta.xml`
4. Score using the 110-point rubric from the `cirra-ai-sf-flow` skill
5. Track: flow name, score, issues found

### Local mode (CLI-first)

Do not run one giant query with `Flow.Metadata` for all rows. Instead:

1. Export flow definitions (with active version IDs).
2. Iterate active IDs and query one Flow row per ID; store each in `audit_output/flow_json/<Id>.json`.
3. Parallelize in controlled batches (e.g., 6-12 workers).

### Cloud mode (MCP-only)

Mandatory workaround for metadata-field restriction:

- `tooling_api_query` FlowDefinition list first.
- For each `ActiveVersionId`, fetch exactly one flow record with metadata.
- Retry transient failures with smaller concurrency and backoff.

## Phase 4 — Collect and score LWC

Paginate LWC bundle metadata using an Id cursor:

1. Fetch `Id`, `DeveloperName`, `MasterLabel`, `ApiVersion` for each batch via `tooling_api_query`
   on `LightningComponentBundle`
2. Fetch each component's source files:
   - Local: bulk export `LightningComponentResource` then group by bundle id
   - Cloud: `metadata_read` per bundle (or paged tooling query on resources)
3. Write each component to `./audit_output/intermediate/lwc/<DeveloperName>/` before scoring
4. Score using the rubric from the `cirra-ai-sf-lwc` skill
5. Track: component name, score, issues found

### Local mode (CLI-first)

```bash
sf data query --use-tooling-api --query \
"SELECT Id, DeveloperName, MasterLabel, ApiVersion FROM LightningComponentBundle WHERE NamespacePrefix = null ORDER BY Id" \
--target-org <org> --json > audit_output/lwc_bundles.json

sf data query --use-tooling-api --query \
"SELECT Id, LightningComponentBundleId, FilePath, Source FROM LightningComponentResource WHERE LightningComponentBundle.NamespacePrefix = null ORDER BY Id" \
--target-org <org> --json > audit_output/lwc_resources.json
```

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

### Local mode (CLI-first)

Prefer CLI file exports for PermissionSet / PSG / PSG component / assignment datasets because
MCP responses are frequently truncated for these objects in large orgs.

### Cloud mode (MCP-only)

- Always paginate with `Id` cursor.
- Avoid requesting extra columns not needed for scoring.
- Persist each batch locally and merge after retrieval.

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

Also query active user count:

```soql
SELECT COUNT(Id) total FROM User WHERE IsActive = true
```

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

If tooling columns differ in a target org/API version, fallback order:

1. `tooling_api_query(CustomObject)` with minimal known-safe fields
2. `sobjects_list(customObjectsOnly=true)` to get API names
3. `sobject_describe` per object for detail

### 6b. For each custom object, describe its structure

```
sobject_describe(sObject="<ObjectApiName>")
```

Write a summary to `./audit_output/intermediate/metadata/<ObjectApiName>.md` with:

- Field count (standard vs custom)
- Relationship count (Lookup vs Master-Detail)
- Validation rule count
- Record type count

### Local mode (CLI-first)

To improve completeness and speed, supplement with:

- Tooling query on `CustomField` (group by `TableEnumOrId`)
- Tooling query on `ValidationRule`
- SOQL query on `RecordType`

Then enrich per-object summaries using these datasets.

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

DOCX formatting requirement:

- If direct HTML conversion is unreadable, regenerate DOCX with fixed-width bordered tables
  and landscape layout (see `docx-report-formatting` skill).

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

### Local execution tools (when available)

- Salesforce CLI (`sf`)
- `jq` (recommended for post-processing JSON exports)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc.
The skill and its contents are provided independently and are not part of the Cirra AI product itself.
Use of Cirra AI is subject to its own separate terms and conditions.
For credits and attribution see [CREDITS.md](CREDITS.md).
