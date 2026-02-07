---
name: sf-permissions
description: >
  Salesforce Permission Set analysis, hierarchy viewer, and "Who has X?" auditing
  via Cirra AI MCP tools. Use when analyzing permissions, visualizing PS/PSG hierarchies,
  finding which Permission Sets grant access to specific objects, fields, or Apex classes,
  auditing user access, or managing Permission Set assignments. Requires the Cirra AI
  MCP connector.
---

# sf-permissions

Salesforce Permission Set analysis, visualization, and auditing via **Cirra AI MCP tools**.

## Connecting to the Org

Call `cirra_ai_init` with `scope: "global"` before any queries. Confirm the connected org with the user before proceeding.

## Cirra AI soql_query — Required Parameters

**Every** parameter must be provided or the call fails with a validation error:

```
sObject:     "PermissionSet"                    # Required
fields:      ["Id", "Name", "Label"]            # Required — JSON array
whereClause: "IsOwnedByProfile = false"         # Required — use "" if none
orderBy:     "Label ASC"                        # Required — use "" if none
groupBy:     ""                                 # Required — use "" if none
limit:       200                                # Required — integer
```

Omitting `orderBy` or `groupBy` causes `invalid_type: expected string, received undefined`.

### Other Useful Cirra AI Tools

| Tool                                | Purpose                                                                 |
| ----------------------------------- | ----------------------------------------------------------------------- |
| `soql_query`                        | Query PS, PSG, assignments, object/field/setup entity permissions       |
| `tooling_api_query`                 | Tab settings, system permissions, `UserEntityAccess`, `UserFieldAccess` |
| `metadata_read`                     | Read full PS metadata (type `PermissionSet`, fullNames array)           |
| `permission_set_create`             | Create a new PS                                                         |
| `permission_set_update`             | Modify object, field, system permissions on a PS                        |
| `permission_set_assignments_add`    | Assign PS to users                                                      |
| `permission_set_assignments_remove` | Remove PS from users                                                    |
| `permission_set_assignments_list`   | List assignments for users and/or PS                                    |
| `profile_describe`                  | View profile-level permissions                                          |
| `sobject_describe`                  | List all fields/record types on an object                               |

---

## Workflows

### 1. Full Org Permission Audit

Run these four queries **in parallel** (they are independent):

**Q1 — All Permission Sets + system permission flags:**

```
sObject: "PermissionSet"
fields: ["Id","Name","Label","Description","IsOwnedByProfile",
         "PermissionsModifyAllData","PermissionsViewAllData",
         "PermissionsManageUsers","PermissionsViewSetup","PermissionsApiEnabled"]
whereClause: "IsOwnedByProfile = false"
orderBy: "Label ASC"  |  groupBy: ""  |  limit: 200
```

**Q2 — All Permission Set Groups:**

```
sObject: "PermissionSetGroup"
fields: ["Id","DeveloperName","MasterLabel","Status","Description"]
whereClause: ""  |  orderBy: "MasterLabel ASC"  |  groupBy: ""  |  limit: 200
```

**Q3 — PSG component membership (which PS belong to which PSG):**

```
sObject: "PermissionSetGroupComponent"
fields: ["PermissionSetGroupId","PermissionSetGroup.DeveloperName",
         "PermissionSetId","PermissionSet.Name","PermissionSet.Label"]
whereClause: ""  |  orderBy: ""  |  groupBy: ""  |  limit: 500
```

**Q4 — All active PS assignments (excluding profile-owned):**

```
sObject: "PermissionSetAssignment"
fields: ["PermissionSetId","PermissionSet.Name","PermissionSet.Label",
         "PermissionSetGroupId","PermissionSetGroup.DeveloperName",
         "AssigneeId","Assignee.Name"]
whereClause: "PermissionSet.IsOwnedByProfile = false"
orderBy: "PermissionSet.Label ASC"  |  groupBy: ""  |  limit: 2000
```

**Analysis checklist:**

- Flag PS with `PermissionsModifyAllData = true` as HIGH risk
- Flag PS with `PermissionsViewAllData = true` or `PermissionsManageUsers = true` as MEDIUM risk
- Identify PSGs with Status != "Updated" (outdated)
- Count assigned users per PS (cross-reference Q1 with Q4)
- Identify unassigned PS (in Q1 but no matching Q4 records)
- Build PSG → PS hierarchy tree from Q2 + Q3

