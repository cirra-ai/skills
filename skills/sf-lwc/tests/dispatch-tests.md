# sf-lwc dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## create with explicit argument

- **Input**: `/sf-lwc create accountSummaryCard`
- **Dispatch**: Create LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `tooling_api_query`, `metadata_create`
- **Should NOT call**: `metadata_update`, `metadata_read`, `metadata_list`
- **Should ask user**: yes (gather requirements: purpose, target placement, data source, target objects, special requirements)
- **Follow-up skills**: `sf-apex`

**Notes**: Full PICKLES workflow applies because no detail about data binding or complexity is given. The skill checks for an existing component via `tooling_api_query` before generating the bundle. `cirra_ai_init` is always called first.

---

## create fast-path simple component

- **Input**: `/sf-lwc create helloWorldBanner`
- **Dispatch**: Create LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `tooling_api_query`, `metadata_create`
- **Should NOT call**: `metadata_update`, `metadata_read`
- **Should ask user**: no (component name and intent are unambiguous; static display component qualifies for fast path)
- **Follow-up skills**: `sf-apex`

**Notes**: A "hello world" banner is a static display component with no data binding, qualifying for the fast path. Basic accessibility and no-hardcoded-colors checks still apply; full 165-point PICKLES scoring is skipped.

---

## update with component name and change description

- **Input**: `/sf-lwc update contactCard fix dark mode colors`
- **Dispatch**: Update LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `metadata_read`, `metadata_update`
- **Should NOT call**: `metadata_create`, `tooling_api_query`, `metadata_list`
- **Should ask user**: no (component name and requested change are both present)
- **Follow-up skills**: `sf-apex`

**Notes**: `metadata_read` retrieves the current bundle before modifications. After applying the dark-mode CSS fix, each modified file is validated with `validate_slds.py` before `metadata_update` deploys the result.

---

## update missing component name

- **Input**: `/sf-lwc update`
- **Dispatch**: Update LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `metadata_read`, `metadata_update`
- **Should NOT call**: `metadata_create`
- **Should ask user**: yes (no component name provided; must ask which component to update and what changes are needed)
- **Follow-up skills**: `sf-apex`

**Notes**: Edge case — the argument string after `update` is empty. The skill must prompt the user for both the component name and the desired changes before proceeding.

---

## validate single component by name

- **Input**: `/sf-lwc validate accountDashboard`
- **Dispatch**: Validate LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`, `metadata_list`
- **Should ask user**: no (component name is explicit)
- **Follow-up skills**: `sf-apex`

**Notes**: Single-component validation. After `metadata_read`, bundle files are written to `/tmp/validate_accountDashboard/`, each file is passed to `validate_slds.py`, then the temp directory is deleted. A combined per-category score report is shown.

---

## validate all components

- **Input**: `/sf-lwc validate All`
- **Dispatch**: Validate LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `metadata_list`, `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: no (the keyword `All` is an explicit known input)
- **Follow-up skills**: `sf-apex`

**Notes**: Edge case for bulk validation. `metadata_list` retrieves all LightningComponentBundle records, then bundles are fetched and validated in batches of 10. Components averaging below 100/165 (61%) are flagged. If a batch read fails, the skill falls back to individual `metadata_read` calls.

---

## no arguments — show menu

- **Input**: `/sf-lwc`
- **Dispatch**: Ask the user (see below)
- **Init required**: no
- **Init timing**: after-menu
- **Path**: n/a
- **First tool**: n/a (no MCP tools called before user selects)
- **Should NOT call**: `cirra_ai_init`, `metadata_create`, `metadata_read`, `metadata_update`, `metadata_list`
- **Should ask user**: yes (no argument provided; the dispatch table explicitly routes to the menu)
- **Menu options**: 1. Create — scaffold a new Lightning Web Component, 2. Update — fetch, modify, validate, and redeploy, 3. Validate — score an existing LWC
- **Follow-up skills**: `sf-apex`

**Notes**: `cirra_ai_init` must NOT be called before the user selects an option. Init timing is `after-menu` — once the user picks a workflow, init runs as the first step of that workflow.

---

## natural language ambiguous request

- **Input**: `/sf-lwc I need a component that shows related contacts for an account`
- **Dispatch**: Create LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `tooling_api_query`, `sobject_describe`, `metadata_create`
- **Should NOT call**: `metadata_update`, `metadata_list`
- **Should ask user**: yes (intent maps to create but requirements are underspecified — placement, data source (likely GraphQL for related records), and component name are all missing)
- **Follow-up skills**: `sf-apex`

**Notes**: Natural-language phrasing with no explicit `create` keyword. The intent is clearly a new component, so dispatch routes to Create LWC. Because it involves related records and cross-object data, the full PICKLES workflow applies. `sobject_describe` may be called to understand the Account-Contact relationship before generating wire adapters.

---

## validate a local file

