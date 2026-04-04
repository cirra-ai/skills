---
name: sf-audit
plugin: cirra-ai-sf
argument-hint: '[full|apex|flow|lwc|metadata|permissions] ...'
description: >
  Run a comprehensive Salesforce org audit. Inventories and scores Apex classes, triggers,
  Flows, Process Builders, Workflow Rules, LWC components, custom objects/fields, validation
  rules, formula fields, approval processes, escalation/assignment/auto-response rules,
  Profiles, and Permission Sets. Scans all formula and criteria logic for hardcoded Record
  IDs, Campaign names, Profile names, URLs, and other fragile values. Generates Word, Excel,
  and HTML reports. Use when asked to audit a Salesforce org, review org health, or run an
  org health check.
  Usage: /sf-audit [full|apex|flow|lwc|metadata|permissions] ...
metadata:
  version: 2.1.0
---

# Salesforce Org Audit

Run a comprehensive Salesforce org audit covering code quality, automation
health, data model design, and the permission model.

**Scoring**: Where a numeric rubric exists, defer to the corresponding domain
skill (`sf-apex`, `sf-flow`, `sf-lwc`,
`sf-metadata`). Do not invent your own criteria.

For categories without a numeric rubric (Triggers, Workflow Rules, Process
Builders, Profiles, Validation Rules, Formula Fields, Approval Processes,
Escalation Rules, Assignment Rules, Auto-Response Rules), produce an inventory
with qualitative findings and severity classifications.

---

## Dispatch

Parse `$ARGUMENTS` to determine the audit scope:

| First argument or intent                | Workflow                       |
| --------------------------------------- | ------------------------------ |
| `full`, no scope specified after asking | Full Org Audit (all domains)   |
| `apex`                                  | Apex-only audit                |
| `flow`                                  | Flow/automation-only audit     |
| `lwc`                                   | LWC-only audit                 |
| `metadata`, `data-model`                | Metadata/data-model-only audit |
| `permissions`                           | Permissions-only audit         |
| _(no argument or unclear)_              | Ask the user (see below)       |

When the audit scope is missing or unclear, **you MUST use `AskUserQuestion`** before proceeding:

```
AskUserQuestion(question="What would you like to audit?\n\n1. **Full** — comprehensive audit of the entire org\n2. **Apex** — Apex classes and triggers only\n3. **Flow** — Flows, Process Builders, and Workflow Rules only\n4. **LWC** — Lightning Web Components only\n5. **Metadata** — custom objects, fields, and data model only\n6. **Permissions** — Profiles, Permission Sets, and Permission Set Groups only")
```

Do NOT guess the scope or default to a full audit. Wait for the user's answer.

---

## Start here every time — read `audit_state.md` first

Before doing anything else, check whether a working document already exists:

```
Read: ./audit_output/audit_state.md
```

- **File exists** — you are resuming a previous audit. Read the state, note
  what is complete, and pick up from the `## Next Step` section. Tell the user:
  "Resuming audit from [last completed phase]. [X] of [Y] components processed."

- **File does not exist** — this is a fresh audit. Proceed to Prerequisites,
  then Environment Detection, then Phase A.

Keep `audit_state.md` up to date throughout. Update it after completing each
domain in Phase C. This file is your contract with your future self after
a context compaction.

---

## Prerequisites

Call `cirra_ai_init()` first if not already done this session.

---

## Execution modes

Determine execution mode once, before Phase A. Four modes are supported —
see `references/execution-modes.md` for detection logic and full details.

### Audit-specific mode behaviour

| Mode                      | Body retrieval                      | Queries                |
| ------------------------- | ----------------------------------- | ---------------------- |
| `sfdx-repo`               | Read from disk (no API calls)       | MCP for live-only data |
| `cli`                     | `sf project retrieve start -m`      | `sf data query --json` |
| `mcp-plus-code-execution` | MCP tools; download `artifactUrl`   | MCP tools              |
| `mcp-core`                | MCP tools; `fetch_more` with cursor | MCP tools              |

**`sfdx-repo` specifics:**

- Read `.cls`, `.trigger`, `.flow-meta.xml`, and LWC bundles from disk.
- Still use MCP for live-only data: permission assignments, user counts,
  PSG status, active user queries.
- For incremental audits: use `git log` to detect changed files (Phase A3).

**`cli` specifics:**

- Bulk retrieve via `sf project retrieve start -m <type>`.
- Queries via `sf data query -q "..." --target-org <org> --json`.
- For incremental audits: filter by `LastModifiedDate` in queries.

**`mcp-plus-code-execution` specifics:**

- Bulk query first (e.g. `tooling_api_query: SELECT Id, Name, Body FROM
ApexClass WHERE NamespacePrefix = null ORDER BY Id`).
- When the response includes `instructions.artifactUrl`, download it and
  write the JSON to `./audit_output/intermediate/` for local processing.
- Run `pre_score.py` on the downloaded files (Strategy A).

**`mcp-core` specifics:**

- Same bulk queries, but page through large responses with
  `fetch_more(artifactId=..., cursor=_pagination.nextCursor)`.
- Process in batches of 5; discard bodies between batches (Strategy B).

In all modes, use MCP tools (`soql_query`, `tooling_api_query`,
`sobject_describe`) for targeted lookups when CLI is not needed.

---

## Incremental audit detection

If the user mentions a previous audit, asks to "update" an audit, or provides
a path to prior audit output, this is an **incremental audit**.

### Locating the previous audit

Look for `audit_state.md` in one of:

1. A user-provided path (e.g. `~/audits/2026-01/audit_output/`)
2. A git repository the user specifies
3. The default `./audit_output/` directory (if it contains a completed audit)

