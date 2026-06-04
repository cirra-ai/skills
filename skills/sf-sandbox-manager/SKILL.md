---
name: sf-sandbox-manager
plugin: cirra-ai-sf
argument-hint: '[checkout|checkin|status|create|delete|recommend|setup] {name} ...'
metadata:
  version: 1.0.0
description: >
  Salesforce sandbox and scratch org pool manager. Check out clean environments,
  use them for tasks, and check them back in for recycling. Includes recommendation
  engine for sandbox vs scratch org selection. Works via Cirra AI MCP Server.
  Usage: /sf-sandbox-manager [checkout|checkin|status|create|delete|recommend|setup] ...
---

# Salesforce Sandbox & Scratch Org Pool Manager

Manage a shared pool of Salesforce sandbox and scratch org environments. Check out clean environments for development or testing, use them, and check them back in for recycling. Covers the full environment lifecycle: provisioning, checkout, check-in, refresh, and decommissioning.

This skill uses **Cirra AI MCP tools** for all sandbox pool operations and the **Salesforce CLI** for scratch org management. No custom server extensions are required.

## Dispatch

Parse `$ARGUMENTS` to determine which workflow to follow:

| First argument or intent                                | Workflow                 |
| ------------------------------------------------------- | ------------------------ |
| `checkout`, "get me an org", "I need an environment"    | Checkout Environment     |
| `checkin`, `return`, "done with", "release"             | Check In Environment     |
| `status`, `list`, "show environments", "pool"           | Pool Status              |
| `create`, "add to pool", "provision", "new sandbox"     | Create Environment       |
| `delete`, `destroy`, "remove from pool", "decommission" | Delete Environment       |
| `recommend`, "should I use", "sandbox or scratch"       | Recommendation Engine    |
| `setup`, `configure`, "set up pool", "initialize pool"  | Pool Setup               |
| _(no argument or unclear)_                              | Ask the user (see below) |

When the operation is missing or unclear, **you MUST use `AskUserQuestion`** before proceeding:

```
AskUserQuestion(question="What would you like to do?\n\n1. **Checkout** — get a clean environment to work in\n2. **Check in** — return an environment you're done with\n3. **Status** — see all environments and who's using them\n4. **Create** — provision a new sandbox or scratch org\n5. **Delete** — permanently remove an environment\n6. **Recommend** — help me decide sandbox vs scratch org\n7. **Setup** — configure the environment pool (first-time)")
```

Do NOT guess the operation or default to one. Wait for the user's answer.

---

## Core Responsibilities

1. **Pool Setup**: Create and configure `Environment_Pool__c` custom object for tracking sandboxes
2. **Checkout**: Reserve an available environment for a user's task
3. **Check In**: Return an environment for reuse or flag it for refresh
4. **Create**: Provision new sandboxes (via Tooling API) or scratch orgs (via CLI)
5. **Delete**: Decommission environments permanently
6. **Pool Status**: Show all environments with availability, checked-out-by, and health
7. **Recommendation Engine**: Help users choose between sandbox types and scratch orgs

---

## State Management

### Sandboxes — Custom Object (`Environment_Pool__c`)

Sandboxes have no native pool/checkout concept. The `Environment_Pool__c` custom object in the production org tracks who checked out what, availability, and lifecycle state. All pool operations use existing Cirra AI MCP tools (`soql_query`, `sobject_dml`, `tooling_api_dml`).

The object schema is defined in `assets/pool-object-schema.json`. See `references/pool-object-setup.md` for complete setup documentation.

**`Environment_Pool__c` fields:**

| Field API Name          | Type      | Purpose                                                |
| ----------------------- | --------- | ------------------------------------------------------ |
| `Environment_Name__c`   | Text(80)  | Sandbox name                                           |
| `Environment_Type__c`   | Picklist  | Developer, Developer_Pro, Partial, Full                |
| `Status__c`             | Picklist  | Available, Checked_Out, Pending_Reset, Creating, Error |
| `Checked_Out_By__c`     | Text(255) | User email or name                                     |
| `Checkout_Timestamp__c` | DateTime  | When checked out                                       |
| `Expected_Return__c`    | DateTime  | When user expects to finish                            |
| `Expiry_Date__c`        | Date      | Sandbox refresh eligibility date                       |
| `Purpose__c`            | Text(255) | What the checkout is for                               |
| `Org_Id__c`             | Text(18)  | 18-char org ID of the sandbox                          |
| `Login_Url__c`          | Url       | Login URL for the sandbox                              |
| `Last_Reset__c`         | DateTime  | Last time sandbox was refreshed                        |
| `Sandbox_Process_Id__c` | Text(18)  | SandboxProcess record ID (for status polling)          |

