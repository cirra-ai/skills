## Flow MCP Patterns

### General rules

- Do **not** hard-code IDs (queues, users, record types) in flows
- Use Entry Conditions (formulas in the `start` block) instead of a Decision with an empty action
- Set layout to Auto-Layout (`CanvasMode: AUTO_LAYOUT_CANVAS`)
- Do **not** create a new flow to fix an issue — create a new **version** instead
- Do **not** say something "cannot be done via API" — always attempt it

### ⚠️ Query Tool Routing (prevents "sObject type not supported" errors)

Flow-related objects live in **two different APIs**. Using the wrong query
tool fails outright:

| Object                                                                       | API              | Query tool                   |
| ---------------------------------------------------------------------------- | ---------------- | ---------------------------- |
| `Flow`, `FlowDefinition`, `FlowTestCoverage`                                 | Tooling API      | `tooling_api_query` **only** |
| `FlowDefinitionView`, `FlowVersionView`, `FlowInterview`, `FlowInterviewLog` | Standard sObject | `soql_query` **only**        |

- `tooling_api_query` on `FlowDefinitionView` fails with
  `sObject type 'FlowDefinitionView' is not supported` — it is a standard
  object, not a Tooling API object.
- **Never use SOSL on flows.** `tooling_api_search` (SOSL) on `Flow` or
  `FlowDefinition` fails with `entity type Flow does not support search`,
  and `FlowDefinitionView` is not searchable either. To find a flow by
  name, use SOQL with `LIKE`:
  - `soql_query`: `SELECT DurableId, ApiName, Label FROM FlowDefinitionView WHERE ApiName LIKE '%Lead%' OR Label LIKE '%Lead%'`
  - or `tooling_api_query`: `SELECT Id, DeveloperName FROM FlowDefinition WHERE DeveloperName LIKE '%Lead%'`

**FlowDefinitionView columns** — it has **no `DeveloperName` and no `Status`**
(use `ApiName` for the name and `IsActive` for active state). Available
columns (verified via `sobject_describe`): `Id`, `DurableId`, `ApiName`,
`Label`, `Description`, `ProcessType`, `TriggerType`, `TriggerObjectOrEventId`,
`TriggerObjectOrEventLabel`, `TriggerOrder`, `RecordTriggerType`,
`NamespacePrefix`, `ActiveVersionId`, `LatestVersionId`, `VersionNumber`,
`IsActive`, `IsOutOfDate`, `IsTemplate`, `IsOverridable`, `OverriddenById`,
`OverriddenFlowId`, `SourceTemplateId`, `IsSwingFlow`, `Builder`,
`ManageableState`, `InstalledPackageName`, `HasAsyncAfterCommitPath`,
`Environments`, `SupportedEnvironments`, `ApiVersion`, `CapacityCategory`,
`AreMetricsLoggedToDataCloud`, `LastModifiedBy`, `LastModifiedDate`.

Note: on this object `LastModifiedBy` is a plain **text** field (the user's
display name), not a relationship — selecting it directly is valid here, and
there is no `LastModifiedById` column.

Flow catalog query (summary info about flows, e.g. finding Process Builder
processes to migrate):

```
soql_query(query="SELECT DurableId, ApiName, Label, Description, ProcessType, TriggerType, IsActive, LastModifiedDate, LastModifiedBy FROM FlowDefinitionView WHERE ProcessType = 'Workflow'")
```

### List all flows (with active and latest version info)

```
tooling_api_query(sObject="FlowDefinition", fields=["Id","DeveloperName","NamespacePrefix","MasterLabel","Description","ActiveVersionId","ActiveVersion.VersionNumber","LatestVersionId","LatestVersion.VersionNumber","LatestVersion.Status","LatestVersion.MasterLabel","LatestVersion.Description"])
```

### Retrieve a specific flow version

First get the version Id from the FlowDefinition query above, then:

```
tooling_api_query(sObject="Flow", fields=["Id","FullName","DefinitionId","Definition.DeveloperName","MasterLabel","Description","VersionNumber","Status","Metadata","ProcessType"], whereClause="Id='<flow version id>'")
```

Note: do **not** include `FullName` or `Metadata` in multi-record queries — only single-record retrieval supports these.

### Create a new flow

```
metadata_create(type="Flow", metadata=[{"fullName": "Flow_Name", "label": "Flow Name", "apiVersion": 65, "processType": "AutoLaunchedFlow", "status": "Draft", ...}])
```

### Update a flow (creates a new version)

1. Retrieve current metadata: `metadata_read(type="Flow", fullNames=["Flow_Name"])`
2. Apply changes to the metadata object
3. Deploy: `metadata_update(type="Flow", metadata=[{...}], upsert=True)`
   - **`upsert=True` is required when the flow's latest version is Active** — a plain update errors with _"active can't be overwritten."_ Upsert creates a new version instead of overwriting the active one.
   - **Do NOT change the `fullName`** — version numbers are managed automatically
   - In production: deploy as `status: Draft` and ask user to activate manually if you get an error

### Activate / deactivate a flow version

```
metadata_update(type="FlowDefinition", metadata=[{"fullName": "Flow_Name", "activeVersionNumber": <version>}])
```

To deactivate all versions: set `activeVersionNumber` to `0`.

### Delete a flow

1. Deactivate: `metadata_update(type="FlowDefinition", metadata=[{"fullName": "Flow_Name", "activeVersionNumber": 0}])`
2. Delete all versions: `tooling_api_dml(operation="delete", sObject="Flow", record={"Id": "<flow version id>"})` (repeat for each version)

### Check flow test coverage

```
tooling_api_query(sObject="Flow", fields=["Definition.DeveloperName"], whereClause="Status = 'Active' AND (ProcessType = 'AutolaunchedFlow' OR ProcessType = 'Workflow' OR ProcessType = 'CustomEvent' OR ProcessType = 'InvocableProcess') AND Id NOT IN (SELECT FlowVersionId FROM FlowTestCoverage)")
```

### Find paused or failed flow interviews

```
soql_query(sObject="FlowInterview", fields=["Id","Name","CurrentElement","InterviewStatus","PauseLabel","CreatedDate"], whereClause="InterviewStatus IN ('Paused', 'Failed')")
```

---
