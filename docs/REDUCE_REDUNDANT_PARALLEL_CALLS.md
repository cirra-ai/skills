# Reduce Redundant Parallel Salesforce API Calls

## Problem

During stress testing of the MCP server with Claude, the AI agent frequently issued 5+ parallel tool calls to Salesforce, causing timeouts. The pattern:

1. Agent needs permission set data -> fires `soql_query` for PermissionSet, PermissionSetGroup, ObjectPermissions, and User queries **all in parallel**
2. Each query is a separate MCP tool call -> separate HTTP request -> separate Salesforce API call
3. Salesforce rate limits and per-org API quotas throttle parallel calls
4. Later-completing calls exceed the client's 30s timeout

The same queries succeeded when run **sequentially** with no other calls in flight.

## Root Cause

The skills/prompts don't guide the agent on Salesforce API concurrency limitations. The agent treats SF queries like database queries that can be freely parallelized, but Salesforce has:
- Per-org API rate limits (typically 100K calls/24h, but concurrent call limits are much lower)
- Connection throttling under parallel load
- System objects (PermissionSet, User, Profile) that are inherently slow to query

## Recommended Changes

### 1. Add concurrency guidance to permission-related skills

Skills that query system objects (PermissionSet, PermissionSetGroup, User, Profile, ObjectPermissions) should include guidance like:

```
## Salesforce API Concurrency

When querying Salesforce system objects (PermissionSet, User, Profile, ObjectPermissions),
run queries SEQUENTIALLY rather than in parallel. These objects are large system tables
that respond slowly under concurrent load. Parallel queries to these objects frequently
cause timeouts.

For other objects (custom objects, Account, Contact, etc.), parallel queries are fine.
```

### 2. Consolidate related queries into fewer calls

Instead of 4 separate SOQL queries for permission analysis, guide the agent to:
- Use relationship queries (subqueries) to fetch related data in fewer calls
- Example: `SELECT Id, Name, (SELECT SobjectType, PermissionsRead FROM ObjectPerms) FROM PermissionSet WHERE Id IN (...)` instead of separate PermissionSet + ObjectPermissions queries

### 3. Add batch query patterns to SOQL skill

The SOQL/data skill should include patterns for efficiently querying related data:

```
## Efficient Multi-Object Queries

Instead of running separate queries for related objects, use:

1. **Relationship subqueries**: Include child records in the parent query
   SELECT Id, Name, (SELECT Field FROM ChildRelationship) FROM ParentObject

2. **Composite queries**: When objects aren't directly related, query the primary
   object first, then use the IDs in a single follow-up query with IN clause

3. **Sequential execution for system objects**: PermissionSet, User, Profile,
   and ObjectPermissions queries should run one at a time
```

## Files to Update

Look for skills/prompts related to:
- Permission analysis / permission set queries
- User management / user queries
- SOQL query building
- Any skill that might trigger multiple parallel SF queries

## Expected Impact

- Fewer timeout errors during permission analysis workflows
- More predictable query completion times
- Better utilization of Salesforce API quotas