### Scratch Orgs — Salesforce CLI (source of truth)

Scratch orgs are fully managed by the Salesforce CLI. The CLI tracks them locally (`~/.sf/`). No `Environment_Pool__c` record is needed for scratch orgs.

Scratch org operations require `cli` or `sfdx-repo` execution mode. When CLI is unavailable (`mcp-core` or `mcp-plus-code-execution`), the skill explains the limitation and offers sandbox as a fallback.

---

## Execution Modes

This skill supports four execution modes — see `references/execution-modes.md` for detection logic and full details.

| Mode                      | Sandbox | Scratch Org   | Pool Tracking |
| ------------------------- | ------- | ------------- | ------------- |
| `sfdx-repo`               | Full    | Full          | Full          |
| `cli`                     | Full    | Full          | Full          |
| `mcp-plus-code-execution` | Full    | Limited       | Full          |
| `mcp-core`                | Full    | Not supported | Full          |

All sandbox pool operations go through MCP tools regardless of mode. The mode determines whether scratch org CLI commands are available.

---

## Phase 1: Initialization & Capability Detection

**FIRST**: Call `cirra_ai_init()` with no parameters:

```
cirra_ai_init()
```

- If a default org is configured, proceed immediately and confirm with the user:
  > "I've connected to **[org]**. Would you like me to use the defaults, or do you want to select different options?"
- If no default is configured, ask for the Salesforce user/alias before proceeding.

Do **not** ask for org details before calling `cirra_ai_init()`.

**THEN**: Detect pool and environment capabilities.

### Step 1: Check if Environment_Pool\_\_c exists

Use `sobject_describe` on `Environment_Pool__c` to verify the pool tracking object exists.

- `HAS_POOL = true` if `sobject_describe(sObject="Environment_Pool__c")` succeeds
- `HAS_POOL = false` if it returns an error (object not found)

If `HAS_POOL = false` and the user's workflow requires it (checkout, checkin, status, create sandbox), trigger the **Pool Setup** workflow automatically before continuing.

### Step 2: Detect execution mode for scratch org support

Determine whether the Salesforce CLI is available:

- `HAS_CLI = true` if the execution mode is `cli` or `sfdx-repo`
- `HAS_CLI = false` if the execution mode is `mcp-core` or `mcp-plus-code-execution`

When scratch org operations are requested but `HAS_CLI = false`, inform the user:

> "Scratch org management requires the Salesforce CLI, which isn't available in your current setup. I can help you with a sandbox instead — would you like me to recommend the best sandbox type for your task?"

### Step 3: Query org edition and sandbox limits

Use `soql_query` to check the org's edition and sandbox capacity:

- sObject: `Organization`
- fields: `["Id", "Name", "OrganizationType", "IsSandbox"]`
- whereClause: ``
- orderBy: ``
- groupBy: ``
- limit: `1`

If `IsSandbox = true`, warn the user: "You're connected to a sandbox org. Sandbox creation and pool management should be done from the production org."

### Capability Summary

| Operation             | Requires                                |
| --------------------- | --------------------------------------- |
| Pool Setup            | Production org (not sandbox)            |
| Checkout Sandbox      | HAS_POOL                                |
| Check In Sandbox      | HAS_POOL                                |
| Pool Status           | HAS_POOL (sandbox) or HAS_CLI (scratch) |
| Create Sandbox        | HAS_POOL + Production org               |
| Create Scratch Org    | HAS_CLI                                 |
| Delete Sandbox        | HAS_POOL + Production org               |
| Delete Scratch Org    | HAS_CLI                                 |
| Recommendation Engine | (no prerequisites)                      |

---

## Tool Usage Notes

