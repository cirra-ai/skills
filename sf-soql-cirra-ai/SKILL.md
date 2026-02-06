---
name: sf-soql
description: >
  Advanced SOQL skill with natural language to query generation, query optimization,
  relationship traversal, aggregate functions, and performance analysis. Build efficient
  queries that respect governor limits and security requirements. Powered by Cirra AI MCP Server.
license: MIT
metadata:
  version: "2.0.0"
  author: "Jag Valaiyapathy"
  migrated_to_cirra_ai: "2025-02"
  scoring: "100 points across 5 categories"
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "python3 ${SHARED_HOOKS}/scripts/guardrails.py"
          timeout: 5000
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "python3 ${SKILL_HOOKS}/post-tool-validate.py"
          timeout: 10000
        - type: command
          command: "python3 ${SHARED_HOOKS}/suggest-related-skills.py sf-soql"
          timeout: 5000
  SubagentStop:
    - type: command
      command: "python3 ${SHARED_HOOKS}/scripts/chain-validator.py sf-soql"
      timeout: 5000
---

# sf-soql: Salesforce SOQL Query Expert (Cirra AI Edition)

Expert database engineer specializing in Salesforce Object Query Language (SOQL). Generate optimized queries from natural language, analyze query performance, and ensure best practices for governor limits and security. This version uses the Cirra AI MCP Server for query execution instead of the Salesforce CLI.

## Core Responsibilities

1. **Natural Language → SOQL**: Convert plain English requests to optimized queries
2. **Query Execution**: Use Cirra AI tools to execute SOQL and Tooling API queries
3. **Query Optimization**: Analyze and improve query performance
4. **Relationship Queries**: Build parent-child and child-parent traversals
5. **Aggregate Functions**: COUNT, SUM, AVG, MIN, MAX with GROUP BY
6. **Security Enforcement**: Ensure FLS and sharing rules compliance
7. **Governor Limit Awareness**: Design queries within limits

## Workflow (4-Phase Pattern)

### Phase 1: Requirements Gathering

Use **AskUserQuestion** to gather:
- What data is needed (objects, fields)
- Filter criteria (WHERE conditions)
- Sort requirements (ORDER BY)
- Record limit requirements
- Use case (display, processing, reporting)

### Phase 2: Query Generation

**Natural Language Examples**:

| Request | Generated SOQL |
|---------|----------------|
| "Get all active accounts with their contacts" | `SELECT Id, Name, (SELECT Id, Name FROM Contacts) FROM Account WHERE IsActive__c = true` |
| "Find contacts created this month" | `SELECT Id, Name, Email FROM Contact WHERE CreatedDate = THIS_MONTH` |
| "Count opportunities by stage" | `SELECT StageName, COUNT(Id) FROM Opportunity GROUP BY StageName` |
| "Get accounts with revenue over 1M sorted by name" | `SELECT Id, Name, AnnualRevenue FROM Account WHERE AnnualRevenue > 1000000 ORDER BY Name` |

### Phase 3: Optimization

**Query Optimization Checklist**:

1. **Selectivity**: Does WHERE clause use indexed fields?
2. **Field Selection**: Only query needed fields (not SELECT *)
3. **Limit**: Is LIMIT appropriate for use case?
4. **Relationship Depth**: Avoid deep traversals (max 5 levels)
5. **Aggregate Queries**: Use for counts instead of loading all records

### Phase 4: Validation & Execution via Cirra AI

```python
# Initialize Cirra AI MCP Server (required first)
cirra_ai_init(sf_user="your-sf-user")

# Execute SOQL query using structured parameters
soql_query(
    sf_user="your-sf-user",
    sObject="Account",
    fields=["Id", "Name", "Industry"],
    whereClause="IsActive__c = true",
    limit=10
)

# Analyze query plan using Tooling API
tooling_api_query(
    sf_user="your-sf-user",
    sObject="QueryResource",
    fields=["query", "executionTime", "cardinality"],
    limit=1
)

# Describe object structure
sobject_describe(
    sf_user="your-sf-user",
    sObject="Account"
)
```

---

## Best Practices (100-Point Scoring)

| Category | Points | Key Rules |
|----------|--------|-----------|
| **Selectivity** | 25 | Indexed fields in WHERE, selective filters |
| **Performance** | 25 | Appropriate LIMIT, minimal fields, no unnecessary joins |
| **Security** | 20 | WITH SECURITY_ENFORCED or stripInaccessible |
| **Correctness** | 15 | Proper syntax, valid field references |
| **Readability** | 15 | Formatted, meaningful aliases, comments |

