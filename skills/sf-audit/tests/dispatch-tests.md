# sf-audit dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## full audit explicit

- **Input**: `/sf-audit full`
- **Dispatch**: Full Org Audit (all domains)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `soql_query`, `sobject_describe`, `metadata_read`
- **Should NOT call**: `fetch_more`
- **Should ask user**: yes (Scale Gate in A6 — ask "Score all / Score a sample / Quick pass only" if any domain exceeds 10 components; ask for Deep Dive approval in Phase B)
- **Follow-up skills**: `sf-apex`, `sf-flow`, `sf-lwc`, `sf-metadata`, `sf-permissions`

**Notes**: The `full` hint signals a comprehensive audit covering all eight Phase C domains (C1–C8). The skill must read `audit_state.md` first to check for a prior run, then execute Phase A (Quick Pass), present the Phase B approval gate, and proceed through Phases C–E. All domain sub-skills are candidates for follow-up remediation work.

---

## apex-only audit

- **Input**: `/sf-audit apex`
- **Dispatch**: Apex-only audit (C1-C2)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `soql_query`
- **Should NOT call**: `sobject_describe`, `metadata_read`
- **Should ask user**: yes (Phase B approval gate before starting Deep Dive on C1/C2; Scale Gate in A6 if Apex class/trigger count exceeds 10)
- **Follow-up skills**: `sf-apex`

**Notes**: The `apex` hint scopes the audit to Apex Classes (C1) and Apex Triggers (C2) only. Phase A still runs in full to build an inventory, but Phase C skips C3–C8. The skill should note in Phase B that only Apex domains are being scored. The scoring rubric is sourced from `sf-apex`; `sf-apex` is the primary follow-up skill for remediation.

---

## flow audit

- **Input**: `/sf-audit flow`
- **Dispatch**: Flow/automation-only audit (C3-C4)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `soql_query`
- **Should NOT call**: `sobject_describe`, `metadata_read`
- **Should ask user**: yes (Phase B approval gate; Scale Gate in A6 if active Flow count exceeds 10)
- **Follow-up skills**: `sf-flow`

**Notes**: Scopes the Deep Dive to Flows (C3) and Process Builders (C4). Flow bodies must be fetched one at a time due to the Tooling API single-row constraint on `Flow` with `Metadata`. Process Builders are inventoried only — not scored against the Flow rubric. The skill should surface migration-priority findings for Process Builders.

---

## lwc audit

- **Input**: `/sf-audit lwc`
- **Dispatch**: LWC-only audit (C5)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `metadata_read`
- **Should NOT call**: `sobject_describe`
- **Should ask user**: yes (Phase B approval gate; Scale Gate in A6 if LWC count exceeds 10)
- **Follow-up skills**: `sf-lwc`

**Notes**: Scopes the Deep Dive to LWC Components (C5) only. Phase A still collects counts for all component types. The 165-point rubric from `sf-lwc` is applied in C5. `metadata_read` or `LightningComponentResource` Tooling query is used to retrieve bundle source. `soql_query` is not needed for LWC source retrieval specifically, though it may be used in Phase A for Permission Set/Profile counts.

---

## metadata audit

- **Input**: `/sf-audit metadata`
- **Dispatch**: Metadata/data-model-only audit (C7)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `sobject_describe`, `soql_query`, `metadata_list`, `metadata_read`
- **Should NOT call**: `fetch_more`
- **Should ask user**: yes (Phase B approval gate; Scale Gate in A6 if custom object count exceeds 10)
- **Follow-up skills**: `sf-metadata`

**Notes**: Scopes the Deep Dive to the Data Model (C7, C7b, C8, C8b): custom objects, fields, validation rules, formula fields, and unused fields. Validation-rule formulas come from `Metadata.errorConditionFormula`, one rule at a time. Formula bodies come from `FieldDefinition.Metadata.formula`, one field at a time. Layouts and reports are listed with `metadata_list` and read by exact `fullName` — no wildcards, and `Report` is not queried through `tooling_api_query`. A population check that returns `INVALID_FIELD` records `has_data: null` and a field-level security finding. The 120-point rubric is sourced from `sf-metadata`. Output for this scoped audit is one HTML report, not the 18-document full pack.

---

## permissions audit