The Cirra AI MCP Server's `soql_query` tool requires structured parameters, not raw SOQL strings. Always provide:

- `sObject` — the object API name
- `fields` — array of field names
- `whereClause` — the WHERE condition (without the `WHERE` keyword)
- `orderBy` — ORDER BY clause (pass empty string `""` if not needed)
- `groupBy` — GROUP BY clause (pass empty string `""` if not needed)
- `limit` — max records to return

For DML operations, use `sobject_dml` with `sObject`, `operation` (insert/update/delete/upsert), and `records` array. For delete operations, use `recordIds` (string array of IDs) instead of `records`.

See `references/mcp-pagination.md` for handling large result sets.

---

## 1. Pool Setup

One-time configuration to create the `Environment_Pool__c` custom object and its fields. This is auto-triggered when a sandbox workflow runs and the pool object doesn't exist.

### Step 1: Confirm with user

Before creating any metadata, confirm:

```
AskUserQuestion(question="The environment pool tracking object (Environment_Pool__c) doesn't exist in this org yet. I need to create it along with a Permission Set for access.\n\nShall I set it up now?")
```

### Step 2: Create the custom object

Use `sobject_create`:

```
sobject_create(
  name="Environment_Pool",
  label="Environment Pool",
  pluralLabel="Environment Pool",
  nameFieldLabel="Pool Entry Name",
  nameFieldType="AutoNumber",
  nameFieldFormat="ENV-{0000}",
  description="Tracks sandbox environments for pool checkout/checkin lifecycle management"
)
```

### Step 3: Create all fields

Use `sobject_field_create` for each field defined in `assets/pool-object-schema.json`. Create them in this order:

1. `Environment_Name__c` — Text(80), required

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Environment_Name",
     fieldType="Text",
     label="Environment Name",
     length=80,
     required=true,
     description="Sandbox name as it appears in Salesforce Setup"
   )
   ```

2. `Environment_Type__c` — Picklist

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Environment_Type",
     fieldType="Picklist",
     label="Environment Type",
     picklistValues=["Developer", "Developer_Pro", "Partial", "Full"],
     required=true,
     description="Sandbox type (maps to SandboxInfo.LicenseType)"
   )
   ```

3. `Status__c` — Picklist

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Status",
     fieldType="Picklist",
     label="Status",
     picklistValues=["Available", "Checked_Out", "Pending_Reset", "Creating", "Error"],
     required=true,
     description="Current lifecycle state of this environment"
   )
   ```

4. `Checked_Out_By__c` — Text(255)

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Checked_Out_By",
     fieldType="Text",
     label="Checked Out By",
     length=255,
     required=false,
     description="Email or name of the user who has this environment checked out"
   )
   ```

5. `Checkout_Timestamp__c` — DateTime

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Checkout_Timestamp",
     fieldType="DateTime",
     label="Checkout Timestamp",
     required=false,
     description="When this environment was checked out"
   )
   ```

6. `Expected_Return__c` — DateTime

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Expected_Return",
     fieldType="DateTime",
     label="Expected Return",
     required=false,
     description="When the user expects to be done with this environment"
   )
   ```

7. `Expiry_Date__c` — Date

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Expiry_Date",
     fieldType="Date",
     label="Expiry Date",
     required=false,
     description="Sandbox refresh eligibility date"
   )
   ```

8. `Purpose__c` — Text(255)

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Purpose",
     fieldType="Text",
     label="Purpose",
     length=255,
     required=false,
     description="What this checkout is for (feature name, ticket number, etc.)"
   )
   ```

9. `Org_Id__c` — Text(18)

   ```
   sobject_field_create(
     objectName="Environment_Pool__c",
     fieldName="Org_Id",
     fieldType="Text",
     label="Org ID",
     length=18,
     required=false,
     description="18-character org ID of the sandbox"
   )
   ```

10. `Login_Url__c` — Url

    ```
    sobject_field_create(
      objectName="Environment_Pool__c",
      fieldName="Login_Url",
      fieldType="Url",
      label="Login URL",
      required=false,
      description="Login URL for the sandbox environment"
    )
    ```

