---
name: cirra-ai-sf-audit
description: >
  Salesforce audit suite — orchestrates Apex, Flow, and Data plugins
  with Cirra AI MCP Server for org-wide audits. Use when the user needs
  to run a Salesforce org audit spanning code, flows, data, and reports.
license: MIT
metadata:
  version: '2.0.0'
  author: 'Cirra AI'
mcpTools:
  required:
    - cirra_ai_init
---

# cirra-ai-sf-audit: Salesforce Audit Suite

Orchestrates three independent Salesforce plugins into a unified development workflow. Each plugin works standalone; this meta-skill coordinates them when all three are active.

## CRITICAL: Dependency Check on Session Start

When this skill is loaded, you MUST check whether the sub-plugins listed below are also installed and available. Check by looking for their SKILL.md files or skill names in the current session.

If any sub-plugin is **missing**, warn the user immediately:

> "cirra-ai-sf-audit is an orchestration layer for three sub-plugins. I can see that **[missing plugin(s)]** is not installed. This means I won't have access to [what it provides]. You can install it with `claude /plugin install github:cirra-ai/skills/[plugin-name]`, or I can proceed on a best-effort basis without it."

Then proceed with whatever plugins ARE available. Do not silently fall back to generic knowledge — the user should know what they're missing so they can make an informed choice.

If plugins **are** available you MUST use them! Don't make up your own methodology

## Sub-Plugins

| Plugin | Domain | Scoring |
|---|---|---|
| **cirra-ai-sf-apex** | Apex classes, triggers, tests, batch jobs | 150 points / 8 categories |
| **cirra-ai-sf-flow** | Record-triggered, screen, autolaunched, scheduled flows | 110 points / 6 categories |
| **cirra-ai-sf-data** | SOQL queries, DML operations, test data factories | Pass/fail pre-flight checks |

Each plugin includes its own MCP deployment validator — no cross-plugin dependencies.

## Routing Rules

When a user request arrives, route to the appropriate plugin:

| Request Type | Route To | Examples |
|---|---|---|
| Write/review Apex code | cirra-ai-sf-apex | "Create a trigger handler", "Review this Apex class" |
| Create/validate a Flow | cirra-ai-sf-flow | "Build a record-triggered flow", "Score this flow XML" |
| Query/insert/update data | cirra-ai-sf-data | "Query all Accounts", "Create 200 test records" |
| Mixed (code + data) | Both | "Deploy the trigger and create test data" |

## Orchestration Order

When building a complete feature:

```
1. cirra-ai-sf-metadata  →  Create custom objects/fields (if needed)
2. cirra-ai-sf-apex      →  Deploy Apex classes/triggers
   cirra-ai-sf-flow      →  Deploy Flows (parallel with Apex if independent)
3. cirra-ai-sf-data      →  Create test data, verify with SOQL
```

Objects and fields must exist before code that references them can be deployed.

## Validation Flow

Each plugin validates its own domain independently:

- **cirra-ai-sf-data**: Pre-flight checks on `soql_query` / `sobject_dml` params (missing sObject, PII detection, syntax errors) — pass/fail
- **cirra-ai-sf-apex**: 150-point scoring on `metadata_create` / `metadata_update` for ApexClass/ApexTrigger — delegates to ApexValidator
- **cirra-ai-sf-flow**: 110-point scoring on `metadata_create` / `metadata_update` for Flow/FlowDefinition — delegates to EnhancedFlowValidator

No plugin needs to import from another plugin's codebase.

## Prerequisites

**CRITICAL**: Call `cirra_ai_init()` once per session before using any Cirra AI MCP tools.

```python
cirra_ai_init(sf_user="your-username")
```

## Org Audit Orchestration

The suite includes a full org audit workflow via `hooks/scripts/audit_runner.py`. This coordinates the collection, scoring, and reporting phases across all sub-plugins.

### Audit Routing

| Request Type | Route To | Script |
|---|---|---|
| Full org audit | cirra-ai-sf-audit (orchestrator) | `audit_runner.py` |
| Score all Apex classes | cirra-ai-sf-apex | `score_apex_classes.py` |
| Score all Flows | cirra-ai-sf-flow | `score_flows.py` |
| Audit + report generation | cirra-ai-sf-audit (orchestrator) | `audit_runner.py` |

### Output-Directory-First Architecture

**ALL intermediate and output files MUST be written to the `--output-dir` directory.** This is the default and non-negotiable practice:

```
{output_dir}/
├── intermediate/          # Batch data, progress checkpoints, raw scores
│   ├── apex_batch_*.json
│   ├── flow_batch_*.json
│   ├── apex_scoring_progress.json
│   └── flow_scoring_progress.json
├── scripts/               # Audit scripts (copied here for portability)
│   ├── audit_runner.py
│   ├── score_apex_classes.py
│   └── score_flows.py
├── Salesforce_Org_Audit_Report.docx
├── Salesforce_Org_Audit_Scores.xlsx
└── Salesforce_Org_Audit_Report.html
```

### Running an Audit

```bash
# Initialize
python3 audit_runner.py --output-dir ./audit_output --generate-queries

# Check progress
python3 audit_runner.py --output-dir ./audit_output --status

# Reset
python3 audit_runner.py --output-dir ./audit_output --reset
```

### Audit Phases

| Phase | Description | Script |
|---|---|---|
| 0 | Plugin Discovery | orchestrator |
| 1 | Initialize Cirra AI | `cirra_ai_init()` |
| 2 | Count Components | `tooling_api_query` |
| 3 | Collect Apex Data | `tooling_api_query` (paginated) |
| 4 | Collect Flow Data | `tooling_api_query` + `metadata_read` |
| 5 | Score Apex Classes | `score_apex_classes.py` (150-pt rubric) |
| 6 | Score Flows | `score_flows.py` (110-pt rubric) |
| 7-9 | Generate Reports | Word, Excel, HTML |
| 10 | Validate Reports | File existence + content checks |

## Related Skills

These plugins complement the core three but are independent:

| Skill | Purpose |
|---|---|
| cirra-ai-sf-metadata | Custom objects, fields, Permission Sets |
| cirra-ai-sf-lwc | Lightning Web Components |
| cirra-ai-sf-soql | Advanced SOQL optimization |
| cirra-ai-sf-ai-agentscript | Agentforce agent authoring |
