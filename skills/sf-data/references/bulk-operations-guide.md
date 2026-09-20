# Bulk Operations Guide

How to move more than a few hundred records in or out of an org through the
Cirra AI MCP Server. Two tools wrap Salesforce **Bulk API 2.0**:

- `bulk_dml` — insert, update, upsert, delete, hardDelete (ingest jobs)
- `bulk_query` — large extracts (query jobs)

Both are asynchronous: the tool submits the job, waits up to **90 seconds**,
and either returns the finished result or a `jobId` you pass back to keep
waiting or to abort. Full parameter tables live in
`../../../shared/references/cirra-mcp-tools.md`.

## Decision Matrix — pick the smallest correct mechanism

| Situation                                                     | Use                                         | Why                                                                                         |
| ------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Up to 200 records to insert / update / upsert / delete        | `sobject_dml`                               | Synchronous, per-record results in the response, one call                                   |
| More than 200 records, data already in the conversation       | `bulk_dml` with inline `records`            | One job instead of N batches; Salesforce handles chunking                                   |
| More than 200 records, data in a CSV the user has             | `bulk_dml` with **no** `records`            | Opens a job the user fills by uploading the CSV from chat — the file never transits the LLM |
| Delete more than 200 records by ID                            | `bulk_dml(operation="delete", recordIds=…)` | Records go to the Recycle Bin                                                               |
| Permanently delete (skip Recycle Bin)                         | `bulk_dml(operation="hardDelete", …)`       | Needs the **Bulk API Hard Delete** permission and explicit user approval                    |
| Read up to a few hundred rows, aggregates, subqueries, TYPEOF | `soql_query`                                | REST; supports every SOQL clause; default `limit` 200                                       |
| Export thousands of rows, or `soql_query` times out           | `bulk_query`                                | PK-chunked extract; no GROUP BY / aggregates / OFFSET / TYPEOF / subqueries                 |
| Include deleted or archived rows in an export                 | `bulk_query(queryAll=true)`                 |                                                                                             |

Apex test-data factories in `assets/factories/` are **not** a bulk mechanism:
Cirra cannot run anonymous Apex, so they only run inside a deployed test class
(see `anonymous-apex-guide.md`). Seed data with `sobject_dml` or `bulk_dml`.

## `bulk_dml` — ingest jobs

Always ask for explicit user approval before starting a job; every
operation changes data. For `hardDelete` restate that the rows will skip the
Recycle Bin and cannot be undeleted.

### Insert with inline records

```
bulk_dml(
  operation="insert",
  sObject="Account",
  records=[
    {"Name": "Acme Corp", "Industry": "Technology"},
    {"Name": "Globex Inc", "Industry": "Finance"}
    // ... any number of rows
  ]
)
```

### Update (records must carry `Id`)

```
bulk_dml(
  operation="update",
  sObject="Account",
  records=[
    {"Id": "001xx000003DGbYAAW", "Industry": "Healthcare"},
    {"Id": "001xx000003DGbZAAW", "Industry": "Finance"}
  ]
)
```

### Upsert (needs an External ID field)

```
bulk_dml(
  operation="upsert",
  sObject="Account",
  externalIdField="External_Id__c",
  records=[
    {"External_Id__c": "EXT-001", "Name": "Acme Corp"},
    {"External_Id__c": "EXT-002", "Name": "Globex Inc"}
  ]
)
```

The external ID field must exist and be flagged External ID — verify with
`sobject_describe` first, or create it with `sobject_field_create`.

### Delete / hardDelete by ID

```
bulk_dml(
  operation="delete",
  sObject="Account",
  recordIds=["001xx000003DGbYAAW", "001xx000003DGbZAAW", ...]
)
```

`recordIds` takes precedence over `records` for delete and hardDelete. Get
the IDs from `soql_query` (a few hundred) or `bulk_query` (thousands).

### CSV upload from chat (data never passes through the LLM)

Omit both `records` and `recordIds`:

```
bulk_dml(operation="insert", sObject="Account")
```

The response contains an upload control / URL. The user uploads the CSV
there; the file goes straight to Salesforce. Before opening the job:

1. `sobject_describe` the object and confirm the CSV header uses **field API
   names** (`Industry`, not `Industry Label`), that required fields are
   present, and that picklist values are valid.
