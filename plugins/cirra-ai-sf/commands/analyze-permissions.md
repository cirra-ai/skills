---
name: analyze-permissions
description: Analyze Salesforce Permission Sets and Permission Set Groups. Find who has access to specific objects, fields, or Apex classes. Audit user permissions and identify security risks.
---

Analyze permission structures in a Salesforce org.

## Parsing the request

| Input after `/analyze-permissions` | Interpretation                        |
| ---------------------------------- | ------------------------------------- |
| `Account`                          | Find all PS with Account access       |
| `Account.AnnualRevenue`            | Find all PS with access to that field |
| `john@company.com`                 | Show all permissions for that user    |
| `hierarchy`                        | Show the full PS/PSG hierarchy        |
| `ModifyAllData`                    | Find PS with that system permission   |
| _(no argument)_                    | Ask the user what to analyze          |

## Workflow

### 1. Determine the analysis type

Use AskUserQuestion if the request is ambiguous:

- **Hierarchy**: Show all PS/PSG in the org
- **Object Access**: Find who has access to a specific object
- **Field Access**: Find who has access to a specific field
- **User Permissions**: Show all permissions for a user
- **Security Audit**: Find overly broad permissions

### 2. Run the appropriate queries

**Permission hierarchy**:

```
soql_query(sObject="PermissionSet", fields=["Id", "Name", "Label", "Description"], whereClause="IsOwnedByProfile = false AND Type != 'Group'")
soql_query(sObject="PermissionSetGroup", fields=["Id", "DeveloperName", "MasterLabel", "Status"])
soql_query(sObject="PermissionSetGroupComponent", fields=["PermissionSetGroup.DeveloperName", "PermissionSet.Name"])
```

**Object access** (e.g., "Who can delete Account?"):

```
soql_query(sObject="ObjectPermissions", fields=["Parent.Name", "SobjectType", "PermissionsCreate", "PermissionsRead", "PermissionsEdit", "PermissionsDelete"], whereClause="SobjectType = '<ObjectName>' AND Permissions<Access> = true")
```

**Field access** (e.g., "Who can edit Account.AnnualRevenue?"):

```
soql_query(sObject="FieldPermissions", fields=["Parent.Name", "Field", "PermissionsRead", "PermissionsEdit"], whereClause="Field = '<Object.Field>' AND PermissionsEdit = true")
```

**User permissions**:

```
soql_query(sObject="PermissionSetAssignment", fields=["PermissionSet.Name", "PermissionSetGroup.DeveloperName"], whereClause="AssigneeId = '<UserId>'")
```

Then for each assigned PS, query ObjectPermissions and FieldPermissions.

**Security audit** (find ModifyAllData, ViewAllData):

```
soql_query(sObject="PermissionSet", fields=["Name", "Label", "PermissionsModifyAllData", "PermissionsViewAllData"], whereClause="PermissionsModifyAllData = true AND IsOwnedByProfile = false")
```

### 3. Present results

Format results as clear tables showing:

- Permission Set/Group names
- What access they grant
- How many users are assigned (where applicable)
- Security concerns flagged

### 4. Recommend improvements

Based on the analysis, suggest:

- Consolidating overlapping PS into PSGs
- Removing overly broad permissions
- Creating missing PS for proper access control
