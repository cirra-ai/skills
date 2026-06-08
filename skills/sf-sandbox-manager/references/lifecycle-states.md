# Lifecycle States

State machine documentation for `Environment_Pool__c.Status__c`.

## States

| State           | Description                                                |
| --------------- | ---------------------------------------------------------- |
| `Available`     | Ready for checkout. No user assigned.                      |
| `Checked_Out`   | Reserved by a user. Tracking who, when, and purpose.       |
| `Pending_Reset` | Returned dirty. Needs refresh before reuse.                |
| `Creating`      | Sandbox is being provisioned or refreshed. Not yet usable. |
| `Error`         | Provisioning or refresh failed. Needs manual intervention. |

## State Transitions

```
                    ┌──────────────────────────────────┐
                    │                                  │
                    ▼                                  │
Creating ──────→ Available ◄──────── Pending_Reset ◄──┤
    │               │                     ▲            │
    │               │                     │            │
    │               ▼                     │            │
    │          Checked_Out ───────────────┘            │
    │               │                                  │
    │               └── (clean) ──→ Available ─────────┘
    │
    └──────────→ Error
                    │
                    └──→ Creating (retry)
                    └──→ (Deleted)

Any state ──→ (Deleted) via Delete Environment workflow
```

## Transition Details

### Creating → Available

**Trigger**: Sandbox provisioning or refresh completes successfully.

**Detection**: Poll `SandboxProcess` via `tooling_api_query`. When `Status = 'Completed'`:

```
tooling_api_query(
  sObject="SandboxProcess",
  fields=["Id", "SandboxName", "Status", "CopyProgress"],
  whereClause="Id = '<sandbox_process_id>'",
  limit=1
)
```

**MCP calls**:

```
sobject_dml(
  sObject="Environment_Pool__c",
  operation="update",
  records=[{
    "Id": "<pool_record_id>",
    "Status__c": "Available",
    "Last_Reset__c": "<current_datetime_ISO>",
    "Sandbox_Process_Id__c": ""
  }]
)
```

### Available → Checked_Out

**Trigger**: User checks out an environment.

**MCP calls**:

```
sobject_dml(
  sObject="Environment_Pool__c",
  operation="update",
  records=[{
    "Id": "<pool_record_id>",
    "Status__c": "Checked_Out",
    "Checked_Out_By__c": "<user_email>",
    "Checkout_Timestamp__c": "<current_datetime_ISO>",
    "Expected_Return__c": "<expected_return_datetime_ISO>",
    "Purpose__c": "<purpose>"
  }]
)
```

### Checked_Out → Available (clean check-in)

**Trigger**: User returns environment in clean state.

**MCP calls**:

```
sobject_dml(
  sObject="Environment_Pool__c",
  operation="update",
  records=[{
    "Id": "<pool_record_id>",
    "Status__c": "Available",
    "Checked_Out_By__c": "",
    "Checkout_Timestamp__c": null,
    "Expected_Return__c": null,
    "Purpose__c": ""
  }]
)
```

### Checked_Out → Pending_Reset (dirty check-in)

**Trigger**: User returns environment that needs refresh.

**MCP calls**:

```
sobject_dml(
  sObject="Environment_Pool__c",
  operation="update",
  records=[{
    "Id": "<pool_record_id>",
    "Status__c": "Pending_Reset",
    "Checked_Out_By__c": "",
    "Checkout_Timestamp__c": null,
    "Expected_Return__c": null,
    "Purpose__c": ""
  }]
)
```

### Pending_Reset → Creating (refresh initiated)

**Trigger**: Admin initiates sandbox refresh.

**MCP calls**:

1. Get SandboxInfo ID:

```
tooling_api_query(
  sObject="SandboxInfo",
  fields=["Id", "SandboxName"],
  whereClause="SandboxName = '<sandbox_name>'",
  limit=1
)
```

2. Create SandboxProcess (triggers refresh):

```
tooling_api_dml(
  sObject="SandboxProcess",
  operation="create",
  records=[{
    "SandboxInfoId": "<sandbox_info_id>",
    "SandboxName": "<sandbox_name>",
    "LicenseType": "<type>"
  }]
)
```

3. Update pool record:

```
sobject_dml(
  sObject="Environment_Pool__c",
  operation="update",
  records=[{
    "Id": "<pool_record_id>",
    "Status__c": "Creating",
    "Sandbox_Process_Id__c": "<new_sandbox_process_id>"
  }]
)
```

### Creating → Error

**Trigger**: Sandbox provisioning or refresh fails.

**Detection**: `SandboxProcess.Status` is `Error` or process has been in `Processing`/`Pending` for an abnormally long time.

**Thresholds for "stuck" detection**:

- Developer/Developer Pro: > 2 hours
- Partial Copy: > 12 hours
- Full Copy: > 48 hours

**MCP calls**:

```
sobject_dml(
  sObject="Environment_Pool__c",
  operation="update",
  records=[{
    "Id": "<pool_record_id>",
    "Status__c": "Error"
  }]
)
```

### Error → Creating (retry)

**Trigger**: Admin retries provisioning after fixing the issue.

Same as Pending_Reset → Creating transition.

### Any State → (Deleted)

**Trigger**: Admin decommissions the environment.

**MCP calls**:

1. Delete the sandbox (if it exists):

```
tooling_api_dml(
  sObject="SandboxInfo",
  operation="delete",
  recordIds=["<sandbox_info_id>"]
)
```

2. Delete the pool record:

```
sobject_dml(
  sObject="Environment_Pool__c",
  operation="delete",
  recordIds=["<pool_record_id>"]
)
```

## Overdue Checkout Detection

A checkout is considered overdue when:

- `Status__c = 'Checked_Out'`
- `Expected_Return__c < NOW()`

The Pool Status workflow highlights overdue checkouts. No automatic action is taken — the skill informs the user and suggests contacting the person who has it checked out.

## Health Checks

During Pool Status, the skill performs these health checks:

| Check                | Condition                                | Action                       |
| -------------------- | ---------------------------------------- | ---------------------------- |
| Overdue checkout     | `Expected_Return__c` in the past         | Highlight in status table    |
| Stuck creating       | `Creating` beyond threshold (see above)  | Update to Error, notify user |
| Nearing expiry       | `Expiry_Date__c` within 7 days           | Warn in status table         |
| Orphaned pool record | No matching `SandboxInfo` in Tooling API | Flag for review              |
