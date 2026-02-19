---
name: query
description: Execute a SOQL query against a Salesforce org. Accepts a natural language description, a SOQL string, or an object name to query. Guides through field discovery and displays paginated results.
---

Run a SOQL query via the Cirra AI MCP Server and display the results.

## Parsing the request

| Input after `/query` | Interpretation |
|---|---|
| `SELECT Id, Name FROM Account LIMIT 10` | Raw SOQL — execute directly |
| `Account` | Object name — ask what fields/filters to apply |
| `open opportunities over $1M` | Natural language — translate to SOQL, confirm before running |
| *(no argument)* | Ask the user what to query |

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

- Use explicit field lists — avoid `SELECT *` patterns
- Add appropriate `WHERE` clauses and `LIMIT` to avoid returning excessive rows
- Use relationship traversal where it simplifies the query (e.g. `Account.Name` from Contact)
- For aggregate queries, include `GROUP BY` and appropriate aggregate functions

### 3. Confirm before running (for large or destructive queries)

If the query has no `LIMIT` or the user asked for all records, confirm the scope before executing.

### 4. Execute

```
soql_query(
  sObject="<ObjectName>",
  fields=["Id", "Name", ...],
  whereClause="<filter>",
  limit=<n>,
  sf_user="<sf_user>"
)
```

### 5. Display results

- Show a summary: record count, object, key fields
- Display results as a table (truncate long field values)
- For large result sets, show the first 20 rows and note total count
- Provide a cleanup query if test data was the subject
