# sf-data dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## raw SOQL query

- **Input**: `/sf-data SELECT Id, Name FROM Account LIMIT 10`
- **Dispatch**: Query Data
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `soql_query`
- **Should ask user**: no (query is explicit)
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Follow-up skills**: `sf-data` (refine or export results), `sf-metadata` (inspect object schema)

**Notes**: A raw SOQL string is recognized directly — no translation needed. The dispatch table says "a SOQL string" routes to Query Data. Should execute via `soql_query` and display results as a table.

---

## natural language query

- **Input**: `/sf-data open opportunities over $1M`
- **Dispatch**: Query Data
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Should call**: `soql_query`
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Should ask user**: yes (confirm generated SOQL before running)
- **Follow-up skills**: `sf-data` (refine query or export), `sf-metadata` (inspect Opportunity schema)

**Notes**: Natural language input routes to Query Data. The workflow says to translate to SOQL and "confirm before running" for natural language. Should first describe Opportunity to discover fields, then construct SOQL with Amount > 1000000 and IsClosed = false.

---

## build optimized query

- **Input**: `/sf-data build-query Account with filter on Email`
- **Dispatch**: Build Optimized Query
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Should call**: `soql_query`
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Should ask user**: no
- **Follow-up skills**: `sf-data` (run or refine the generated query), `sf-metadata` (review field indexing)

**Notes**: `build-query` keyword routes to Build Optimized Query. This workflow includes an explicit optimization pass — check against the Query Optimization Checklist (selectivity, field selection, limit sizing, relationship depth). Email is an indexed field so the selectivity score should be high.

---

## insert records

- **Input**: `/sf-data insert 5 test Accounts`
- **Dispatch**: Insert/Update/Delete Records
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `sobject_describe`
- **Should call**: `sobject_dml`
- **Tool params**: `operation: insert, sObject: Account`
- **Should NOT call**: `soql_query` (before insert — used after for verification)
- **Should ask user**: no (if requirements are clear)
- **Batch limit**: 200 records per call
- **Follow-up skills**: `sf-data` (query to verify inserts, generate cleanup query)

**Notes**: `insert` keyword routes to DML workflow. Must discover required fields via `sobject_describe` before constructing records. 5 records is well under the 200-record batch limit. After insert, should verify results and provide a cleanup query for test data.

---

## delete with large batch

- **Input**: `/sf-data delete 500 Account records where Industry = 'Test'`
- **Dispatch**: Bulk Operations
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **Should call**: `soql_query` (IDs, `limit=500`), `bulk_dml`
- **Tool params**: `operation: delete, sObject: Account, recordIds: [...]`
- **Should NOT call**: `metadata_create`, `sobject_dml` (would need 3 batches)
- **Should ask user**: yes (confirm the destructive operation and the count)
- **Follow-up skills**: `sf-data` (verify deletion with a `COUNT(Id)` query)

**Notes**: 500 records exceeds the 200-record `sobject_dml` limit, so the dispatch table routes to Bulk Operations. Query the IDs first (raise `limit` or use `bulk_query`), show the count, get approval, then one `bulk_dml(operation="delete", recordIds=[...])` job. If the tool returns a `jobId` after 90 s, re-call with `jobId`. Do not offer `hardDelete` unless the user asks for it.

---

## validate a query

- **Input**: `/sf-data validate SELECT Id FROM Account WHERE Name LIKE '%test%'`
- **Dispatch**: Validate Data Operation
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **Should NOT call**: `soql_query` (validation only, no execution)
- **Should ask user**: no
- **Follow-up skills**: `sf-data` (run the query after addressing validation warnings)

**Notes**: `validate` keyword routes to Validate Data Operation. This is a dry-run — validate the query without executing it. Should run pre-flight validation (Tier 1 for data ops) and report any issues. The LIKE '%test%' pattern is a known selectivity concern (leading wildcard).

---

## describe object

- **Input**: `/sf-data describe Contact`
- **Dispatch**: Describe Object
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `sobject_describe`
- **Tool params**: `sObject: Contact`
- **Should NOT call**: `soql_query`, `sobject_dml`
- **Should ask user**: no
- **Follow-up skills**: `sf-data` (query Contact records), `sf-metadata` (modify Contact schema)

**Notes**: `describe` keyword routes to Describe Object. Should call `sobject_describe` and display the object's field list, relationships, and key metadata. This is the same workflow as sf-metadata's describe but accessed through the data skill.

---

## no arguments — show menu

- **Input**: `/sf-data`
- **Dispatch**: (none — present menu)
- **Init required**: no
- **Init timing**: after-menu
- **Path**: n/a
- **Should ask user**: yes
- **Menu options**: Query, Build query, Insert/update/upsert/delete, Bulk, Validate, Describe
- **Should NOT call**: `soql_query`, `sobject_dml`, `bulk_dml`, `sobject_describe`, `metadata_create`
- **Follow-up skills**: (depends on menu selection)

**Notes**: No arguments, no intent. Present the six-option dispatch menu. No tools called until user selects.

---

## bare object name

- **Input**: `/sf-data Account`
- **Dispatch**: Query Data
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **Should ask user**: yes (ask what fields/filters to apply)
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Follow-up skills**: `sf-data` (run the query once fields/filters are confirmed), `sf-metadata` (inspect Account schema)

**Notes**: A bare object name routes to Query Data per the dispatch table ("an object name"). But the workflow says to "ask what fields/filters to apply" when only an object name is given — don't blindly SELECT \* FROM Account.

---

## update records

