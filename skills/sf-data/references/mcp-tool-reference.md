## Cirra AI MCP Tool Reference

### 1. Initialize Connection

**Tool**: `cirra_ai_init`
**Purpose**: Initialize Cirra AI session and authenticate org
**Must be called FIRST before any other operations**

```
cirra_ai_init()
```

Call with no parameters — uses the default org. If a default is configured, confirm with the user. If no default, ask for the Salesforce user/alias before proceeding.

### 2. Query Records (SOQL)

**Tool**: `soql_query`
**Purpose**: Execute SOQL queries to retrieve data

```
Parameters:
  - sObject: "Account" (required)
  - fields: ["Id", "Name", "Industry"] (optional; uses SELECT *)
  - whereClause: "Industry='Technology'" (optional — omit for no filter; do NOT pass empty string "")
  - limit: 100 (optional; default is 100 — set explicitly for larger result sets)
  - orderBy: "Name ASC" (optional)
  - sf_user: Connection identifier
```

> **Large results**: When a response includes `instructions.artifactId`, the
> full result exceeded ~75 k and was stored as an artifact. Retrieve it
> using the strategy for your execution mode — see
> `references/mcp-pagination.md` for details. In short:
>
> - **`mcp-plus-code-execution`**: download `instructions.artifactUrl`
> - **`mcp-core`**: `fetch_more(artifactId=..., cursor=_pagination.nextCursor)`
>   — cursor is **required**

> **whereClause caveat**: Never pass an empty string `""` for `whereClause` — it generates malformed SQL (`WHERE ""`). Either omit the parameter entirely or use `"Id != null"` to select all records.

**Example**: Query Accounts in Technology

```
soql_query(
  sObject="Account",
  fields=["Id", "Name", "Industry", "BillingCity"],
  whereClause="Industry='Technology' AND BillingCity != null",
  limit=500,
  sf_user="prod"
)
```

### 3. DML Operations (Insert/Update/Delete/Upsert)

**Tool**: `sobject_dml`
**Purpose**: Create, modify, or delete records

```
Parameters:
  - sObject: "Account" (required)
  - operation: "insert"|"update"|"delete"|"upsert" (required)
  - records: [...] (array of record objects; used for insert/update/upsert, max 200 per call)
  - recordIds: ["id1", "id2"] (string array; used for delete only, max 200 per call)
  - externalIdField: "ExternalId__c" (required for upsert)
  - sf_user: Connection identifier
```

> **200-record limit**: The MCP server rejects calls with > 200 records (`EXCEEDED_ID_LIMIT`).
> Split larger operations into batches of <= 200.

**Example 1: Insert Records**

```
sobject_dml(
  sObject="Account",
  operation="insert",
  records=[
    {"Name": "Test Acct 1", "Industry": "Technology"},
    {"Name": "Test Acct 2", "Industry": "Finance"}
  ],
  sf_user="prod"
)
```

**Example 2: Bulk Upsert Records**

> **Prerequisite**: Upsert requires a field explicitly marked as **External ID** on the target
> object. Standard fields (`Id`, `Name`) are **not** valid external ID fields for upsert.
> Before upserting, verify that a custom External ID field exists (e.g. `ExternalId__c`) — use
> `sobject_describe` to check, or create one with `sobject_field_create` (fieldType `Text`,
> `externalId: true`). Using a non-External-ID field will result in an API error.

```
sobject_dml(
  sObject="Account",
  operation="upsert",
  externalIdField="ExternalId__c",
  records=[
    {"ExternalId__c": "EXT001", "Name": "Updated Account", "Industry": "Tech"},
    {"ExternalId__c": "EXT002", "Name": "New Account", "Industry": "Finance"}
  ],
  sf_user="prod"
)
```

**Example 3: Delete Records by ID**

```
sobject_dml(
  sObject="Account",
  operation="delete",
  recordIds=["001xx000003DHP", "001xx000003DHQ"],
  sf_user="prod"
)
```

### 4. Describe Object (Metadata)

**Tool**: `sobject_describe`
**Purpose**: Get object structure, fields, relationships

```
Parameters:
  - sObject: "Account" (required)
  - sf_user: Connection identifier
```

**Example**: Get Account structure

```
sobject_describe(
  sObject="Account",
  sf_user="prod"
)
```

Response includes: fields (name, type, required, length), relationships, record types, etc.

> **IMPORTANT**: `sobject_describe` is NOT authoritative for field accessibility. A field may appear in the describe response but still fail SOQL queries (`No such column`), LWC schema imports, or Metadata API deployments due to FLS, profile restrictions, or org-level configuration. Always verify critical fields with a test SOQL query before relying on describe output for data operations or component development.

### 5. Tooling API Queries

**Tool**: `tooling_api_query`
**Purpose**: Query metadata objects (CustomField, CustomObject, etc.)

```
Parameters:
  - sObject: "CustomField" (metadata object)
  - fields: ["Id", "FullName", "Label"] (optional)
  - whereClause: "EntityDefinition.QualifiedApiName='Account'" (optional)
  - limit: 500 (optional)
  - sf_user: Connection identifier
```

**Example**: Find all custom fields on Account

```
tooling_api_query(
  sObject="CustomField",
  whereClause="EntityDefinition.QualifiedApiName='Account'",
  sf_user="prod"
)
```

---
