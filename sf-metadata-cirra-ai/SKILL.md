---
name: sf-metadata-cirra-ai
description: >
  Generates and queries Salesforce metadata with 120-point scoring via Cirra AI MCP Server.
  Use when creating custom objects, fields, profiles, permission sets, validation rules,
  or querying org metadata structures.
license: MIT
metadata:
  version: '1.0.0'
  author: 'Cirra AI (refactored from sf-skills by Jag Valaiyapathy)'
  scoring: '120 points across 6 categories'
---

# sf-metadata-cirra-ai: Salesforce Metadata Generation and Org Querying

Expert Salesforce administrator specializing in metadata architecture, security model design, and schema best practices. Generate production-ready metadata and query org structures using Cirra AI MCP Server tools.

## Core Responsibilities

1. **Metadata Generation**: Create Custom Objects, Fields, Profiles, Permission Sets, Validation Rules, Record Types, Page Layouts
2. **Org Querying**: Describe objects, list fields, query metadata using Cirra AI MCP Server
3. **Validation & Scoring**: Score metadata against 6 categories (0-120 points)
4. **Cross-Skill Integration**: Provide metadata discovery for related workflows
5. **Direct Metadata Operations**: Deploy metadata directly via Cirra AI metadata APIs

## ⚠️ CRITICAL: Direct API Workflow

Unlike the original sf-metadata which uses local file generation, this version operates directly on Salesforce orgs:

```
1. Gather Requirements (with cirra_ai_init)
2. Query existing metadata (sobject_describe, metadata_list)
3. Create/Update metadata directly (metadata_create, sobject_field_create, etc.)
4. Validate results (scoring system)
5. Verify in org (query operations)
```

---

## ⚠️ CRITICAL: Field-Level Security

**Created fields are INVISIBLE until FLS is configured!** Always prompt for Permission Set generation after creating objects/fields.

---

## Workflow (5-Phase Pattern)

### Phase 1: Requirements Gathering & Initialization

First, initialize Cirra AI connection:

```
Call: cirra_ai_init(cirra_ai_team="[user's team]", scope="metadata")
```

Then use **AskUserQuestion** to gather:

- Operation type: **Generate** metadata OR **Query** org metadata
- If generating:
  - Metadata type (Object, Field, Profile, Permission Set, Validation Rule, Record Type, Layout)
  - Target object (for fields, validation rules, record types)
  - Specific requirements (field type, data type, relationships, picklist values)
- If querying:
  - Query type (describe object, list fields, list metadata)
  - Object name or metadata type to query

**Then**:

1. Call cirra_ai_init if not already done
2. Query existing metadata using appropriate tools
3. Create TodoWrite tasks for multi-step operations

### Phase 2: Query Execution / Metadata Discovery

#### For Querying (Cirra AI MCP Tools)

| Query Type              | Tool                | Parameters                                   |
| ----------------------- | ------------------- | -------------------------------------------- |
| Describe object         | `sobject_describe`  | sObject, sf_user                             |
| List custom objects     | `sobjects_list`     | customObjectsOnly=true, sf_user              |
| List all metadata types | `metadata_describe` | sf_user                                      |
| List metadata elements  | `metadata_list`     | type, sf_user                                |
| Query records with SOQL | `soql_query`        | sObject, fields, whereClause, limit, sf_user |
| Query tooling API       | `tooling_api_query` | sObject, fields, whereClause, limit, sf_user |

**Example Query Execution**:

```
sobject_describe(sObject="Account", sf_user="admin@org.com")
metadata_list(type="CustomObject", sf_user="admin@org.com")
soql_query(sObject="Account", fields=["Id","Name","Type"], limit=10, sf_user="admin@org.com")
```

**Present query results** in structured format:

```
📊 Object: Account
════════════════════════════════════════

📁 Standard Fields: 45
📁 Custom Fields: 12
🔗 Relationships: 8
📝 Validation Rules: 3
📋 Record Types: 2

Custom Fields:
├── Industry_Segment__c (Picklist)
├── Annual_Revenue__c (Currency)
├── Primary_Contact__c (Lookup → Contact)
└── ...
```

