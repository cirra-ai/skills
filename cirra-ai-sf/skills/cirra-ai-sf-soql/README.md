# cirra-ai-sf-soql

Salesforce SOQL query expert skill for Claude Cowork and Claude Code. Build optimized SOQL queries from natural language, execute them, and get results via the Cirra AI MCP Server.

## Features

- **Natural Language to SOQL**: Convert plain English to optimized queries
- **Query Execution**: Run queries directly against the org
- **Query Optimization**: Analyze and improve query performance
- **Relationship Queries**: Parent-child and child-parent traversals
- **Aggregate Functions**: COUNT, SUM, AVG, MIN, MAX with GROUP BY

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Usage

#### In Claude Cowork or Claude Code

Use the pre-built command

```
/build-query
```

#### In other tools

Invoke the skill:

```
Skill: cirra-ai-sf-soql
Request: "Show me all opportunities closing this quarter with amount over $100K"
```

### Common Operations

| Operation | Example Request |
| --------- | ------------------------------------------------------- |
| Simple Query | "Get all active accounts" |
| Relationship | "Get accounts with their contacts" |
| Aggregate | "Count opportunities by stage" |
| Optimization | "Optimize this SOQL query for performance" |
| Natural Language | "Who are our top 10 customers by revenue?" |

## Related Skills

| Skill | When to Use |
| -------------------- | -------------------------------------------------------- |
| cirra-ai-sf-data | For DML operations (insert, update, delete) |
| cirra-ai-sf-metadata | For object discovery before querying |
| cirra-ai-sf-permissions | For permission-related queries |

## Cirra AI MCP Tools

| Operation | MCP Tool |
| --------- | ------------------------------------------ |
| Execute Query | `soql_query(sObject, fields, whereClause)` |
| Describe Object | `sobject_describe(sObject)` |
| Tooling Query | `tooling_api_query(sObject, fields)` |

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
