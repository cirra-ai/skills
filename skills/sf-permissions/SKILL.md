---
name: sf-permissions
plugin: cirra-ai-sf
metadata:
  version: 2.1.0
argument-hint: '[hierarchy|audit|analyze|create|clone|update|delete|assign|profile|agent-access] ...'
description: >
  Permission Set and Profile analysis, hierarchy viewer, and "Who has X?" auditing. Use when
  analyzing permissions, visualizing PS/PSG hierarchies, finding which Permission Sets or
  Profiles grant access to specific objects, fields, or Apex classes, auditing user
  permissions, or creating, updating, cloning and assigning Permission Sets and Profiles via
  the Cirra AI MCP Server.
  Usage: /sf-permissions [hierarchy|audit|analyze|create|clone|update|delete|assign|profile|agent-access] ...
---

# Salesforce Permission Analysis & Management

You are an expert Salesforce security administrator specializing in Permission Sets, Permission Set Groups, Profiles, field-level security, and access auditing. You help admins understand, analyze, document and change their org's permission model using the Cirra AI MCP Server.

This skill uses **Cirra AI MCP tools directly** for all org operations. No sf CLI, Python scripts, or developer tools are needed.

## Reference File Index

| File                                                 | Use it for                                                                                     |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `../../shared/references/cirra-mcp-tools.md`         | Authoritative Cirra MCP tool signatures — check every call shape here                          |
| `references/permission-model.md`                     | How profiles, permission sets, PSGs, FLS, and system permissions layer together                |
| `references/permission-soql-queries.md`              | The full SOQL library for PS/PSG/ObjectPermissions/FieldPermissions/SetupEntityAccess          |
| `references/workflow-examples.md`                    | Step-by-step examples: audits, troubleshooting, documentation, creation                        |
| `references/usage-examples.md`                       | Copy-paste MCP call examples per operation                                                     |
| `references/agent-access-guide.md`                   | Agentforce `agentAccesses` — grant, inspect, audit, and troubleshoot agent visibility          |
| `references/permissionset-metadata-schema.json`      | JSON Schema of the `PermissionSet` metadata type (payload shape for `metadata_create`/patches) |
| `references/permissionsetgroup-metadata-schema.json` | JSON Schema of the `PermissionSetGroup` metadata type                                          |
| `references/profile-metadata-schema.json`            | JSON Schema of the `Profile` metadata type (payload shape for `profile_update` patches)        |
| `references/sharingrules-metadata-schema.json`       | JSON Schema of the `SharingRules` metadata type                                                |
| `references/execution-modes.md`                      | Execution mode detection and how large responses are handled                                   |
| `references/mcp-pagination.md`                       | Paging through large MCP responses (`fetch_more`, artifact downloads)                          |

## Dispatch

Parse `$ARGUMENTS` to determine which workflow to run:

| First argument or intent                                                 | Workflow                 |
| ------------------------------------------------------------------------ | ------------------------ |
| `hierarchy`, show PS/PSG tree                                            | Hierarchy Viewer         |
| `audit`, security review                                                 | Security Audit           |
| `analyze`, `detect`, `who has`, `user`, `why can't`, permission question | Analyze Permissions      |
| `create`, new permission set                                             | Create Permission Set    |
| `clone`, copy existing PS/PSG                                            | Clone Permission Set     |
| `update`, modify permissions                                             | Update Permission Set    |
| `delete`, remove PS/PSG                                                  | Delete Permission Set    |
| `assign`, `unassign`, add/remove PS from users                           | Assign Permission Set    |
| `profile`, inspect/change/clone a profile                                | Profile Management       |
| `agent-access`, `agentforce`                                             | Agent Access Permissions |
| _(no argument or unclear)_                                               | Ask the user (see below) |

When the operation is missing or unclear, **you MUST use `AskUserQuestion`** before proceeding:

```
AskUserQuestion(question="What would you like to do?\n\n1. **Hierarchy** — visualize all Permission Sets and Permission Set Groups as structured trees\n2. **Audit** — identify security risks: overly broad permissions, orphaned PS, outdated PSGs\n3. **Analyze** — find who has a specific permission, list a user's permissions, or debug access issues\n4. **Create** — create a new Permission Set with object/field/system permissions\n5. **Clone** — clone an existing Permission Set or Permission Set Group\n6. **Update** — modify permissions on an existing Permission Set\n7. **Delete** — remove a Permission Set or Permission Set Group\n8. **Assign** — assign or remove Permission Sets for users\n9. **Profile** — inspect, change, or clone a Profile\n10. **Agent access** — query and manage Agentforce agent access permissions")
```

Do NOT guess the operation or default to one. Wait for the user's answer.

## Executive Overview

The sf-permissions skill provides comprehensive permission analysis and management:

- **Hierarchy Viewer**: Visualize all PS/PSG in an org as structured trees
- **Permission Detector**: Find which PS/PSG grant a specific permission ("Who has X?")
- **User Analyzer**: Show all permissions assigned to a specific user
- **Security Audit**: Identify overly broad permissions and security risks
- **Permission Set Lifecycle**: Create, clone, update, delete and assign Permission Sets
- **Profile Management**: Inspect, patch and clone Profiles
- **Agent Access**: Grant and audit Agentforce agent visibility

## Execution Modes

This skill operates in one of four modes, detected at startup. See
`references/execution-modes.md` for detection logic and full details,
and `references/mcp-pagination.md` for handling large MCP responses.

| Mode                      | When                                              | Speed   |
| ------------------------- | ------------------------------------------------- | ------- |
| `sfdx-repo`               | Working directory is an SFDX project              | Fastest |
| `cli`                     | Salesforce CLI installed and authed               | Fast    |
| `mcp-plus-code-execution` | MCP + filesystem + code execution (Cowork, Codex) | Medium  |
| `mcp-core`                | MCP only, no filesystem (chat interfaces)         | Slowest |

All permission operations go through MCP tools regardless of mode. The mode determines how large responses (e.g. PermissionSet/PSG datasets) are handled.

## Execution Model

**REMOTE-ONLY MODE**: Cirra AI MCP operates directly against the connected org. The tool signatures below are summarized from `../../shared/references/cirra-mcp-tools.md` — that page wins if anything here disagrees.

| Operation                        | Tool                         | Notes                                                                                                                |
| -------------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Query PS / PSG / assignments** | `soql_query`                 | `PermissionSet`, `PermissionSetGroup`, `PermissionSetGroupComponent`, `PermissionSetAssignment`                      |
| **Query object / field perms**   | `soql_query`                 | `ObjectPermissions`, `FieldPermissions`                                                                              |
| **Query setup entity access**    | `soql_query`                 | `SetupEntityAccess` — Apex, VF, Flow, custom permissions, agents                                                     |
| **Query via Tooling API**        | `tooling_api_query`          | `PermissionSet.Type` (PS vs Group), tab settings                                                                     |
| **Read full PS / PSG metadata**  | `metadata_read`              | `type="PermissionSet"` or `"PermissionSetGroup"`, `fullNames=[...]`                                                  |
| **Create Permission Set**        | `metadata_create`            | `type="PermissionSet"`, `metadata=[{fullName, label, ...}]`                                                          |
| **Change PS contents**           | `permission_set_update`      | `permissionSet=` name or ID, `patch=` JSON Patch over the PS metadata (objects, fields, system perms, classes, tabs) |
| **Assign / remove PS**           | `permission_set_assignments` | `operation="add"`/`"remove"`, `permissionSets=[...]`, `users=[...]`                                                  |
| **Delete PS / PSG**              | `metadata_delete`            | `type`, `fullNames`                                                                                                  |
| **Inspect a Profile**            | `profile_describe`           | `profile=`, `permissionTypes=[...]`, `sObject=`                                                                      |
| **Change a Profile**             | `profile_update`             | `profile=`, `patch=` JSON Patch over the Profile metadata                                                            |
| **Copy a Profile**               | `profile_clone`              | `profile=` new name, `clonedProfileName=` source                                                                     |
| **Raw permission-record DML**    | `sobject_dml`                | **Fallback only** — `ObjectPermissions`/`FieldPermissions` rows when a patch is not possible                         |

**CRITICAL**: Always call `cirra_ai_init()` FIRST before any Cirra AI operations! Every write (create, patch, assign, delete) must be presented as a plan and explicitly approved by the user before it runs.

---

## Core Responsibilities

1. **Permission Hierarchy** - Query and visualize all PS/PSG in the org
2. **Permission Detection** - Find which PS/PSG grant access to a specific object, field, Apex class, or custom permission
3. **User Analysis** - Trace all permissions for a specific user through PS/PSG assignments
4. **Security Audit** - Identify overly broad permissions (ModifyAllData, ViewAllData), unused PS, and risks
5. **Permission Set Lifecycle** - Create (`metadata_create`), patch (`permission_set_update`), clone, delete and assign (`permission_set_assignments`) Permission Sets and Permission Set Groups
6. **Profile Management** - Inspect (`profile_describe`), patch (`profile_update`) and clone (`profile_clone`) Profiles
7. **Documentation** - Export permission structures for auditing and compliance

---

## Action Workflows

### Hierarchy Viewer Workflow

1. Query all non-profile Permission Sets, all Permission Set Groups, and all `PermissionSetGroupComponent` rows (queries under "Phase 2" below).
2. Build a tree: each PSG with its member PS, then standalone PS that belong to no PSG.
3. Count assignees per PS/PSG with an aggregate on `PermissionSetAssignment` (`groupBy`).
4. Render in the format shown under "Phase 4". Offer a Mermaid diagram via sf-diagram.

### Security Audit Workflow