From the previous `audit_state.md`, extract:

- **Audit date** — the timestamp of the last completed audit
- **Component inventory** — names and scores of all previously scored components
- **Skipped components** — what was excluded and why

### Delta detection (per mode)

| Mode                      | How to find changed components                                               |
| ------------------------- | ---------------------------------------------------------------------------- |
| `sfdx-repo`               | `git log --after="<prev_date>" --name-only --diff-filter=ACMR -- force-app/` |
| `cli`                     | Add `AND LastModifiedDate > <prev_date>` to Tooling/SOQL queries             |
| `mcp-plus-code-execution` | Add `AND LastModifiedDate > <prev_date>` to Tooling/SOQL queries             |
| `mcp-core`                | Add `AND LastModifiedDate > <prev_date>` to Tooling/SOQL queries             |

### Delta categories

Classify every component into one of:

| Category      | Action                                                     |
| ------------- | ---------------------------------------------------------- |
| **Changed**   | Re-score against current rubric                            |
| **New**       | Score as new (not in previous audit)                       |
| **Removed**   | Mark as removed in reports                                 |
| **Unchanged** | Carry forward previous score — do not re-fetch or re-score |

Track these categories in `audit_state.md` and in the final reports.

---

## Handling large MCP responses

See `references/mcp-pagination.md` for the full artifact and pagination
reference. Key points for audits:

- **`mcp-plus-code-execution`**: download `instructions.artifactUrl` and
  write JSON to `./audit_output/intermediate/` for local processing with
  `pre_score.py`.
- **`mcp-core`**: page through with
  `fetch_more(artifactId=..., cursor=_pagination.nextCursor)`. Process in
  batches of 5; discard bodies between batches.
- **`sfdx-repo` / `cli`**: bodies come from disk or CLI — artifact
  responses are uncommon.

### Additional MCP constraints

1. **Flow single-row constraint** — Tooling query on `Flow` with `Metadata`
   returns only one row. Fetch Flow IDs first, then one row per ID.
2. **Permission queries** — PermissionSet/PSG datasets hit limits quickly.
   Use cursor windows and persist per-batch.

---

## Phase A — Quick Pass (always runs first)

The Quick Pass is a lightweight inventory. It fetches only metadata headers
— no source bodies — so it completes quickly even for large orgs.

**Goals:**

1. Count every component type across the whole org
2. Classify each component: **local** (NamespacePrefix = null) vs
   **managed package** (NamespacePrefix != null)
3. Flag known generated / unmodifiable classes (see skip list below)
4. Collect surface quality signals: API versions, class sizes
5. If incremental: detect the delta (changed components since last audit)
6. Estimate the cost of the Deep Dive so the user can make an informed decision

### A1 — Component counts

**cli / MCP modes** — query counts:

```
tooling_api_query: SELECT COUNT(Id) total FROM ApexClass WHERE NamespacePrefix = null
tooling_api_query: SELECT COUNT(Id) total FROM ApexClass WHERE NamespacePrefix != null
tooling_api_query: SELECT COUNT(Id) total FROM ApexTrigger WHERE NamespacePrefix = null
tooling_api_query: SELECT COUNT(Id) total FROM FlowDefinition WHERE ActiveVersionId != null AND NamespacePrefix = null
tooling_api_query: SELECT COUNT(Id) total FROM LightningComponentBundle WHERE NamespacePrefix = null
tooling_api_query: SELECT COUNT(Id) total FROM CustomObject WHERE NamespacePrefix = null
tooling_api_query: SELECT COUNT(Id) total FROM ValidationRule WHERE NamespacePrefix = null
tooling_api_query: SELECT COUNT(Id) total FROM WorkflowRule WHERE NamespacePrefix = null
tooling_api_query: SELECT COUNT(Id) total FROM CustomField WHERE NamespacePrefix = null AND Formula != null
soql_query: SELECT COUNT(Id) total FROM PermissionSet WHERE IsOwnedByProfile = false AND NamespacePrefix = null AND Type != 'Group'
soql_query: SELECT COUNT(Id) total FROM PermissionSetGroup
soql_query: SELECT COUNT(Id) total FROM Profile
```

**sfdx-repo mode** — count files on disk:

```bash
find force-app/main/default/classes -name "*.cls" | wc -l
find force-app/main/default/triggers -name "*.trigger" | wc -l
find force-app/main/default/flows -name "*.flow-meta.xml" | wc -l
find force-app/main/default/lwc -mindepth 1 -maxdepth 1 -type d | wc -l
```

Supplement with MCP queries for live-only data (Profiles, Permission Sets,
PSGs, user counts).

### A2 — Surface metadata for Apex classes (local only)

Fetch name, size, and API version — no body — for all local Apex classes.

**cli / MCP modes:**

```
tooling_api_query: SELECT Id, Name, LengthWithoutComments, ApiVersion
  FROM ApexClass
  WHERE NamespacePrefix = null
  ORDER BY Id
```

If the response includes `instructions.artifactId`, retrieve using the
strategy for your execution mode (see `references/mcp-pagination.md`).

**sfdx-repo mode** — read `-meta.xml` files for ApiVersion; use file size as
a proxy for `LengthWithoutComments`.

From this data, immediately flag:

- Classes with `ApiVersion < 50.0` (more than 4 years old) — LOW risk
- Classes with `LengthWithoutComments > 5000` — flag as large, note for review
- Classes matching the **generated/skip list** (see below)

### A3 — Delta detection (incremental only)

Skip this step for fresh audits.

**sfdx-repo mode:**

