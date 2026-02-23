# Cirra AI Salesforce Skills — Integration Test Plan

## Overview

This test plan exercises **all 4 skills** and **all 13 commands** in the `cirra-ai-sf`
plugin end-to-end against a live Salesforce org via the Cirra AI MCP Server.

The plan is divided into phases that must run in order:

| Phase          | Script                     | Purpose                                                                  |
| -------------- | -------------------------- | ------------------------------------------------------------------------ |
| 0 — Smoke      | `00_smoke_test.md`         | 2-minute gate: verify MCP, data path, and metadata path are functional   |
| 1a — Data      | `01a_setup_data.md`        | Insert all test data records (runs even if metadata path failed)         |
| 1b — Metadata  | `01b_setup_metadata.md`    | Create Apex, Flows, and LWC (gated on Phase 0 TC-003 passing)            |
| 2 — Validate   | `02_validate_artifacts.md` | Run every `/validate-*` command and `/query-data` to confirm correctness |
| 3 — Update     | `03_update_artifacts.md`   | Modify every artifact type and re-validate                               |
| 4 — Audit      | `04_audit_and_report.md`   | Run `/audit-org`, generate reports, check completeness                   |

A cleanup script (`99_cleanup.md`) tears down all test artifacts.

> **Smoke test gate:** If TC-003 (metadata path) fails, skip Phase 1b entirely and
> mark all metadata tests in Phases 2, 3, and 4 as BLOCKED. Data tests (1a, 2 data
> section, 3 data section) can still proceed.

See `BUG_INVESTIGATION_GUIDE.md` when a test produces an unexpected failure.
Use `REPORT_TEMPLATE.md` to record results.

---

## Scope Matrix

### Skills Covered

| Skill            | Create           | Validate           | Update                  | Audit   |
| ---------------- | ---------------- | ------------------ | ----------------------- | ------- |
| cirra-ai-sf-data | Phase 1 (insert) | Phase 2 (query)    | Phase 3 (update/upsert) | Phase 4 |
| cirra-ai-sf-apex | Phase 1 (create) | Phase 2 (validate) | Phase 3 (update)        | Phase 4 |
| cirra-ai-sf-flow | Phase 1 (create) | Phase 2 (validate) | Phase 3 (update)        | Phase 4 |
| cirra-ai-sf-lwc  | Phase 1 (create) | Phase 2 (validate) | Phase 3 (update)        | Phase 4 |

### Commands Covered

| Command          | Phase(s) | Test Coverage                                                                  |
| ---------------- | -------- | ------------------------------------------------------------------------------ |
| `/insert-data`   | 1, 3     | Single insert, bulk 201+, hierarchy, CSV-style, upsert                         |
| `/query-data`    | 2, 3     | Parent-child, child-parent, aggregate, polymorphic, semi/anti-join             |
| `/validate-data` | 2        | Pre-flight on insert JSON, SOQL syntax, PII detection                          |
| `/create-apex`   | 1        | Trigger+TAF action, Service, Selector, Batch, Queueable, Invocable, Test class |
| `/validate-apex` | 2        | Single class, comma-list, `--all`                                              |
| `/update-apex`   | 3        | Add method to service, modify trigger action logic                             |
| `/create-flow`   | 1        | Before-save RT, After-save RT, Screen, Autolaunched, Scheduled, Platform Event |
| `/validate-flow` | 2        | Single flow, comma-list, `--all`                                               |
| `/update-flow`   | 3        | Add decision branch, add error handling, add screen                            |
| `/create-lwc`    | 1        | Wire-based datatable, Form component, Flow screen, Modal, GraphQL              |
| `/validate-lwc`  | 2        | Single component, comma-list, `--all`                                          |
| `/update-lwc`    | 3        | Add dark mode CSS, add column, fix accessibility                               |
| `/audit-org`     | 4        | Full org audit with Word/Excel/HTML report generation                          |

### MCP Tools Exercised