### Phase 3: Generation / Direct Metadata Operations

#### For Object Creation

```
sobject_create(
  sf_user="admin@org.com",
  sObject="MyCustom__c",
  label="My Custom Object",
  pluralLabel="My Custom Objects",
  deploymentStatus="Deployed",
  description="Purpose of this object",
  enableActivities=true,
  enableHistory=true,
  enableReports=true,
  enableSearch=true,
  sharingModel="Public Read/Write"
)
```

#### For Field Creation

```
sobject_field_create(
  sf_user="admin@org.com",
  sObject="MyCustom__c",
  fieldName="My_Field__c",
  label="My Field",
  fieldType="Text",
  description="Field purpose",
  properties={
    "length": 100,
    "required": false
  }
)
```

For picklist fields, use:

```
sobject_field_create(
  sf_user="admin@org.com",
  sObject="Account",
  fieldName="Industry_Segment__c",
  label="Industry Segment",
  fieldType="Picklist",
  properties={
    "restrictedPicklist": false,
    "picklist": {
      "picklistValues": [
        {"value": "Technology"},
        {"value": "Healthcare"},
        {"value": "Finance"}
      ]
    }
  }
)
```

#### For Profile Operations

```
profile_describe(profile="System Administrator", sf_user="admin@org.com")
profile_update(
  profile="Custom_Profile",
  sf_user="admin@org.com",
  patch=[
    {
      "op": "add",
      "path": "/objectPermissions",
      "value": {
        "object": "MyCustom__c",
        "allowCreate": true,
        "allowRead": true,
        "allowEdit": true,
        "allowDelete": false
      }
    }
  ]
)
```

#### For Permission Set Operations

```
permission_set_create(
  sf_user="admin@org.com",
  name="CustomObject_Access",
  label="Custom Object Access",
  description="Access to MyCustom__c and related fields",
  hasActivationRequired=false
)

permission_set_update(
  sf_user="admin@org.com",
  permissionSet="CustomObject_Access",
  patch=[
    {
      "op": "add",
      "path": "/objectPermissions",
      "value": {
        "object": "MyCustom__c",
        "allowCreate": true,
        "allowRead": true,
        "allowEdit": true,
        "allowDelete": true
      }
    },
    {
      "op": "add",
      "path": "/fieldPermissions",
      "value": {
        "field": "MyCustom__c.My_Field__c",
        "readable": true,
        "editable": true
      }
    }
  ]
)

permission_set_assignments_add(
  sf_user="admin@org.com",
  users=["user@org.com"],
  permissionSets=["CustomObject_Access"]
)
```

#### For Record Type Operations

```
record_type_create(
  sf_user="admin@org.com",
  sObject="Opportunity",
  name="Enterprise_Deal",
  label="Enterprise Deal",
  description="Record type for enterprise customers",
  active=true,
  defaultLayout="Opportunity-Enterprise Layout"
)
```

#### For Page Layout Operations

```
page_layout_create(
  sf_user="admin@org.com",
  sObject="Account",
  layoutName="Account-Standard Layout",
  layoutSections="Standard"
)

page_layout_update(
  sf_user="admin@org.com",
  sObject="Account",
  layout="Account-Custom",
  patch=[
    {
      "op": "add",
      "path": "/layoutSections/0/layoutColumns/0/layoutItems",
      "value": {
        "field": "My_Custom_Field__c"
      }
    }
  ]
)
```

#### For Value Set Operations

```
value_set_create(
  sf_user="admin@org.com",
  name="Industry_Values",
  masterLabel="Industry Values",
  description="Global picklist for industry classifications",
  sorted=false,
  values=[
    {"value": "Technology", "isDefault": false},
    {"value": "Healthcare", "isDefault": false},
    {"value": "Finance", "isDefault": false},
    {"value": "Manufacturing", "isDefault": false}
  ]
)
```

#### For Metadata CRUD Operations (Advanced)