```bash
git log --after="<prev_audit_date>" --name-only --diff-filter=ACMR \
  -- force-app/main/default/classes/ force-app/main/default/triggers/ \
     force-app/main/default/flows/ force-app/main/default/lwc/
```

Parse the output to identify changed files. Map file paths to component names.

**cli / MCP modes:**

Add `AND LastModifiedDate > <prev_audit_date>` to the A2 query and equivalent
queries for triggers, flows, and LWC. Components not in the result set are
unchanged — carry forward their previous scores.

Also detect removed components: any component in the previous inventory that
no longer appears in the current full inventory count.

### A4 — Surface metadata for Flows and LWC

**Flows:**

```
tooling_api_query: SELECT Id, DeveloperName, ActiveVersionId,
  ActiveVersion.VersionNumber, ActiveVersion.ProcessType
  FROM FlowDefinition
  WHERE ActiveVersionId != null AND NamespacePrefix = null
  ORDER BY Id
```

Separate by `ActiveVersion.ProcessType`: Flows vs Process Builders.

**LWC:**

```
tooling_api_query: SELECT Id, DeveloperName, ApiVersion
  FROM LightningComponentBundle
  WHERE NamespacePrefix = null
  ORDER BY Id
```

### A5 — Write `audit_state.md`

Create `./audit_output/audit_state.md` with the Quick Pass results:

```markdown
# Audit State — {ORG_NAME} — {DATE}

## Mode

EXEC_MODE: sfdx-repo | cli | mcp-plus-code-execution | mcp-core
AUDIT_TYPE: fresh | incremental (previous: {PREV_DATE})

## Component Inventory (Phase A complete)

| Domain           | Local | Managed | Skipped (generated) | Delta |
| ---------------- | ----- | ------- | ------------------- | ----- |
| Apex Classes     | X     | Y       | Z                   | D     |
| Apex Triggers    | X     | -       | -                   | D     |
| Active Flows     | X     | -       | -                   | D     |
| Process Builders | X     | -       | -                   | D     |
| LWC Components   | X     | -       | -                   | D     |
| Custom Objects   | X     | -       | -                   | D     |
| Validation Rules | X     | -       | -                   | -     |
| Workflow Rules   | X     | -       | -                   | -     |
| Permission Sets  | X     | -       | -                   | -     |
| PSGs             | X     | -       | -                   | -     |
| Profiles         | X     | -       | -                   | -     |

(Delta column: number of changed/new components for incremental audits)

## Skip List Applied

- MetadataService (generated, 12,000+ lines — not user-controlled)
- [any other skipped classes with reason]

## Surface Findings from Quick Pass

- [API version warnings]
- [oversized class flags]

## Deep Dive Progress

- [ ] C1: Apex Classes (0 / X local)
- [ ] C2: Apex Triggers (0 / X)
- [ ] C3: Flows (0 / X)
- [ ] C4: Process Builders (0 / X)
- [ ] C5: LWC (0 / X)
- [ ] C6: Permissions
- [ ] C7: Data Model (0 / X objects)
- [ ] C8: Workflow Rules

## Scores Accumulated

[populated as deep dive runs]

## Carried Forward (incremental only)

[list of unchanged components with their previous scores]

## Next Step

-> Awaiting user approval for Deep Dive (Phase B)
```

### A6 — Scale Gate

After writing `audit_state.md`, check whether the org is large enough to
warrant special handling. Count the scoreable components per domain:

| Domain       | Count | Over 10? |
| ------------ | ----- | -------- |
| Apex Classes | {n}   | Y/N      |
| Triggers     | {n}   | Y/N      |
| Flows        | {n}   | Y/N      |
| LWC          | {n}   | Y/N      |
| Objects      | {n}   | Y/N      |

**If ANY domain exceeds 10**, inform the user before proceeding to Phase B:

> I found **{total}** components to score across **{domains}** domains.
>
> - **"Score all"** — I'll score every component.
> - **"Score a sample"** — I'll score the top 10 per domain ranked by risk
>   (old API version, large size, naming anomalies). The rest get surface
>   metrics only.
> - **"Quick pass only"** — Report with inventory data, no body downloads.

Record the user's choice in `audit_state.md` under `## Scoring Strategy`
(`full | sample | quick_pass`). Phase B and Phase C reference this value.

**If no domain exceeds 10**, proceed directly to Phase B.

### Generated / skip list

The following classes should be **noted but not scored** in the Deep Dive.
They are large or generated files that the org developer does not directly
author and cannot meaningfully improve:

| Class name pattern                       | Reason                                                          |
| ---------------------------------------- | --------------------------------------------------------------- |
| `MetadataService`                        | Andrew Fawcett's Apex Metadata API — generated, ~12,000 lines   |
| `fflib_*`                                | FinancialForce Apex Common library (managed-package equivalent) |
| `Callable_MockProvider`, `CallableMock*` | Test infrastructure, not production logic                       |

More broadly: if a class has `LengthWithoutComments > 8000` **and** a name
that does not correspond to a business domain concept (e.g. it looks like a
library or framework class), flag it for user confirmation rather than
spending time scoring it.

---

## Phase B — User Approval Gate

After Phase A, present a summary and ask for approval before starting the
Deep Dive. This is important: the Deep Dive can cost hundreds of API calls
on a large org.

Present something like:

---

**Quick Pass complete for {ORG_NAME}.**

**Local components to score:**

- Apex Classes: **{X}** (excl. {Z} generated/skipped)
- Apex Triggers: **{X}**
- Active Flows: **{X}** (incl. {PB} Process Builders)
- LWC Components: **{X}**
- Custom Objects: **{X}**

**Execution mode:** `{EXEC_MODE}`

