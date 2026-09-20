# sf-metadata

Salesforce metadata operations skill for AI coding tools. Create custom objects, fields, validation rules, record types, and permission sets directly in your org via the Cirra AI MCP Server.

## Features

- **Metadata Creation**: Create Custom Objects, Custom Metadata Types and Custom Settings, Fields, Validation Rules, Record Types, Global Value Sets, Permission Sets, List Views, Page Layouts, Lightning Pages (FlexiPages), Quick Actions, Custom Tabs, Custom Apps, and External Client App OAuth policies via MCP
- **Org Querying**: Describe objects, list fields, query metadata using Tooling API
- **Access Strategy**: Propose a specific, no-guesswork access plan after creating objects/fields/list views — exact profiles + permission sets for object/FLS access, page layouts, Lightning record pages, and list-view/Kanban visibility
- **Validation & Scoring**: Score metadata against 6 categories (0-120 points)

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Usage

#### Installation

Invoke the unified skill:

```
/sf-metadata
/sf-metadata create custom object Invoice__c
/sf-metadata describe Account
```

#### In other tools

Invoke the skill:

```
Skill: sf-metadata
Request: "Create a custom object called Invoice__c with Amount, Status, and Due Date fields"
```

### Common Operations

| Operation               | Example Request                                                              |
| ----------------------- | ---------------------------------------------------------------------------- |
| Create Object           | "Create a custom object called Inspection\_\_c"                              |
| Create Field            | "Add a Currency field called Amount\_\_c to Invoice\_\_c"                    |
| Create Validation       | "Add a validation rule requiring Close Date when Status is Closed"           |
| Describe Object         | "Describe the Account object and show all fields"                            |
| Create Permission Set   | "Generate a Permission Set for the Invoice\_\_c object"                      |
| Update ECA OAuth policy | "Pre-authorize the MCP_Client_User permission set on my External Client App" |

## Related Skills

| Skill          | When to Use                                        |
| -------------- | -------------------------------------------------- |
| sf-data        | Query, create records, build/optimize SOQL queries |
| sf-permissions | Analyze and audit permission sets                  |
| sf-apex        | Create Apex classes and triggers                   |
| sf-flow        | Create and validate Flows                          |

## Cirra AI MCP Tools — for developers

> This section is for Salesforce developers building integrations. Admins can skip it.

| Operation                    | MCP Tool                                                                                                                                                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Create custom object         | `sobject_create` (CMDT / Custom Settings: `metadata_create(type="CustomObject")`)                                                                                                                                                     |
| Create custom field          | `sobject_field_create` (grants connected-user FLS; never `metadata_create` for `CustomField`)                                                                                                                                         |
| Create record type           | `record_type_create` (layout assignment + profile availability)                                                                                                                                                                       |
| Create global value set      | `value_set_create`                                                                                                                                                                                                                    |
| Create other metadata        | `metadata_create(type, metadata)` — ValidationRule, PermissionSet, ListView, Layout, FlexiPage…                                                                                                                                       |
| Update metadata              | `sobject_update`, `sobject_field_update`, `record_type_update`, `value_set_update`, `page_layout_update`, `permission_set_update`, or `metadata_update(type, metadata \| fullName + patch)` — `metadata` replaces the whole component |
| Delete metadata              | `metadata_delete(type, fullNames)`                                                                                                                                                                                                    |
| Describe object              | `sobject_describe(sObject)`                                                                                                                                                                                                           |
| Discover / read metadata     | `metadata_describe`, `metadata_list(type)`, `metadata_read(type, fullNames, format)`                                                                                                                                                  |
| Query metadata (Tooling API) | `tooling_api_query(sObject="CustomField", fields=[...], whereClause="...")`                                                                                                                                                           |

Full signatures: [`shared/references/cirra-mcp-tools.md`](../../shared/references/cirra-mcp-tools.md).

## Execution Modes

| Mode                      | When                                              | Speed   |
| ------------------------- | ------------------------------------------------- | ------- |
| `sfdx-repo`               | Working directory is an SFDX project              | Fastest |
| `cli`                     | Salesforce CLI installed and authed               | Fast    |
| `mcp-plus-code-execution` | MCP + filesystem + code execution (Cowork, Codex) | Medium  |
| `mcp-core`                | MCP only, no filesystem (chat interfaces)         | Slowest |

All metadata operations go through MCP tools regardless of mode. The mode
determines how large responses are handled and whether local tooling is
available.

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
