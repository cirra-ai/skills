<!-- Parent: sf-permissions/SKILL.md -->

# Common Workflows & Examples

## Workflow 1: Audit "Who can delete Accounts?"

```
User: "Who has delete access to the Account object?"

1. soql_query on ObjectPermissions (SobjectType = 'Account' AND PermissionsDelete = true)
2. Resolve Parent.Name IDs to PS names; for each PS, get PSG membership (PermissionSetGroupComponent)
3. For each PS/PSG, count assigned users (PermissionSetAssignment with groupBy)
4. Display results in table format
```

## Workflow 2: Troubleshoot User Access

```
User: "Why can't John edit Opportunities?"

1. Look up John's User Id, then his PermissionSetAssignment rows
2. Check whether any assigned PS grants Opportunity edit (ObjectPermissions)
3. Check the profile with profile_describe(profile=..., permissionTypes=["objectPermissions"], sObject="Opportunity")
4. If nothing grants it, suggest which PS/PSG to assign (permission_set_assignments) or which PS to patch
```

## Workflow 3: Document Permission Set

```
User: "Export the Sales_Manager PS for documentation"

1. metadata_read(type="PermissionSet", fullNames=["Sales_Manager"]) — full object/field/system/class/tab access
2. Render as tables (one per permission type)
3. Optionally generate a Mermaid diagram showing PSG membership (sf-diagram)
```

## Example 1: Full Org Audit

```
User: "Give me a complete picture of permissions in my org"

Agent:
1. Runs the hierarchy queries to show all PS/PSG
2. Identifies PSGs with "Outdated" status
3. Counts users per PS
4. Generates a Mermaid diagram for documentation
```

## Example 2: Security Review

```
User: "Find all PS that grant ModifyAllData"

Agent:
1. soql_query on PermissionSet where PermissionsModifyAllData = true
2. Lists PS names and assigned user counts
3. Flags any non-admin PS with this powerful permission
```

## Example 3: Permission Set Creation

```
User: "Create a PS for contractors with read-only Account access"

Agent:
1. Presents the plan (name Contractor_Account_ReadOnly_PS, Account read only) and gets approval
2. metadata_create(type="PermissionSet", metadata=[{fullName, label, hasActivationRequired: false}])
3. permission_set_update(permissionSet="Contractor_Account_ReadOnly_PS", patch=[{"op": "add", "path": "/objectPermissions/-", "value": {"object": "Account", "allowRead": true, "allowCreate": false, "allowEdit": false, "allowDelete": false, "viewAllRecords": false, "modifyAllRecords": false, "viewAllFields": false}}])
4. Verifies with metadata_read and offers to assign it with permission_set_assignments
```

## Example 4: Profile Change

```
User: "Give the Custom Sales User profile read access to Invoice__c"

Agent:
1. profile_describe(profile="Custom Sales User", permissionTypes=["objectPermissions"], sObject="Invoice__c") — confirm current state
2. Presents the plan; suggests a Permission Set instead if the org convention is PS-based
3. profile_update(profile="Custom Sales User", patch=[{"op": "add", "path": "/objectPermissions/-", "value": {"object": "Invoice__c", "allowRead": true, "allowCreate": false, "allowEdit": false, "allowDelete": false, "viewAllRecords": false, "modifyAllRecords": false}}])
4. Re-runs profile_describe to verify
```
