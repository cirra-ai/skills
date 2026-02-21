---
name: audit-runner
description: >
  Runs a full Salesforce org audit across Apex and Flows. Uses the cirra-ai-sf-apex
  and cirra-ai-sf-flow skills for scoring. Generates Word, Excel, and HTML reports.
skills:
  - cirra-ai-sf-apex
  - cirra-ai-sf-flow
---

Run a complete Salesforce org audit. Follow these phases in order.

## Prerequisites

Call `cirra_ai_init()` first if not already done this session.

## Phase 1 — Count components

Query how many Apex classes and active Flows exist so the user knows the scope:

```
tooling_api_query: ApexClass WHERE NamespacePrefix = null → COUNT
tooling_api_query: FlowDefinition WHERE ActiveVersionId != null AND NamespacePrefix = null → COUNT
```

Tell the user: "Found X Apex classes and Y active Flows. Starting audit..."

## Phase 2 — Collect and score Apex

For each Apex class (paginate in batches of 200 using Id cursor):

1. Fetch `Id`, `Name`, `LengthWithoutComments`, `ApiVersion` via `tooling_api_query`
2. Fetch `Body` for each class individually (one at a time to avoid size limits)
3. Score using the 150-point rubric from the `cirra-ai-sf-apex` skill (preloaded in your context)
4. Track: class name, score, issues found

## Phase 3 — Collect and score Flows

For each active Flow (paginate using Id cursor):

1. Fetch `Id`, `DeveloperName`, `MasterLabel`, `ActiveVersionId` via `tooling_api_query`
2. Fetch Flow XML via `metadata_read` (one at a time)
3. Score using the 110-point rubric from the `cirra-ai-sf-flow` skill (preloaded in your context)
4. Track: flow name, score, issues found

## Phase 4 — Generate reports

Produce three report files in `./audit_output/` (create the directory if needed).
Never scatter files into the working directory root.

### Word report (`Salesforce_Org_Audit_Report.docx`)

- Executive summary: org name, date, total components audited
- Apex section: scores ranked lowest to highest, top issues per class
- Flow section: same structure
- Recommendations: top 5 highest-impact improvements

### Excel report (`Salesforce_Org_Audit_Scores.xlsx`)

- Sheet 1 — Apex: columns Name, Score, Category Breakdown, Top Issues
- Sheet 2 — Flows: same structure
- Sheet 3 — Summary: overall health score, component counts

### HTML report (`Salesforce_Org_Audit_Report.html`)

- Same content as Word, formatted for browser viewing
- Include a score distribution chart if possible

## Phase 5 — Summarise

Tell the user:

- Overall org health score (average across all components)
- Number of components scoring below 70 (needs attention)
- Top 3 most common issues
- Where report files were saved

## Routing reference

When the user asks about a specific domain during or after the audit:

| Request                     | Skill                  |
| --------------------------- | ---------------------- |
| Fix or review an Apex class | `cirra-ai-sf-apex`     |
| Fix or review a Flow        | `cirra-ai-sf-flow`     |
| Query or update data        | `cirra-ai-sf-data`     |
| Create objects or fields    | `cirra-ai-sf-metadata` |

## Build order (when fixing issues)

If the audit reveals work to be done, recommend this deployment order:

1. **Metadata** — create/update custom objects and fields first
2. **Apex + Flows** — deploy in parallel if independent; Apex before Flows if Flows invoke Apex
3. **Data** — load test data and verify with SOQL after code is deployed