**Scoring Thresholds**:
```
⭐⭐⭐⭐⭐ 90-100 pts → Production-optimized query
⭐⭐⭐⭐   80-89 pts  → Good query, minor optimizations possible
⭐⭐⭐    70-79 pts   → Functional, performance concerns
⭐⭐      60-69 pts   → Basic query, needs improvement
⭐        <60 pts    → Problematic query
```

---

## SOQL Reference

### Basic Query Structure

```sql
SELECT field1, field2, ...
FROM ObjectName
WHERE condition1 AND condition2
ORDER BY field1 ASC/DESC
LIMIT number
OFFSET number
```

### Field Selection

```sql
-- Specific fields (recommended)
SELECT Id, Name, Industry FROM Account

-- All fields (avoid in Apex - use only in Developer Console)
SELECT FIELDS(ALL) FROM Account LIMIT 200

-- Standard fields only
SELECT FIELDS(STANDARD) FROM Account
```

### WHERE Clause Operators

| Operator | Example | Notes |
|----------|---------|-------|
| `=` | `Name = 'Acme'` | Exact match |
| `!=` | `Status != 'Closed'` | Not equal |
| `<`, `>`, `<=`, `>=` | `Amount > 1000` | Comparison |
| `LIKE` | `Name LIKE 'Acme%'` | Wildcard match |
| `IN` | `Status IN ('New', 'Open')` | Multiple values |
| `NOT IN` | `Type NOT IN ('Other')` | Exclude values |
| `INCLUDES` | `Interests__c INCLUDES ('Golf')` | Multi-select picklist |
| `EXCLUDES` | `Interests__c EXCLUDES ('Golf')` | Multi-select exclude |

### Date Literals

| Literal | Meaning |
|---------|---------|
| `TODAY` | Current day |
| `YESTERDAY` | Previous day |
| `THIS_WEEK` | Current week (Sun-Sat) |
| `LAST_WEEK` | Previous week |
| `THIS_MONTH` | Current month |
| `LAST_MONTH` | Previous month |
| `THIS_QUARTER` | Current quarter |
| `THIS_YEAR` | Current year |
| `LAST_N_DAYS:n` | Last n days |
| `NEXT_N_DAYS:n` | Next n days |

```sql
-- Created in last 30 days
SELECT Id FROM Account WHERE CreatedDate = LAST_N_DAYS:30

-- Modified this month
SELECT Id FROM Contact WHERE LastModifiedDate = THIS_MONTH
```

---

## Relationship Queries

### Child-to-Parent (Dot Notation)

```sql
-- Access parent fields
SELECT Id, Name, Account.Name, Account.Industry
FROM Contact
WHERE Account.AnnualRevenue > 1000000

-- Up to 5 levels
SELECT Id, Contact.Account.Owner.Manager.Name
FROM Case
```

### Parent-to-Child (Subquery)

```sql
-- Get parent with related children
SELECT Id, Name,
       (SELECT Id, FirstName, LastName FROM Contacts),
       (SELECT Id, Name, Amount FROM Opportunities WHERE StageName = 'Closed Won')
FROM Account
WHERE Industry = 'Technology'
```

### Relationship Names

| Object | Relationship Name | Example |
|--------|-------------------|---------|
| Account → Contacts | `Contacts` | `(SELECT Id FROM Contacts)` |
| Account → Opportunities | `Opportunities` | `(SELECT Id FROM Opportunities)` |
| Account → Cases | `Cases` | `(SELECT Id FROM Cases)` |
| Contact → Cases | `Cases` | `(SELECT Id FROM Cases)` |
| Opportunity → OpportunityLineItems | `OpportunityLineItems` | `(SELECT Id FROM OpportunityLineItems)` |

### Custom Object Relationships

```sql
-- Custom relationship: add __r suffix
SELECT Id, Name, Custom_Object__r.Name
FROM Another_Object__c

-- Child relationship: add __r suffix
SELECT Id, (SELECT Id FROM Custom_Children__r)
FROM Parent_Object__c
```

---

## Aggregate Queries

### Basic Aggregates

```sql
-- Count all records
SELECT COUNT() FROM Account

-- Count with alias
SELECT COUNT(Id) cnt FROM Account

-- Sum, Average, Min, Max
SELECT SUM(Amount), AVG(Amount), MIN(Amount), MAX(Amount)
FROM Opportunity
WHERE StageName = 'Closed Won'
```

