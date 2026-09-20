<!-- Parent: sf-permissions/SKILL.md -->

# sf-permissions Usage Examples

Copy-paste Cirra AI MCP calls for each operation. Call `cirra_ai_init()` first; every
write needs the user's explicit approval. Signatures: `../../../shared/references/cirra-mcp-tools.md`.

## 1. Hierarchy — all PS, PSGs and their components

```
soql_query(sObject="PermissionSet", fields=["Id", "Name", "Label", "Type"], whereClause="IsOwnedByProfile = false AND Type != 'Group'")
soql_query(sObject="PermissionSetGroup", fields=["Id", "DeveloperName", "MasterLabel", "Status"], whereClause="Id != null")
soql_query(sObject="PermissionSetGroupComponent", fields=["PermissionSetGroup.DeveloperName", "PermissionSet.Name"], whereClause="Id != null")
```

## 2. Who has X?

```
# Object — who can delete Account?
soql_query(sObject="ObjectPermissions", fields=["Parent.Name", "Parent.Label"], whereClause="SobjectType = 'Account' AND PermissionsDelete = true")

# Field — who can read a sensitive field?
soql_query(sObject="FieldPermissions", fields=["Parent.Name", "Field", "PermissionsRead", "PermissionsEdit"], whereClause="Field = 'Contact.SSN__c' AND PermissionsRead = true")

# Apex class
soql_query(sObject="SetupEntityAccess", fields=["Parent.Name"], whereClause="SetupEntityType = 'ApexClass' AND SetupEntityId IN (SELECT Id FROM ApexClass WHERE Name = 'MyApexController')")

# Custom permission
soql_query(sObject="SetupEntityAccess", fields=["Parent.Name"], whereClause="SetupEntityType = 'CustomPermission' AND SetupEntityId IN (SELECT Id FROM CustomPermission WHERE DeveloperName = 'Can_Approve_Expenses')")

# System permission — who has ModifyAllData?
soql_query(sObject="PermissionSet", fields=["Name", "Label", "IsOwnedByProfile", "Profile.Name"], whereClause="PermissionsModifyAllData = true")
```

`Parent.Name` comes back as a `0PS...` ID — resolve with
`soql_query(sObject="PermissionSet", fields=["Id", "Name", "Label"], whereClause="Id IN ('0PS...')")`.

## 3. User analysis

```
soql_query(sObject="User", fields=["Id", "Name", "Username", "Profile.Name"], whereClause="Username = 'john.smith@company.com'")
soql_query(sObject="PermissionSetAssignment", fields=["PermissionSet.Name", "PermissionSetGroup.DeveloperName"], whereClause="AssigneeId = '005xx000001234AAA'")
profile_describe(profile="Custom Sales User", permissionTypes=["objectPermissions", "fieldPermissions", "userPermissions"], sObject="Opportunity")
```

## 4. Create a permission set and fill it

```
metadata_create(type="PermissionSet", metadata=[{"fullName": "Contractor_Account_ReadOnly_PS", "label": "Contractor Account Read Only", "hasActivationRequired": false}])

permission_set_update(
  permissionSet="Contractor_Account_ReadOnly_PS",
  patch=[
    {"op": "add", "path": "/objectPermissions/-", "value": {"object": "Account", "allowRead": true, "allowCreate": false, "allowEdit": false, "allowDelete": false, "viewAllRecords": false, "modifyAllRecords": false, "viewAllFields": false}},
    {"op": "add", "path": "/fieldPermissions/-", "value": {"field": "Account.AnnualRevenue", "readable": true, "editable": false}},
    {"op": "add", "path": "/tabSettings/-", "value": {"tab": "standard-Account", "visibility": "Visible"}}
  ]
)
```

## 5. Update an existing permission set

```
# Grant a system permission
permission_set_update(permissionSet="Sales_Admin", patch=[{"op": "add", "path": "/userPermissions/-", "value": {"name": "ViewAllData", "enabled": true}}])

# Turn an existing object permission's delete flag off (index from metadata_read)
metadata_read(type="PermissionSet", fullNames=["Sales_Admin"])
permission_set_update(permissionSet="Sales_Admin", patch=[{"op": "replace", "path": "/objectPermissions/2/allowDelete", "value": false}])
```

## 6. Clone / delete

```
metadata_read(type="PermissionSet", fullNames=["Sales_Admin"])
metadata_create(type="PermissionSet", metadata=[{...cloned, "fullName": "Sales_Viewer", "label": "Sales Viewer"}])
metadata_delete(type="PermissionSet", fullNames=["Unused_Legacy_PS"])
```

## 7. Assign / remove

```
permission_set_assignments(operation="add", permissionSets=["Contractor_Account_ReadOnly_PS"], users=["jane@company.com"])
permission_set_assignments(operation="remove", permissionSets=["Unused_Legacy_PS"], users=["jane@company.com", "john@company.com"])
```

## 8. Profiles

```
profile_describe(profile="Standard User", permissionTypes=["objectPermissions", "tabVisibilities"], sObject="Case")
profile_clone(profile="Support Agent - Limited", clonedProfileName="Standard User")
profile_update(profile="Support Agent - Limited", patch=[{"op": "add", "path": "/objectPermissions/-", "value": {"object": "Case", "allowRead": true, "allowCreate": true, "allowEdit": true, "allowDelete": false, "viewAllRecords": false, "modifyAllRecords": false}}])
```

## 9. Agent access

```
permission_set_update(permissionSet="Case_Assist_Access", patch=[{"op": "add", "path": "/agentAccesses/-", "value": {"agentName": "Case_Assist", "enabled": true}}])
permission_set_assignments(operation="add", permissionSets=["Case_Assist_Access"], users=["jane@company.com"])
```

See `agent-access-guide.md` for inspection and troubleshooting.
