---
name: cirra-ai-sf-apex
description: >
  Generates and reviews Salesforce Apex code with 2025 best practices and 150-point
  scoring using Cirra AI MCP Server metadata API. Use when writing Apex classes, triggers,
  test classes, batch jobs, or reviewing existing Apex code for bulkification, security,
  and SOLID principles.
---

# cirra-ai-sf-apex: Salesforce Apex Code Generation and Review (Cirra AI Edition)

Expert Apex developer specializing in clean code, SOLID principles, and 2025 best practices. Generate production-ready, secure, performant, and maintainable Apex code with deployment via Cirra AI MCP Server.

## Core Responsibilities

1. **Code Generation**: Create Apex classes, triggers (TAF), tests, async jobs from requirements
2. **Code Review**: Analyze existing Apex for best practices violations with actionable fixes
3. **Validation & Scoring**: Score code against 8 categories (0-150 points)
4. **Metadata Deployment**: Deploy via Cirra AI MCP Server (metadata_create/metadata_update/metadata_read)

---

## Workflow (5-Phase Pattern)

### Phase 1: Requirements Gathering & MCP Initialization

**FIRST**: Call `cirra_ai_init()` with no parameters:

```
cirra_ai_init()
```

- If a default org is configured, proceed immediately and confirm with the user:
  > "I've connected to **[org]**. Would you like me to use the defaults, or do you want to select different options?"
- If no default is configured, ask for the Salesforce user/alias before proceeding.

Do **not** ask for org details before calling `cirra_ai_init()`.

**Then** use **AskUserQuestion** to gather (for code generation tasks):

- Class type (Trigger, Service, Selector, Batch, Queueable, Test, Controller)
- Primary purpose (one sentence)
- Target object(s)
- Test requirements

**Then**:

1. Check existing code: `tooling_api_query(sObject="ApexClass", whereClause="Name LIKE '%Account%'")`
2. Check for existing Trigger Actions Framework: `tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'TA_%'")`
3. Create TodoWrite tasks

---

### Phase 2: Design & Template Selection

**Select template** (for reference - code is generated as strings):
| Class Type | Reference Template |
|------------|----------|
| Trigger | Standard TAF trigger pattern |
| Trigger Action | TA_ObjectName_Purpose naming |
| Service | Service layer pattern |
| Selector | Selector pattern for queries |
| Batch | Batch Apex pattern |
| Queueable | Queueable/async pattern |
| Test | Test class with PNB patterns |
| Test Data Factory | Factory pattern for test data |
| Standard Class | Standard utility/controller class |

**Template-Free Design**: Generate Apex code directly as strings following naming conventions and patterns. No file system templates needed.

---

### Phase 3: Code Generation/Review

**For Generation**:

1. Generate Apex code as a STRING (not saved to file system)
2. Apply naming conventions (see best practices section)
3. Include ApexDoc comments
4. Generate corresponding test class as STRING
5. Validate code against guardrails (see below)

**For Review**:

1. List classes: `tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'AccountService%'")`
2. Retrieve class body: `tooling_api_query(sObject="ApexClass", fields=["Id","FullName","Name","Body","Metadata"], whereClause="Id = '<classId>'")`
2. Analyze against best practices
3. Generate improvement report with specific fixes

**Run Validation**:

```
Score: XX/150 ⭐⭐⭐⭐ Rating
├─ Bulkification: XX/25
├─ Security: XX/25
├─ Testing: XX/25
├─ Architecture: XX/20
├─ Clean Code: XX/20
├─ Error Handling: XX/15
├─ Performance: XX/10
└─ Documentation: XX/10
```

---

### ⛔ GENERATION GUARDRAILS (MANDATORY)

**BEFORE generating ANY Apex code, Claude MUST verify no anti-patterns are introduced.**

If ANY of these patterns would be generated, **STOP and ask the user**:

> "I noticed [pattern]. This will cause [problem]. Should I:
> A) Refactor to use [correct pattern]
> B) Proceed anyway (not recommended)"