- **Input**: `/sf-audit permissions`
- **Dispatch**: Permissions-only audit (C6)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `soql_query`, `tooling_api_query`
- **Should NOT call**: `sobject_describe`, `metadata_read`, `fetch_more`
- **Should ask user**: no (Phase C6 does not download source bodies and does not require a separate user approval gate beyond Phase B)
- **Follow-up skills**: `sf-permissions`

**Notes**: Scopes the Deep Dive to Profiles and Permissions (C6) only. This phase is "fast" because it relies entirely on SOQL queries — no source body downloads. Key queries cover `Profile`, `PermissionSet`, `PermissionSetGroup`, `PermissionSetGroupComponent`, `PermissionSetAssignment`, and active `User` count. Findings are classified CRITICAL through LOW per the severity table in C6.

---

## no arguments — default behavior

- **Input**: `/sf-audit`
- **Dispatch**: Ask the user (see below)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `soql_query`, `sobject_describe`, `metadata_read`
- **Should NOT call**: `fetch_more`
- **Should ask user**: yes (no scope was given, so ask in plain text which domains to audit; do not default to a full audit and do not call a question tool with more than 4 options)
- **Follow-up skills**: `sf-apex`, `sf-flow`, `sf-lwc`, `sf-metadata`, `sf-permissions`

**Notes**: With no argument hint the skill asks which scope to run and does not default to a full audit. The question is plain text because the catalog has more than 4 options and claude.ai's question tool allows at most 4. It must first check for `audit_state.md` to determine whether this is a fresh or resuming run. After the user picks a scope, the Phase B approval gate is mandatory before any body downloads begin.

---

## scoped apex-and-flow audit

- **Input**: `/sf-audit apex flow`
- **Dispatch**: Combined scopes (union of the named domains)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `soql_query`
- **Should NOT call**: `sobject_describe`, `metadata_read`
- **Should ask user**: yes (Phase B presents a scoped approval gate — "Yes, just Apex and Flows" path — before deep-dive begins; Scale Gate A6 applies to Apex class/trigger and Flow counts)
- **Follow-up skills**: `sf-apex`, `sf-flow`

**Notes**: Every scope token counts, not only the first. `apex` and `flow` together run C1–C4 and do not run LWC, metadata, or permissions. Phase C9 checks only those domains. The report is the scoped HTML report, not the 18-document pack. Phase B confirms the combined scope before the deep dive.

---

## natural language — audit my org

- **Input**: `/sf-audit run an audit on my org`
- **Dispatch**: Ask the user (see below)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`, `sobject_describe`, `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (no scope keyword, so ask which domains to audit; do not assume a full audit)
- **Follow-up skills**: `sf-apex`, `sf-flow`, `sf-lwc`, `sf-metadata`, `sf-permissions`

**Notes**: Natural language without a scope keyword is unclear. Ask in plain text and wait. Do not start a full audit until the user says so. The user may name more than one scope, and those tokens are a union.

---

## metadata and permissions combined scope

- **Input**: `/sf-audit metadata permissions`
- **Dispatch**: Combined scopes (union of the named domains)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`, `sobject_describe`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (Phase B approval required before deep-dive scoring)
- **Follow-up skills**: `sf-metadata`, `sf-permissions`

**Notes**: `metadata and permissions` is a combined scope, not "first token wins". `metadata` runs C7, C7b, C8, and C8b. `permissions` runs C6. C1–C5 do not run. Phase B confirms that set. The report is one HTML document for those domains.

---

## lwc and metadata combined scope

- **Input**: `/sf-audit lwc metadata`
- **Dispatch**: Combined scopes (union of the named domains)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`, `sobject_describe`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (Phase B approval required before deep-dive scoring)
- **Follow-up skills**: `sf-lwc`, `sf-metadata`

**Notes**: Combines LWC (C5) with metadata (C7, C7b, C8, C8b). Both tokens are kept. Skip C1–C4 and C6. Phase B confirms the union before the deep dive.

---

## review synonym for audit

- **Input**: `/sf-audit review apex`
- **Dispatch**: Apex-only audit (C1-C2)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (Phase B approval required before deep-dive scoring)
- **Follow-up skills**: `sf-apex`

**Notes**: The word `review` is not in the dispatch table explicitly but the intent maps to audit. The `apex` scope keyword should still be detected — should run C1 (Apex Classes) and C2 (Apex Triggers) only. Phase B user approval is required before deep-dive begins. Tests natural language intent resolution combined with scope filtering.
