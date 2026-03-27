# sf-flow dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## create with explicit flow name

- **Input**: `/sf-flow create Auto_Lead_Assignment`
- **Dispatch**: Create Flow
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `sf_user: <default or prompted>`
- **Should call**: `sobject_describe`, `metadata_list`, `metadata_create`, `tooling_api_query`
- **Should NOT call**: `metadata_read`, `metadata_update`
- **Should ask user**: yes (gather flow type, trigger object, trigger event, primary purpose, and special requirements via AskUserQuestion)
- **Menu options**: n/a
- **Follow-up skills**: `sf-data`, `sf-metadata`

**Notes**: The `create` argument-hint routes directly to the Create Flow workflow. Init must be called before any MCP tool. The skill should check `metadata_list` first to confirm the flow doesn't already exist with this name. After deployment, `tooling_api_query` is required to verify the flow is not `InvalidDraft`. Should NOT call `metadata_read` or `metadata_update` because this is a new flow creation.

---

## create simple fast-path flow

- **Input**: `/sf-flow create Before_Contact_Default set the Email field to "noreply@example.com" if blank`
- **Dispatch**: Create Flow
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `sf_user: <default or prompted>`
- **Should call**: `sobject_describe`, `metadata_create`, `tooling_api_query`
- **Should NOT call**: `metadata_read`, `metadata_update`, `metadata_list`
- **Should ask user**: no (requirements are explicit and self-contained)
- **Menu options**: n/a
- **Follow-up skills**: `sf-data`

**Notes**: This is a single-field, before-save record-triggered flow with no ambiguity. The fast path applies: skip full 5-phase workflow and detailed requirements gathering, but still call `cirra_ai_init`, verify the Contact object via `sobject_describe`, run guardrail anti-pattern checks, deploy, and verify status. Full 110-point scoring is skipped; only guardrail checks apply.

---

## update with flow name and change description

- **Input**: `/sf-flow update Auto_Lead_Assignment add a fault path to the assignment step`
- **Dispatch**: Update Flow
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `sf_user: <default or prompted>`
- **Should call**: `metadata_read`, `metadata_update`, `tooling_api_query`
- **Should NOT call**: `metadata_create`, `metadata_list`
- **Should ask user**: no (flow name and change are explicit)
- **Menu options**: n/a
- **Follow-up skills**: `sf-data`

**Notes**: The `update` argument-hint with a named flow routes to Update Flow. The skill fetches the current XML via `metadata_read`, reviews the existing structure, applies the fault-path change, validates, then deploys via `metadata_update`. Must NOT call `metadata_create` — this is a modification, not a new deployment. Post-deployment `tooling_api_query` is required to check for `InvalidDraft`.

---

## validate single flow by API name

- **Input**: `/sf-flow validate Screen_Case_Intake`
- **Dispatch**: Validate Flow
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `sf_user: <default or prompted>`
- **Should call**: `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`, `sobject_describe`
- **Should ask user**: no (flow name is explicit)
- **Menu options**: n/a
- **Follow-up skills**: `sf-flow`

**Notes**: The `validate` argument-hint routes to Validate Flow. The skill fetches the flow XML via `metadata_read`, writes it to `/tmp/validate_Screen_Case_Intake.flow-meta.xml`, runs `validate_flow_cli.py`, then deletes the temp file. No deployment tools should be called. The output is a 110-point scored report across 6 categories. Offering `/sf-flow update` as a follow-up is appropriate if issues are found.

---

## no arguments — show menu

- **Input**: `/sf-flow`
- **Dispatch**: Ask the user (see below)
- **Init required**: no
- **Init timing**: after-menu
- **Path**: n/a
- **First tool**: n/a
- **Tool params**: n/a
- **Should call**: n/a (no tools called before user selects an option)
- **Should NOT call**: `cirra_ai_init`, `metadata_create`, `metadata_read`, `metadata_list`
- **Should ask user**: yes (present the three-option menu before taking any action)
- **Menu options**:
  1. **Create** — generate a new Flow
  2. **Update** — fetch, modify, validate, and redeploy
  3. **Validate** — score an existing Flow
- **Follow-up skills**: n/a

**Notes**: When `$ARGUMENTS` is empty, the skill must present the menu and wait for the user's selection before calling any tools, including `cirra_ai_init`. Init timing is `after-menu` — the skill only initializes after the user has chosen an action. No MCP calls should be made before a selection is confirmed.

---

## ambiguous natural language — infer create

- **Input**: `/sf-flow I need a flow that sends a Chatter post when an Opportunity is marked Closed Won`
- **Dispatch**: Create Flow
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `sf_user: <default or prompted>`
- **Should call**: `sobject_describe`, `metadata_list`, `metadata_create`, `tooling_api_query`
- **Should NOT call**: `metadata_read`, `metadata_update`
- **Should ask user**: yes (confirm trigger event — before/after save — and ask about entry conditions to prevent infinite loops on after-save flows)
- **Menu options**: n/a
- **Follow-up skills**: `sf-data`