### GROUP BY

```sql
-- Count by field
SELECT Industry, COUNT(Id)
FROM Account
GROUP BY Industry

-- Multiple groupings
SELECT StageName, CALENDAR_YEAR(CloseDate), COUNT(Id)
FROM Opportunity
GROUP BY StageName, CALENDAR_YEAR(CloseDate)
```

### HAVING Clause

```sql
-- Filter aggregated results
SELECT Industry, COUNT(Id) cnt
FROM Account
GROUP BY Industry
HAVING COUNT(Id) > 10
```

### GROUP BY ROLLUP

```sql
-- Subtotals
SELECT LeadSource, Rating, COUNT(Id)
FROM Lead
GROUP BY ROLLUP(LeadSource, Rating)
```

---

## Query Optimization

### Indexing Strategy

**Indexed Fields** (Always Selective):
- Id
- Name
- OwnerId
- CreatedDate
- LastModifiedDate
- RecordTypeId
- External ID fields
- Master-Detail relationship fields
- Lookup fields (when unique)

**Standard Indexed Fields by Object**:
- Account: AccountNumber, Site
- Contact: Email
- Lead: Email
- Case: CaseNumber
- Opportunity: -

### Selectivity Rules

```
A filter is selective when it returns:
- < 10% of total records for first 1 million
- < 5% of total records for additional records
- OR uses an indexed field
```

### Optimization Patterns

```sql
-- Non-selective (scans all records)
SELECT Id FROM Lead WHERE Status = 'Open'

-- Selective (uses index + selective filter)
SELECT Id FROM Lead
WHERE Status = 'Open'
AND CreatedDate = LAST_N_DAYS:30
LIMIT 10000

-- Leading wildcard (can't use index)
SELECT Id FROM Account WHERE Name LIKE '%corp'

-- Trailing wildcard (uses index)
SELECT Id FROM Account WHERE Name LIKE 'Acme%'
```

### Query Plan Analysis with Tooling API

```python
# Use Tooling API to analyze query performance
tooling_api_query(
    sf_user="your-sf-user",
    sObject="QueryResource",
    fields=["query", "cardinality", "executionTime"],
    limit=1
)
```

**Plan Output Interpretation**:
- `Cardinality`: Estimated rows returned
- `ExecutionTime`: Query execution time in milliseconds
- `Fields`: Index fields used
- `LeadingOperationType`: How the query starts (Index vs TableScan)

---

## Security Patterns

### WITH SECURITY_ENFORCED

```sql
-- Throws exception if user lacks FLS
SELECT Id, Name, Phone
FROM Account
WITH SECURITY_ENFORCED
```

### WITH USER_MODE / SYSTEM_MODE

```sql
-- Respects sharing rules (default in Apex)
SELECT Id, Name FROM Account WITH USER_MODE

-- Bypasses sharing rules (use with caution)
SELECT Id, Name FROM Account WITH SYSTEM_MODE
```

### In Apex: stripInaccessible

```apex
// Strip inaccessible fields instead of throwing
SObjectAccessDecision decision = Security.stripInaccessible(
    AccessType.READABLE,
    [SELECT Id, Name, SecretField__c FROM Account]
);
List<Account> safeAccounts = decision.getRecords();
```

---

## Governor Limits

| Limit | Synchronous | Asynchronous |
|-------|-------------|--------------|
| Total SOQL Queries | 100 | 200 |
| Records Retrieved | 50,000 | 50,000 |
| Query Rows (queryMore) | 2,000 | 2,000 |
| Query Locator Rows | 10 million | 10 million |

### Efficient Patterns

```sql
-- Query all, filter in Apex (inefficient)
SELECT Id, Name FROM Account
-- Then filter 50,000 records in Apex

-- Filter in SOQL (efficient)
SELECT Id, Name FROM Account
WHERE Industry = 'Technology' AND IsActive__c = true
LIMIT 1000

-- Multiple queries in loop (inefficient)
for (Contact c : contacts) {
    Account a = [SELECT Name FROM Account WHERE Id = :c.AccountId];
}

-- Single query with Map (efficient)
Map<Id, Account> accounts = new Map<Id, Account>(
    [SELECT Id, Name FROM Account WHERE Id IN :accountIds]
);
```

---

## SOQL FOR Loops

```apex
// For large datasets - doesn't load all into heap
for (Account acc : [SELECT Id, Name FROM Account WHERE Industry = 'Technology']) {
    // Process one record at a time
    // Governor: Uses queryMore internally (200 at a time)
}

// With explicit batch size
for (List<Account> accs : [SELECT Id, Name FROM Account]) {
    // Process 200 records at a time
}
```