### 2. Who Has Access to X?

#### Object permissions (e.g., Account delete):

```
sObject: "ObjectPermissions"
fields: ["Parent.Name","Parent.Label","SobjectType",
         "PermissionsCreate","PermissionsRead","PermissionsEdit",
         "PermissionsDelete","PermissionsViewAllRecords","PermissionsModifyAllRecords"]
whereClause: "SobjectType = 'Account' AND PermissionsDelete = true"
orderBy: "Parent.Label ASC"  |  groupBy: ""  |  limit: 200
```

#### Field permissions (e.g., Account.AnnualRevenue edit):

```
sObject: "FieldPermissions"
fields: ["Parent.Name","Parent.Label","Field","PermissionsRead","PermissionsEdit"]
whereClause: "Field = 'Account.AnnualRevenue' AND PermissionsEdit = true"
orderBy: "Parent.Label ASC"  |  groupBy: ""  |  limit: 200
```

#### Setup entity access (Apex, VF, Flows, Custom Permissions):

Query `SetupEntityAccess` filtered by `SetupEntityType` (`ApexClass`, `ApexPage`, `Flow`, `CustomPermission`). Cross-reference `SetupEntityId` with the target entity queried by Name.

#### System permissions (e.g., ModifyAllData):

```
sObject: "PermissionSet"
fields: ["Id","Name","Label"]
whereClause: "PermissionsModifyAllData = true AND IsOwnedByProfile = false"
orderBy: "Label ASC"  |  groupBy: ""  |  limit: 200
```

### 3. User Permission Analysis

**Step 1** — Get user's PS assignments:

```
sObject: "PermissionSetAssignment"
fields: ["PermissionSetId","PermissionSet.Name","PermissionSet.Label",
         "PermissionSetGroupId","PermissionSetGroup.DeveloperName"]
whereClause: "AssigneeId = '005...' AND PermissionSet.IsOwnedByProfile = false"
orderBy: "PermissionSet.Label ASC"  |  groupBy: ""  |  limit: 200
```

**Step 2** — For each assigned PS, query `ObjectPermissions` and `FieldPermissions` with `ParentId = '<PS_ID>'`.

**Step 3** — Check effective access with `tooling_api_query`:

```
sObject: "UserEntityAccess"
fields: ["EntityDefinitionId","IsCreatable","IsReadable","IsUpdatable","IsDeletable"]
whereClause: "UserId = '005...'"
limit: 200
```

### 4. Permission Set Management

**Create:** Use `permission_set_create` with `label`, `name`, `description`.

**Update permissions:** Use `permission_set_update` with patch array:

```json
[
  {
    "op": "add",
    "type": "objectPermissions",
    "object": "Account",
    "permissions": { "read": true, "create": true, "edit": true, "delete": false }
  },
  {
    "op": "add",
    "type": "fieldPermissions",
    "object": "Account",
    "field": "AnnualRevenue",
    "permissions": { "read": true, "edit": true }
  }
]
```

**Assign/unassign:** Use `permission_set_assignments_add` / `permission_set_assignments_remove` with `permissionSets` and `users` arrays.

### 5. Agentforce Agent Access

Employee Agents need an `agentAccesses` element in a Permission Set. Check with `metadata_read`, create/update with `metadata_create` or `metadata_update` (type `PermissionSet`):

```xml
<PermissionSet>
    <agentAccesses>
        <agentName>Case_Assist</agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Case Assist Agent Access</label>
</PermissionSet>
```

| Symptom                     | Solution                                                               |
| --------------------------- | ---------------------------------------------------------------------- |
| No Agentforce icon          | Assign `CopilotSalesforceUser` PS via `permission_set_assignments_add` |
| Icon visible, agent missing | Add `agentAccesses` element via `metadata_update`                      |
| "Agent not found" error     | Ensure `agentName` matches the agent's `developer_name` exactly        |

---

## References

- [Permission Model](docs/permission-model.md) — Profiles, PS, PSG, permission types, best practices
- [SOQL Reference](docs/soql-reference.md) — Complete catalog of permission-related SOQL queries