2. Tell the user the expected header row.
3. After the upload, pass the returned `jobId` back to `bulk_dml` to wait for
   the result. If the job is still Open (no CSV yet), the response repeats
   the upload URL instead of closing an empty job.

**CSV format:** first row = field API names, UTF-8, comma delimiter, one
object per file, relationship fields as `Account.External_Id__c` style
columns when upserting by external ID on the parent.

### Waiting and aborting

```
bulk_dml(jobId="7508b00000ABCDEAA4")             # wait again for the same job
bulk_dml(jobId="7508b00000ABCDEAA4", abort=true) # cancel it
```

When `jobId` is set, `records`/`operation`/`sObject` are ignored.

## `bulk_query` — query jobs

```
bulk_query(
  sObject="Contact",
  fields=["Id", "Name", "Email", "Account.Name"],
  whereClause="CreatedDate = LAST_N_DAYS:365"
)
```

Rules:

- `whereClause` is optional here — omit it to export every row.
- **Omit `limit` and `orderBy`** for real extracts. Both disable PK chunking
  and can make the job slow or time out. If a limited query times out, retry
  without `limit`.
- Child-to-parent fields (`Account.Name`) are fine. **Not supported:**
  `GROUP BY`, aggregate functions, `OFFSET`, `TYPEOF`, parent-to-child
  subqueries. For those use `soql_query`.
- `queryAll=true` includes deleted and archived rows (useful for Recycle Bin
  audits and for finding rows to `hardDelete`).
- Same `jobId` / `abort` handling as `bulk_dml`.

Large results come back paginated or as an artifact — follow
`mcp-pagination.md` (download `artifactAccess.downloadUrl` when the host
can write files, otherwise `fetch_more` with the cursor).

## End-to-end patterns

### Mass update from an export

1. `bulk_query` the rows with the fields you need (`Id` plus the fields you
   will change).
2. Transform locally (or in context for small sets).
3. `bulk_dml(operation="update", records=[...])` — or open an empty job and
   let the user upload the edited CSV.
4. Verify with an aggregate `soql_query` (`COUNT(Id)` grouped by the changed
   field).

### Purge test data

1. `soql_query`/`bulk_query` for `Id` with a tight filter
   (`Name LIKE 'DATATEST_%'`).
2. Show the count and a sample; get approval.
3. `bulk_dml(operation="delete", sObject=..., recordIds=[...])` — children
   before parents.
4. Re-run the count query; expect 0.

## Bulk API limits (per 24 hours, rolling)

| Limit                        | Value                             |
| ---------------------------- | --------------------------------- |
| Records ingested             | 150,000,000                       |
| Batches (Bulk API 1.0 + 2.0) | 15,000                            |
| Max CSV upload per job       | 150 MB                            |
| Query job result retention   | 7 days                            |
| Query wait per tool call     | 90 s, then `jobId` for re-polling |

## Error handling

- Ingest results list **successful**, **failed** and **unprocessed** rows.
  Failed rows carry the Salesforce error (`REQUIRED_FIELD_MISSING`,
  `FIELD_CUSTOM_VALIDATION_EXCEPTION`, `DUPLICATES_DETECTED`, ...). Fix the
  rows and resubmit only those.
- A job stuck in `InProgress` after several re-polls is usually blocked by
  a trigger or flow doing too much per chunk; `abort` and consult sf-apex /
  sf-flow.
- `INVALID_OPERATION` on `hardDelete` means the user lacks the Bulk API Hard
  Delete permission (grant via a permission set with sf-permissions, or fall
  back to `delete`).
- Bulk API triggers still fire in chunks of 200 records, so bulkification
  bugs surface here exactly as with `sobject_dml`.

## Best practices

1. **Describe first** — validate field API names, required fields and
   picklist values before the job, not after 10,000 failures.
2. **Sandbox first** — run the same job in a sandbox before production.
3. **Get approval** — every `bulk_dml` operation, and especially
   `hardDelete`, needs an explicit yes from the user.
4. **Keep the result** — record the `jobId`, counts and the failed-row list in
   the completion summary so the user can retry or audit.
5. **Prefer CSV upload** for anything the user already has in a file; it
   avoids pasting thousands of rows into the conversation.
