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
