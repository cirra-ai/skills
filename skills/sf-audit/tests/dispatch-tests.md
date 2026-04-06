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
- **Dispatch**: Apex-only audit
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
- **Dispatch**: Flow/automation-only audit
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
- **Dispatch**: LWC-only audit
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
- **Dispatch**: Metadata/data-model-only audit
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `sobject_describe`, `soql_query`
- **Should NOT call**: `metadata_read`, `fetch_more`
- **Should ask user**: yes (Phase B approval gate; Scale Gate in A6 if custom object count exceeds 10)
- **Follow-up skills**: `sf-metadata`

**Notes**: Scopes the Deep Dive to the Data Model (C7), which covers custom objects, fields, relationships, and validation rules. Uses `sobject_describe` per object and `tooling_api_query` for `ValidationRule`. The 120-point rubric is sourced from `sf-metadata`. Workflow Rule inventory (C8) should also run since it is metadata-adjacent and lightweight.

---

## permissions audit

- **Input**: `/sf-audit permissions`
- **Dispatch**: Permissions-only audit
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
- **Dispatch**: Full Org Audit (all domains)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `soql_query`, `sobject_describe`, `metadata_read`
- **Should NOT call**: `fetch_more`
- **Should ask user**: yes (no argument-hint was given, so the skill runs a full audit by default; it must still ask at Phase B before starting the Deep Dive, and at Scale Gate A6 if any domain exceeds 10 components)
- **Follow-up skills**: `sf-apex`, `sf-flow`, `sf-lwc`, `sf-metadata`, `sf-permissions`

**Notes**: With no argument hint the skill defaults to a full audit across all domains. It must first check for `audit_state.md` to determine whether this is a fresh or resuming run. The Phase B approval gate is mandatory before any body downloads begin. All domain follow-up skills are relevant since the full audit covers every Phase C sub-phase.

---

## scoped apex-and-flow audit

- **Input**: `/sf-audit apex flow`
- **Dispatch**: Full Org Audit (all domains)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none — init takes no arguments)`
- **Should call**: `tooling_api_query`, `soql_query`
- **Should NOT call**: `sobject_describe`, `metadata_read`
- **Should ask user**: yes (Phase B presents a scoped approval gate — "Yes, just Apex and Flows" path — before deep-dive begins; Scale Gate A6 applies to Apex class/trigger and Flow counts)
- **Follow-up skills**: `sf-apex`, `sf-flow`

**Notes**: Multiple argument hints narrow the audit to Apex Classes (C1), Apex Triggers (C2), Flows (C3), and Process Builders (C4). The Phase B prompt should reflect the scoped selection, matching the "Yes, just Apex and Flows" option described in Phase B. Phase C9 (Completeness Gate) only validates the approved domains. LWC, Metadata, and Permissions domains are excluded and should be marked "Not audited" in the reports.

---

## natural language — audit my org

- **Input**: `/sf-audit run an audit on my org`
- **Dispatch**: Full Org Audit (all domains)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`, `sobject_describe`, `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (confirm full audit scope before proceeding)
- **Follow-up skills**: `sf-apex`, `sf-flow`, `sf-lwc`, `sf-metadata`, `sf-permissions`

**Notes**: Natural language without an explicit scope keyword should be interpreted as a full audit request. The dispatch table maps unclear/no-argument to full audit. Should confirm scope with the user before starting the multi-phase process. All eight audit domains (C1–C8) should be included.

---

## metadata and permissions combined scope

- **Input**: `/sf-audit metadata permissions`
- **Dispatch**: Full Org Audit (all domains)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`, `sobject_describe`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (Phase B approval required before deep-dive scoring)
- **Follow-up skills**: `sf-metadata`, `sf-permissions`

**Notes**: Multiple scope keywords combine — `metadata` activates C7 (Data Model) + C8 (Workflow Rules), and `permissions` activates C6 (Profiles and Permissions). Should NOT run C1–C5 phases. Phase B user approval is required before deep-dive begins, consistent with other scoped audit tests.

---

## lwc and metadata combined scope

- **Input**: `/sf-audit lwc metadata`
- **Dispatch**: Full Org Audit (all domains)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`, `sobject_describe`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (Phase B approval required before deep-dive scoring)
- **Follow-up skills**: `sf-lwc`, `sf-metadata`

**Notes**: Combines LWC (C5) with Data Model (C7+C8) scopes. Tests that non-adjacent scope keywords are properly combined. Should skip C1–C4 and C6. Phase B user approval is required before deep-dive begins.

---

## review synonym for audit

- **Input**: `/sf-audit review apex`
- **Dispatch**: Full Org Audit (all domains)
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`, `tooling_api_query`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (Phase B approval required before deep-dive scoring)
- **Follow-up skills**: `sf-apex`

**Notes**: The word `review` is not in the dispatch table explicitly but the intent maps to audit. The `apex` scope keyword should still be detected — should run C1 (Apex Classes) and C2 (Apex Triggers) only. Phase B user approval is required before deep-dive begins. Tests natural language intent resolution combined with scope filtering.