11. `Last_Reset__c` — DateTime

    ```
    sobject_field_create(
      objectName="Environment_Pool__c",
      fieldName="Last_Reset",
      fieldType="DateTime",
      label="Last Reset",
      required=false,
      description="Last time this sandbox was refreshed/reset"
    )
    ```

12. `Sandbox_Process_Id__c` — Text(18)
    ```
    sobject_field_create(
      objectName="Environment_Pool__c",
      fieldName="Sandbox_Process_Id",
      fieldType="Text",
      label="Sandbox Process ID",
      length=18,
      required=false,
      description="SandboxProcess record ID for polling creation/refresh status"
    )
    ```

### Step 4: Create Permission Set

Use `metadata_create` to create a Permission Set granting access to the pool object and all its fields:

```
metadata_create(
  type="PermissionSet",
  metadata=[{
    "fullName": "Environment_Pool_Access",
    "label": "Environment Pool Access",
    "description": "Grants full access to Environment_Pool__c for sandbox pool management",
    "objectPermissions": [{
      "object": "Environment_Pool__c",
      "allowCreate": true,
      "allowRead": true,
      "allowEdit": true,
      "allowDelete": true,
      "viewAllRecords": true,
      "modifyAllRecords": false
    }],
    "fieldPermissions": [
      {"field": "Environment_Pool__c.Environment_Name__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Environment_Type__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Status__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Checked_Out_By__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Checkout_Timestamp__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Expected_Return__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Expiry_Date__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Purpose__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Org_Id__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Login_Url__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Last_Reset__c", "editable": true, "readable": true},
      {"field": "Environment_Pool__c.Sandbox_Process_Id__c", "editable": true, "readable": true}
    ]
  }]
)
```

### Step 5: Verify and report

Use `sobject_describe(sObject="Environment_Pool__c")` to confirm the object and all fields were created.

Report to the user:

> "Environment pool is set up. The `Environment_Pool__c` object has been created with all tracking fields and a Permission Set (`Environment_Pool_Access`). Assign this Permission Set to users who need to manage the sandbox pool."

---

## 2. Checkout Environment

Reserve an available sandbox or scratch org for use.

### Sandbox Checkout

**Step 1: Query available environments.**

Use `soql_query`:

- sObject: `Environment_Pool__c`
- fields: `["Id", "Name", "Environment_Name__c", "Environment_Type__c", "Status__c", "Login_Url__c", "Expiry_Date__c", "Last_Reset__c"]`
- whereClause: `Status__c = 'Available'`
- orderBy: `Last_Reset__c DESC`
- groupBy: ``
- limit: `50`

**Step 2: Handle results.**

If **no environments are available**:

```
AskUserQuestion(question="No sandbox environments are currently available.\n\n1. **Create** — provision a new sandbox\n2. **Recommend** — help me choose the right environment type\n3. **Status** — show all environments (including checked-out ones)")
```

If **one or more are available**, present them to the user:

```
AskUserQuestion(question="Which environment would you like to check out?\n\n1. **dev-sandbox-1** — Developer, last reset 3 days ago\n2. **qa-sandbox** — Developer Pro, last reset 1 week ago\n3. **staging** — Partial Copy, last reset 2 weeks ago")
```

**Step 3: Gather checkout details.**

Ask the user:

```
AskUserQuestion(question="What are you using this environment for?\n\nPlease provide:\n- **Purpose**: brief description (e.g., 'JIRA-1234 feature development')\n- **Expected duration**: when will you be done? (e.g., '3 days', 'end of sprint')")
```

**Step 4: Update the pool record.**

Use `sobject_dml`:

- sObject: `Environment_Pool__c`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "<pool_record_id>",
      "Status__c": "Checked_Out",
      "Checked_Out_By__c": "<user_email_or_name>",
      "Checkout_Timestamp__c": "<current_datetime_ISO>",
      "Expected_Return__c": "<expected_return_datetime_ISO>",
      "Purpose__c": "<purpose_text>"
    }
  ]
  ```

**Step 5: Provide connection details.**

Present the sandbox details:

- Environment name and type
- Login URL (use `link_build` if available)
- Checked-out-by and expected return date
- Offer to switch the active MCP connection: "Would you like me to connect to this sandbox now?" If yes, use `sf_connection_manage`.

### Scratch Org Checkout

Scratch orgs are ephemeral — "checkout" means creating a new one. Route to **Create Environment** (scratch org path).

---

## 3. Check In Environment

Return an environment that is no longer needed.

### Identify the environment

If the user specifies a name or ID, use it directly. Otherwise, query environments checked out by the current user:

Use `soql_query`:

- sObject: `Environment_Pool__c`
- fields: `["Id", "Name", "Environment_Name__c", "Environment_Type__c", "Status__c", "Checkout_Timestamp__c", "Purpose__c"]`
- whereClause: `Status__c = 'Checked_Out'`
- orderBy: `Checkout_Timestamp__c DESC`
- groupBy: ``
- limit: `20`

If multiple environments are checked out, present a list and ask which one to return.

### Ask about condition

```
AskUserQuestion(question="What condition is the environment in?\n\n1. **Clean** — ready for someone else to use immediately\n2. **Dirty** — needs a refresh before reuse (data changes, config drift)\n3. **Decommission** — no longer needed, remove from pool permanently")
```

### Apply the check-in

**Clean** — set back to Available:

Use `sobject_dml`:

- sObject: `Environment_Pool__c`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "<pool_record_id>",
      "Status__c": "Available",
      "Checked_Out_By__c": "",
      "Checkout_Timestamp__c": null,
      "Expected_Return__c": null,
      "Purpose__c": ""
    }
  ]
  ```

**Dirty** — set to Pending_Reset:

Use `sobject_dml`:

- sObject: `Environment_Pool__c`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "<pool_record_id>",
      "Status__c": "Pending_Reset",
      "Checked_Out_By__c": "",
      "Checkout_Timestamp__c": null,
      "Expected_Return__c": null,
      "Purpose__c": ""
    }
  ]
  ```

Then offer to initiate a sandbox refresh:

> "Would you like me to start a refresh on this sandbox? It will be unavailable during the refresh (typically 30 min to several hours depending on type)."

If yes, see **Refresh Sandbox** in section 4.

**Decommission** — route to **Delete Environment** (section 5).

### Scratch Org Check-In

For scratch orgs, "check in" means deleting it (they can't be reused). Route to **Delete Environment** (scratch org path) with a note:

> "Scratch orgs are ephemeral — checking in means deleting it. A new one can be created anytime."

---

## 4. Create Environment

Provision a new sandbox or scratch org.

### Step 1: Determine environment type

If the user hasn't specified a type, run the **Recommendation Engine** inline (section 6) to help them choose.

If the user specifies "scratch org" but `HAS_CLI = false`, inform them and offer sandbox as fallback.

### Sandbox Creation

**Step 1: Gather sandbox details.**

```
AskUserQuestion(question="What type of sandbox do you need?\n\n1. **Developer** — schema only, 200 MB, fastest to create (minutes)\n2. **Developer Pro** — schema only, 1 GB, for larger datasets\n3. **Partial Copy** — schema + sample data, 5 GB, takes hours\n4. **Full Copy** — complete production clone, takes hours to days")
```

Ask for a sandbox name (alphanumeric, max 10 characters).

**Step 2: Create the sandbox via Tooling API.**

Use `tooling_api_dml`:

- sObject: `SandboxInfo`
- operation: `create`
- records:
  ```json
  [
    {
      "SandboxName": "<sandbox_name>",
      "LicenseType": "<Developer|Developer_Pro|Partial|Full>",
      "Description": "<purpose>"
    }
  ]
  ```

Capture the `SandboxProcess` ID from the response.

**Step 3: Create the pool tracking record.**

Use `sobject_dml`:

- sObject: `Environment_Pool__c`
- operation: `insert`
- records:
  ```json
  [
    {
      "Environment_Name__c": "<sandbox_name>",
      "Environment_Type__c": "<type>",
      "Status__c": "Creating",
      "Sandbox_Process_Id__c": "<sandbox_process_id>",
      "Purpose__c": "<purpose>"
    }
  ]
  ```

**Step 4: Report estimated time.**

| Type          | Estimated Creation Time |
| ------------- | ----------------------- |
| Developer     | 5–30 minutes            |
| Developer Pro | 5–30 minutes            |
| Partial Copy  | 1–6 hours               |
| Full Copy     | 2–24 hours              |

> "Sandbox **<name>** is being created. Estimated time: **<estimate>**. Use `/sf-sandbox-manager status` to check progress."

### Refresh Sandbox

To refresh an existing sandbox (from `Pending_Reset` state):

**Step 1: Query the SandboxInfo record.**

Use `tooling_api_query`:

- sObject: `SandboxInfo`
- fields: `["Id", "SandboxName", "LicenseType"]`
- whereClause: `SandboxName = '<sandbox_name>'`
- limit: `1`

**Step 2: Create a SandboxProcess to trigger the refresh.**

Use `tooling_api_dml`:

- sObject: `SandboxProcess`
- operation: `create`
- records:
  ```json
  [
    {
      "SandboxInfoId": "<sandbox_info_id>",
      "SandboxName": "<sandbox_name>",
      "LicenseType": "<type>"
    }
  ]
  ```

**Step 3: Update the pool record.**

Use `sobject_dml`:

- sObject: `Environment_Pool__c`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "<pool_record_id>",
      "Status__c": "Creating",
      "Sandbox_Process_Id__c": "<new_sandbox_process_id>"
    }
  ]
  ```