| Anti-Pattern                 | Detection                           | Impact                            |
| ---------------------------- | ----------------------------------- | --------------------------------- |
| SOQL inside loop             | `for(...) { [SELECT...] }`          | Governor limit failure (100 SOQL) |
| DML inside loop              | `for(...) { insert/update }`        | Governor limit failure (150 DML)  |
| Missing sharing              | `class X {` without keyword         | Security violation                |
| Hardcoded ID                 | 15/18-char ID literal               | Deployment failure                |
| Empty catch                  | `catch(e) { }`                      | Silent failures                   |
| String concatenation in SOQL | `'SELECT...WHERE Name = \'' + var`  | SOQL injection                    |
| Test without assertions      | `@IsTest` method with no `Assert.*` | False positive tests              |

**DO NOT generate anti-patterns even if explicitly requested.** Ask user to confirm the exception with documented justification.

### ✅ MANDATORY DELIVERABLES

**Every Apex generation MUST include these artifacts.** Do NOT deliver a class or trigger without the corresponding items below.

#### 1. Triggers MUST have a helper class

Never put business logic directly in a trigger body. Always extract logic into a separate handler/helper class:

- **If TAF is installed** → generate the trigger (`new MetadataTriggerHandler().run()`) + one or more `TA_Object_Purpose` action classes
- **If TAF is NOT installed** → generate a thin trigger that delegates to a handler class (e.g., `AccountTriggerHandler`) containing all logic

The trigger file should contain only routing; the helper class holds the logic. This is non-negotiable regardless of how simple the logic seems.

#### 2. Unit tests for ALL generated Apex

Every class **and** every trigger (including its helper/handler) MUST have a corresponding test class delivered in the same response. The test class MUST include at minimum the PNB pattern:

- **P**ositive — happy-path test
- **N**egative — error/exception test
- **B**ulk — 251+ records test

If the generated code includes both a trigger + helper class, the test class should cover both (trigger fires correctly, helper logic works in isolation).

Do NOT defer test generation to a later step or offer it as optional. Tests are part of the deliverable, not follow-up work.

---

### Phase 4: Metadata Deployment

**Step 1: Generate Code String**
Generate Apex code as a STRING with full ApexDoc comments and validation.

**Step 2: Deploy via Cirra AI MCP**

```
metadata_create(
  type="ApexClass",
  metadata=[{
    "fullName": "AccountService",
    "apiVersion": "65.0",
    "status": "Active",
    "body": "[YOUR APEX CODE STRING HERE]"
  }]
)
```

**Step 3: Verify Deployment**

```
metadata_read(
  type="ApexClass",
  fullNames=["AccountService"]
)
```

**Step 4: Test Execution** (via SOQL on ApexTestResult)

```
tooling_api_query(
  sObject="ApexTestResult",
  whereClause="TestClassName = 'AccountServiceTest' ORDER BY CreatedDate DESC LIMIT 10"
)
```

---

### Phase 5: Documentation & Testing Guidance

**Completion Summary**:

```
✓ Apex Code Complete: [ClassName]
  Type: [type] | API: 65.0
  Deployment: VIA CIRRA AI MCP (metadata_create)
  Test Class: [TestClassName]
  Validation: PASSED (Score: XX/150)

Next Steps: Run tests via Cirra AI, verify via metadata_read, monitor logs
```

---

## Best Practices (150-Point Scoring)

| Category           | Points | Key Rules                                                                        |
| ------------------ | ------ | -------------------------------------------------------------------------------- |
| **Bulkification**  | 25     | NO SOQL/DML in loops; collect first, operate after; test 251+ records            |
| **Security**       | 25     | `WITH USER_MODE`; bind variables; `with sharing`; `Security.stripInaccessible()` |
| **Testing**        | 25     | 90%+ coverage; Assert class; positive/negative/bulk tests; Test Data Factory     |
| **Architecture**   | 20     | TAF triggers; Service/Domain/Selector layers; SOLID; dependency injection        |
| **Clean Code**     | 20     | Meaningful names; self-documenting; no `!= false`; single responsibility         |
| **Error Handling** | 15     | Specific before generic catch; no empty catch; custom business exceptions        |
| **Performance**    | 10     | Monitor with `Limits`; cache expensive ops; scope variables; async for heavy     |
| **Documentation**  | 10     | ApexDoc on classes/methods; meaningful params                                    |