```
metadata_create(
  sf_user="admin@org.com",
  type="ValidationRule",
  metadata=[
    {
      "fullName": "Account.Annual_Revenue_Check",
      "active": true,
      "description": "Ensure annual revenue is positive",
      "errorConditionFormula": "Annual_Revenue__c < 0",
      "errorMessage": "Annual revenue must be greater than zero",
      "errorDisplayField": "Annual_Revenue__c"
    }
  ]
)

metadata_read(
  sf_user="admin@org.com",
  type="CustomObject",
  fullNames=["Account__c"]
)

metadata_update(
  sf_user="admin@org.com",
  type="CustomObject",
  metadata=[
    {
      "fullName": "Account__c",
      "description": "Updated description"
    }
  ]
)
```

### Phase 3.5: Permission Set Auto-Generation

**After creating Custom Objects or Fields, ALWAYS prompt the user:**

```
AskUserQuestion:
  question: "Would you like me to generate a Permission Set for [ObjectName__c] field access?"
  header: "FLS Setup"
  options:
    - label: "Yes, generate Permission Set"
      description: "Creates [ObjectName]_Access with object CRUD and field access"
    - label: "No, I'll handle FLS manually"
      description: "Skip Permission Set generation - you'll configure FLS via Setup or Profile"
```

**If user selects "Yes":**

1. **Query created field information** using metadata_read or sobject_describe
2. **Filter field permissions** according to rules below
3. **Generate Permission Set** using permission_set_create and permission_set_update

**Permission Set Generation Rules:**

| Field Type      | Include in Permission Set? | Notes                                              |
| --------------- | -------------------------- | -------------------------------------------------- |
| Required fields | ❌ NO                      | Auto-visible, Salesforce rejects in Permission Set |
| Optional fields | ✅ YES                     | Include with readable=true, editable=true          |
| Formula fields  | ✅ YES                     | Include with readable=true, editable=false         |
| Roll-Up Summary | ✅ YES                     | Include with readable=true, editable=false         |
| Master-Detail   | ❌ NO                      | Controlled by parent object permissions            |
| Name field      | ❌ NO                      | Always visible, cannot be in Permission Set        |

---

### Phase 4: Deployment (Direct Org Operations)

Unlike the file-based approach, this workflow deploys directly:

1. **Create metadata directly** using Cirra AI tools (as shown in Phase 3)
2. **Verify creation** immediately using query tools
3. **Assign permissions** if needed using permission_set_assignments_add

---

### Phase 5: Verification

**For Created Metadata**:

```
✓ Metadata Complete: [MetadataName]
  Type: [CustomObject/CustomField/Profile/etc.]
  Created via: Cirra AI MCP Server
  Validation: PASSED (Score: XX/120)

Next Steps:
  1. Verify in Setup → Object Manager → [Object]
  2. Check Field-Level Security for new fields
  3. Add to Page Layouts if needed
  4. Assign Permission Sets to users
```

**For Queries**:

- Present results in structured format
- Highlight relevant information
- Offer follow-up actions (create field, modify permissions, etc.)

---

## Best Practices (Built-In Enforcement)

### Critical Requirements

**Structure & Format** (20 points):

- Valid metadata structure following Salesforce API patterns (-10 if invalid)
- Correct object/field naming conventions (-5 if missing)
- API version current (using latest Cirra AI tools) (-5 if outdated)
- Proper categorization and organization (-5 if wrong)

**Naming Conventions** (20 points):

- Custom objects/fields end with `__c` (-3 each violation)
- Use PascalCase for API names: `Account_Status__c` not `account_status__c` (-2 each)
- Meaningful labels (no abbreviations like `Acct`, `Sts`) (-2 each)
- Relationship names follow pattern: `[ParentObject]_[ChildObjects]` (-3)

**Data Integrity** (20 points):

- Required fields have sensible defaults or validation (-5)
- Number fields have appropriate precision/scale (-3)
- Picklist values properly defined with labels (-3)
- Relationship delete constraints specified (SetNull, Restrict, Cascade) (-3)
- Formula field syntax valid (-5)
- Roll-up summaries reference correct fields (-3)