### Scratch Org Creation

Requires `cli` or `sfdx-repo` execution mode.

**Step 1: Choose a scratch org definition.**

Use templates from `assets/scratch-org-templates/`:

```
AskUserQuestion(question="Which scratch org template?\n\n1. **Minimal** — basic org with standard features\n2. **Full-featured** — includes common features (Communities, Service Cloud, etc.)\n3. **Custom** — I'll provide my own definition file")
```

**Step 2: Set duration and alias.**

Ask for:

- Alias (e.g., `feature-xyz`)
- Duration in days (1–30, default 7)

**Step 3: Create the scratch org.**

Run via CLI:

```bash
sf org create scratch \
  --definition-file <template_path> \
  --alias <alias> \
  --duration-days <duration> \
  --set-default \
  --json
```

**Step 4: Report results.**

Parse the JSON output and present:

- Org ID
- Username
- Login URL
- Expiration date

> "Scratch org **<alias>** is ready. It expires in **<duration>** days. Use `sf org open --target-org <alias>` to open it in a browser."

---

## 5. Delete Environment

Permanently remove an environment. This is a destructive operation — always confirm.

### Confirmation

```
AskUserQuestion(question="Are you sure you want to permanently delete **<environment_name>** (<type>)?\n\nThis action cannot be undone. The sandbox/scratch org and all its data will be destroyed.\n\n1. **Yes, delete it**\n2. **No, cancel**")
```

### Sandbox Deletion

**Step 1: Get the SandboxInfo record.**

Use `tooling_api_query`:

- sObject: `SandboxInfo`
- fields: `["Id", "SandboxName"]`
- whereClause: `SandboxName = '<sandbox_name>'`
- limit: `1`

**Step 2: Delete the sandbox.**

Use `tooling_api_dml`:

- sObject: `SandboxInfo`
- operation: `delete`
- recordIds: `["<sandbox_info_id>"]`

**Step 3: Delete the pool record.**

Use `sobject_dml`:

- sObject: `Environment_Pool__c`
- operation: `delete`
- recordIds: `["<pool_record_id>"]`

### Scratch Org Deletion

Requires `cli` or `sfdx-repo` execution mode.

```bash
sf org delete scratch --target-org <alias> --no-prompt
```

---

## 6. Pool Status

Show all environments with their current state.

### Sandbox Pool Status

**Step 1: Query all pool records.**

Use `soql_query`:

- sObject: `Environment_Pool__c`
- fields: `["Id", "Name", "Environment_Name__c", "Environment_Type__c", "Status__c", "Checked_Out_By__c", "Checkout_Timestamp__c", "Expected_Return__c", "Purpose__c", "Login_Url__c", "Expiry_Date__c", "Last_Reset__c", "Sandbox_Process_Id__c"]`
- whereClause: ``
- orderBy: `Environment_Name__c ASC`
- groupBy: ``
- limit: `200`

**Step 2: Poll creating sandboxes for live status.**

