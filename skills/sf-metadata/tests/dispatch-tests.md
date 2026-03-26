# sf-metadata dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## describe PermissionSet

- **Input**: `/sf-metadata describe PermissionSet`
- **Dispatch**: Describe Object
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `sobject_describe`
- **Tool params**: `sObject: PermissionSet`
- **Should NOT call**: `metadata_create`, `metadata_update`, `metadata_delete`
- **Should ask user**: no
- **Follow-up skills**: `sf-data`, `sf-permissions`, `sf-diagram`

**Notes**: Direct keyword match on `describe`. The object name `PermissionSet` is a standard object — should be passed through to `sobject_describe` without modification. Expect structured output showing fields and settings. Single, unambiguous operation qualifies for fast path.

---

## create a custom field on Account

- **Input**: `/sf-metadata create a currency field called AnnualBudget on Account`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast (single field, unambiguous)
- **First tool**: `sobject_describe`
- **Tool params**: `sObject: Account`
- **Should call**: `metadata_create`
- **Should NOT call**: `metadata_update`, `metadata_delete`, `tooling_api_dml`
- **Should ask user**: no (requirements are clear), but must prompt for FLS after creation
- **Post-action**: prompt for Permission Set generation (FLS)
- **Follow-up skills**: `sf-data`, `sf-permissions`

**Notes**: The `create` keyword routes to Create Metadata. Even though the user gave all details, the workflow should first describe the target object to verify the field doesn't already exist, then call `metadata_create` with type `CustomField`. After creation, must prompt about FLS — deployed fields are invisible without it. Fast path applies: single, unambiguous metadata operation.

---

## update a validation rule

- **Input**: `/sf-metadata update`
- **Dispatch**: Update Metadata
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (target not specified, needs discovery)
- **Should ask user**: yes (no target specified)
- **Should NOT call**: `metadata_create`, `metadata_delete`

**Notes**: The `update` keyword matches but no target is given. The workflow should ask what metadata component to update before proceeding with `sobject_describe` or `tooling_api_query` to discover current state.

---

## delete a custom object

- **Input**: `/sf-metadata delete MyCustomObject__c`
- **Dispatch**: Delete Metadata
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (destructive — always confirm)
- **Should call**: `metadata_delete`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (confirm before destructive operation)

**Notes**: `delete` keyword routes correctly. The workflow MUST confirm with the user before executing — this is a destructive operation. The `metadata_delete` call needs the metadata type and fullName.

---

## no arguments — show menu

- **Input**: `/sf-metadata`
- **Dispatch**: (none — present menu)
- **Init required**: no
- **Init timing**: after-menu (defer init until workflow selected)
- **Path**: n/a
- **Should ask user**: yes
- **Menu options**: Create, Update, Delete, Describe

**Notes**: No arguments means unclear intent. The skill should present the numbered menu with all four options. No MCP tools should be called before the user picks an option. Init is deferred until a workflow is selected — no point initializing a session without knowing what to do.

---

## ambiguous intent

- **Input**: `/sf-metadata PermissionSet`
- **Dispatch**: (ambiguous — could be describe or create)
- **Init required**: no
- **Init timing**: after-menu (defer until intent clarified)
- **Path**: n/a
- **Should ask user**: yes

**Notes**: Just an object name with no verb. The dispatch table doesn't have a direct match for bare object names. The skill should ask whether the user wants to describe, create fields on, update, or delete the object.

---

## describe all custom objects

- **Input**: `/sf-metadata describe all custom objects`
- **Dispatch**: Describe Object
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (multi-step: list then describe)
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: CustomObject`
- **Should NOT call**: `metadata_create`, `metadata_update`, `metadata_delete`
- **Should ask user**: no

**Notes**: The `describe` keyword routes correctly. The "all custom objects" qualifier means list all custom objects first (via `tooling_api_query`), then let the user pick which to describe in detail. This follows the parsing table in the Describe Object workflow.
