---
name: build-query
description: Build a performance-optimized SOQL query with selectivity analysis and query tuning. Use /query for quick query execution without optimization guidance.
---

Build an optimized SOQL query via the Cirra AI MCP Server, with an explicit optimization pass for indexed field selection, limit sizing, wildcard patterns, and relationship consolidation. Use `/query` if you just need to run a query quickly without optimization guidance.

## Parsing the request

| Input after `/build-query`              | Interpretation                                               |
| --------------------------------------- | ------------------------------------------------------------ |
| `SELECT Id, Name FROM Account LIMIT 10` | Raw SOQL - execute directly                                  |
| `Account`                               | Object name - discover fields, ask what to query             |
| `open opportunities over $1M`           | Natural language - translate to SOQL, confirm before running |
| _(no argument)_                         | Ask the user what to query                                   |

## Workflow

### 1. Discover object structure (if needed)

If the user provided an object name or natural language, describe the object first:

```
sobject_describe(
  sObject="<ObjectName>",
  sf_user="<sf_user>"
)
```

Use field names and types from the response to build an accurate SOQL query.

### 2. Construct the query

- Use explicit field lists - avoid SELECT \* patterns
- Add appropriate `WHERE` clauses to filter results
- Add `LIMIT` to avoid returning excessive rows
- Use relationship traversal where it simplifies the query (e.g., `Account.Name` from Contact)
- For aggregate queries, include `GROUP BY` and appropriate aggregate functions

### 3. Optimize

Check the query against these optimization rules:

- **Selectivity**: Use indexed fields in WHERE (Id, Name, CreatedDate, Email, External IDs)
- **Field Selection**: Only query needed fields
- **Limit**: Appropriate LIMIT for the use case
- **Wildcards**: Trailing wildcards use indexes (`LIKE 'Acme%'`), leading wildcards don't
- **Relationships**: Combine related queries to reduce query count

### 4. Confirm before running (for large queries)

If the query has no `LIMIT` or the user asked for all records, confirm the scope before executing.

### 5. Execute

```
soql_query(
  sObject="<ObjectName>",
  fields=["Id", "Name", ...],
  whereClause="<filter>",
  orderBy="<sort>",
  limit=<n>,
  sf_user="<sf_user>"
)
```

### 6. Display results

- Show a summary: record count, object, key fields
- Display results as a table (truncate long field values)
- For large result sets, show the first 20 rows and note total count
- Suggest follow-up queries or refinements