[If incremental:]
**Delta since {PREV_DATE}:** {D} components changed, {N} new, {R} removed.
{U} unchanged scores will be carried forward.

[If mcp-plus-code-execution or mcp-core mode:]
**Estimated cost:** ~{total} sequential API calls.
For reference: 500 classes ~ 500 API calls ~ 20-40 minutes.

**Managed packages excluded by default.** {Y} managed-package classes
will be skipped unless you ask me to include them.

**Surface findings noticed in Quick Pass:**

- {count} classes older than API v50 ({list top 5})
- {count} classes larger than 5,000 lines
- {list any other flags}

**Proceed with full Deep Dive?** You can also say:

- "Yes, full audit" — scores all domains
- "Yes, just Apex and Flows" — skips LWC, Metadata
- "Just show me the quick pass results" — lightweight report from Phase A
  data only, no body downloads

[If the user chose "Score a sample" in A6, remind them here:
"You selected sample scoring — I'll score the top 10 per domain by risk."]

---

If the user says "just quick pass results", skip to Phase D (reports) and
generate reports based on what Phase A collected. Mark unscored domains as
"Not audited — surface metrics only."

---

## Phase C — Deep Dive

> **MANDATORY (when user chose "Score all" in A6): Score EVERY component. No sampling. No shortcuts.**
>
> When the user chose "Score all" in A6, you MUST individually fetch, read, and
> score **every single** Apex class, trigger, Flow, and LWC component in the
> org (minus the generated/skip list and managed packages). Do NOT:
>
> - Score a "representative sample" and extrapolate
> - Score only the first N items and summarize the rest
> - Skip items because the org is large or you are running low on context
> - Group multiple components into a single score
> - Estimate scores based on metadata (size, API version) without reading the body
>
> The batch sizes (20 for Apex, 10 for Flows/LWC) are **checkpointing
> intervals**, not limits. After each batch, update `audit_state.md` and
> continue to the next batch until every component is scored.
>
> **Completeness check:** Before marking any sub-phase complete, compare the
> count of scored components against the inventory count from Phase A. If they
> do not match (after accounting for skipped/generated items), you are not done.
> Keep processing until: `scored + skipped + carried_forward == inventory count`.
> (For fresh audits, `carried_forward` is 0.)

### Environment-aware processing

Choose your processing strategy based on what the environment supports:

**Strategy A — Pre-score on disk** (`sfdx-repo`, `cli`, or
`mcp-plus-code-execution`):

1. Fetch all bodies to `./audit_output/intermediate/` (via local filesystem,
   CLI bulk retrieve, or `artifactUrl` download — whichever mode applies)
2. Run the pre-scoring orchestrator:
   ```bash
   python scripts/pre_score.py \
     --intermediate-dir ./audit_output/intermediate \
     --output-dir ./audit_output \
     --threshold 70
   ```
3. Read `./audit_output/pre_score_summary.json`. Only review components
   listed in `needs_llm_review` (those scoring below 70% of max). Accept all
   other scores as-is — **do not load their bodies into context**.
4. For flagged components: read the body, apply the domain rubric, adjust the
   score if the script produced a false positive, and record the final score.
5. Write the final JSON score files and proceed to Phase C9 / Phase D.

This strategy keeps component bodies **out of context entirely** for the
majority of components, allowing audits of 500+ component orgs.

**Strategy B — Batch in context** (`mcp-core`):

1. Process components in batches of **5** (not 20). For each component:
   a. Fetch the body (via `fetch_more` with cursor, or direct query)
   b. Score it against the rubric
   c. Record the score in `audit_state.md` under `## Scores Accumulated`
   as one row: `| Name | Score/Max | Top Issue |`
   d. **Discard the body** before loading the next component
2. Never hold more than 2 component bodies in context simultaneously.
3. After each batch of 5, update `audit_state.md` with progress.

**How to choose:** Use Strategy A in `sfdx-repo`, `cli`, or
`mcp-plus-code-execution` mode. Use Strategy B in `mcp-core` mode.
See `references/execution-modes.md` for detection logic.

---

Update `audit_state.md` after completing each sub-phase. If the conversation
gets interrupted (context compaction, session end), the next session can
resume from the state file.

**In every phase: skip components where `NamespacePrefix != null`.**

**For incremental audits:** only process changed/new components. Carry forward
previous scores for unchanged components. Mark removed components.

### C1 — Apex Classes (deep)

**Score every local class.** Process in batches of 20 (for checkpointing). For each batch:

1. Fetch `Body`:
   - **sfdx-repo**: read from `force-app/main/default/classes/<ClassName>.cls`
   - **cli**: `sf project retrieve start -m ApexClass --target-org <org>`
     (bulk, one CLI call for all classes)
   - **MCP modes**: bulk query first — `tooling_api_query: SELECT Id, Name,
Body FROM ApexClass WHERE NamespacePrefix = null ORDER BY Id`. If the
     response includes `instructions.artifactId`, retrieve using the
     strategy for your mode (see `references/mcp-pagination.md`). Fall back
     to `SELECT Body FROM ApexClass WHERE Id = '<id>'` one at a time only
     if bulk query is not available.
2. Write each body to `./audit_output/intermediate/apex/<ClassName>.cls`
3. Score using the 150-point rubric from `sf-apex`
4. Track: class name, score, top 3 issues
5. After each batch of 20: update `audit_state.md` with progress and scores

**Skip any class on the generated/skip list.** Note its name and reason in
`audit_state.md` but do not score it.

**Continue batches until every local class is scored.** Then compute:

- Mean and median score
- Count below 70 (needs attention), below 50 (critical)
- Top 5 most common issue types across all classes

