---
name: cirra-ai-sf-audit
description: >
  Run a full Salesforce org audit across Apex, Flows, and LWC. Scores all
  components against quality rubrics and generates Word, Excel, and HTML reports.
  Use when asked to audit a Salesforce org, review org health, score org quality,
  run an org health check, or audit apex flows and lwc.
---

# cirra-ai-sf-audit: Salesforce Org Audit

Run a complete Salesforce org audit. Follow these phases in order.

**Scoring**: Use the rubrics from the `cirra-ai-sf-apex`, `cirra-ai-sf-flow`, and
`cirra-ai-sf-lwc` skills, which should be loaded in your context alongside this skill.
Do not invent your own criteria.

## Prerequisites

Call `cirra_ai_init()` first if not already done this session.

<!-- AUTO-GENERATED FROM shared/audit-phases.md — DO NOT EDIT BELOW THIS LINE -->
## Phase 1 — Count components

Query how many components exist so the user knows the scope:

```
tooling_api_query: ApexClass WHERE NamespacePrefix = null → COUNT
tooling_api_query: FlowDefinition WHERE ActiveVersionId != null AND NamespacePrefix = null → COUNT
tooling_api_query: LightningComponentBundle WHERE NamespacePrefix = null → COUNT
```

Tell the user: "Found X Apex classes, Y active Flows, and Z LWC components. Starting audit..."

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

## Phase 5 — Generate reports

Produce three report files in `./audit_output/` (create the directory if needed).
Never scatter files into the working directory root.

### Word report (`Salesforce_Org_Audit_Report.docx`)

- Executive summary: org name, date, total components audited
- Apex section: scores ranked lowest to highest, top issues per class
- Flow section: same structure
- LWC section: same structure
- Recommendations: top 5 highest-impact improvements across all domains

### Excel report (`Salesforce_Org_Audit_Scores.xlsx`)

- Sheet 1 — Apex: columns Name, Score, Category Breakdown, Top Issues
- Sheet 2 — Flows: same structure
- Sheet 3 — LWC: same structure
- Sheet 4 — Summary: overall health score, component counts per domain

### HTML report (`Salesforce_Org_Audit_Report.html`)

- Same content as Word, formatted for browser viewing
- Include a score distribution chart if possible
- For each Apex class, link to its source file in `intermediate/apex/<ClassName>.cls`
- For each LWC component, link to its directory in `intermediate/lwc/<DeveloperName>/`

## Phase 6 — Summarise

Tell the user:

- Overall org health score (average across all components and domains)
- Number of components scoring below 70 (needs attention), broken down by domain
- Top 3 most common issues per domain
- Where report files were saved

## Routing reference

When the user asks about a specific domain during or after the audit:

| Request                        | Skill              |
| ------------------------------ | ------------------ |
| Fix or review an Apex class    | `cirra-ai-sf-apex` |
| Fix or review a Flow           | `cirra-ai-sf-flow` |
| Fix or review an LWC component | `cirra-ai-sf-lwc`  |
| Query or update data           | `cirra-ai-sf-data` |

## Build order (when fixing issues)

If the audit reveals work to be done, recommend this deployment order:

1. **Apex + Flows + LWC** — deploy in parallel if independent; Apex before Flows/LWC if they invoke Apex
2. **Data** — load test data and verify with SOQL after code is deployed

---

## Dependencies

### Cirra AI MCP Server tools

#### Required

- cirra_ai_init
- tooling_api_query
- metadata_read

#### Optional

- soql_query
- sobject_describe
