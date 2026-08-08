## SOQL Query Building (with or without execution)

This skill helps build, review, and optimize SOQL queries even when you don't need to execute them. Use this when:

- A user asks "how would I query..." or "write me a SOQL query for..."
- Reviewing existing SOQL in Apex code or Flows
- Building queries for documentation or training materials

### Natural Language to SOQL

Parse user requests and translate to SOQL:

| Request                                        | Generated SOQL                                                                            |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------- |
| "Get all active accounts with their contacts"  | `SELECT Id, Name, (SELECT Id, Name FROM Contacts) FROM Account WHERE IsActive__c = true`  |
| "Find contacts created this month"             | `SELECT Id, Name, Email FROM Contact WHERE CreatedDate = THIS_MONTH`                      |
| "Count opportunities by stage"                 | `SELECT StageName, COUNT(Id) FROM Opportunity GROUP BY StageName`                         |
| "Top 10 opportunities by amount"               | `SELECT Id, Name, Amount FROM Opportunity ORDER BY Amount DESC LIMIT 10`                  |
| "Contacts without email"                       | `SELECT Id, Name FROM Contact WHERE Email = null`                                         |
| "Accounts with revenue over 1M sorted by name" | `SELECT Id, Name, AnnualRevenue FROM Account WHERE AnnualRevenue > 1000000 ORDER BY Name` |

### Query Optimization Checklist

When building or reviewing SOQL queries:

1. **Selectivity**: Does WHERE clause use indexed fields? (Id, Name, CreatedDate, Email, External IDs)
2. **Field Selection**: Only query needed fields (never use SELECT \* patterns)
3. **Limit**: Is LIMIT appropriate for the use case?
4. **Relationship Depth**: Avoid deep traversals (max 5 levels)
5. **Aggregate vs Full Load**: Use aggregates for counts instead of loading all records

**Key Rules**:

- Trailing wildcards use indexes (`LIKE 'Acme%'`), leading wildcards don't (`LIKE '%corp'`)
- Filter in SOQL, not after retrieval
- Use `LIMIT` appropriate to use case
- Combine queries using relationships to reduce query count

### SOQL Anti-Patterns (Quick Reference)

| Anti-Pattern                        | Fix                                          |
| ----------------------------------- | -------------------------------------------- |
| SELECT \* (all fields)              | List only needed fields                      |
| No WHERE clause on large objects    | Add filters to reduce result set             |
| No LIMIT clause                     | Add appropriate LIMIT for use case           |
| Leading wildcard (`LIKE '%corp'`)   | Use trailing wildcard (`LIKE 'Acme%'`)       |
| Query in a loop                     | Collect IDs first, query once with IN clause |
| Hardcoded record IDs                | Use named references or external IDs         |
| Non-indexed field in WHERE          | Use indexed fields (Id, Name, CreatedDate)   |
| Negative operators (`!=`, `NOT IN`) | Query for what you want, not what you don't  |
| Formula fields in WHERE             | Use the underlying indexed field             |

### SOQL Query Scoring (100 Points)

| Category        | Points | Key Rules                                               |
| --------------- | ------ | ------------------------------------------------------- |
| **Selectivity** | 25     | Indexed fields in WHERE, selective filters              |
| **Performance** | 25     | Appropriate LIMIT, minimal fields, no unnecessary joins |
| **Security**    | 20     | WITH SECURITY_ENFORCED or USER_MODE where applicable    |
| **Correctness** | 15     | Proper syntax, valid field references                   |
| **Readability** | 15     | Formatted, meaningful structure                         |

**Thresholds**: 90-100 Production-optimized | 80-89 Good | 70-79 Performance concerns | <70 Needs improvement

**Exemption for trivial queries**: Ad-hoc queries, exploratory data inspection, and test queries are exempt from scoring thresholds. Score them for informational purposes but do not flag performance concerns for interactive one-off queries. Governor limits protect the org.

---
