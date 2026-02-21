# cirra-ai-sf-metadata

Salesforce metadata operations skill for Claude Cowork and Claude Code. Create custom objects, fields, validation rules, record types, and permission sets directly in your org via the Cirra AI MCP Server.

## Features

- **Metadata Creation**: Create Custom Objects, Fields, Validation Rules, Record Types via MCP
- **Org Querying**: Describe objects, list fields, query metadata using Tooling API
- **FLS Management**: Auto-generate Permission Sets after creating objects/fields
- **Validation & Scoring**: Score metadata against 6 categories (0-120 points)

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Usage

#### In Claude Cowork or Claude Code

Use one of the pre-built commands

```
/create-metadata
/describe-object
```

#### In other tools

Invoke the skill:

```
Skill: cirra-ai-sf-metadata
Request: "Create a custom object called Invoice__c with Amount, Status, and Due Date fields"
```

### Common Operations

| Operation | Example Request |
| --------- | ------------------------------------------------------- |
| Create Object | "Create a custom object called Inspection__c" |
| Create Field | "Add a Currency field called Amount__c to Invoice__c" |
| Create Validation | "Add a validation rule requiring Close Date when Status is Closed" |
| Describe Object | "Describe the Account object and show all fields" |
| Create Permission Set | "Generate a Permission Set for the Invoice__c object" |

## Related Skills

| Skill | When to Use |
| -------------------- | -------------------------------------------------------- |
| cirra-ai-sf-data | Query and create records for objects |
| cirra-ai-sf-permissions | Analyze and audit permission sets |
| cirra-ai-sf-soql | Build and optimize SOQL queries |
| cirra-ai-sf-apex | Create Apex classes and triggers |
| cirra-ai-sf-flow | Create and validate Flows |

## Cirra AI MCP Tools

| Operation | MCP Tool |
| --------- | ------------------------------------------ |
| Create Metadata | `metadata_create(type, metadata)` |
| Update Metadata | `metadata_update(type, metadata)` |
| Describe Object | `sobject_describe(sObject)` |
| Query Metadata | `tooling_api_query(sObject, fields)` |

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