For any record with `Status__c = 'Creating'` and a `Sandbox_Process_Id__c`, check the actual status:

Use `tooling_api_query`:

- sObject: `SandboxProcess`
- fields: `["Id", "SandboxName", "Status", "CopyProgress", "Description"]`
- whereClause: `Id = '<sandbox_process_id>'`
- limit: `1`

If `Status = 'Completed'`, update the pool record:

Use `sobject_dml`:

- sObject: `Environment_Pool__c`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "<pool_record_id>",
      "Status__c": "Available",
      "Last_Reset__c": "<current_datetime_ISO>"
    }
  ]
  ```

If `Status = 'Error'` or `Status = 'Deleted'`, update accordingly.

### Scratch Org Status

If `HAS_CLI = true`, also list scratch orgs:

```bash
sf org list --clean --json
```

Parse the output and include scratch orgs in the combined status table.

### Present Combined Status

Display a table combining both sandbox pool records and scratch orgs:

```
| Name             | Type          | Status       | Checked Out By     | Since       | Purpose            | Expiry     |
| ---------------- | ------------- | ------------ | ------------------ | ----------- | ------------------ | ---------- |
| dev-sandbox-1    | Developer     | Available    | —                  | —           | —                  | 2026-07-01 |
| qa-sandbox       | Developer Pro | Checked Out  | jane@company.com   | 2 days ago  | JIRA-456 QA        | 2026-08-15 |
| staging          | Partial Copy  | Creating     | —                  | —           | Sprint 42 UAT      | —          |
| scratch-feature  | Scratch Org   | Active       | —                  | —           | Feature X          | 5 days     |
```

Highlight:

- Overdue checkouts (past `Expected_Return__c`)
- Environments nearing expiry
- Sandboxes stuck in `Creating` for too long (> 24 hours for Developer, > 48 hours for Partial/Full)

---

## 7. Recommendation Engine

Help users choose between sandbox types and scratch orgs.

### Detect user expertise level

If the user's language suggests a non-technical background (e.g., "I need a test environment", no Salesforce jargon), use simplified questions. If they use technical terms (sandbox, scratch org, Dev Hub), use the full matrix.

### Simplified Questions (Non-Technical Users)

```
AskUserQuestion(question="Let me help you find the right environment. Will you need real customer data from production?")
```

If yes → "Full data or just a sample?"

- Full → **Full Copy Sandbox**
- Sample → **Partial Copy Sandbox**

If no:

```
AskUserQuestion(question="How long will you need this environment?\n\n1. **A few days** — quick testing or feature work\n2. **A few weeks** — sprint-length work\n3. **Ongoing** — long-running project or permanent test environment")
```

- A few days + HAS_CLI → **Scratch Org**
- A few days + no CLI → **Developer Sandbox**
- A few weeks → **Developer Sandbox** (or Scratch Org if CLI available)
- Ongoing → **Developer Sandbox**

### Full Decision Matrix (Technical Users)

Gather requirements using the decision tree documented in `references/recommendation-engine.md`:

1. **Need production data?** → Full/Partial sandbox
2. **Need installed packages or complex config?** → Developer Sandbox (or Scratch Org with 2GP packages)
3. **Duration?** → Short: Scratch Org; Long: Developer Sandbox
4. **Constraints**: No CLI → Sandbox only; No Dev Hub → Sandbox only; Sandbox limit reached → Scratch Org only

### Present Recommendation

After evaluating, present the recommendation with rationale:

> **Recommendation: Developer Sandbox**
>
> Based on your requirements:
>
> - You don't need production data ✓
> - You need the environment for 2+ weeks ✓
> - Installed packages need to be available ✓
>
> A Developer sandbox copies the schema from production (no data), provisions in minutes, and persists until you no longer need it.
>
> **Alternative**: If you only needed it for a few days and had the Salesforce CLI, a scratch org would be faster to provision and fully disposable.

See `references/sandbox-types-guide.md` for the complete comparison matrix.

---

## Lifecycle State Machine

```
Creating ──→ Available ⇄ Checked_Out
                │                │
                │                ├──→ Available     (clean check-in)
                │                └──→ Pending_Reset (dirty check-in)
                │
                └──→ Pending_Reset ──→ Creating (refresh) ──→ Available
                │
  Any state ──→ Error (from provisioning/refresh failure)
  Any state ──→ (Deleted) via Delete Environment workflow
