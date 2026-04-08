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

---

## create a custom object

- **Input**: `/sf-metadata create a custom object called Invoice__c with Status, Amount, and DueDate fields`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_create`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (object name and fields are specified)
- **Post-action**: FLS prompt — ask user which Permission Sets need access to the new object and fields
- **Follow-up skills**: `sf-permissions`, `sf-data`

**Notes**: `create` keyword with "custom object" routes to Create Metadata. Should create the object first via `metadata_create`, then create each field. Must prompt about FLS after field creation — new fields are invisible without Permission Set access.

---

## create a validation rule

- **Input**: `/sf-metadata create a validation rule on Account to require Phone when Industry is Technology`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `sobject_describe`, `metadata_create`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (requirements are clear)
- **Follow-up skills**: `sf-data`

**Notes**: `create` keyword with "validation rule" routes to Create Metadata. Should describe the Account object first to verify field API names (Phone, Industry), then create the ValidationRule via `metadata_create` with appropriate error condition formula and error message.

---

## update a field label

- **Input**: `/sf-metadata update the label on Account.CustomField__c to "Primary Contact Email"`
- **Dispatch**: Update Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `fast`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_update`
- **Should NOT call**: `metadata_create`, `metadata_delete`
- **Should ask user**: no (field and new label are specified)
- **Follow-up skills**: none

**Notes**: `update` keyword with specific field and new label routes to Update Metadata. Simple single-operation update — fast path applies. Should update the field's label via `metadata_update`.

---

## delete a custom field

- **Input**: `/sf-metadata delete Account.OldField__c`
- **Dispatch**: Delete Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_delete`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: yes (confirm before destructive operation)
- **Follow-up skills**: none

**Notes**: `delete` keyword with a field API name routes to Delete Metadata. Must confirm with the user before deleting — field deletion is destructive and may break reports, flows, and Apex code. Should warn about downstream dependencies.

---

## create a record type

- **Input**: `/sf-metadata create a record type on Case called Internal_Support for internal support cases`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `sobject_describe`, `metadata_create`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (object, name, and purpose are specified)
- **Follow-up skills**: `sf-permissions`

**Notes**: `create` keyword with "record type" routes to Create Metadata. Should describe the Case object first to verify it exists, then create the RecordType via `metadata_create`. May need to set up page layout assignment after creation.

---

## natural language — add a picklist field

- **Input**: `/sf-metadata add a picklist field called Priority__c on Opportunity with values High, Medium, Low`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `sobject_describe`, `metadata_create`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (all requirements are specified)
- **Post-action**: FLS prompt — ask user which Permission Sets need access to the new field
- **Follow-up skills**: `sf-permissions`

**Notes**: Natural language "add a field" maps to Create Metadata. The request includes field type (picklist), API name, object, and values. Should describe Opportunity to verify it exists, then create the CustomField via `metadata_create` with picklist values. Must prompt about FLS after creation.

---

## clone a page layout

- **Input**: `/sf-metadata clone the Account page layout to "CirraTest Account Layout"`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `fast`
- **First tool**: `cirra_ai_init`
- **Should call**: `page_layout_clone`
- **Should NOT call**: `metadata_create`, `metadata_delete`, `metadata_update`
- **Should ask user**: no (source and target are specified)
- **Follow-up skills**: none

**Notes**: "clone" with "page layout" routes to Create Metadata. The `page_layout_clone` tool handles layout duplication directly. Should verify the source layout exists before cloning. No FLS prompt needed — layouts don't affect field visibility.

---

## update a page layout — add fields

- **Input**: `/sf-metadata update the Account layout to add AnnualRevenue to the Information section`
- **Dispatch**: Update Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`, `page_layout_update`
- **Should NOT call**: `metadata_create`, `metadata_delete`
- **Should ask user**: no (field and section are specified)

**Notes**: "update" with "layout" routes to Update Metadata. Must `metadata_read` the layout first to discover the current structure (section indices, column indices), then use `page_layout_update` with a JSON Patch `add` operation. Fields already on the layout cause errors — check before adding.

---

## create a Lightning Record Page

- **Input**: `/sf-metadata create a Lightning Record Page for Account with highlights panel and record detail`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_create`
- **Tool params**: `type: FlexiPage`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (object and components are specified)
- **Follow-up skills**: none

**Notes**: "create" with "Lightning Record Page" routes to Create Metadata with type `FlexiPage`. Must set `type: RecordPage`, `sobjectType: Account`. Use `flexipage:recordHomeTemplateDesktop` template. Use `force:detailPanel` (not `force:recordDetail`). No FLS prompt needed.

---

## create a Lightning App Page

- **Input**: `/sf-metadata create a Lightning App Page called "Sales Dashboard" with a rich text header and list view`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_create`
- **Tool params**: `type: FlexiPage`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (name and components are specified)

**Notes**: "create" with "Lightning App Page" routes to Create Metadata with type `FlexiPage`. Must set `type: AppPage` — no `sobjectType` allowed. Use `flexipage:defaultAppHomeTemplate` template with region name `main`.

---

## create a Lightning Home Page

- **Input**: `/sf-metadata create a Lightning Home Page with an assistant and tasks list view`
- **Dispatch**: Create Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_create`
- **Tool params**: `type: FlexiPage`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (components are specified)

**Notes**: "create" with "Lightning Home Page" routes to Create Metadata with type `FlexiPage`. Must set `type: HomePage` — no `sobjectType` allowed. Use `home:desktopTemplate` template with regions: `top`, `bottomLeft`, `bottomRight`, `sidebar`.

---

## update a Lightning Page — add component

- **Input**: `/sf-metadata update CirraTest_Account_Record_Page to add a Chatter feed component`
- **Dispatch**: Update Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`, `metadata_update`
- **Tool params**: `type: FlexiPage`
- **Should NOT call**: `metadata_create`, `metadata_delete`
- **Should ask user**: no (page and component are specified)

**Notes**: "update" with a Lightning page name routes to Update Metadata. Must `metadata_read` the FlexiPage first to discover current regions and components, then `metadata_update` with the full `flexiPageRegions` array including the new component. Existing components must be preserved.

---

## update a page layout — complex multi-operation

- **Input**: `/sf-metadata update the Case layout: add a new Escalation section, add Account Name to Information, remove Internal Comments, and add Activities related list`
- **Dispatch**: Update Metadata
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `metadata_read`, `page_layout_update`
- **Should NOT call**: `metadata_create`, `metadata_delete`
- **Should ask user**: no (all changes are specified)

**Notes**: Multiple layout changes should be batched into a single `page_layout_update` call with a multi-operation JSON Patch array. Must `metadata_read` first to get current structure. The patch array should contain 4+ operations (add section, add field, remove field, add related list).