| Tool                | Operations Tested                                                         |
| ------------------- | ------------------------------------------------------------------------- |
| `cirra_ai_init`     | Session initialization (Phase 1 start)                                    |
| `soql_query`        | SELECT, WHERE, ORDER BY, LIMIT, relationships, aggregates, subqueries     |
| `sobject_dml`       | insert, update, delete, upsert — single and bulk (201+)                   |
| `sobject_describe`  | Standard objects (Account, Contact, Opportunity, Case, Lead, Task, Event) |
| `tooling_api_query` | ApexClass, ApexTrigger, FlowDefinition, LightningComponentBundle          |
| `tooling_api_dml`   | Create/update ApexClass, ApexTrigger                                      |
| `metadata_create`   | Flow, LightningComponentBundle                                            |
| `metadata_update`   | Flow, LightningComponentBundle                                            |
| `metadata_read`     | Flow XML, LWC bundles                                                     |
| `metadata_list`     | Flow, LightningComponentBundle                                            |
| `metadata_delete`   | Flow, LightningComponentBundle (cleanup)                                  |

### Validation Scripts Exercised

| Script                                      | Skill            | Scoring                         |
| ------------------------------------------- | ---------------- | ------------------------------- |
| `validate_apex.py` / `validate_apex_cli.py` | Apex             | 150-point (8 categories)        |
| `validate_flow.py` / `validate_flow_cli.py` | Flow             | 110-point (6 categories)        |
| `validate_slds.py`                          | LWC              | 165-point (8 categories)        |
| `mcp_validator.py` / `mcp_validator_cli.py` | Data, Apex, Flow | Pre-flight Tier 1 + Tier 2      |
| `soql_validator.py`                         | Data             | SOQL syntax validation          |
| `llm_pattern_validator.py`                  | Apex             | LLM anti-pattern detection      |
| `template_validator.py`                     | LWC              | Template anti-pattern detection |
| `simulate_flow.py`                          | Flow             | Flow simulation                 |

---

## Test Data Naming Convention

All test artifacts use the prefix `CirraTest_` for easy identification and cleanup.

| Type           | Naming Pattern          | Examples                      |
| -------------- | ----------------------- | ----------------------------- |
| Accounts       | `CirraTest_Account_NNN` | CirraTest_Account_001         |
| Contacts       | `CirraTest_Contact_NNN` | CirraTest_Contact_001         |
| Opportunities  | `CirraTest_Opp_NNN`     | CirraTest_Opp_001             |
| Cases          | `CirraTest_Case_NNN`    | CirraTest_Case_001            |
| Leads          | `CirraTest_Lead_NNN`    | CirraTest_Lead_001            |
| Tasks          | `CirraTest_Task_NNN`    | CirraTest_Task_001            |
| Events         | `CirraTest_Event_NNN`   | CirraTest_Event_001           |
| Apex Classes   | `CirraTest_*`           | CirraTest_AccountService      |
| Apex Triggers  | `CirraTest_*Trigger`    | CirraTest_AccountTrigger      |
| Flows          | `CirraTest_*`           | CirraTest_Account_Before_Save |
| LWC Components | `cirraTest*`            | cirraTestAccountDashboard     |

---

## Prerequisites

- Salesforce org accessible via Cirra AI MCP Server
- `cirra_ai_init()` completes successfully
- Trigger Actions Framework (TAF) installed in org (for trigger tests)
- Standard objects available: Account, Contact, Opportunity, Case, Lead, Task, Event
- User has Modify All Data + Customize Application permissions

---

## Success Criteria

| Metric                                              | Target                       |
| --------------------------------------------------- | ---------------------------- |
| All artifacts created without error                 | 100%                         |
| Apex validation scores                              | >= 90/150 on all classes     |
| Flow validation scores                              | >= 88/110 on all flows       |
| LWC validation scores                               | >= 100/165 on all components |
| All update operations succeed                       | 100%                         |
| Validation scores maintain or improve after updates | Yes                          |
| Audit report generated with all three formats       | .docx + .xlsx + .html        |
| All test data cleaned up                            | 100%                         |
