---
name: create-metadata
description: Create Salesforce metadata (custom objects, fields, validation rules, record types, permission sets) directly in an org via the Cirra AI MCP Server.
---

Create new Salesforce metadata components in an org.

## Workflow

### 1. Gather requirements

Use AskUserQuestion to collect:

- **Metadata type**: Custom Object, Custom Field, Validation Rule, Record Type, Permission Set, or other
- **Target object**: Which Salesforce object is involved (for fields, rules, etc.)
- **Specific requirements**: Field type, validation formula, picklist values, etc.

### 2. Check for existing metadata

Before creating, verify nothing already exists with that name.

**For an object**:

```
tooling_api_query(
  sObject="CustomObject",
  whereClause="DeveloperName = '<ObjectName>'",
  fields=["DeveloperName", "Label"]
)
```

**For a field**:

```
sobject_describe(
  sObject="<ObjectName>"
)
```

Check the fields list in the response to see if the field already exists.

### 3. Create the metadata

Use `metadata_create` with the appropriate type and metadata definition.

**Custom Object**:

```
metadata_create(
  type="CustomObject",
  metadata=[{
    "fullName": "<ObjectName__c>",
    "label": "<Label>",
    "pluralLabel": "<PluralLabel>",
    "nameField": {"label": "<NameFieldLabel>", "type": "AutoNumber", "displayFormat": "<PREFIX>-{0000}"},
    "deploymentStatus": "Deployed",
    "sharingModel": "ReadWrite"
  }]
)
```

**Custom Field**:

```
metadata_create(
  type="CustomField",
  metadata=[{
    "fullName": "<Object>.<FieldName__c>",
    "label": "<Label>",
    "type": "<FieldType>",
    "description": "<Description>"
  }]
)
```

**Validation Rule**:

```
metadata_create(
  type="ValidationRule",
  metadata=[{
    "fullName": "<Object>.<RuleName>",
    "active": true,
    "errorConditionFormula": "<Formula>",
    "errorMessage": "<Message>"
  }]
)
```

### 4. Generate Permission Set (for objects/fields)

After creating objects or fields, ask the user if they want a Permission Set generated for FLS access. Deployed fields are **invisible** without FLS configuration.

```
metadata_create(
  type="PermissionSet",
  metadata=[{
    "fullName": "<ObjectName>_Access",
    "label": "<ObjectName> Access",
    "description": "Grants access to <ObjectName> and its fields",
    "objectPermissions": [{"object": "<ObjectName__c>", "allowCreate": true, "allowRead": true, "allowEdit": true, "allowDelete": true}],
    "fieldPermissions": [{"field": "<Object.Field__c>", "editable": true, "readable": true}]
  }]
)
```

### 5. Verify

Describe the object to confirm the metadata was created:

```
sobject_describe(sObject="<ObjectName>")
```

### 6. Report

Show the user what was created, the validation score (if applicable), and any next steps (e.g., assign the Permission Set to users, add fields to page layouts).