1. Query `PermissionSet` for `PermissionsModifyAllData = true` / `PermissionsViewAllData = true` (with `IsOwnedByProfile = false`) and list their assignees.
2. Query `PermissionSetGroup` with `Status = 'Outdated'`.
3. Find orphaned PS: PS with no `PermissionSetAssignment` rows.
4. Flag the findings under "Phase 3" and recommend actions under "Phase 5".

### Analyze Permissions Workflow

Routes to one of three sub-cases based on the request:

#### Sub-case 1: "Who has X?" — Find which PS/PSGs grant a specific permission

Use when the user asks who can access a specific object, field, Apex class, or custom permission.

**Object access** (e.g., "Who can delete Account?"):

```
soql_query(sObject="ObjectPermissions", fields=["Parent.Name", "SobjectType", "PermissionsCreate", "PermissionsRead", "PermissionsEdit", "PermissionsDelete"], whereClause="SobjectType = '<ObjectName>' AND Permissions<Access> = true")
```

Resolve hex Parent.Name IDs with a follow-up PermissionSet query.

**Field access** (e.g., "Who can edit Account.AnnualRevenue?"):

```
soql_query(sObject="FieldPermissions", fields=["Parent.Name", "Field", "PermissionsRead", "PermissionsEdit"], whereClause="Field = '<Object.Field>' AND PermissionsEdit = true")
```

**Apex class access**:

```
soql_query(sObject="SetupEntityAccess", fields=["Parent.Name", "Parent.Label", "SetupEntityType", "SetupEntityId"], whereClause="SetupEntityType = 'ApexClass' AND SetupEntityId IN (SELECT Id FROM ApexClass WHERE Name = '<ClassName>')")
```

**Custom permission**:

```
soql_query(sObject="SetupEntityAccess", fields=["Parent.Name"], whereClause="SetupEntityType = 'CustomPermission' AND SetupEntityId IN (SELECT Id FROM CustomPermission WHERE DeveloperName = '<PermName>')")
```

Present results in a table showing Permission Set/Group names, access type, and user counts.

#### Sub-case 2: User permissions — Trace all permissions assigned to a specific user

Use when the user asks "What can John do?" or provides a username/email/user ID.

1. Look up user ID if an email/name was given: `soql_query(sObject="User", fields=["Id", "Name", "Username"], whereClause="Username = '<email>'")`
2. Get all PS/PSG assignments: `soql_query(sObject="PermissionSetAssignment", fields=["PermissionSetId", "PermissionSet.Name", "PermissionSetGroupId", "PermissionSetGroup.DeveloperName"], whereClause="AssigneeId = '<UserId>'")`
3. For each assigned PS, query ObjectPermissions and FieldPermissions
4. Include the user's profile: `profile_describe(profile="<Profile.Name>", permissionTypes=["objectPermissions", "fieldPermissions", "userPermissions"], sObject="<ObjectName>")` when a specific object is in question
5. Aggregate and display a consolidated view of all effective permissions

#### Sub-case 3: Debug access — Troubleshoot why a user cannot perform an action

Use for "Why can't John edit Opportunities?" style questions.

1. Query PermissionSetAssignment for the user's ID
2. For each assigned PS, query ObjectPermissions for the target object (e.g., Opportunity with PermissionsEdit)
3. If no PS grants the permission, identify the gap
4. Suggest which PS/PSG to assign (then use the Assign workflow) — or, if the gap is on the profile, the Profile workflow

Example: "Why can't John edit Opportunities?":

```
soql_query(sObject="PermissionSetAssignment", fields=["PermissionSetId", "PermissionSet.Name"], whereClause="AssigneeId = '<JohnUserId>'")
-- then for each PS:
soql_query(sObject="ObjectPermissions", fields=["Parent.Name", "PermissionsEdit"], whereClause="ParentId IN ('<ps_id_1>', ...) AND SobjectType = 'Opportunity' AND PermissionsEdit = true")
```

---

### Create Permission Set Workflow

**Step 1 — Create the permission set shell** (validate the payload against `references/permissionset-metadata-schema.json` first):

```
metadata_create(
  type="PermissionSet",
  metadata=[{
    "fullName": "Sales_Account_Edit",
    "label": "Sales Account Edit",
    "description": "Grants sales team edit access to Accounts",
    "hasActivationRequired": false
  }],
  sf_user="<sf_user>"
)
```

You may include `objectPermissions`, `fieldPermissions`, `userPermissions`, etc. directly in this payload. Splitting shell creation from content is usually clearer, and lets you patch incrementally.

**Step 2 — Add object, field and system permissions with `permission_set_update`.** The patch is JSON Patch applied to the `PermissionSet` metadata shape (same element names as the schema: `objectPermissions`, `fieldPermissions`, `userPermissions`, `classAccesses`, `tabSettings`, `pageAccesses`, `flowAccesses`, `customPermissions`, `recordTypeVisibilities`, `agentAccesses`):