**Verify:** `scored + skipped + carried_forward == Phase A local class count`.
If not, identify and score the missing classes before proceeding.

Update `audit_state.md`: mark C1 complete, record aggregate stats.

### C2 — Apex Triggers (deep)

**Score every local trigger.** Follow the same completeness rules as C1.

1. Fetch trigger metadata:
   ```
   tooling_api_query: SELECT Id, Name, TableEnumOrId, ApiVersion, Status
     FROM ApexTrigger WHERE NamespacePrefix = null
   ```
2. Fetch `Body`:
   - **sfdx-repo**: read from `force-app/main/default/triggers/<Name>.trigger`
   - **cli**: `sf project retrieve start -m ApexTrigger --target-org <org>`
   - **MCP modes**: bulk query with artifact retrieval (same pattern as C1).
     Fall back to `SELECT Body FROM ApexTrigger WHERE Id = '<id>'` one at a
     time if needed.
3. Write each to `./audit_output/intermediate/triggers/<TriggerName>.trigger`
4. Score against the Apex rubric where applicable. Also flag trigger-specific
   issues:

| Finding                                                         | Severity |
| --------------------------------------------------------------- | -------- |
| Logic in trigger body instead of a handler class                | HIGH     |
| No bulkification (SOQL/DML inside loop over Trigger.new)        | CRITICAL |
| Multiple triggers on same object + event (execution order risk) | HIGH     |
| Missing before/after context checks                             | MEDIUM   |
| ApiVersion < 55.0                                               | LOW      |

**Verify:** `scored + skipped + carried_forward == Phase A local trigger count`.

Update `audit_state.md`: mark C2 complete.

### C3 — Flows (deep)

**Score every active Flow** (excluding Process Builders — those go to C4).
Use the Flow ID list from Phase A4.

1. Fetch flow definitions:
   - **sfdx-repo**: read from `force-app/main/default/flows/<Name>.flow-meta.xml`
   - **cli**: `sf project retrieve start -m Flow --target-org <org>`
   - **MCP modes**: `tooling_api_query` on `Flow` WHERE `Id = '<id>'` (one
     row per ID — single-row constraint applies)
2. Write each to `./audit_output/intermediate/flows/<DeveloperName>.flow-meta.xml`
3. Score using the 110-point rubric from `sf-flow`
4. Separate Process Builders (`ProcessType = 'Workflow'`) — inventory only,
   no Flow rubric score (see C4)
5. After every 10 flows, update `audit_state.md`

**Continue until every active Flow is scored.** Then verify:
`scored_flows + skipped_flows + carried_forward == Phase A active Flow count` and
`process_builders == Phase A Process Builder count`.

Update `audit_state.md`: mark C3 complete.

### C4 — Process Builders (inventory)

Process Builders (`ProcessType = 'Workflow'`) are legacy. Do not score
against the Flow rubric. Inventory and flag:

| Finding                                         | Severity |
| ----------------------------------------------- | -------- |
| Active Process Builder (should migrate to Flow) | HIGH     |
| > 10 criteria nodes                             | MEDIUM   |
| Invokes Apex actions                            | MEDIUM   |
| Multiple Process Builders on same object        | HIGH     |

Write to `./audit_output/intermediate/process_builders/inventory.md`.
Update `audit_state.md`: mark C4 complete.

### C5 — LWC (deep)

**Score every local LWC component.** Follow the same completeness rules as C1.

1. Fetch component source:
   - **sfdx-repo**: read from `force-app/main/default/lwc/<Name>/`
   - **cli**: `sf project retrieve start -m LightningComponentBundle --target-org <org>`
   - **MCP modes**: `metadata_read` or `LightningComponentResource` Tooling
     query grouped by bundle ID
2. Write each to `./audit_output/intermediate/lwc/<DeveloperName>/`
3. Score using the 165-point rubric from `sf-lwc`
4. After every 10 components, update `audit_state.md`

**Continue until every LWC component is scored.** Then verify:
`scored + skipped + carried_forward == Phase A local LWC count`.

Update `audit_state.md`: mark C5 complete.

### C6 — Profiles and Permissions

This phase does **not** download source bodies, so it runs faster than C1-C5.
Skip `NamespacePrefix != null`.

Run in this order:

1. Inventory Profiles
2. Inventory Permission Sets and Permission Set Groups (local namespace only)
3. Detect overly broad permissions
4. Count PS assignments, identify orphaned and over-assigned PSs
5. Check PSG health (Status = 'Outdated')

#### Key queries for C6

```
soql_query: SELECT Id, Name, UserType FROM Profile

soql_query: SELECT Id, Name, Label, Description, PermissionsModifyAllData,
  PermissionsViewAllData, PermissionsManageUsers, PermissionsAuthorApex
  FROM PermissionSet
  WHERE IsOwnedByProfile = false AND NamespacePrefix = null AND Type != 'Group'

soql_query: SELECT Id, DeveloperName, MasterLabel, Status, Description
  FROM PermissionSetGroup

soql_query: SELECT PermissionSetGroupId, PermissionSetGroup.DeveloperName,
  PermissionSetId, PermissionSet.Name
  FROM PermissionSetGroupComponent

soql_query: SELECT PermissionSetId, PermissionSet.Name, COUNT(Id) assignments
  FROM PermissionSetAssignment
  WHERE PermissionSet.IsOwnedByProfile = false
  GROUP BY PermissionSetId, PermissionSet.Name

soql_query: SELECT COUNT(Id) FROM User WHERE IsActive = true
```

Findings classification:

| Severity | Examples                                                                                    |
| -------- | ------------------------------------------------------------------------------------------- |
| CRITICAL | Non-admin PS with ModifyAllData; orphaned PS with broad access                              |
| HIGH     | PS with ViewAllData on sensitive objects; outdated PSGs; custom Profiles with ModifyAllData |
| MEDIUM   | Overlapping PSs that should be consolidated into PSGs                                       |
| LOW      | Missing descriptions on PSs; unused Profiles                                                |

Write outputs to `./audit_output/intermediate/permissions/`.
Update `audit_state.md`: mark C6 complete.

### C7 — Data Model, Validation Rules, and Formula Fields

**Score every local custom object.** Paginate `CustomObject` where `NamespacePrefix = null`.

For each custom object:

1. `sobject_describe(sObject="<ApiName>")` — get field count, relationship
   count, record type count
2. Score against the 120-point rubric from `sf-metadata`
3. Write summary to `./audit_output/intermediate/metadata/<ObjectApiName>.md`

#### Validation rules

Fetch the **full formula body** so hardcoded values can be detected:

```
tooling_api_query: SELECT Id, EntityDefinition.QualifiedApiName, ValidationName,
  Active, Description, ErrorConditionFormula, ErrorMessage
  FROM ValidationRule WHERE NamespacePrefix = null
```

For each validation rule, scan `ErrorConditionFormula` for anti-patterns using
these regex patterns:

| Pattern (case-insensitive)                                                                                                                                                 | What it catches                                               |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `[a-zA-Z0-9]{15,18}` that matches an Id format (starts with `[0-9a-zA-Z]{3}` and passes Salesforce Id checksum or is a known prefix like `001`, `006`, `00Q`, `701`, etc.) | Hardcoded Record IDs                                          |
| Quoted string literals containing object names that exist in the org (e.g. `"Enterprise"`, `"Gold Partner"`)                                                               | Hardcoded record type / picklist names (fragile if renamed)   |
| `Campaign` or campaign-name string literals                                                                                                                                | Hardcoded Campaign names                                      |
| `Profile` name string literals (e.g. `"System Administrator"`, `"Sales User"`)                                                                                             | Hardcoded Profile names (use `$Profile.Name` sparingly)       |
| URL string literals (`https://`, `http://`)                                                                                                                                | Hardcoded URLs (should use Custom Metadata or Custom Setting) |

Findings for validation rules:

| Finding                                                            | Severity |
| ------------------------------------------------------------------ | -------- |
| Formula contains hardcoded Record ID(s)                            | HIGH     |
| Formula contains hardcoded Campaign name(s)                        | HIGH     |
| Formula contains hardcoded Profile name(s)                         | MEDIUM   |
| Formula contains hardcoded URL(s)                                  | MEDIUM   |
| Formula contains hardcoded record-type or picklist value string(s) | MEDIUM   |
| Active rule with no description                                    | MEDIUM   |
| Rule with no bypass mechanism (`$Permission` or custom setting)    | MEDIUM   |
| Inactive rules (cleanup candidates)                                | LOW      |
| Object with > 20 active rules (complexity risk)                    | MEDIUM   |

#### Formula fields

Fetch formula field definitions for every local custom object:

```
tooling_api_query: SELECT Id, EntityDefinition.QualifiedApiName, DeveloperName,
  QualifiedApiName, DataType, TableEnumOrId, Formula
  FROM CustomField
  WHERE NamespacePrefix = null AND Formula != null
```

> **Note:** The `Formula` field is only available via the Tooling API on
> `CustomField`. In `sfdx-repo` mode, read formula bodies from
> `force-app/main/default/objects/<Object>/fields/<Field>.field-meta.xml`
> (the `<formula>` element).

For each formula field, scan the `Formula` body for the same anti-patterns
listed above for validation rules (hardcoded IDs, Campaign names, Profile
names, URLs, record-type/picklist strings).

Additional formula-field-specific findings:

| Finding                                                            | Severity |
| ------------------------------------------------------------------ | -------- |
| Formula contains hardcoded Record ID(s)                            | HIGH     |
| Formula contains hardcoded Campaign name(s)                        | HIGH     |
| Formula contains hardcoded Profile name(s)                         | MEDIUM   |
| Formula contains hardcoded URL(s)                                  | MEDIUM   |
| Formula contains hardcoded record-type or picklist value string(s) | MEDIUM   |
| Formula references field that does not exist (compile error risk)  | HIGH     |
| Formula exceeds 5 000 characters (readability / compile-size risk) | MEDIUM   |
| Formula uses `VLOOKUP` (deprecated function)                       | MEDIUM   |
| Formula has deeply nested `IF` statements (> 5 levels)             | LOW      |

Write formula field findings to
`./audit_output/intermediate/metadata/formula_fields.md` and persist to
`formula_fields.json`.

Cross-object analysis (beyond per-object scoring):

- Objects with no relationships (orphaned objects)
- Missing descriptions on custom objects
- Outdated API versions (< 55.0)
- Objects with > 100 custom fields (complexity risk)

**Verify:** `scored + skipped + carried_forward == Phase A local custom object count`.

Update `audit_state.md`: mark C7 complete.

### C8 — Workflow Rules

#### Inventory and criteria

```
tooling_api_query: SELECT Id, Name, TableEnumOrId
  FROM WorkflowRule WHERE NamespacePrefix = null
```

For each workflow rule, retrieve the **full metadata** (criteria formula and
actions) so formulas can be inspected:

```
metadata_read: type=WorkflowRule, fullNames=["<ObjectApiName>.<RuleName>", ...]
```