**Security & FLS** (20 points):

- Field-Level Security considerations documented (-5 if sensitive field exposed)
- Sensitive field types flagged (SSN patterns, Credit Card patterns) (-10)
- Object sharing model appropriate for data sensitivity (-5)
- Permission Sets preferred over Profile modifications (advisory)

**Documentation** (20 points):

- Description present and meaningful on objects/fields (-5 if missing)
- Help text for user-facing fields (-3 each)
- Clear error messages for validation rules (-3)
- Inline comments in complex formulas (-3)

**Best Practices** (20 points):

- Use Permission Sets over Profiles when possible (-3 if Profile-first)
- Avoid hardcoded Record IDs in formulas (-5 if found)
- Use Global Value Sets for reusable picklists (advisory)
- Master-Detail vs Lookup selection appropriate for use case (-3)
- Record Types have associated Page Layouts (-3)

### Scoring

**Thresholds**: ⭐⭐⭐⭐⭐ 108+ | ⭐⭐⭐⭐ 96-107 | ⭐⭐⭐ 84-95 | Block: <72

---

## Field Type Selection Guide

| Type         | Salesforce                   | Notes                              |
| ------------ | ---------------------------- | ---------------------------------- |
| Text         | Text / Text Area (Long/Rich) | ≤255 chars / multi-line / HTML     |
| Numbers      | Number / Currency            | Decimals or money (org currency)   |
| Boolean      | Checkbox                     | True/False                         |
| Choice       | Picklist / Multi-Select      | Single/multiple predefined options |
| Date         | Date / DateTime              | With or without time               |
| Contact      | Email / Phone / URL          | Validated formats                  |
| Relationship | Lookup / Master-Detail       | Optional / required parent         |
| Calculated   | Formula / Roll-Up            | Derived from fields / children     |

---

## Relationship Decision Matrix

| Scenario             | Use                      | Reason                                |
| -------------------- | ------------------------ | ------------------------------------- |
| Parent optional      | Lookup                   | Child can exist without parent        |
| Parent required      | Master-Detail            | Cascade delete, roll-up summaries     |
| Many-to-Many         | Junction Object          | Two Master-Detail relationships       |
| Self-referential     | Hierarchical Lookup      | Same object (e.g., Account hierarchy) |
| Cross-object formula | Master-Detail or Formula | Access parent fields                  |

---

## Common Validation Rule Patterns

| Pattern              | Formula                                                   | Use                               |
| -------------------- | --------------------------------------------------------- | --------------------------------- |
| Conditional Required | `AND(ISPICKVAL(Status,'Closed'), ISBLANK(Close_Date__c))` | Field required when condition met |
| Email Regex          | `NOT(REGEX(Email__c, "^[a-zA-Z0-9._-]+@..."))`            | Format validation                 |
| Future Date          | `Due_Date__c < TODAY()`                                   | Date constraints                  |
| Cross-Object         | `AND(Account.Type != 'Customer', Amount__c > 100000)`     | Related field checks              |

---

## Cirra AI Tool Reference

### Initialization

```
cirra_ai_init(cirra_ai_team="your-team", scope="metadata", sf_user="admin@org.com")
```

### Query Tools

```
sobject_describe(sObject="Account", sf_user="admin@org.com")
sobjects_list(customObjectsOnly=false, sf_user="admin@org.com")
metadata_list(type="CustomObject", sf_user="admin@org.com")
metadata_describe(sf_user="admin@org.com")
soql_query(sObject="Account", fields=["Id","Name"], limit=10, sf_user="admin@org.com")
tooling_api_query(sObject="CustomObject", fields=["Id","DeveloperName"], sf_user="admin@org.com")
```

### Creation Tools

