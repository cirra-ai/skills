# Cirra AI MCP Server — tool signatures

The single source of truth for how Cirra skills call the Cirra AI MCP Server.
Every example in a SKILL.md or reference must match these shapes;
`scripts/check_mcp_signatures.py` (run by `scripts/validate-skills.sh`) fails
CI on the most common mistakes. When the server schema and this page disagree,
the server schema wins — update this page.

All tools accept two optional connection selectors: `sf_user` (Salesforce
username of the connection to use) and `cirra_ai_team` (team that owns that
connection; must be passed together with `sf_user`). There is no `orgAlias`
parameter. Call `cirra_ai_init()` once before any other tool and read the
instructions it returns.

---

## Query tools

### `soql_query` — SOQL against the REST API

| Parameter      | Required | Notes                                                                                                        |
| -------------- | -------- | ------------------------------------------------------------------------------------------------------------ |
| `sObject`      | yes      | API name of the object                                                                                       |
| `fields`       | yes      | List of field names. Relationship fields and aggregates allowed                                              |
| `whereClause`  | yes      | WHERE clause text without the `WHERE` keyword. Literal values only. Use `Id != null` when you need every row |
| `orderBy`      | no       | ORDER BY clause text. Never put `ORDER BY` inside `whereClause`                                              |
| `limit`        | no       | Default **200**. Never put `LIMIT` inside `whereClause`                                                      |
| `groupBy`      | no       | GROUP BY clause for aggregate queries                                                                        |
| `havingClause` | no       | HAVING clause; requires `groupBy`                                                                            |
| `pageSize`     | no       | Page size when the response paginates                                                                        |

There is **no `query=` parameter**. A raw SOQL string is not accepted.

```
soql_query(
  sObject="Account",
  fields=["Id", "Name", "Owner.Name"],
  whereClause="Industry = 'Technology' AND CreatedDate = LAST_N_DAYS:30",
  orderBy="CreatedDate DESC",
  limit=50
)
```

Encrypted fields are masked automatically. For thousands of rows, or when a
query times out, use `bulk_query`. To read a debug log, query `ApexLog` and
include `Body` in `fields` (at most 5 logs with `Body` per call).

### `tooling_api_query` — SOQL against the Tooling API

Same parameters and rules as `soql_query` (`sObject`, `fields`, `whereClause`
required; `orderBy`, `limit`, `groupBy`, `pageSize` optional), plus:

| Parameter | Notes                                                                                                                                                                                |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `format`  | `json` (default), `xml` or `source`. For metadata-backed objects (ApexClass, CustomField, Flow, Layout, PermissionSet…) `xml`/`source` attach Metadata API retrieve files per record |

```
tooling_api_query(
  sObject="ApexClass",
  fields=["Id", "Name", "ApiVersion", "Body"],
  whereClause="Name = 'AccountService'"
)
```

### `tooling_api_search` — SOSL against the Tooling API

Finds Apex, Flows and other Tooling records that reference a string. Data SOSL
(against regular sObjects) is **not** available through the server; use SOQL
`LIKE` filters instead.

### `bulk_query` — Bulk API 2.0 query job

| Parameter     | Required         | Notes                                                                        |
| ------------- | ---------------- | ---------------------------------------------------------------------------- |
| `sObject`     | to start a job   |                                                                              |
| `fields`      | to start a job   | Child-to-parent fields allowed; no subqueries or aggregates                  |
| `whereClause` | no               | Omit to export every row                                                     |
| `orderBy`     | no               | Disables PK chunking; avoid for large extracts                               |
| `limit`       | no               | Also disables PK chunking; omit for bulk extracts                            |
| `queryAll`    | no               | Include deleted and archived rows                                            |
| `jobId`       | to wait or abort | Pass back the id returned when the job was still running after the 90 s wait |
| `abort`       | no               | With `jobId`, cancel the job                                                 |

Not supported: `GROUP BY`, aggregates, `OFFSET`, `TYPEOF`, parent-to-child
subqueries.

### `fetch_more` — next page of a large response

`fetch_more(artifactId=<artifactAccess.artifactId>, cursor=<_pagination.nextCursor>)`.
Prefer the artifact download URL when the response offers one; `fetch_more`
loads data into the context window. See `mcp-pagination.md`.

---

## Record DML

### `sobject_dml` — up to ~200 records

| Parameter         | Required             | Notes                                                                                                 |
| ----------------- | -------------------- | ----------------------------------------------------------------------------------------------------- |
| `operation`       | yes                  | `insert`, `update`, `upsert`, `delete`. (Not `create`.) Ask for explicit user approval first          |
| `sObject`         | yes                  | API name. (Not `sobjectType`.)                                                                        |
| `records`         | insert/update/upsert | Array of records. `update` needs `Id`; `insert`/`upsert` must not carry `Id`. **Not used for delete** |
| `recordIds`       | delete               | Array of record IDs to delete                                                                         |
| `externalIdField` | upsert               | External ID field API name                                                                            |
| `dmlOptions`      | no                   | `{ "allOrNone": true }` makes the whole batch fail on any error (default `false`)                     |

```
sobject_dml(operation="insert", sObject="Contact", records=[{ "LastName": "Ng", "AccountId": "001..." }])
sobject_dml(operation="delete", sObject="Contact", recordIds=["003...", "003..."])
```

For more than ~200 records use `bulk_dml`.

### `bulk_dml` — Bulk API 2.0 ingest job