> **`sfdx-repo` mode:** read from
> `force-app/main/default/workflows/<ObjectApiName>.workflow-meta.xml`
> (each `<rules>` element contains `<formula>` and `<criteriaItems>`).

From the metadata, extract:

1. **Criteria formula** (`<formula>` element or `formula` property) — the
   Boolean expression that fires the rule.
2. **Field-update formulas** — each `WorkflowFieldUpdate` may have a
   `formula` property when `operation = Formula`.
3. **Email template references** — from `WorkflowAlert` actions.

#### Anti-pattern scanning

Scan every criteria formula and field-update formula for the same hardcoded-
value patterns used in C7 (Record IDs, Campaign names, Profile names, URLs,
record-type/picklist strings).

Write to `./audit_output/intermediate/workflow_rules/inventory.md`.

Findings:

| Finding                                                               | Severity |
| --------------------------------------------------------------------- | -------- |
| Active Workflow Rule (should migrate to Flow)                         | HIGH     |
| Field updates that may conflict with Flows on same object             | CRITICAL |
| Outbound messages (integration dependency)                            | MEDIUM   |
| Multiple automation types on same object (Workflow + Flow + PB)       | CRITICAL |
| Criteria formula contains hardcoded Record ID(s)                      | HIGH     |
| Criteria formula contains hardcoded Campaign name(s)                  | HIGH     |
| Field-update formula contains hardcoded Record ID(s)                  | HIGH     |
| Field-update formula contains hardcoded value(s) (Profile, URL, etc.) | MEDIUM   |

Update `audit_state.md`: mark C8 complete.

### C8b — Other Declarative Logic (approval, escalation, assignment rules)

Salesforce stores Boolean / formula logic in several additional metadata types.
Inventory each and scan for hardcoded-value anti-patterns.

#### Approval processes

```
metadata_read: type=ApprovalProcess, fullNames=["*"]
```

> **`sfdx-repo` mode:** read from
> `force-app/main/default/approvalProcesses/`.

For each approval process, inspect:

- **Entry criteria formula** (`entryCriteria.formula`)
- **Step criteria formulas** (each `approvalStep.entryCriteria.formula`)

Findings:

| Finding                                                    | Severity |
| ---------------------------------------------------------- | -------- |
| Entry criteria contains hardcoded Record ID(s)             | HIGH     |
| Entry criteria contains hardcoded Campaign/Profile name(s) | MEDIUM   |
| Step criteria contains hardcoded value(s)                  | MEDIUM   |
| Active approval process with no description                | LOW      |

#### Escalation rules

```
metadata_read: type=EscalationRules, fullNames=["Case"]
```

> Escalation rules typically exist only on Case. If the org customises other
> objects, query `metadata_list: type=EscalationRules` first.

Inspect each `<escalationRule>` → `<ruleEntry>` for `<formula>` or
`<criteriaItems>` containing hardcoded values.

#### Assignment rules (Lead & Case)

```
metadata_read: type=AssignmentRules, fullNames=["Lead", "Case"]
```

Inspect each `<assignmentRule>` → `<ruleEntry>` for `<formula>` or
`<criteriaItems>` containing hardcoded values.

#### Auto-response rules (Lead & Case)

```
metadata_read: type=AutoResponseRules, fullNames=["Lead", "Case"]
```

Inspect each `<autoResponseRule>` → `<ruleEntry>` for `<formula>` or
`<criteriaItems>` containing hardcoded values.

#### Consolidated findings for C8b

| Finding                                                      | Severity |
| ------------------------------------------------------------ | -------- |
| Approval entry/step criteria contains hardcoded Record ID(s) | HIGH     |
| Approval entry/step criteria contains hardcoded name(s)      | MEDIUM   |
| Escalation rule criteria contains hardcoded value(s)         | MEDIUM   |
| Assignment rule criteria contains hardcoded value(s)         | MEDIUM   |
| Auto-response rule criteria contains hardcoded value(s)      | MEDIUM   |

Write all C8b findings to
`./audit_output/intermediate/declarative_logic/other_rules.md` and persist
to `other_rules_findings.json`.

Update `audit_state.md`: mark C8b complete.

---

## Phase C9 — Completeness Gate (before reports)

Before proceeding to Phase D, verify that every **user-approved** domain is
complete. Read `audit_state.md` and check only the domains the user selected
in Phase B. (For a full audit, check all rows; for a selective audit like
"just Apex and Flows", check only the approved domains.)

| Domain       | Expected (from Phase A)        | Scored | Skipped | Carried Fwd | Match? |
| ------------ | ------------------------------ | ------ | ------- | ----------- | ------ |
| Apex Classes | {A1 local Apex class count}    | {n}    | {n}     | {n}         | Y/N    |
| Triggers     | {A1 local Apex trigger count}  | {n}    | {n}     | {n}         | Y/N    |
| Flows        | {A4 active Flow count}         | {n}    | {n}     | {n}         | Y/N    |
| LWC          | {A4 local LWC count}           | {n}    | {n}     | {n}         | Y/N    |
| Objects      | {A1 local custom object count} | {n}    | {n}     | {n}         | Y/N    |

Match = `Scored + Skipped + Carried Fwd == Expected`. (For fresh audits,
Carried Fwd is 0 for all rows.)

**If any approved-domain row shows "N", go back and score the missing
components before generating reports.** Domains the user excluded in Phase B
should be marked "Not audited" and do not block report generation.

---

## Phase D — Reports

Produce three report files in `./audit_output/`. See `references/report-template.md`
for brand tokens (Cirra AI blue `#417AE4`, cyan `#14DDDD`), HTML CSS, docx-js
patterns, and openpyxl patterns — follow it exactly for consistent output.
If the user provides their own template, use that instead — their template
always takes precedence over the default.

