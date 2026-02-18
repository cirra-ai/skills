# cirra-ai-sf-data

Salesforce data operations skill for Claude Code. Provides SOQL expertise, test data factories, bulk operations, and pre-flight validation for data operations.

## Features

- **CRUD Operations**: Create, read, update, delete records via Cirra AI MCP Server
- **SOQL Expertise**: Complex relationship queries, polymorphic fields, aggregations
- **Test Data Factories**: Bulk-ready Apex factories for standard objects
- **Bulk Operations**: Import/export via Bulk API 2.0
- **Record Tracking & Cleanup**: Savepoint/rollback, cleanup scripts
- **Pre-Flight Validation**: Lightweight pass/fail checks for data operations (PII detection, missing params, syntax errors)

## Installation

```bash
# Install standalone
claude /plugin install github:cirra-ai/skills/cirra-ai-sf-data

# Or install the complete Cirra AI skills suite
claude /plugin install github:cirra-ai/skills
```

## Usage

Invoke the skill:

```
Skill(skill="cirra-ai-sf-data")
Request: "Create 251 test Account records with varying Industries for trigger testing in org dev"
```

### Common Operations

| Operation   | Example Request                                         |
| ----------- | ------------------------------------------------------- |
| Query       | "Query all Accounts with related Contacts in org dev"   |
| Create      | "Create 10 test Opportunities at various stages"        |
| Bulk Insert | "Insert 500 accounts from accounts.csv"                 |
| Update      | "Update Account 001xxx with new Industry"               |
| Delete      | "Delete all test records with Name LIKE 'Test%'"        |
| Cleanup     | "Generate cleanup script for all records created today" |

## Related Skills

| Skill | When to Use |
| --- | --- |
| cirra-ai-sf-apex | Generate Apex code, triggers, test classes (with 150-point scoring) |
| cirra-ai-sf-flow | Create and validate Salesforce Flows (with 110-point scoring) |
| cirra-ai-sf-metadata | Describe objects, create custom fields, Permission Sets |

## Cirra AI MCP Tools

| Operation   | MCP Tool                                       |
| ----------- | ---------------------------------------------- |
| Query       | `soql_query(sObject, fields, whereClause)`     |
| Create      | `sobject_dml(operation="insert", ...)`         |
| Update      | `sobject_dml(operation="update", ...)`         |
| Delete      | `sobject_dml(operation="delete", ...)`         |
| Upsert      | `sobject_dml(operation="upsert", ...)`         |
| Describe    | `sobject_describe(sObject)`                    |
| Tooling     | `tooling_api_query(sObject, fields)`           |

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