| Parameter         | Required          | Notes                                                                                                                                         |
| ----------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `operation`       | to start a job    | `insert`, `update`, `upsert`, `delete`, `hardDelete` (needs the Bulk API Hard Delete permission). Ask for approval first                      |
| `sObject`         | to start a job    |                                                                                                                                               |
| `records`         | no                | Inline rows. Omit `records` and `recordIds` to open a job the user fills by uploading a CSV from chat (the file never passes through the LLM) |
| `recordIds`       | delete/hardDelete | Takes precedence over `records`                                                                                                               |
| `externalIdField` | upsert            |                                                                                                                                               |
| `jobId`           | to wait or abort  | Returned when the job is still running after the 90 s wait                                                                                    |
| `abort`           | no                | With `jobId`                                                                                                                                  |

### `tooling_api_dml` — one Tooling API record

`operation` (`insert`/`update`/`delete`/`upsert`), `sObject`, and either
`record` (single object; `update` needs `Id`) or `recordId` (delete only).
Used for `ApexClass`, `ApexTrigger`, `TraceFlag`, `DebugLevel`, and other
Tooling objects. For `TraceFlag` prefer `LogType = USER_DEBUG`.

---

## Metadata API

| Tool                | Required                                    | Notes                                                                                                                                                                                                                                  |
| ------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `metadata_describe` | —                                           | Lists the metadata types the org supports                                                                                                                                                                                              |
| `metadata_list`     | `type`                                      | Lists components of a type (optionally by folder)                                                                                                                                                                                      |
| `metadata_read`     | `type`, `fullNames`                         | `format` = `json` (default), `xml` (retrieve files) or `source` (DX source files). Reading a parent (`CustomObject:Obj`) returns its children                                                                                          |
| `metadata_create`   | `type`, `metadata` (array)                  | Each record needs `fullName`. **Not for CustomField** — use `sobject_field_create` so FLS is granted                                                                                                                                   |
| `metadata_update`   | `type` + `metadata` or `fullName` + `patch` | `metadata` **replaces the whole component** for ApprovalProcess, Layout, Flow, StandardValueSet, GlobalValueSet: read, merge, resend — or use `patch` (JSON Patch, applied server-side). `upsert=true` for Flows creates a new version |
| `metadata_delete`   | `type`, `fullNames`                         |                                                                                                                                                                                                                                        |

JSON Patch paths may address array children by `name` or `fullName`
(`/decisions/My_Decision`, `/fields/My_Field__c`); numeric indices always work.

---

## sObject and field metadata

| Tool                                        | Purpose                                                                                         |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `sobjects_list`                             | List objects in the org                                                                         |
| `sobject_describe`                          | Fields, relationships and record types of one object (`sObject` = API name, label or ID)        |
| `sobject_create`                            | Create a custom object (regular objects; CMDT and Custom Settings go through `metadata_create`) |
| `sobject_update`                            | Update object properties (label, description, sharing model…)                                   |
| `sobject_field_create`                      | Create a custom field **and** grant FLS to the connected user                                   |
| `sobject_field_update`                      | Update a custom field                                                                           |
| `record_type_create` / `record_type_update` | Record types including layout assignment and profile availability                               |
| `value_set_create` / `value_set_update`     | Global value sets                                                                               |
| `page_layout_clone` / `page_layout_update`  | Page layouts                                                                                    |
| `tooling_api_describe`                      | Describe a Tooling API object                                                                   |

---

## Users, profiles, permissions

| Tool                                              | Required                                                | Notes                                                                                                          |
| ------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `user_describe`                                   | `user`                                                  | Full user metadata by name, username, email or ID                                                              |
| `user_create`                                     | —                                                       | Create a user (optionally cloned from a template user)                                                         |
| `user_update`                                     | `user`, `operation`                                     | `activate`, `deactivate`, `freeze`, `unfreeze`, `reset_password`, `unlock_password`, `update` (+ `properties`) |
| `profile_describe`                                | profile                                                 |                                                                                                                |
| `profile_update`                                  | `profile`, `patch` (JSON Patch)                         | Object permissions, FLS, tab visibility, system permissions                                                    |
| `profile_clone`                                   | —                                                       |                                                                                                                |
| `permission_set_update`                           | `permissionSet`, `patch` (JSON Patch)                   | Object and field access, system permissions. Prefer over raw `ObjectPermissions`/`FieldPermissions` DML        |
| `permission_set_assignments`                      | `operation` (`add`/`remove`), `permissionSets`, `users` | Names, labels or IDs accepted                                                                                  |
| `group_create` / `group_update` / `group_members` | —                                                       | Public groups and queues                                                                                       |

---

## Other

| Tool                           | Notes                                                                                                                                                                                                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `run_tests`                    | Runs Apex tests and native Flow Tests asynchronously; returns a job id to poll (`AsyncApexJob` / `ApexTestQueueItem`, results in `ApexTestResult`). `tests=[{className, testMethods}]` or `testLevel` (`RunSpecifiedTests`, `RunLocalTests`, `RunAllTestsInOrg`) with `category` (`Apex`, `Flow`) |
| `connect_rest`                 | Only resources under `/services/data/vXX.X/connect/` (`method` required; `path`, `queryParams`, `body`). Never guess paths. `/chatter/`, `/sandbox/`, `/platform/…`, `/graphql` and `/tooling/executeAnonymous` are **not** reachable                                                             |
| `report_run`                   | Run a report and return its results                                                                                                                                                                                                                                                               |
| `cms_content` / `cms_delivery` | Salesforce CMS authoring and delivery                                                                                                                                                                                                                                                             |
| `link_build`                   | Build a Setup or record link for the user                                                                                                                                                                                                                                                         |
| `sf_connection_manage`         | Manage Salesforce connections                                                                                                                                                                                                                                                                     |
| `logout`                       | End the Cirra session                                                                                                                                                                                                                                                                             |

**Not available:** anonymous Apex execution, Code Analyzer/PMD, source-tree deploys, data SOSL, `/query/?explain` query plans.