**For incremental audits:** include all components (changed + unchanged) in
reports. Mark each component's status:

- **Re-scored** — changed since last audit, freshly evaluated
- **Carried forward** — unchanged since last audit, previous score retained
- **New** — not in previous audit
- **Removed** — in previous audit but no longer in org

Include a delta summary section showing what changed between audits.

### Word report (`Salesforce_Org_Audit_Report.docx`)

Sections (in order):

1. Executive summary: org, date, full component inventory, overall health score
2. [If incremental] Delta summary: changes since previous audit
3. Apex Classes: scores ranked lowest to highest, top issues per class
4. Apex Triggers: inventory with findings
5. Flows: scores ranked lowest to highest, top issues per flow
6. Process Builders: inventory with migration priorities
7. LWC: scores ranked lowest to highest, top issues per component
8. Profiles & Permissions: hierarchy and findings by severity
9. Data Model: object scores ranked lowest to highest, field/relationship summary
10. Validation Rules: inventory with findings (including formula anti-patterns)
11. Formula Fields: inventory with hardcoded-value findings
12. Workflow Rules: inventory with migration priorities and formula findings
13. Other Declarative Logic: approval, escalation, assignment, and auto-response rule findings
14. Automation Overlap: objects with multiple automation types active
15. Hardcoded Values Summary: cross-cutting view of all hardcoded IDs, names, and URLs found across formulas, validation rules, workflow rules, and other logic
16. Top 10 recommendations across all domains

Mark any domain that was not fully scored (e.g. "quick pass only") as
"Surface metrics only — body not downloaded."

### Excel report (`Salesforce_Org_Audit_Scores.xlsx`)

One sheet per domain, plus a Summary sheet. Columns per domain:

- Apex Classes: Name, Score, API Version, Lines, Top Issues, Status
- Apex Triggers: Name, Object, Events, Findings, Severity, Status
- Flows: Name, ProcessType, Score, Top Issues, Status
- Process Builders: Name, Object, Criteria Count, Actions, Priority
- LWC: Name, Score, Category Breakdown, Top Issues, Status
- Profiles: Name, UserType, Key Permissions, Findings
- Permission Sets: Name, Label, Assignments, Findings, Severity
- Custom Objects: Name, Score, Field Count, Relationship Count, Top Issues
- Validation Rules: Name, Object, Active, Findings, Severity
- Formula Fields: Name, Object, DataType, Formula Length, Findings, Severity
- Workflow Rules: Name, Object, Action Types, Priority, Formula Findings
- Other Declarative Logic: Type, Name, Object, Findings, Severity
- Hardcoded Values: Component Type, Component Name, Value Found, Category (ID/Name/URL), Severity
- Summary: overall score, component counts, finding counts by severity,
  automation overlap matrix, [if incremental] delta summary

(Status column for incremental audits: Re-scored / Carried forward / New)

### HTML report (`Salesforce_Org_Audit_Report.html`)

Same content as Word, formatted for browser. Include:

- Score distribution visual (bar chart or table)
- Links to intermediate source files
- Collapsible PS/PSG hierarchy tree
- Automation overlap matrix table
- [If incremental] Delta highlight: colour-code changed vs unchanged rows

### Post-generation review

After all three reports are written, ask the user:

> "Reports are ready. Would you like to adjust the style, layout, or structure
> of any of the reports before we wrap up?"

If the user requests changes, regenerate only the affected report(s).

---

## Phase E — Summary to user

Tell the user:

- **Org inventory**: full counts for every category (including formula fields)
- **Overall health score**: weighted average across scored domains
- **Components needing attention**: count below 70, by domain
- **Permissions findings**: count by severity
- **Legacy automation**: active Workflow Rules and Process Builders count
- **Automation overlap warnings**: objects with multiple automation types
- **Hardcoded values found**: total count of hardcoded Record IDs, Campaign
  names, Profile names, URLs, and other fragile literals found across
  validation rules, formula fields, workflow rules, and other declarative logic
- **Top 3 most common issues per domain**
- **Skipped components**: what was skipped and why (generated classes,
  managed packages)
- [If incremental] **Delta summary**: what changed since last audit,
  score trends (improved / regressed / unchanged)
- **Where report files were saved**

Update `audit_state.md`: mark all phases complete.

---

## Routing reference

| Request                             | Skill            |
| ----------------------------------- | ---------------- |
| Fix or review an Apex class/trigger | `sf-apex`        |
| Fix or review a Flow                | `sf-flow`        |
| Fix or review an LWC component      | `sf-lwc`         |
| Fix a permission or Profile issue   | `sf-permissions` |
| Fix a metadata / data model issue   | `sf-metadata`    |
| Query or update data                | `sf-data`        |
| Visualize architecture or hierarchy | `sf-diagram`     |

## Build order (when fixing issues)

1. **Metadata** — fix data model issues first
2. **Permissions** — update Profiles, PSs, PSGs after metadata is correct
3. **Apex + Flows + LWC** — deploy in parallel if independent
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
- fetch_more — paginate through large responses with cursor (`mcp-core`
  mode; see `references/mcp-pagination.md`)

### Local execution tools

- Python 3 — for `pre_score.py` and `generate_reports.py` (Strategy A only)
- Salesforce CLI (`sf`) — for `cli` mode bulk retrieval and queries
- `jq` (optional) — for post-processing CLI JSON exports
- `git` — for `sfdx-repo` mode incremental delta detection

---

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed
by Cirra AI, Inc. The skill and its contents are provided independently and
are not part of the Cirra AI product itself.
