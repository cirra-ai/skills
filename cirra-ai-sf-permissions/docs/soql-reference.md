# Permission SOQL Reference

All queries below use Cirra AI's `soql_query` tool. Remember: `whereClause`, `orderBy`, and `groupBy` must always be provided (use `""` when not needed).

## Permission Set Queries

### All Permission Sets (non-profile)

```
sObject: PermissionSet
fields: [Id, Name, Label, Description, IsOwnedByProfile, Type]
whereClause: "IsOwnedByProfile = false"
```

### All Permission Set Groups

```
sObject: PermissionSetGroup
fields: [Id, DeveloperName, MasterLabel, Status, Description]
```

### PSG Components (which PS are in a Group)

```
sObject: PermissionSetGroupComponent
fields: [PermissionSetGroupId, PermissionSetGroup.DeveloperName,
         PermissionSetId, PermissionSet.Name, PermissionSet.Label]
```

### User's PS Assignments

```
sObject: PermissionSetAssignment
fields: [AssigneeId, PermissionSetId, PermissionSet.Name,
         PermissionSetGroupId, PermissionSetGroup.DeveloperName]
whereClause: "AssigneeId = '005xx...' AND PermissionSet.IsOwnedByProfile = false"
```

## Object Permissions

### All Object Permissions for a PS

```
sObject: ObjectPermissions
fields: [SobjectType, PermissionsCreate, PermissionsRead, PermissionsEdit,
         PermissionsDelete, PermissionsViewAllRecords, PermissionsModifyAllRecords]
whereClause: "ParentId = '0PS...'"
orderBy: "SobjectType ASC"
```

### Find PS with Specific Object Access

```
sObject: ObjectPermissions
fields: [Parent.Name, Parent.Label, SobjectType, PermissionsDelete]
whereClause: "SobjectType = 'Account' AND PermissionsDelete = true"
```

## Field Permissions

### All Field Permissions for a PS

```
sObject: FieldPermissions
fields: [Field, PermissionsRead, PermissionsEdit]
whereClause: "ParentId = '0PS...'"
orderBy: "Field ASC"
```

### Find PS with Specific Field Access

```
sObject: FieldPermissions
fields: [Parent.Name, Parent.Label, Field, PermissionsRead, PermissionsEdit]
whereClause: "Field = 'Account.AnnualRevenue' AND PermissionsEdit = true"
```

## Setup Entity Access (Apex, VF, Flows, Custom Permissions)

### All Setup Entity Access for a PS

```
sObject: SetupEntityAccess
fields: [SetupEntityType, SetupEntityId]
whereClause: "ParentId = '0PS...'"
```

### Find PS with Apex Class Access

Two-step: first query `ApexClass` for the Id, then filter `SetupEntityAccess`:

```
sObject: SetupEntityAccess
fields: [Parent.Name, Parent.Label]
whereClause: "SetupEntityType = 'ApexClass' AND SetupEntityId = '<apex_class_id>'"
```

### Find PS with Custom Permission

Two-step: first query `CustomPermission` by `DeveloperName`, then:

```
sObject: SetupEntityAccess
fields: [Parent.Name, Parent.Label]
whereClause: "SetupEntityType = 'CustomPermission' AND SetupEntityId = '<custom_perm_id>'"
```

Note: Cirra AI's `soql_query` does not support sub-selects (`SetupEntityId IN (SELECT ...)`). Use two separate queries instead.

## System Permissions

### Find PS with ModifyAllData

```
sObject: PermissionSet
fields: [Id, Name, Label]
whereClause: "PermissionsModifyAllData = true AND IsOwnedByProfile = false"
```

### Find PS with ViewSetup

```
sObject: PermissionSet
fields: [Id, Name, Label]
whereClause: "PermissionsViewSetup = true AND IsOwnedByProfile = false"
```

### Available System Permission Fields on PermissionSet

PermissionsModifyAllData, PermissionsViewAllData, PermissionsManageUsers,
PermissionsViewSetup, PermissionsApiEnabled, PermissionsRunReports,
PermissionsExportReport, PermissionsEditPublicDocuments, PermissionsManageCategories

## User Count Queries

### Count Users per PS (via assignments)

Query all `PermissionSetAssignment` records and aggregate in analysis — Cirra AI's `soql_query` does not support `COUNT()` with `GROUP BY`.

## Metadata Queries

### All Custom Permissions

```
sObject: CustomPermission
fields: [Id, DeveloperName, MasterLabel, Description]
```

### All Apex Classes

```
sObject: ApexClass
fields: [Id, Name, NamespacePrefix, IsValid]
```

## Tooling API Queries

Use `tooling_api_query` for metadata not available via standard SOQL:

### Tab Settings for a PS

```
sObject: PermissionSetTabSetting
fields: [Name, Visibility]
whereClause: "ParentId = '0PS...'"
```

### Effective User Object Access

```
sObject: UserEntityAccess
fields: [EntityDefinitionId, IsCreatable, IsReadable, IsUpdatable, IsDeletable]
whereClause: "UserId = '005...'"
```

### Effective User Field Access

```
sObject: UserFieldAccess
fields: [FieldDefinitionId, IsAccessible, IsUpdatable]
whereClause: "UserId = '005...' AND EntityDefinitionId = 'Account'"
```
