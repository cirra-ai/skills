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
- **Dispatch**: Insert/Update/Delete Records
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **Should call**: `soql_query`, `sobject_dml`
- **Should NOT call**: `metadata_create`, `sobject_describe`
- **Should ask user**: yes (confirm destructive operation, confirm batching)
- **Batch limit**: 200 records per call — must split into 3 batches
- **Follow-up skills**: `sf-data` (verify deletion with a follow-up query)

**Notes**: `delete` routes to DML workflow. 500 records exceeds the 200-record batch limit — must split into batches. Should first query to get record IDs, then delete in batches of 200 (200 + 200 + 100). Must confirm with user before executing a bulk delete.

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
- **Menu options**: Query, Build query, Insert/update/upsert/delete, Validate, Describe
- **Should NOT call**: `soql_query`, `sobject_dml`, `sobject_describe`, `metadata_create`
- **Follow-up skills**: (depends on menu selection)

**Notes**: No arguments, no intent. Present the five-option dispatch menu. No tools called until user selects.

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