**Notes**: Natural language without an explicit `create`/`update`/`validate` keyword should be parsed by intent. "I need a flow that…" clearly signals a new flow request, mapping to Create Flow. The full 5-phase workflow applies because entry conditions and trigger configuration need clarification. The guardrail check for after-save flows updating the same object must be applied. The skill should confirm entry conditions before generating to prevent the infinite-loop anti-pattern.

---

## validate all flows in org

- **Input**: `/sf-flow validate All`
- **Dispatch**: Validate Flow
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `sf_user: <default or prompted>`
- **Should call**: `metadata_list`, `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`, `sobject_describe`
- **Should ask user**: no
- **Menu options**: n/a
- **Follow-up skills**: `sf-flow`

**Notes**: The `All` keyword triggers a full-org audit. The skill first calls `metadata_list(type="Flow")` to retrieve all flow names, then fetches XML in batches of 20 via `metadata_read`. If a batch fails, the backoff strategy applies (retry with 10, then 5, then individual reads). Each flow is written to a temp file, validated, and the temp file is deleted. Output is a summary table sorted by score ascending (worst first), with flows below 88/110 highlighted as requiring attention.

---

## edge case — update without flow name

- **Input**: `/sf-flow update`
- **Dispatch**: Update Flow
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `sf_user: <default or prompted>`
- **Should call**: `metadata_list`, `metadata_read`, `metadata_update`, `tooling_api_query`
- **Should NOT call**: `metadata_create`
- **Should ask user**: yes (no flow name provided — must ask which flow to update and what changes are needed before fetching anything)
- **Menu options**: n/a
- **Follow-up skills**: `sf-data`

**Notes**: The `update` keyword is present but no flow API name follows. Per SKILL.md: "If no flow name is given, ask the user which flow to update and what changes are needed." The skill should call `cirra_ai_init` and then ask for the flow name before calling `metadata_read`. Optionally, `metadata_list` can be called first to present a list of existing flows for the user to choose from. Must not proceed to `metadata_read` or `metadata_update` until both the flow name and the desired changes are confirmed.

---

## validate a local flow file

- **Input**: `/sf-flow validate force-app/main/default/flows/Auto_Lead_Assignment.flow-meta.xml`
- **Dispatch**: Validate Flow
- **Init required**: no (local file — no org needed for validation)
- **Init timing**: `n/a`
- **Path**: `fast`
- **Should NOT call**: `cirra_ai_init`, `metadata_read`, `metadata_create`, `metadata_update`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Local file path ending in `.flow-meta.xml` means validate directly without fetching from org. The validation script runs locally. No MCP tools needed for pure local validation. Same fast path as sf-apex local file validation.

---

## validate comma-separated list

- **Input**: `/sf-flow validate Auto_Lead_Assignment,Screen_Case_Intake,Scheduled_Data_Cleanup`
- **Dispatch**: Validate Flow
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`, `sobject_describe`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Comma-separated list triggers bulk validation. Should fetch each flow's XML via `metadata_read`, validate each, and produce a summary table sorted by score ascending. Falls back to individual reads if batch fetch fails.

---

## review synonym for validate

- **Input**: `/sf-flow review Auto_Lead_Assignment`
- **Dispatch**: Validate Flow
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`, `sobject_describe`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: The dispatch table lists `review` as a synonym for `validate`. Should route to Validate Flow workflow — fetch the flow XML via `metadata_read`, run 110-point scoring, and return the report.

---

## create a screen flow

- **Input**: `/sf-flow create Case_Intake_Screen a screen flow for case submission with customer details`
- **Dispatch**: Create Flow
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `sobject_describe`, `metadata_list`, `metadata_create`, `tooling_api_query`
- **Should NOT call**: `metadata_read`, `metadata_update`
- **Should ask user**: no (flow type and purpose are explicit)
- **Follow-up skills**: `sf-data`, `sf-metadata`

**Notes**: `create` keyword with explicit flow name and description routes to Create Flow. The description mentions "screen flow" so the flow type is specified. Should check for existing flow via `metadata_list`, describe Case object via `sobject_describe`, generate screen flow XML with input screens and a DML element, deploy via `metadata_create`, and verify via `tooling_api_query`.

---

## create a scheduled flow

- **Input**: `/sf-flow create Nightly_Stale_Lead_Cleanup scheduled flow to close stale leads older than 90 days`
- **Dispatch**: Create Flow
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `sobject_describe`, `metadata_list`, `metadata_create`, `tooling_api_query`
- **Should NOT call**: `metadata_read`, `metadata_update`
- **Should ask user**: no (flow type and purpose are explicit)
- **Follow-up skills**: `sf-data`

**Notes**: `create` keyword with "scheduled flow" specifies the flow type. Should generate a Scheduled-Triggered Flow with a Get Records element filtering Leads by LastModifiedDate < 90 days ago, an Update Records element to set Status = 'Closed', and fault paths on both DML elements. Schedule configuration should be confirmed.

---

## score synonym for validate

- **Input**: `/sf-flow score Auto_Lead_Assignment`
- **Dispatch**: Validate Flow
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`, `sobject_describe`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: The dispatch table lists `score` as a synonym for `validate`. Should route to Validate Flow — same behavior as "validate single flow by API name".

---
