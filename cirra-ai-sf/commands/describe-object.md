---
name: describe-object
description: Describe a Salesforce object's metadata including fields, relationships, record types, and validation rules. Provides a comprehensive overview of an object's structure.
---

Describe a Salesforce object and display its metadata structure.

## Parsing the request

| Input after `/describe-object` | Interpretation                                             |
| ------------------------------ | ---------------------------------------------------------- |
| `Account`                      | Object name - describe it directly                         |
| `all custom objects`           | List all custom objects first, then describe selected ones |
| _(no argument)_                | Ask the user which object to describe                      |

## Workflow

### 1. Describe the object

```
sobject_describe(
  sObject="<ObjectName>",
  sf_user="<sf_user>"
)
```

### 2. Display the results

Present the object metadata in a structured format:

**Object Overview**: Label, API name, key settings (sharing model, etc.)

**Fields**: Display as a table with:

- API Name
- Label
- Type
- Required (yes/no)
- Relationship target (for Lookup/Master-Detail)

**Relationships**: List parent and child relationships

**Record Types**: List available record types if any

### 3. Query additional metadata (if requested)

**Validation rules on the object**:

```
tooling_api_query(
  sObject="ValidationRule",
  whereClause="EntityDefinition.QualifiedApiName = '<ObjectName>'",
  fields=["ValidationName", "Active", "ErrorMessage"]
)
```

**Custom fields with details**:

```
tooling_api_query(
  sObject="CustomField",
  whereClause="EntityDefinition.QualifiedApiName = '<ObjectName>'",
  fields=["DeveloperName", "Label", "DataType", "Description"]
)
```

### 4. Offer follow-up actions

Based on what was discovered, suggest relevant next steps:

- "Create a new field on this object" -> `/create-metadata`
- "Query records from this object" -> `/query`
- "Analyze permissions for this object" -> `/analyze-permissions`
- "Create an ERD diagram" -> `/create-diagram`