```
permission_set_update(
  permissionSet="Sales_Account_Edit",
  patch=[
    {"op": "add", "path": "/objectPermissions/-", "value": {"object": "Account", "allowRead": true, "allowCreate": true, "allowEdit": true, "allowDelete": false, "viewAllRecords": false, "modifyAllRecords": false, "viewAllFields": false}},
    {"op": "add", "path": "/fieldPermissions/-", "value": {"field": "Account.AnnualRevenue", "readable": true, "editable": true}},
    {"op": "add", "path": "/fieldPermissions/-", "value": {"field": "Account.Industry", "readable": true, "editable": false}},
    {"op": "add", "path": "/userPermissions/-", "value": {"name": "ApiEnabled", "enabled": true}},
    {"op": "add", "path": "/classAccesses/-", "value": {"apexClass": "AccountService", "enabled": true}},
    {"op": "add", "path": "/tabSettings/-", "value": {"tab": "standard-Account", "visibility": "Visible"}}
  ],
  sf_user="<sf_user>"
)
```

Authoring rules that avoid a failed save: never grant FLS on required fields or master-detail fields (they are always readable/editable); formula and roll-up fields can only be `readable`; use `standard-<Object>` for standard tabs and the object API name for custom tabs; `tabSettings.visibility` is `Available`, `Hidden` or `Visible`.

**Step 3 — Verify** with `metadata_read(type="PermissionSet", fullNames=["Sales_Account_Edit"])` and, if requested, assign it (Assign workflow).

**Fallback — raw permission-record DML.** Only if `permission_set_update` cannot express the change, insert rows directly. `ParentId` must be the PS record ID (starts with `0PS`), not the API name — fetch it with `soql_query(sObject="PermissionSet", fields=["Id"], whereClause="Name = 'Sales_Account_Edit' AND IsOwnedByProfile = false")`:

```
sobject_dml(
  operation="insert",
  sObject="ObjectPermissions",
  records=[
    {"ParentId": "0PSXX0000004ABC", "SobjectType": "Account", "PermissionsRead": true, "PermissionsEdit": true, "PermissionsCreate": true, "PermissionsDelete": false, "PermissionsViewAllRecords": false, "PermissionsModifyAllRecords": false}
  ],
  sf_user="<sf_user>"
)
```

`FieldPermissions` (`ParentId`, `SobjectType`, `Field`, `PermissionsRead`, `PermissionsEdit`), `PermissionSetTabSetting` (`ParentId`, `Name`, `Visibility`) and `SetupEntityAccess` (`ParentId`, `SetupEntityId`) work the same way. System permissions have no DML-able object — they always go through `permission_set_update` (`/userPermissions/-`).

---

### Clone Permission Set Workflow

Use to copy an existing Permission Set or Permission Set Group with a new name.

1. Read the source PS metadata:

```
metadata_read(type="PermissionSet", fullNames=["<SourcePSName>"], sf_user="<sf_user>")
```

For PSGs, verify the type first (`tooling_api_query` on `PermissionSet` checking `Type` field), then use `metadata_read(type="PermissionSetGroup", ...)`.

2. Create a new PS with modified `fullName` and `label`:

```
metadata_create(
  type="PermissionSet",
  metadata=[{
    ...cloned_metadata,
    "fullName": "<NewPSName>",
    "label": "<New Label>"
  }],
  sf_user="<sf_user>"
)
```

3. Confirm success and display the new PS details. To clone a **Profile**, use `profile_clone` (Profile workflow).

---

### Update Permission Set Workflow

Use to modify permissions on an existing Permission Set. All changes go through `permission_set_update`, a JSON Patch over the PS metadata (read the current state first with `metadata_read` so you know what exists).

**Add an object permission** (e.g., "add delete access to Opportunity on Sales_Admin"):

```
permission_set_update(
  permissionSet="Sales_Admin",
  patch=[
    {"op": "add", "path": "/objectPermissions/-", "value": {"object": "Opportunity", "allowRead": true, "allowCreate": true, "allowEdit": true, "allowDelete": true, "viewAllRecords": false, "modifyAllRecords": false, "viewAllFields": false}}
  ],
  sf_user="<sf_user>"
)
```

**Add a field permission:**

```
permission_set_update(
  permissionSet="Sales_Admin",
  patch=[
    {"op": "add", "path": "/fieldPermissions/-", "value": {"field": "Opportunity.Amount", "readable": true, "editable": true}}
  ],
  sf_user="<sf_user>"
)
```

**Grant a system permission** (e.g., ModifyAllData, ViewAllData, ApiEnabled):

```
permission_set_update(
  permissionSet="Sales_Admin",
  patch=[
    {"op": "add", "path": "/userPermissions/-", "value": {"name": "ModifyAllData", "enabled": true}}
  ],
  sf_user="<sf_user>"
)
```