**Thresholds**: ✅ 90+ (Deploy) | ⚠️ 67-89 (Review) | ❌ <67 (Block - fix required)

---

## Trigger Actions Framework (TAF)

### Quick Reference

**When to Use**: If TAF package is installed in target org

**Check Installation**:

```
tooling_api_query(
  sObject="InstalledSubscriberPackage",
  whereClause="Name = 'Trigger Actions Framework'"
)
```

**Trigger Pattern** (one per object):

```apex
trigger AccountTrigger on Account (before insert, after insert, before update, after update, before delete, after delete, after undelete) {
    new MetadataTriggerHandler().run();
}
```

**Action Class** (one per behavior):

```apex
public class TA_Account_SetDefaults implements TriggerAction.BeforeInsert {
    public void beforeInsert(List<Account> newList) {
        for (Account acc : newList) {
            if (acc.Industry == null) {
                acc.Industry = 'Other';
            }
        }
    }
}
```

**Deploy Action Class**:

```
metadata_create(
  type="ApexClass",
  metadata=[{
    "fullName": "TA_Account_SetDefaults",
    "apiVersion": "65.0",
    "status": "Active",
    "body": "[GENERATED APEX CODE]"
  }]
)
```

**⚠️ CRITICAL**: TAF triggers do NOTHING without `Trigger_Action__mdt` records! Each action class needs a corresponding Custom Metadata record (deploy manually or via separate metadata deployment).

**Fallback**: If TAF is NOT installed, use standard trigger pattern (non-TAF).

---

## Async Decision Matrix

| Scenario                        | Use                     |
| ------------------------------- | ----------------------- |
| Simple callout, fire-and-forget | `@future(callout=true)` |
| Complex logic, needs chaining   | `Queueable`             |
| Process millions of records     | `Batch Apex`            |
| Scheduled/recurring job         | `Schedulable`           |
| Post-queueable cleanup          | `Queueable Finalizer`   |

---

## Modern Apex Features (API 65.0)

- **Null coalescing**: `value ?? defaultValue`
- **Safe navigation**: `record?.Field__c`
- **User mode**: `WITH USER_MODE` in SOQL
- **Assert class**: `Assert.areEqual()`, `Assert.isTrue()`

**Breaking Change (API 62.0)**: Cannot modify Set while iterating - throws `System.FinalException`

---

## Flow Integration (@InvocableMethod)

Apex classes can be called from Flow using `@InvocableMethod`. This pattern enables complex business logic, DML, callouts, and integrations from declarative automation.

### Quick Pattern

```apex
public with sharing class RecordProcessor {

    @InvocableMethod(label='Process Record' category='Custom')
    public static List<Response> execute(List<Request> requests) {
        List<Response> responses = new List<Response>();
        for (Request req : requests) {
            Response res = new Response();
            res.isSuccess = true;
            res.processedId = req.recordId;
            responses.add(res);
        }
        return responses;
    }

    public class Request {
        @InvocableVariable(label='Record ID' required=true)
        public Id recordId;
    }

    public class Response {
        @InvocableVariable(label='Is Success')
        public Boolean isSuccess;
        @InvocableVariable(label='Processed ID')
        public Id processedId;
    }
}
```

**Deploy via Cirra AI**:

```
metadata_create(
  type="ApexClass",
  metadata=[{
    "fullName": "RecordProcessor",
    "apiVersion": "65.0",
    "status": "Active",
    "body": "[YOUR INVOCABLE METHOD CODE]"
  }]
)
```

---

## Testing Best Practices

### The 3 Test Types (PNB Pattern)

Every feature needs:

1. **Positive**: Happy path test
2. **Negative**: Error handling test
3. **Bulk**: 251+ records test

**Example**:

```apex
@IsTest
static void testPositive() {
    Account acc = new Account(Name = 'Test', Industry = 'Tech');
    insert acc;
    Assert.areEqual('Tech', [SELECT Industry FROM Account WHERE Id = :acc.Id].Industry);
}

@IsTest
static void testNegative() {
    try {
        insert new Account(); // Missing Name
        Assert.fail('Expected DmlException');
    } catch (DmlException e) {
        Assert.isTrue(e.getMessage().contains('REQUIRED_FIELD_MISSING'));
    }
}

@IsTest
static void testBulk() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 251; i++) {
        accounts.add(new Account(Name = 'Bulk ' + i));
    }
    insert accounts;
    Assert.areEqual(251, [SELECT COUNT() FROM Account]);
}
```

**Deploy Test Class**:

```
metadata_create(
  type="ApexClass",
  metadata=[{
    "fullName": "AccountServiceTest",
    "apiVersion": "65.0",
    "status": "Active",
    "body": "[YOUR TEST CLASS CODE]"
  }]
)
```

---

## Common Exception Types

When writing test classes, use these specific exception types:

| Exception Type         | When to Use                   |
| ---------------------- | ----------------------------- |
| `DmlException`         | Insert/update/delete failures |
| `QueryException`       | SOQL query failures           |
| `NullPointerException` | Null reference access         |
| `ListException`        | List operation failures       |
| `LimitException`       | Governor limit exceeded       |
| `CalloutException`     | HTTP callout failures         |

---

## Cirra AI MCP Server Integration

### Required Initialization

**ALWAYS start with**:

```
cirra_ai_init()
```

Call with no parameters — uses the default org. If a default is configured, confirm with the user before proceeding. If no default is configured, ask for the Salesforce user/alias.

This initializes the connection to Cirra AI MCP Server and provides access to all Salesforce metadata operations.

### MCP Tools Mapping

| Operation       | CLI Command                       | MCP Tool            | Example                                                                  |
| --------------- | --------------------------------- | ------------------- | ------------------------------------------------------------------------ |
| Query Apex code | `sf data query`                   | `soql_query`        | `soql_query(sObject="ApexClass", whereClause="Name = 'AccountService'")` |
| Query metadata  | `sf data query --use-tooling-api` | `tooling_api_query` | `tooling_api_query(sObject="ApexClass")`                                 |
| Deploy class    | `sf project deploy`               | `metadata_create`   | `metadata_create(type="ApexClass", metadata=[...])`                      |
| Update class    | `sf project deploy` (existing)    | `metadata_update`   | `metadata_update(type="ApexClass", metadata=[...])`                      |
| List classes    | `sf project retrieve`             | `tooling_api_query` | `tooling_api_query(sObject="ApexClass", whereClause="Name = 'AccountService'")` |
| Retrieve class body | `sf project retrieve`         | `tooling_api_query` | `tooling_api_query(sObject="ApexClass", fields=["Id","FullName","Name","Body","Metadata"], whereClause="Id = '<classId>'")` |
| Describe object | `sf sobject describe`             | `sobject_describe`  | `sobject_describe(sObject="Account")`                                    |
| Delete class    | `sf project delete`               | `metadata_delete`   | `metadata_delete(type="ApexClass", fullNames=["AccountService"])`        |
| Test results    | `sf apex test run` (query)        | `tooling_api_query` | `tooling_api_query(sObject="ApexTestResult")`                            |

### Metadata API Format

When deploying via `metadata_create` or `metadata_update`, use this format:

```
metadata_create(
  type="ApexClass",
  metadata=[{
    "fullName": "ClassName",
    "apiVersion": "65.0",
    "status": "Active",
    "body": "public class ClassName { ... }"
  }]
)
```

For triggers:

```
metadata_create(
  type="ApexTrigger",
  metadata=[{
    "fullName": "AccountTrigger",
    "apiVersion": "65.0",
    "status": "Active",
    "body": "trigger AccountTrigger on Account (...) { ... }",
    "triggerEvents": ["before insert", "after insert", ...]
  }]
)
```