---

## Advanced Features

### Polymorphic Relationships (What)

```sql
-- Query polymorphic fields
SELECT Id, What.Name, What.Type
FROM Task
WHERE What.Type IN ('Account', 'Opportunity')

-- TYPEOF for conditional fields
SELECT
    TYPEOF What
        WHEN Account THEN Name, Phone
        WHEN Opportunity THEN Name, Amount
    END
FROM Task
```

### Semi-Joins and Anti-Joins

```sql
-- Semi-join: Records that HAVE related records
SELECT Id, Name FROM Account
WHERE Id IN (SELECT AccountId FROM Contact)

-- Anti-join: Records that DON'T HAVE related records
SELECT Id, Name FROM Account
WHERE Id NOT IN (SELECT AccountId FROM Opportunity)
```

### Format in Aggregate Queries

```sql
-- Format currency/date in results
SELECT FORMAT(Amount), FORMAT(CloseDate)
FROM Opportunity
```

### convertCurrency()

```sql
-- Convert to user's currency
SELECT Id, convertCurrency(Amount)
FROM Opportunity
```

---

## Cirra AI MCP Server Tools

### Prerequisites

Call `cirra_ai_init` BEFORE using any other Cirra AI tools:

```python
cirra_ai_init(sf_user="your-salesforce-username")
```

### Core Tools

#### soql_query

Execute standard SOQL queries with structured parameters.

```python
soql_query(
    sf_user="your-sf-user",
    sObject="Account",              # Required: Object to query
    fields=["Id", "Name", "Phone"], # Optional: Fields to retrieve
    whereClause="IsActive__c = true AND Industry = 'Technology'",  # Optional
    limit=10,                        # Optional: Record limit
    orderBy="Name ASC"              # Optional: Sort order
)
```

**Important Difference from SF CLI**: The tool takes structured parameters instead of a raw SOQL string. Construct the query components and pass them separately.

#### tooling_api_query

Query the Tooling API for metadata and performance analysis.

```python
tooling_api_query(
    sf_user="your-sf-user",
    sObject="ApexClass",            # Tooling API object
    fields=["Id", "Name", "Body"],
    whereClause="NamespacePrefix = null",
    limit=50
)
```

#### sobject_describe

Get detailed metadata for a Salesforce object.

```python
sobject_describe(
    sf_user="your-sf-user",
    sObject="Account"
)
```

Returns: Field definitions, relationships, record types, validation rules, etc.

#### sobjects_list

List all available objects in the org.

```python
sobjects_list(
    sf_user="your-sf-user",
    customObjectsOnly=False
)
```

---

## Migration from SF CLI to Cirra AI

### Old: SF CLI Command
```bash
sf data query --query "SELECT Id, Name FROM Account WHERE IsActive__c = true" --target-org my-org
```

### New: Cirra AI MCP Server
```python
# Step 1: Initialize (only once per session)
cirra_ai_init(sf_user="username")

# Step 2: Execute query with structured parameters
soql_query(
    sf_user="username",
    sObject="Account",
    fields=["Id", "Name"],
    whereClause="IsActive__c = true"
)
```

### Key Changes

1. **Parameters are Structured**: Pass field lists, WHERE clauses, and ORDER BY separately instead of building raw SOQL strings
2. **Org Context**: Use `sf_user` parameter instead of `--target-org` flag
3. **Format is Implicit**: Results are returned as structured data, no need to specify `--json` or `--csv`
4. **Bulk Queries**: Use standard `soql_query` with appropriate LIMIT values
5. **Query Plan Analysis**: Use `tooling_api_query` instead of the CLI's `--use-tooling-api --plan` flags

---

## Best Practices for Cirra AI Integration

### 1. Always Initialize First
```python
cirra_ai_init(sf_user="your-username")
```

### 2. Use Structured Queries
```python
# Good: Structured parameters
soql_query(
    sf_user="user",
    sObject="Opportunity",
    fields=["Id", "Name", "Amount"],
    whereClause="StageName = 'Closed Won'",
    limit=100
)

# Avoid: Raw SOQL strings are not supported in the same way
```

### 3. Query Performance
```python
# Optimize selectivity - use indexed fields
soql_query(
    sf_user="user",
    sObject="Lead",
    fields=["Id", "Name", "Email"],
    whereClause="CreatedDate = LAST_N_DAYS:30 AND Status = 'Open'",
    limit=1000
)
```

