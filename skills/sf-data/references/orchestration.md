# Multi-Skill Orchestration: sf-data Perspective

How sf-data fits into a multi-skill Salesforce change delivered through the
Cirra AI MCP Server. Everything below runs against the live org — there are
no local source files and no separate deploy step: each skill creates or
updates its metadata in the org directly.

---

## Standard orchestration order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STANDARD MULTI-SKILL ORCHESTRATION ORDER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  0. cirra_ai_init()                                                         │
│     └── Establish the connection; confirm the target org                    │
│                                                                             │
│  1. sf-metadata                                                             │
│     └── Objects, fields, validation rules, permission sets                  │
│         (sobject_create / sobject_field_create / metadata_create)           │
│                                                                             │
│  2. sf-flow / sf-apex                                                       │
│     └── Flows (metadata_create type=Flow), classes and triggers             │
│         (tooling_api_dml / metadata_create type=ApexClass|ApexTrigger)      │
│                                                                             │
│  3. sf-data  ◀── YOU ARE HERE (LAST!)                                       │
│     └── Seed and verify data (sobject_dml / bulk_dml / soql_query)          │
│                                                                             │
│  4. run_tests                                                               │
│     └── Apex tests and Flow tests against the seeded data                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why sf-data goes last

sf-data reads and writes **org data**. The objects, fields and automation it
exercises must already exist in the org, or the calls fail:

```
ERROR: "SObject type 'Quote__c' is not supported"
CAUSE: the object has not been created in this org yet
FIX:   sf-metadata (sobject_create) first, then sf-data
```

| Error                                      | Cause                              | Fix                                                                        |
| ------------------------------------------ | ---------------------------------- | -------------------------------------------------------------------------- |
| `SObject type 'X' not supported`           | Object does not exist in the org   | sf-metadata `sobject_create` first                                         |
| `INVALID_FIELD: No such column 'Field__c'` | Field missing **or** FLS blocks it | sf-metadata `sobject_field_create` (grants FLS) or `permission_set_update` |
| `REQUIRED_FIELD_MISSING`                   | Required field not set             | `sobject_describe`, include every required field                           |
| `FIELD_CUSTOM_VALIDATION_EXCEPTION`        | Validation rule fired              | Use values that satisfy the rule (sf-metadata can show it)                 |

---

## Test data after triggers and flows

Insert test data **after** the automation is in the org, so the insert
exercises it:

```
1. sf-apex   → tooling_api_dml / metadata_create: trigger + handler class
2. sf-flow   → metadata_create(type="Flow"): record-triggered flow, then activate
3. sf-data   ◀── seed records now — triggers and flows fire on insert
4. run_tests → Apex / Flow tests confirm behaviour
```

---

## The 201-record pattern

Cross the 200-record trigger chunk boundary to expose bulkification bugs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BATCH BOUNDARY TESTING                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Records 1-200:    first trigger chunk                                      │
│  Records 201+:     second chunk (crosses the boundary)                      │
│                                                                             │
│  Exposes: N+1 queries, DML in loops, governor limits                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

Two ways to seed 201+ records:

```
# A. One Bulk API job (preferred for 201+; triggers still run per 200-record chunk)
bulk_dml(
  operation="insert",
  sObject="Account",
  records=[{"Name": "Test Account 1"}, ..., {"Name": "Test Account 201"}]
)

# B. Two sobject_dml calls when you want synchronous per-record results
sobject_dml(operation="insert", sObject="Account", records=[ ...200 rows... ])
sobject_dml(operation="insert", sObject="Account", records=[{"Name": "Test Account 201"}])
```

Use **251** when the target is a Flow or other automation you want to see
run across more than one chunk with room to spare.

---

## Cross-skill integration

| From skill  | To sf-data | When                                                 |
| ----------- | ---------- | ---------------------------------------------------- |
| sf-apex     | → sf-data  | "Create 201 Accounts for bulk testing"               |
| sf-flow     | → sf-data  | "Create Opportunities with StageName = 'Closed Won'" |
| sf-metadata | → sf-data  | After creating the object/field, seed sample records |

| From sf-data | To skill      | When                                                                   |
| ------------ | ------------- | ---------------------------------------------------------------------- |
| sf-data      | → sf-metadata | Describe or fix an object (`INVALID_FIELD`, missing External ID field) |
| sf-data      | → sf-apex     | The seed data needs a deployed test class or an Apex data fix          |
| sf-data      | → sf-flow     | A flow fault path fired during the insert                              |

---

## Prerequisites check

```
# Connection and target org
cirra_ai_init()

# Object exists and fields are visible
sobject_describe(sObject="MyObject__c")

# Field-level security when a field is missing from describe or SOQL fails
soql_query(
  sObject="FieldPermissions",
  fields=["Field", "PermissionsRead", "PermissionsEdit", "Parent.Name"],
  whereClause="SobjectType = 'MyObject__c' AND Field = 'MyObject__c.My_Field__c'"
)
```

---

## Factory pattern integration

The Apex factories in `assets/factories/` are templates for **sf-apex test
classes**. Cirra cannot run anonymous Apex, so the flow is:

```
sf-apex:   deploys TestDataFactory_Account.cls + AccountTriggerTest.cls
           ↓
run_tests: executes AccountTriggerTest (factory builds 251 records in the test transaction)
           ↓
sf-data:   seeds persistent sample data for manual / Flow verification via sobject_dml or bulk_dml
```

---

## Cleanup sequence

After testing, clean up in reverse order:

```
1. sf-data   → delete test records (children before parents)
2. sf-flow   → deactivate or remove the test flow (metadata_update / metadata_delete)
3. sf-apex   → remove temporary classes/triggers (tooling_api_dml delete / metadata_delete)
4. sf-metadata → remove temporary fields/objects (metadata_delete)
```

**Cleanup command:**

```
# Query test records
soql_query(sObject="Account", fields=["Id"], whereClause="Name LIKE 'Test%'")

# Delete them (up to 200 per call)
sobject_dml(operation="delete", sObject="Account", recordIds=["001xx...", ...])

# More than 200: one Bulk API job
bulk_dml(operation="delete", sObject="Account", recordIds=["001xx...", ...])
```

---

## Related documentation

| Topic              | Location                                        |
| ------------------ | ----------------------------------------------- |
| Bulk operations    | `references/bulk-operations-guide.md`           |
| Test data patterns | `references/test-data-patterns.md`              |
| Cleanup guide      | `references/cleanup-rollback-guide.md`          |
| Factory templates  | `assets/factories/`                             |
| MCP tool shapes    | `../../../shared/references/cirra-mcp-tools.md` |