- **Input**: `/sf-lwc validate force-app/main/default/lwc/accountCard/accountCard.js`
- **Dispatch**: Validate LWC
- **Init required**: no (local file — no org needed for validation)
- **Init timing**: `n/a`
- **Path**: `fast`
- **Should NOT call**: `cirra_ai_init`, `metadata_read`, `metadata_list`, `tooling_api_query`
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: Local file path means validate directly without fetching from org. The validation script runs locally. No MCP tools needed for pure local validation. Should detect the component directory from the file path and validate the entire bundle if other files exist alongside it.

---

## review synonym for validate

- **Input**: `/sf-lwc review contactDashboard`
- **Dispatch**: Validate LWC
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: no
- **Follow-up skills**: `sf-lwc`

**Notes**: The dispatch table lists `review` as a synonym for `validate`. Should route to Validate LWC — fetch the component bundle via `metadata_read`, run 165-point SLDS 2 scoring, and return the report.

---

## create with wire service data binding

- **Input**: `/sf-lwc create opportunityList a component that displays opportunities using wire service`
- **Dispatch**: Create LWC
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `metadata_create`, `sobject_describe`
- **Should NOT call**: `metadata_read`, `metadata_update`
- **Should ask user**: no (requirements are explicit — wire service, Opportunity data)
- **Follow-up skills**: `sf-data`, `sf-metadata`

**Notes**: `create` with explicit component name and wire service mention routes to Create LWC. Should describe the Opportunity object via `sobject_describe` to get field metadata. The component should use `@wire` with `getRecord` or a custom Apex method. Full PICKLES workflow applies since this involves data integration.

---

## score synonym for validate

- **Input**: `/sf-lwc score accountSummaryCard`
- **Dispatch**: Validate LWC
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: no
- **Follow-up skills**: `sf-lwc`

**Notes**: The dispatch table lists `score` as a synonym for `validate`. Should route to Validate LWC — same behavior as "validate single component by name".

---

## validate comma-separated list

- **Input**: `/sf-lwc validate accountCard,contactList,opportunityDashboard`
- **Dispatch**: Validate LWC
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`
- **Should NOT call**: `metadata_create`, `metadata_update`, `sobject_describe`
- **Should ask user**: no
- **Follow-up skills**: `sf-lwc`

**Notes**: Comma-separated list triggers bulk validation. Should fetch each component's bundle via `metadata_read`, validate each with 165-point SLDS 2 scoring, and produce a summary table sorted by score ascending. Flags components below 100/165 (61%).

---

## create for flow screen integration

- **Input**: `/sf-lwc create caseIntakeForm a screen component for Flow that collects customer case details`
- **Dispatch**: Create LWC
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `metadata_create`, `sobject_describe`
- **Should NOT call**: `metadata_read`, `metadata_update`
- **Should ask user**: no (requirements are clear — Flow screen component)
- **Follow-up skills**: `sf-flow`, `sf-metadata`

**Notes**: `create` with "screen component for Flow" routes to Create LWC. The meta.xml must include `lightning__FlowScreen` target. Should use `@api` properties for Flow input/output and follow the Flow Screen Integration pattern from SKILL.md. Full PICKLES workflow applies.

---

## deployment payload format — create

- **Input**: `/sf-lwc create cirraTestPayloadCheck a simple card that displays a greeting`
- **Dispatch**: Create LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `metadata_create`
- **Should NOT call**: `metadata_update`, `metadata_read`
- **Should ask user**: no
- **Payload format**: The `metadata_create` call MUST use the `lwcResources` structure with `lwcResource` array entries containing `filePath` and Base64-encoded `source`. It MUST NOT use shorthand keys like `html`, `css`, `js`, or `meta` at the top level of the metadata object.
- **Follow-up skills**: `sf-apex`

**Notes**: This test validates the deployment payload format, not just routing. The `metadata_create` Metadata API for LightningComponentBundle requires `lwcResources.lwcResource[]` with Base64-encoded sources — not shorthand top-level keys (`html`, `css`, `js`, `meta`) with raw content. Phase 2 must inspect the constructed `metadata_create` call and verify: (1) a `lwcResources` key exists with a nested `lwcResource` array, (2) each resource has `filePath` (e.g., `lwc/cirraTestPayloadCheck/cirraTestPayloadCheck.js`) and `source` (Base64 string), (3) no top-level `html`, `css`, `js`, or `meta` keys exist on the metadata object. Shorthand keys are a FAIL — this was the exact defect fixed in PR #101.

---

## deployment payload format — update

- **Input**: `/sf-lwc update cirraTestPayloadCheck add a subtitle property`
- **Dispatch**: Update LWC
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`, `metadata_update`
- **Should NOT call**: `metadata_create`, `tooling_api_query`
- **Should ask user**: no
- **Payload format**: The `metadata_update` call MUST use the `lwcResources` structure with Base64-encoded sources. It MUST NOT use shorthand `html`/`css`/`js`/`meta` keys.
- **Follow-up skills**: `sf-apex`

**Notes**: Same payload format validation as the create test, but for `metadata_update`. Phase 2 must verify the `metadata_update` call uses `lwcResources.lwcResource[]` with Base64-encoded `source` fields, not the incorrect shorthand format.