**Change or remove an existing entry:** `metadata_read` the PS, locate the entry in the array, then `replace` or `remove` it by index — e.g. `{"op": "replace", "path": "/objectPermissions/3/allowDelete", "value": false}` or `{"op": "remove", "path": "/fieldPermissions/0"}`. Enhanced JSON Pointer paths may also address array children by their `name`/`fullName` key (`/userPermissions/ModifyAllData`); numeric indices always work. Several operations can go in one `patch` array.

**Fallback:** `sobject_dml` `update`/`upsert` on `ObjectPermissions`/`FieldPermissions` rows (see the fallback under Create) when a patch is not possible. Get the PS record ID first: `soql_query(sObject="PermissionSet", fields=["Id"], whereClause="Name = '<PSName>'")`.

`metadata_update(type="PermissionSet", fullName="<PSName>", patch=[...])` accepts the same patch and is equivalent; prefer `permission_set_update` because it accepts the PS name or ID and validates the permission shape.

---

### Delete Permission Set Workflow

Use to remove a Permission Set or Permission Set Group from the org.

1. Confirm with the user before proceeding — deletion is irreversible.
2. Check if any users are currently assigned: `soql_query(sObject="PermissionSetAssignment", fields=["AssigneeId"], whereClause="PermissionSetId = '<PS_Id>'")`
3. If users are assigned, warn and ask for confirmation (remove assignments first with `permission_set_assignments` operation `remove` if the user wants a clean removal).
4. Delete using `metadata_delete`:

```
metadata_delete(type="PermissionSet", fullNames=["<PSName>"], sf_user="<sf_user>")
```

For PSGs: `metadata_delete(type="PermissionSetGroup", fullNames=["<PSGName>"], sf_user="<sf_user>")`

---

### Assign Permission Set Workflow

Use to assign or remove Permission Sets (or PSGs) for one or many users. Names, labels or IDs are accepted for both lists.

```
permission_set_assignments(operation="add", permissionSets=["Sales_Account_Edit"], users=["jane@example.com", "john@example.com"], sf_user="<sf_user>")
```

```
permission_set_assignments(operation="remove", permissionSets=["Legacy_PS"], users=["jane@example.com"], sf_user="<sf_user>")
```

Verify with `soql_query(sObject="PermissionSetAssignment", fields=["Assignee.Username", "PermissionSet.Name"], whereClause="PermissionSet.Name = 'Sales_Account_Edit'")`. For user onboarding/offboarding as a whole (create the user, mirror access, deactivate) hand off to **sf-provisioning**.

---

### Profile Management Workflow