- **Input**: `/sf-data update Account set Industry to 'Technology' where Name = 'Acme Corp'`
- **Dispatch**: Insert/Update/Delete Records
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `soql_query`
- **Should call**: `sobject_dml`
- **Should NOT call**: `metadata_create`, `tooling_api_query`
- **Should ask user**: no
- **Follow-up skills**: `sf-data` (verify update with a follow-up query)

**Notes**: `update` keyword routes to DML workflow. Should first query to find the record(s) matching the WHERE clause, then use `sobject_dml` with operation "update" and the record Id. Must include the Id field in the update payload.

---

## upsert records with external ID

- **Input**: `/sf-data upsert 10 Account records using ExternalId__c`
- **Dispatch**: Insert/Update/Delete Records
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Should call**: `sobject_dml`
- **Should NOT call**: `metadata_create`, `tooling_api_query`
- **Should ask user**: yes (need record data or ask how to generate it)
- **Follow-up skills**: `sf-data` (verify upsert results)

**Notes**: `upsert` keyword routes to DML workflow. Must verify the External ID field exists via `sobject_describe` before constructing records. The `externalIdField` parameter is required for upsert operations per SKILL.md. 10 records is under the 200-record batch limit.

---

## optimize synonym for build-query

- **Input**: `/sf-data optimize Account query for best performance`
- **Dispatch**: Build Optimized Query
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Should call**: `soql_query`
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Should ask user**: no
- **Follow-up skills**: `sf-data` (run or refine the generated query), `sf-metadata` (review field indexing)

**Notes**: The dispatch table lists `optimize` as a synonym for `build-query`, routing to Build Optimized Query. Should discover the Account object structure, build a query with optimization pass (selectivity, indexed fields, limit sizing, relationship depth), and optionally execute.

---

## aggregate query with GROUP BY

- **Input**: `/sf-data query SELECT StageName, COUNT(Id) cnt FROM Opportunity GROUP BY StageName`
- **Dispatch**: Query Data
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `soql_query`
- **Should NOT call**: `sobject_dml`, `metadata_create`, `sobject_describe`
- **Should ask user**: no (query is explicit)
- **Follow-up skills**: `sf-data` (refine or export results)

**Notes**: Raw SOQL with aggregate function routes to Query Data. The GROUP BY clause is valid SOQL syntax. Should execute directly via `soql_query` and display results as a table with the aggregated counts.

---

## test data creation crossing batch boundary

- **Input**: `/sf-data insert 201 test Accounts for bulk testing`
- **Dispatch**: Bulk Operations
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Should call**: `bulk_dml` (`operation: insert, sObject: Account, records: [201 rows]`)
- **Acceptable alternative**: two `sobject_dml` calls (200 + 1) when synchronous per-record results are wanted
- **Should NOT call**: `metadata_create`, `tooling_api_query`, a single `sobject_dml` with 201 records
- **Should ask user**: yes (approval before the insert job)
- **Follow-up skills**: `sf-data` (query to verify inserts, generate cleanup query), `sf-apex` (if the goal is a deployed trigger test class)

**Notes**: 201 records exceeds the 200-record `sobject_dml` limit, so the preferred path is one `bulk_dml` job — triggers still fire per 200-record chunk, so the boundary is crossed. SKILL.md documents both forms. Do not propose an anonymous-Apex factory: Cirra cannot execute it. After insert, verify with `COUNT(Id)` and provide a cleanup query.

---

## query with relationship traversal

- **Input**: `/sf-data query active accounts with their contacts`
- **Dispatch**: Query Data
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Should call**: `soql_query`
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Should ask user**: yes (confirm generated SOQL before running)
- **Follow-up skills**: `sf-data` (refine query or export)

**Notes**: Natural language query involving parent-to-child relationship. Should translate to SOQL with a subquery for Contacts. Note: the `soql_query` tool does not support subqueries in the fields array — may need two separate queries (Accounts, then Contacts filtered by Account IDs). Should confirm the generated approach with the user.

---

## bulk insert from CSV

- **Input**: `/sf-data bulk insert Account from accounts.csv`
- **Dispatch**: Bulk Operations
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Should call**: `bulk_dml` with `operation: insert, sObject: Account` and **no** `records`
- **Should NOT call**: `sobject_dml`, `metadata_create`; must not ask the user to paste the CSV contents
- **Should ask user**: yes (confirm header row uses field API names; approval before opening the job)
- **Follow-up skills**: `sf-data` (re-poll with `jobId`, verify with a `COUNT(Id)` query)

**Notes**: `bulk` and `csv` keywords route to Bulk Operations. Opening a `bulk_dml` job without `records` returns an upload control so the user can upload the file from chat — the data never passes through the LLM. After the upload, call `bulk_dml(jobId=...)` to collect the result and report succeeded/failed/unprocessed counts.

---

## export thousands of rows

- **Input**: `/sf-data export all Contacts with Account name to csv`
- **Dispatch**: Bulk Operations
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe` (optional — confirm `Account.Name` is reachable)
- **Should call**: `bulk_query` with `sObject: Contact, fields: ["Id", "Name", "Email", "Account.Name"]` and **no** `limit` / `orderBy`
- **Should NOT call**: `soql_query` for the extract itself, `sobject_dml`, `bulk_dml`
- **Should ask user**: no (read-only), unless the object is very large and a filter would help
- **Follow-up skills**: `sf-data` (re-poll with `jobId`; page or download the result per `references/mcp-pagination.md`)

**Notes**: `export` and `csv` route to Bulk Operations; "all Contacts" means thousands of rows, so `bulk_query` rather than `soql_query`. Omit `limit` and `orderBy` so Salesforce can PK-chunk. No aggregates, subqueries, OFFSET or TYPEOF in a bulk query.
