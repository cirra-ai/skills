# cirra-ai-sf-data

Salesforce data and SOQL expert skill for Claude Cowork and Claude Code. Build, optimize, and execute SOQL queries, manage data operations, generate test data, and validate operations via the Cirra AI MCP Server.

> **Note**: This skill incorporates all SOQL query capabilities (formerly cirra-ai-sf-soql). Use this skill for any SOQL-related work — building queries, optimizing them, or executing them.

## Features

- **Natural Language to SOQL**: Convert plain English requests to optimized queries
- **SOQL Query Building & Review**: Build, optimize, and validate queries — with or without executing them
- **Query Optimization**: Analyze selectivity, indexing, and performance
- **Relationship Queries**: Parent-child, child-parent, polymorphic, semi-joins, anti-joins
- **Aggregate Functions**: COUNT, SUM, AVG, MIN, MAX with GROUP BY
- **CRUD Operations**: Create, read, update, delete records via Cirra AI MCP Server
- **Test Data Factories**: Bulk-ready Apex factories for standard objects
- **Bulk Operations**: Insert/update/delete/upsert multiple records efficiently
- **Record Tracking & Cleanup**: Savepoint/rollback, cleanup scripts
- **Pre-Flight Validation**: Lightweight pass/fail checks for data operations (PII detection, missing params, syntax errors)

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Usage

#### In Claude Cowork or Claude Code

Use one of the pre-built commands

```
/insert-data
/query-data
```

#### In other tools

Invoke the skill:

```
Skill: cirra-ai-sf-data
Request: "Create 251 test Account records with varying Industries for trigger testing in my dev sandbox"
```

### Common Operations

| Operation        | Example Request                                          |
| ---------------- | -------------------------------------------------------- |
| Build Query      | "Write a SOQL query to get accounts with their contacts" |
| Optimize Query   | "Optimize this SOQL query for performance"               |
| Natural Language | "Who are our top 10 customers by revenue?"               |
| Execute Query    | "Query all Accounts with related Contacts"               |
| Create           | "Create 10 test Opportunities at various stages"         |
| Bulk Insert      | "Insert 500 accounts from accounts.csv"                  |
| Update           | "Update Account 001xxx with new Industry"                |
| Delete           | "Delete all test records with Name LIKE 'Test%'"         |
| Cleanup          | "Generate cleanup script for all records created today"  |

## Related Skills

| Skill                   | When to Use                                              |
| ----------------------- | -------------------------------------------------------- |
| cirra-ai-sf-apex        | Create and validate Apex code, triggers, test classes    |
| cirra-ai-sf-flow        | Create and validate Salesforce Flows                     |
| cirra-ai-sf-metadata    | Describe objects, fields, permission sets, profiles etc. |
| cirra-ai-sf-permissions | Permission analysis queries                              |
| cirra-ai-sf-diagram     | Visualize query results as diagrams                      |

## Cirra AI MCP Tools

| Operation | MCP Tool                                   |
| --------- | ------------------------------------------ |
| Query     | `soql_query(sObject, fields, whereClause)` |
| Create    | `sobject_dml(operation="insert", ...)`     |
| Update    | `sobject_dml(operation="update", ...)`     |
| Delete    | `sobject_dml(operation="delete", ...)`     |
| Upsert    | `sobject_dml(operation="upsert", ...)`     |
| Describe  | `sobject_describe(sObject)`                |
| Tooling   | `tooling_api_query(sObject, fields)`       |

## Validation Scripts

This skill ships Python validation scripts in `scripts/` for SOQL and data operation validation. These are available for manual use and can be integrated with plugin hooks.

### Available Scripts

| Script                       | Purpose                                                        |
| ---------------------------- | -------------------------------------------------------------- |
| `soql_validator.py`          | SOQL syntax validation, selectivity checks, optimization hints |
| `validate_data_operation.py` | 130-point data operation scoring across 7 categories           |
| `mcp_validator.py`           | MCP parameter validation (Tier 1 data, Tier 2 code)            |
| `mcp_validator_cli.py`       | CLI wrapper for manual pre-flight checks                       |
| `post-write-validate.py`     | Post-write hook for local file validation                      |

### SOQL Validator Checks

For `.soql` and `.apex` files containing SOQL, `soql_validator.py` checks:

| Check                    | What it catches                                                |
| ------------------------ | -------------------------------------------------------------- |
| Syntax errors            | Malformed SOQL                                                 |
| Missing WHERE            | Unbounded queries on large objects                             |
| Missing LIMIT            | Queries without limits that could hit governor limits          |
| Hardcoded IDs            | `WHERE Id = '001...'` — brittle, breaks on org refresh         |
| Non-indexed fields       | WHERE on non-indexed fields causing full table scans           |
| Optimization suggestions | SELECT \* patterns, missing ORDER BY, relationship query hints |

### Manual MCP pre-flight

Validate a data operation payload before calling the MCP tool:

```bash
echo '{"tool":"soql_query","params":{"sObject":"Account","fields":["Id","Name"],"whereClause":"Industry = '\''Technology'\''"}}' \
  | python scripts/mcp_validator_cli.py --format report
```

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