### Query Examples

**Find all Apex classes**:

```
tooling_api_query(
  sObject="ApexClass",
  limit=100
)
```

**Find test results for a class**:

```
tooling_api_query(
  sObject="ApexTestResult",
  whereClause="TestClassName = 'AccountServiceTest' ORDER BY CreatedDate DESC LIMIT 10"
)
```

**Find triggers on Account**:

```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="EntityDefinitionId IN (SELECT Id FROM EntityDefinition WHERE QualifiedApiName = 'Account')"
)
```

**Query with SOQL (not metadata)**:

```
soql_query(
  sObject="Account",
  whereClause="Industry = 'Technology'",
  limit=10
)
```

---

## Cross-MCP Tool Integration

| MCP Tool            | Use Case                             | Example                                                                      |
| ------------------- | ------------------------------------ | ---------------------------------------------------------------------------- |
| `sobject_describe`  | Discover object/fields before coding | `sobject_describe(sObject="Invoice__c")` → get field names, types, CRUD      |
| `soql_query`        | Test code behavior after deploy      | `soql_query(sObject="Account", whereClause="Id IN :accountIds")`             |
| `tooling_api_query` | Check existing Apex classes          | `tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'Account%'")` |
| `tooling_api_query` | Retrieve class body for review       | `tooling_api_query(sObject="ApexClass", fields=["Id","FullName","Name","Body","Metadata"], whereClause="Id = '<classId>'")` |
| `metadata_create`   | Deploy new Apex classes/triggers     | `metadata_create(type="ApexClass", metadata=[...])`                          |
| `metadata_update`   | Update existing Apex code            | `metadata_update(type="ApexClass", metadata=[...])`                          |
| `tooling_api_dml`   | Perform DML on metadata objects      | `tooling_api_dml(operation="update", sObject="ApexClass", record={...})`     |

---

## Field-Level Security & CRUD Checks

Before generating code that accesses fields, use `sobject_describe`:

```
sobject_describe(sObject="Account")
→ Returns: fields[], CRUD permissions, sharing rules
```

In generated code, use:

```apex
// For CRUD/FLS checking
List<String> fieldsToRead = new List<String>{ 'Name', 'Industry' };
Map<String, Schema.SObjectField> fieldMap = Schema.Account.getSObjectType().getDescribe().fields.getMap();

for (String field : fieldsToRead) {
    if (!fieldMap.get(field).getDescribe().isAccessible()) {
        throw new SecurityException('Field ' + field + ' is not accessible');
    }
}
```

Or use `Security.stripInaccessible()`:

```apex
List<Account> accounts = [SELECT Id, Name, Industry FROM Account LIMIT 100];
accounts = (List<Account>) Security.stripInaccessible(AccessType.READABLE, accounts);
```

---

## Limitations & Workarounds

| Feature                  | CLI Support               | MCP Support                              | Workaround                                         |
| ------------------------ | ------------------------- | ---------------------------------------- | -------------------------------------------------- |
| Anonymous Apex execution | `sf apex run`             | ❌ Not available                         | Generate test class and deploy via metadata_create |
| Automatic file sync      | `force-app/main/default/` | ❌ Not available                         | Generate strings, deploy via metadata API          |
| Local templates          | Template file system      | ✅ Reference only (no file access)       | Generate code from patterns in this doc            |
| Metadata deployment      | `sf project deploy`       | ✅ `metadata_create` / `metadata_update` | Full support via MCP                               |
| Code retrieval           | `sf project retrieve`     | ✅ `metadata_read`                       | Full support via MCP                               |
| Test execution           | `sf apex test run`        | Partial - query via `tooling_api_query`  | Query ApexTestResult after deployment              |

---

## Glossary of MCP Terms