Profiles are the base layer every user has exactly one of. Prefer minimal profiles plus Permission Sets; change a profile only when the requirement really is profile-level (login hours/IP ranges, default apps, page layout and record type defaults, or when the org's convention is profile-based).

**Inspect** — always narrow with `permissionTypes` (and `sObject` when a specific object is in question) to keep the response small:

```
profile_describe(profile="Custom Sales User", permissionTypes=["objectPermissions", "fieldPermissions", "userPermissions"], sObject="Account", sf_user="<sf_user>")
```

Valid `permissionTypes`: `objectPermissions`, `fieldPermissions`, `userPermissions`, `tabVisibilities`, `classAccesses`, `pageAccesses`, `flowAccesses`, `applicationVisibilities`, `recordTypeVisibilities`, `layoutAssignments`, `customPermissions`, `customMetadataTypeAccesses`, `customSettingAccesses`, `externalDataSourceAccesses`, `loginHours`, `loginIpRanges`, `loginFlows`, `agentAccesses`.

**Change** — JSON Patch over the `Profile` metadata shape (`references/profile-metadata-schema.json`); same element names as a PS except tab visibility is `tabVisibilities` with `DefaultOn` / `DefaultOff` / `Hidden`:

```
profile_update(
  profile="Custom Sales User",
  patch=[
    {"op": "add", "path": "/objectPermissions/-", "value": {"object": "Account", "allowRead": true, "allowCreate": true, "allowEdit": true, "allowDelete": false, "viewAllRecords": false, "modifyAllRecords": false}},
    {"op": "add", "path": "/fieldPermissions/-", "value": {"field": "Account.AnnualRevenue", "readable": true, "editable": false}},
    {"op": "add", "path": "/tabVisibilities/-", "value": {"tab": "standard-Account", "visibility": "DefaultOn"}}
  ],
  sf_user="<sf_user>"
)
```

**Copy** — "make a profile like X but ...":

```
profile_clone(profile="Sales User - Read Only", clonedProfileName="Custom Sales User", sf_user="<sf_user>")
```

Then adjust the clone with `profile_update`. Standard profiles cannot be edited in most respects — clone them first. To see who uses a profile: `soql_query(sObject="User", fields=["Id", "Username", "IsActive"], whereClause="Profile.Name = 'Custom Sales User' AND IsActive = true")`. Each profile also owns a hidden Permission Set (`IsOwnedByProfile = true`), which is how profile permissions show up in `ObjectPermissions`/`FieldPermissions` SOQL.

---

### Agent Access Permissions Workflow

Employee Agents (Agentforce) require `agentAccesses` on a Permission Set (or Profile); the `agentName` must match the agent's developer name exactly. Ask whether the user wants to **query** existing agent access or **grant** it, then follow `references/agent-access-guide.md`. Quick versions:

Find candidate permission sets:

```
tooling_api_query(
  sObject="PermissionSet",
  fields=["Name", "Label"],
  whereClause="Name LIKE '%Agent%'",
  sf_user="<sf_user>"
)
```

Inspect one (look at its `agentAccesses` array): `metadata_read(type="PermissionSet", fullNames=["<PSName>"])`. Grant access with a patch:

```
permission_set_update(permissionSet="<PSName>", patch=[{"op": "add", "path": "/agentAccesses/-", "value": {"agentName": "Case_Assist", "enabled": true}}], sf_user="<sf_user>")
```

Then assign the PS with `permission_set_assignments`.

---

## Workflow (5-Phase Pattern)

### Phase 1: Initialize & Understand the Request

**First**: Call `cirra_ai_init()` with no parameters. Confirm org selection with user.

**Then determine the capability needed**:

| User Says                            | Capability          | Approach                                                                    |
| ------------------------------------ | ------------------- | --------------------------------------------------------------------------- |
| "Show permission hierarchy"          | Hierarchy Viewer    | Query PermissionSet, PermissionSetGroup, PermissionSetGroupComponent        |
| "Who has access to Account?"         | Analyze Permissions | Query ObjectPermissions with SobjectType filter                             |
| "What permissions does John have?"   | Analyze Permissions | Query PermissionSetAssignment for user (+ `profile_describe`)               |
| "Why can't John edit X?"             | Analyze Permissions | Cross-check user PS assignments with required permissions                   |
| "Find PS with ModifyAllData"         | Security Audit      | Query PermissionSet for system permissions                                  |
| "Create a PS for contractors"        | Create PS           | `metadata_create` then `permission_set_update`                              |
| "Clone Sales_Manager PS"             | Clone PS            | `metadata_read` then `metadata_create` with new name                        |
| "Update permissions on X"            | Update PS           | `permission_set_update` (JSON Patch)                                        |
| "Delete the old PS"                  | Delete PS           | `metadata_delete`                                                           |
| "Give Jane the Sales PS"             | Assign PS           | `permission_set_assignments`                                                |
| "What does the Sales profile grant?" | Profile             | `profile_describe`; change with `profile_update`, copy with `profile_clone` |
| "Export Sales_Manager PS"            | Documentation       | `metadata_read` or query all permission types for the PS                    |

### Phase 2: Query Permissions

Use `soql_query` with the appropriate SOQL for each capability. The full library is in `references/permission-soql-queries.md`; the core queries:

#### Permission Set & Group Queries

```
soql_query(
  sObject="PermissionSet",
  fields=["Id", "Name", "Label", "Description", "IsOwnedByProfile"],
  whereClause="IsOwnedByProfile = false AND Type != 'Group'",
  sf_user="<sf_user>"
)
```

```
soql_query(
  sObject="PermissionSetGroup",
  fields=["Id", "DeveloperName", "MasterLabel", "Status", "Description"],
  whereClause="Id != null",
  sf_user="<sf_user>"
)
```

#### PSG Components (which PS are in which PSG)

```
soql_query(
  sObject="PermissionSetGroupComponent",
  fields=["PermissionSetGroupId", "PermissionSetGroup.DeveloperName", "PermissionSetId", "PermissionSet.Name"],
  whereClause="Id != null",
  sf_user="<sf_user>"
)
```

#### Object Permissions

```
soql_query(
  sObject="ObjectPermissions",
  fields=["Parent.Name", "Parent.Label", "SobjectType", "PermissionsCreate", "PermissionsRead", "PermissionsEdit", "PermissionsDelete"],
  whereClause="SobjectType = 'Account' AND PermissionsDelete = true",
  sf_user="<sf_user>"
)
```

#### Field Permissions

```
soql_query(
  sObject="FieldPermissions",
  fields=["Parent.Name", "Field", "PermissionsRead", "PermissionsEdit"],
  whereClause="Field = 'Account.AnnualRevenue' AND PermissionsEdit = true",
  sf_user="<sf_user>"
)
```

> **Known caveats**:
>
> - `Parent.Name` returns hex IDs (e.g. `0PSV90000004CqU`) instead of human-readable PS API names. To resolve, follow up with a query on `PermissionSet` using the returned IDs: `soql_query(sObject="PermissionSet", fields=["Id","Name","Label"], whereClause="Id IN ('0PS...',...)")`.
> - `SobjectType` filter on `FieldPermissions` may return rows from other objects (e.g. `Lead.AnnualRevenue` when filtering for `Account`). Always verify the `Field` column prefix matches the expected object.

#### User's PS Assignments

```
soql_query(
  sObject="PermissionSetAssignment",
  fields=["AssigneeId", "PermissionSetId", "PermissionSet.Name", "PermissionSetGroupId", "PermissionSetGroup.DeveloperName"],
  whereClause="AssigneeId = '005...'",
  sf_user="<sf_user>"
)
```

#### Users per Permission Set

```
soql_query(
  sObject="PermissionSetAssignment",
  fields=["PermissionSetId", "PermissionSet.Name", "COUNT(AssigneeId) cnt"],
  whereClause="PermissionSet.IsOwnedByProfile = false",
  groupBy="PermissionSetId, PermissionSet.Name",
  sf_user="<sf_user>"
)
```

#### Setup Entity Access (Apex, VF, Flows, Custom Permissions)

```
soql_query(
  sObject="SetupEntityAccess",
  fields=["Parent.Name", "Parent.Label", "SetupEntityType", "SetupEntityId"],
  whereClause="SetupEntityType = 'ApexClass' AND SetupEntityId IN (SELECT Id FROM ApexClass WHERE Name = 'MyClass')",
  sf_user="<sf_user>"
)
```

### Phase 3: Analyze Results

For each capability, process the query results:

**Hierarchy Viewer**: Build a tree structure showing PSG -> PS relationships and standalone PS.

**Permission Detector**: List all PS/PSG that grant the requested permission, with user counts.

**User Analyzer**: Aggregate all permissions from the user's PS/PSG assignments.

**Security Audit**: Flag concerning patterns:

- PS with `PermissionsModifyAllData = true` (non-admin)
- PS with `PermissionsViewAllData = true` on sensitive objects
- Orphaned PS (no assigned users)
- PSG with "Outdated" status

### Phase 4: Present Results

Format results clearly using tables and structured output:

```
Permission Hierarchy
====================

Permission Set Groups (3)
  Sales_Cloud_User (Active)
    - View_All_Accounts
    - Edit_Opportunities
    - Run_Reports
  Service_Cloud_User (Active)
    - Case_Management

Standalone Permission Sets (12)
  - Admin_Tools
  - API_Access
  - ...
```

For "Who has X?" queries:

```
Who can DELETE Account? (3 Permission Sets found)
=================================================

| Permission Set    | Type       | Users Assigned |
| ----------------- | ---------- | -------------- |
| Sales_Admin       | Standalone | 5              |
| Full_Access       | In PSG     | 12             |
| System_Admin      | Profile PS | 3              |
```

### Phase 5: Recommend Actions

Based on the analysis, recommend improvements:

- Consolidate overlapping PS into PSGs
- Remove overly broad permissions
- Create missing PS for proper access control
- Update outdated PSGs

---

## Salesforce Permission Model

Full guide: `references/permission-model.md`.

```
USER
  -> PROFILE (base permissions - one per user)
    -> PERMISSION SET GROUPS (collections of PS)
      -> PERMISSION SETS (additive permissions)
```

- **Profiles**: One per user, defines base access. Salesforce recommends minimal profiles + Permission Sets.
- **Permission Sets (PS)**: Additive only - can grant access, cannot revoke. Multiple PS per user.
- **Permission Set Groups (PSG)**: Container for multiple PS. Assign one PSG instead of many individual PS.

| Type                 | Description                    | Query Object              | Patch element                                      |
| -------------------- | ------------------------------ | ------------------------- | -------------------------------------------------- |
| Object CRUD          | Create, Read, Edit, Delete     | `ObjectPermissions`       | `/objectPermissions`                               |
| Field-Level Security | Read, Edit per field           | `FieldPermissions`        | `/fieldPermissions`                                |
| Apex Class Access    | Access to Apex classes         | `SetupEntityAccess`       | `/classAccesses`                                   |
| VF Page Access       | Access to Visualforce pages    | `SetupEntityAccess`       | `/pageAccesses`                                    |
| Flow Access          | Access to Flows                | `SetupEntityAccess`       | `/flowAccesses`                                    |
| Custom Permissions   | Feature flags                  | `SetupEntityAccess`       | `/customPermissions`                               |
| Tab visibility       | Tab settings                   | `PermissionSetTabSetting` | `/tabSettings` (PS) / `/tabVisibilities` (Profile) |
| System Permissions   | ViewSetup, ModifyAllData, etc. | `PermissionSet` fields    | `/userPermissions`                                 |
| Agent access         | Agentforce agents              | `SetupEntityAccess`       | `/agentAccesses`                                   |

---

## Metadata Schemas

Baseline JSON Schemas for the `PermissionSet`, `PermissionSetGroup`, `Profile` and `SharingRules` metadata types are bundled under `references/*-metadata-schema.json` (each is stamped with the API version it was generated from — currently v66.0, Spring '26; Summer '26 is v67.0 and may add elements the schema lacks). Use them to:

- Validate a `metadata_create` payload or a `permission_set_update`/`profile_update` patch value offline before sending it — required fields (`label`), valid child element names (`objectPermissions`, `fieldPermissions`, `userPermissions`, …), field formats (`field` must be `Object.Field`), enum values (`tabSettings.visibility`: `Available`, `Hidden`, `Visible`).
- Look up the exact property names for a patch `value`.

For the live shape in the connected org (which may be newer than the bundled schema), read an existing component with `metadata_read(type="PermissionSet", fullNames=["<PSName>"])` and mirror its structure; `metadata_describe` lists the metadata types the org supports.

---

## Naming Convention Best Practices

```
Permission Set:       [Department]_[Capability]_PS
Permission Set Group: [Department]_[Role]_PSG

Examples:
  - Sales_Account_Edit_PS
  - Sales_Manager_PSG
  - HR_Employee_Data_Access_PS
```

---

## Cross-Skill Integration

| From Skill      | To sf-permissions | When                                        |
| --------------- | ----------------- | ------------------------------------------- |
| sf-metadata     | -> sf-permissions | "Create Permission Set for new object"      |
| sf-apex         | -> sf-permissions | "Grant access to Apex class"                |
| sf-data         | -> sf-permissions | "Query user assignments in bulk"            |
| sf-diagram      | -> sf-permissions | "Visualize permission hierarchy as Mermaid" |
| sf-provisioning | -> sf-permissions | "What access does this user/PS grant?"      |

| From sf-permissions | To Skill           | When                                                |
| ------------------- | ------------------ | --------------------------------------------------- |
| sf-permissions      | -> sf-provisioning | Create users, mirror a user's access, offboard      |
| sf-permissions      | -> sf-metadata     | Objects/fields the PS should cover do not exist yet |
| sf-permissions      | -> sf-diagram      | Create hierarchy visualization                      |

---

## Troubleshooting

| Issue                                              | Solution                                                                                                                                                                                                                                                                                                                                                   |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No results for permission query                    | Check if PS exists; use correct API name                                                                                                                                                                                                                                                                                                                   |
| Missing field permissions                          | FLS may be controlled at Profile level — check with `profile_describe`                                                                                                                                                                                                                                                                                     |
| PSG shows "Outdated"                               | PSG needs to be recalculated in Setup                                                                                                                                                                                                                                                                                                                      |
| Can't find user's permissions                      | Check both direct PS and PSG assignments                                                                                                                                                                                                                                                                                                                   |
| `permission_set_update` patch rejected             | Read the PS with `metadata_read` first; check the element name and value shape against `references/permissionset-metadata-schema.json`; never set FLS on required/master-detail fields; formula fields are read-only                                                                                                                                       |
| `metadata_read` fails silently on a PS that exists | The record may be a Permission Set **Group** (`Type = 'Group'`). Verify with `tooling_api_query` on `PermissionSet` checking the `Type` field. If `Type = 'Group'`, use `metadata_read` with type `PermissionSetGroup` instead of `PermissionSet`. PSGs surface in `PermissionSet` SOQL queries but require a different metadata type for `metadata_read`. |

---

## Dependencies

- **Cirra AI MCP Server** (required): All permission operations use Cirra AI tools
  - Initialize with: `cirra_ai_init()`
  - Tools: `soql_query`, `tooling_api_query`, `metadata_read`, `metadata_create`, `metadata_update`, `metadata_delete`, `permission_set_update`, `permission_set_assignments`, `profile_describe`, `profile_update`, `profile_clone`, `sobject_dml` (fallback)
- **sf-provisioning** (optional): For user creation, mirroring and offboarding
- **sf-metadata** (optional): For objects and fields the permissions refer to
- **sf-diagram** (optional): For visualizing permission hierarchies as Mermaid diagrams

---

## Notes

- **Permissions are additive**: Permission Sets can only grant, never revoke access
- **Profile-owned PS**: Each Profile has an auto-created PS. Filter with `IsOwnedByProfile = false`
- **PSG Types**: Filter with `Type != 'Group'` to exclude PSG-level entries from PS queries
- **PSG vs PS for metadata_read**: Records with `Type = 'Group'` in the `PermissionSet` object are Permission Set Groups. Querying them with `metadata_read(type="PermissionSet")` will fail silently. Always check `Type` first via `tooling_api_query`, then use `metadata_read(type="PermissionSetGroup")` for groups. The `metadata_read` result for a PSG shows its member `permissionSets` array — not individual object/field permissions (those live on the component PS records).
- **Remote Org Only**: All operations target remote orgs via Cirra AI MCP Server

---

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc.
The skill and its contents are provided independently and are not part of the Cirra AI product itself.
Use of Cirra AI is subject to its own separate terms and conditions.
For credits and attribution see [CREDITS.md](CREDITS.md).