```

See `references/lifecycle-states.md` for complete transition rules and the MCP tool calls at each transition.

---

## Presenting Results

For all operations, follow these patterns:

**Always include:**

- Record IDs and auto-number names (ENV-0001, ENV-0002)
- Environment names and types
- Links to records using `link_build`
- Status with clear labels (avoid internal codes)

**Table format for pool status:**

```
| # | Name | Type | Status | User | Since | Purpose | Expiry |
|---|------|------|--------|------|-------|---------|--------|
```

**Summary format for checkout/checkin:**

```
Environment: dev-sandbox-1 (Developer)
Status: Checked Out → Available
Previous User: jane@company.com
Duration: 3 days
```

---

## When to Load References

- **sandbox-types-guide.md**: When helping users compare sandbox types or answering "what's the difference between Developer and Developer Pro?"
- **recommendation-engine.md**: When running the full recommendation engine decision tree
- **lifecycle-states.md**: When troubleshooting state transitions or understanding what happens at each lifecycle stage
- **pool-object-setup.md**: When the user wants to understand the pool object structure, set it up manually, or customize it
- **managed-package-guide.md**: When discussing packaging `Environment_Pool__c` as a managed/unlocked package for distribution
- **execution-modes.md**: When determining what operations are available in the current execution mode
- **mcp-pagination.md**: When handling large query results from pool status queries

---

## Cross-Skill Integration

| From Skill  | To sf-sandbox-manager | When                                                |
| ----------- | --------------------- | --------------------------------------------------- |
| sf-metadata | → sf-sandbox-manager  | "I need a sandbox to test this metadata deployment" |
| sf-apex     | → sf-sandbox-manager  | "Get me a scratch org for this Apex development"    |
| sf-flow     | → sf-sandbox-manager  | "I need a test environment for this flow"           |

| From sf-sandbox-manager | To Skill         | When                                                 |
| ----------------------- | ---------------- | ---------------------------------------------------- |
| sf-sandbox-manager      | → sf-metadata    | After checkout, set up custom objects in the sandbox |
| sf-sandbox-manager      | → sf-data        | After checkout, populate test data                   |
| sf-sandbox-manager      | → sf-permissions | Audit permissions on `Environment_Pool__c`           |

---

## Common Issues

**Environment_Pool\_\_c object not found:**
Run Pool Setup (`/sf-sandbox-manager setup`) to create the tracking object. This is a one-time setup per org.

**Cannot create sandbox — limit reached:**
Query `SELECT SandboxName FROM SandboxInfo` via `tooling_api_query` to see existing sandboxes. The org may be at its sandbox limit. Delete unused sandboxes or use scratch orgs instead.

**Sandbox stuck in "Creating" state:**
Poll the `SandboxProcess` via `tooling_api_query` to check the real status. If `CopyProgress` hasn't changed in hours, the sandbox creation may have failed. Update the pool record status to `Error`.

**Scratch org creation fails — no Dev Hub:**
The default Dev Hub must be set. In CLI mode, run `sf org login web --set-default-dev-hub` first. In non-CLI modes, scratch orgs are not supported.

**Permission denied on Environment_Pool\_\_c:**
The user needs the `Environment_Pool_Access` Permission Set assigned. Check via `soql_query` on `PermissionSetAssignment`.

**Connected to a sandbox org instead of production:**
Sandbox creation and pool management must be done from the production org. Use `sf_connection_manage` to switch to the production org.

---

## Dependencies

- **Cirra AI MCP Server** (required): All sandbox pool operations use Cirra AI tools
  - Initialize with: `cirra_ai_init()`
  - Tools: soql_query, sobject_dml, sobject_create, sobject_field_create, sobject_describe, metadata_create, tooling_api_query, tooling_api_dml, sf_connection_manage, link_build

- **Salesforce CLI** (optional): Required for scratch org operations
  - Commands: `sf org create scratch`, `sf org list`, `sf org delete scratch`, `sf org display`, `sf org open`

---

## License

MIT License - See LICENSE file for details.