### 4. Complex Queries
For queries with subqueries or complex relationships, build the SOQL string logically, then use the tool with the key components:

```python
# For complex SOQL with relationships
soql_query(
    sf_user="user",
    sObject="Account",
    fields=["Id", "Name"],
    whereClause="Id IN (SELECT AccountId FROM Contact WHERE Email LIKE '%@company.com')",
    limit=500
)
```

---

## Cross-Skill Integration

| Skill | When to Use | Example |
|-------|-------------|---------|
| sf-apex | Embed queries in Apex | `Skill(skill="sf-apex", args="Create service with SOQL query for accounts")` |
| sf-data | Execute queries against org | `Skill(skill="sf-data", args="Query active accounts from production")` |
| sf-debug | Analyze query performance | `Skill(skill="sf-debug", args="Analyze slow query in debug logs")` |
| sf-lwc | Generate wire queries | `Skill(skill="sf-lwc", args="Create component with wired account query")` |

---

## Natural Language Examples

| Request | Cirra AI Execution |
|---------|-------------------|
| "Get me all accounts" | `soql_query(sObject="Account", fields=["Id", "Name"], limit=1000)` |
| "Find contacts without email" | `soql_query(sObject="Contact", fields=["Id", "Name"], whereClause="Email = null")` |
| "Accounts created by John Smith" | `soql_query(sObject="Account", fields=["Id", "Name"], whereClause="CreatedBy.Name = 'John Smith'")` |
| "Top 10 opportunities by amount" | `soql_query(sObject="Opportunity", fields=["Id", "Name", "Amount"], orderBy="Amount DESC", limit=10)` |
| "Accounts in California" | `soql_query(sObject="Account", fields=["Id", "Name"], whereClause="BillingState = 'CA'")` |
| "Contacts with @gmail emails" | `soql_query(sObject="Contact", fields=["Id", "Name", "Email"], whereClause="Email LIKE '%@gmail.com'")` |
| "Opportunities closing this quarter" | `soql_query(sObject="Opportunity", fields=["Id", "Name", "CloseDate"], whereClause="CloseDate = THIS_QUARTER")` |
| "Cases opened in last 7 days" | `soql_query(sObject="Case", fields=["Id", "Subject"], whereClause="CreatedDate = LAST_N_DAYS:7")` |
| "Total revenue by industry" | `soql_query(sObject="Account", fields=["Industry", "SUM(AnnualRevenue)"], groupBy="Industry")` |
| "Count accounts by status" | `soql_query(sObject="Account", fields=["Status__c", "COUNT(Id)"], groupBy="Status__c")` |

---

## Dependencies

**Required**:
- Cirra AI MCP Server connection configured
- Salesforce org authenticated with Cirra AI

**Recommended**:
- sf-debug (for query performance analysis)
- sf-apex (for embedding in Apex code)

---

## Documentation

| Document | Description |
|----------|-------------|
| [soql-reference.md](docs/soql-reference.md) | Complete SOQL syntax reference |
| [cirra-ai-migration.md](docs/cirra-ai-migration.md) | Detailed migration guide from SF CLI |
| [anti-patterns.md](docs/anti-patterns.md) | Common mistakes and how to avoid them |
| [selector-patterns.md](docs/selector-patterns.md) | Query abstraction patterns (vanilla Apex) |
| [field-coverage-rules.md](docs/field-coverage-rules.md) | Ensure queries include all accessed fields (LLM mistake prevention) |

## Templates

| Template | Description |
|----------|-------------|
| [basic-queries.soql](templates/basic-queries.soql) | Basic SOQL syntax examples |
| [aggregate-queries.soql](templates/aggregate-queries.soql) | COUNT, SUM, GROUP BY patterns |
| [relationship-queries.soql](templates/relationship-queries.soql) | Parent-child traversals |
| [optimization-patterns.soql](templates/optimization-patterns.soql) | Selectivity and indexing |
| [selector-class.cls](templates/selector-class.cls) | Selector class template |
| [bulkified-query-pattern.cls](templates/bulkified-query-pattern.cls) | Map-based bulk lookups |

---

## Credits

See [CREDITS.md](CREDITS.md) for acknowledgments of community resources that shaped this skill.

Cirra AI integration and refactoring: February 2025

---

## License

MIT License. See [LICENSE](LICENSE) file.
Copyright (c) 2024-2025 Jag Valaiyapathy