- **MCP**: Model Context Protocol - allows Claude to access external applications like Salesforce
- **Cirra AI**: AI assistant that provides the Salesforce Admin MCP server
- **Metadata API**: Programmatic interface to deploy/retrieve Apex, triggers, config
- **Tooling API**: Query and update (via DML) metadata objects like ApexClass, ApexTrigger, ApexTestResult
- **ApexClass**: Apex class metadata object (stored in Salesforce)
- **ApexTrigger**: Apex trigger metadata object (stored in Salesforce)
- **ApexTestResult**: Test execution result metadata object

---

## Apex Class MCP Patterns

### List all classes
```
tooling_api_query(sObject="ApexClass", fields=["Id","Name","NamespacePrefix","ApiVersion","IsValid","Status","ManageableState"])
```

### Retrieve class body (for review or edit)
```
tooling_api_query(sObject="ApexClass", fields=["Id","FullName","Name","NamespacePrefix","Body","Metadata"], whereClause="Id = '<classId>'")
```

Do **not** use `metadata_read` for ApexClass — it does not return the class body.

### Create a class
```
tooling_api_dml(operation="insert", sObject="ApexClass", record={"Name": "MyClass", "Body": "public class MyClass { ... }", "Status": "Active", "ApiVersion": "65.0"})
```

Always obtain explicit approval before creating, updating, or deleting a class.

### Update a class
```
tooling_api_dml(operation="update", sObject="ApexClass", record={"Id": "<classId>", "Name": "MyClass", "Body": "...", "Status": "Active"})
```

### Delete a class
```
tooling_api_dml(operation="delete", sObject="ApexClass", record={"Id": "<classId>"})
```

Before deleting: check for references in other Apex classes, triggers, LWC, and flows. List references and offer to handle them first.

---

## Dependencies

### Cirra AI MCP Server tools

#### Required

- cirra_ai_init
- soql_query
- tooling_api_query
- metadata_create
- metadata_update
- metadata_read

#### Optional

- sobject_describe
- metadata_delete
- tooling_api_dml
- sobjects_list

---

## Org-Wide Apex Audit

**Do NOT create dashboards, interactive UIs, or artifacts.** Pull the classes, run the analysis, and present results as text directly in the conversation. Generate an HTML or document report only when the user explicitly asks for one.

This plugin includes `hooks/scripts/score_apex_classes.py` — a scalable scorer that audits ALL custom Apex classes in an org using the 150-point rubric.

### Usage

```bash
python3 hooks/scripts/score_apex_classes.py --output-dir ./audit_output [--batch-size 200] [--resume]
```

### Features

- **Pagination**: Fetches classes in batches via `tooling_api_query` with `Id > lastId` cursor
- **Resume**: Saves progress every 50 classes to `{output_dir}/intermediate/apex_scoring_progress.json`
- **Anti-Pattern Detection**: Regex-based detection of SOQL in loops, DML in loops, missing sharing keywords, hardcoded IDs, empty catch blocks, SOQL injection
- **Metadata-Only Scoring**: Falls back to size/API-version heuristics when class body is unavailable
- **Output-Directory-First**: ALL files written to `--output-dir` — no files outside the output tree

### Output Files

```
{output_dir}/intermediate/
├── apex_batch_*.json           # Raw class metadata per batch
├── apex_scoring_progress.json  # Resume checkpoint
├── apex_scores.json            # Individual class scores
└── apex_scoring_summary.json   # Aggregate statistics & distribution
```

### Scoring Thresholds

| Range | Recommendation |
|---|---|
| ≥ 90 | ✅ Deploy |
| 67-89 | ⚠️ Review |
| < 67 | ❌ Block |

---

## Notes

- **API Version**: 65.0 required
- **TAF Optional**: Prefer TAF when package is installed, use standard trigger pattern as fallback
- **Scoring**: Block deployment if score < 67
- **MCP Initialization**: ALWAYS call `cirra_ai_init` first
- **Code as String**: Generate all Apex as strings, deploy via metadata_create/update
- **No Local Files**: Apex code is NOT saved to local file system - lives only in Salesforce org via Metadata API
- **Audit Output**: All audit intermediate files go to `--output-dir` by default

---

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2025 Jag Valaiyapathy

**Refactored for Cirra AI MCP Server by Claude Agent (2025)**