```
sobject_create(sObject="Custom__c", label="Custom", sf_user="admin@org.com")
sobject_field_create(sObject="Account", fieldName="Field__c", fieldType="Text", sf_user="admin@org.com")
metadata_create(type="ValidationRule", metadata=[...], sf_user="admin@org.com")
permission_set_create(name="AccessSet", label="Access Set", sf_user="admin@org.com")
record_type_create(sObject="Account", name="RT", label="Record Type", sf_user="admin@org.com")
page_layout_create(sObject="Account", layoutName="Layout", sf_user="admin@org.com")
value_set_create(name="Values", masterLabel="Values", values=[...], sf_user="admin@org.com")
```

### Update Tools

```
sobject_update(sObject="Custom__c", properties={...}, sf_user="admin@org.com")
sobject_field_update(sObject="Account", fieldName="Field__c", properties={...}, sf_user="admin@org.com")
metadata_update(type="CustomObject", metadata=[...], sf_user="admin@org.com")
metadata_read(type="CustomObject", fullNames=["Account__c"], sf_user="admin@org.com")
permission_set_update(permissionSet="AccessSet", patch=[...], sf_user="admin@org.com")
record_type_update(sObject="Account", recordType="RT", properties={...}, sf_user="admin@org.com")
page_layout_update(sObject="Account", layout="Layout", patch=[...], sf_user="admin@org.com")
value_set_update(name="Values", type="GlobalValueSet", values=[...], sf_user="admin@org.com")
```

### Assignment Tools

```
permission_set_assignments_add(users=["user@org.com"], permissionSets=["AccessSet"], sf_user="admin@org.com")
permission_set_assignments_remove(users=["user@org.com"], permissionSets=["AccessSet"], sf_user="admin@org.com")
group_members_add(users=["user@org.com"], groups=["GroupName"], sf_user="admin@org.com")
group_members_remove(users=["user@org.com"], groups=["GroupName"], sf_user="admin@org.com")
```

### Deletion Tools

```
metadata_delete(type="CustomField", fullNames=["Account.Custom__c"], sf_user="admin@org.com")
sobject_field_delete(sObject="Account", fieldName="Field__c", sf_user="admin@org.com")
```

---

## Metadata Anti-Patterns

| Anti-Pattern                     | Fix                                          |
| -------------------------------- | -------------------------------------------- |
| Profile-based FLS                | Use Permission Sets for granular access      |
| Hardcoded IDs in formulas        | Use Custom Settings or Custom Metadata       |
| Validation rule without bypass   | Add `$Permission.Bypass_Validation__c` check |
| Too many picklist values (>200)  | Consider Custom Object instead               |
| Auto-number without prefix       | Add meaningful prefix: `INV-{0000}`          |
| Roll-up on non-M-D               | Use trigger-based calculation or DLRS        |
| Field label = API name           | Use user-friendly labels                     |
| No description on custom objects | Always document purpose                      |

---

## Key Insights

| Insight                           | Issue                                    | Fix                                                |
| --------------------------------- | ---------------------------------------- | -------------------------------------------------- |
| FLS is the Silent Killer          | Created fields invisible without FLS     | Always prompt for Permission Set generation        |
| Required Fields ≠ Permission Sets | Salesforce rejects required fields in PS | Filter out required fields from field permissions  |
| Direct API Speed                  | Metadata creation is immediate           | No deployment time needed like file-based approach |
| Org Connection Required           | All operations need active sf_user       | Always initialize with cirra_ai_init first         |
| Metadata Consistency              | Direct creation avoids local file issues | Always verify creation with query tools            |

## Common Errors

| Error                             | Fix                                               |
| --------------------------------- | ------------------------------------------------- |
| `Cannot deploy to required field` | Remove from fieldPermissions (auto-visible)       |
| `Field does not exist`            | Create Permission Set with field access           |
| `SObject type 'X' not supported`  | Use sobjects_list to verify object exists         |
| `Invalid metadata structure`      | Check API field names match Salesforce specs      |
| `cirra_ai_init not called`        | Call cirra_ai_init before any metadata operations |

---

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2025 Jag Valaiyapathy (refactored for Cirra AI)
