# sf-apex Plugin Refactoring: CLI to Cirra AI MCP Server

## Overview

The original `sf-apex` skill used the Salesforce CLI (`sf project deploy`, `sf project retrieve`, etc.) for code deployment and retrieval. This refactored version replaces all CLI operations with Cirra AI MCP Server tools, enabling direct programmatic access to Salesforce metadata operations.

---

## Key Transformations

### 1. Deployment Operations

| Original (CLI)                                       | Refactored (MCP)                                    | Impact                                   |
| ---------------------------------------------------- | --------------------------------------------------- | ---------------------------------------- |
| `sf project deploy`                                  | `metadata_create(type="ApexClass", metadata=[...])` | Direct Salesforce API, no CLI wrapper    |
| `sf project deploy` (update)                         | `metadata_update(type="ApexClass", metadata=[...])` | Supports both create and update patterns |
| Local file system: `force-app/main/default/classes/` | String-based code generation                        | No local file I/O, pure API-driven       |

**Example Before**:

```bash
sf project deploy --source-dir force-app/main/default/classes/AccountService.cls
```

**Example After**:

```
metadata_create(
  type="ApexClass",
  metadata=[{
    "fullName": "AccountService",
    "apiVersion": "65.0",
    "status": "Active",
    "body": "[APEX CODE STRING]"
  }]
)
```

---

### 2. Code Retrieval Operations

| Original (CLI)                 | Refactored (MCP)                                   | Impact                                   |
| ------------------------------ | -------------------------------------------------- | ---------------------------------------- |
| `sf project retrieve`          | `metadata_read(type="ApexClass", fullNames=[...])` | Direct metadata retrieval                |
| `Glob: **/*.cls` (file search) | `tooling_api_query(sObject="ApexClass")`           | Query existing code, no file system scan |

**Example Before**:

```bash
sf project retrieve --metadata ApexClass:AccountService
```

**Example After**:

```
metadata_read(
  type="ApexClass",
  fullNames=["AccountService"]
)
```

---

### 3. Metadata Discovery

| Original (CLI)                    | Refactored (MCP)                         | Impact                                       |
| --------------------------------- | ---------------------------------------- | -------------------------------------------- |
| `sf sobject describe Account`     | `sobject_describe(sObject="Account")`    | Direct schema inspection                     |
| `sf data query --use-tooling-api` | `tooling_api_query(sObject="ApexClass")` | Query ApexClass, ApexTrigger, ApexTestResult |
| `sf data query`                   | `soql_query(sObject="Account")`          | Standard SOQL queries with binding           |

**Example Before**:

```bash
sf sobject describe --sobject Account
sf data query --use-tooling-api --query "SELECT Id, Name FROM ApexClass LIMIT 100"
```

**Example After**:

```
sobject_describe(sObject="Account")
tooling_api_query(sObject="ApexClass", limit=100)
```

---

### 4. Removed Operations (Not Supported in MCP)

| Feature                  | Original                        | Reason                             | Workaround                                          |
| ------------------------ | ------------------------------- | ---------------------------------- | --------------------------------------------------- |
| Anonymous Apex execution | `sf apex run`                   | MCP doesn't support anonymous code | Generate test class, deploy via metadata_create     |
| Local file templates     | File system templates           | No file system access via MCP      | Reference patterns in SKILL.md, generate as strings |
| Automatic file sync      | `force-app/` directory watching | No file I/O in MCP                 | Generate strings, deploy via metadata_create        |

---

## Workflow Changes

### Phase 1: Initialization (NEW)

**OLD**: No initialization needed - CLI already authenticated
**NEW**: MUST call `cirra_ai_init` first

```
cirra_ai_init(cirra_ai_team="[TEAM_ID]", sf_user="[ORG_ALIAS]")
```

### Phase 2: Code Generation (SAME CORE)

Apex code generation logic remains identical - all best practices, patterns, scoring maintained.

- TAF triggers still supported
- PNB testing pattern still required
- 150-point scoring unchanged
- All guardrails enforced

### Phase 3: Deployment (REFACTORED)

**OLD**:

1. Write to file system: `force-app/main/default/classes/`
2. Deploy via CLI: `sf project deploy`

**NEW**:

1. Generate as string with ApexDoc
2. Deploy via MCP: `metadata_create(type="ApexClass", metadata=[...])`
3. Verify: `metadata_read(type="ApexClass", fullNames=[...])`

### Phase 4: Review/Retrieval (REFACTORED)

**OLD**:

1. Read local files: `Read: force-app/main/default/classes/AccountService.cls`
2. Check git: `Glob: **/*.cls`

**NEW**:

1. Query: `metadata_read(type="ApexClass", fullNames=["AccountService"])`
2. Or: `tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'Account%'")`

---

## MCP Tool Mapping Reference

| Salesforce CLI                    | MCP Tool                                      | Notes                                           |
| --------------------------------- | --------------------------------------------- | ----------------------------------------------- |
| `sf data query`                   | `soql_query()`                                | Standard data queries (WITH USER_MODE)          |
| `sf data query --use-tooling-api` | `tooling_api_query()`                         | Metadata queries (ApexClass, ApexTrigger, etc.) |
| `sf project deploy`               | `metadata_create()` / `metadata_update()`     | Deploy Apex, triggers, config                   |
| `sf project retrieve`             | `metadata_read()`                             | Retrieve metadata by name                       |
| `sf sobject describe`             | `sobject_describe()`                          | Get object schema (fields, CRUD, sharing)       |
| `sf apex test run`                | `tooling_api_query(sObject="ApexTestResult")` | Query test results (not execution)              |
| (Custom Metadata)                 | `tooling_api_dml()`                           | Create/update TAF Custom Metadata records       |

---

## Code Generation (NO CHANGES)

All Apex code generation patterns remain identical:

### Still Supported

- ✅ Trigger Actions Framework (TAF)
- ✅ Service/Selector/Domain layers
- ✅ Batch Apex, Queueable, @future
- ✅ Test classes with PNB patterns
- ✅ @InvocableMethod (Flow integration)
- ✅ All 150-point scoring rules
- ✅ Security best practices (WITH USER_MODE, binding, FLS)
- ✅ Bulkification guardrails
- ✅ 2025 modern Apex features (null coalescing, safe navigation)

### Code is Now

- Generated as **strings** (not written to file system)
- Deployed via **metadata_create** (not file system)
- Verified with **metadata_read** (not local file read)

---

## Benefits of MCP Refactor

| Benefit                  | Reason                                       |
| ------------------------ | -------------------------------------------- |
| No CLI dependency        | Direct Salesforce API calls                  |
| Programmatic access      | Full control over metadata operations        |
| No file system pollution | Code lives only in Salesforce org            |
| Cloud-native             | Pure API-driven, works from any environment  |
| Faster                   | No CLI startup overhead                      |
| Type-safe                | Structured MCP tool calls with validation    |
| Streaming ready          | Can handle large code bases via metadata API |

---

## Testing the Refactored Skill

### Test 1: Basic Class Deployment

```
User: Generate an Apex service class for Account processing

Claude:
1. Calls: cirra_ai_init()
2. Queries: tooling_api_query(sObject="ApexClass", whereClause="Name LIKE 'Account%'")
3. Generates: AccountService.cls as string
4. Deploys: metadata_create(type="ApexClass", metadata=[...])
5. Verifies: metadata_read(type="ApexClass", fullNames=["AccountService"])
```

### Test 2: Trigger Deployment

```
User: Create a TAF trigger for Account

Claude:
1. Checks TAF installation: tooling_api_query(sObject="InstalledSubscriberPackage")
2. Generates: AccountTrigger.trigger + TA_Account_Action.cls as strings
3. Deploys both via metadata_create
4. Verifies deployment
```

### Test 3: Code Review

```
User: Review my existing AccountService class

Claude:
1. Retrieves: metadata_read(type="ApexClass", fullNames=["AccountService"])
2. Analyzes: Against 150-point scoring
3. Reports: Issues with fixes
4. (Optional) Deploys: metadata_update with fixed code
```

---

## File Structure

### Exploded Layout

```
sf-skills-cirra-ai/sf-apex/exploded/
├── .claude-plugin/
│   └── plugin.json (new MCP tools declaration)
└── skills/sf-apex/
    └── SKILL.md (refactored with MCP operations)
```

### Flat Layout

```
sf-skills-cirra-ai/sf-apex/skill/
└── sf-apex/
    └── SKILL.md (identical to exploded version)
```

---

## Migration Guide for Users

### If you have existing force-app/ code

1. Code is STILL valid - no syntax changes
2. Deploy via: `metadata_create(type="ApexClass", metadata=[...])`
3. Read from org: `metadata_read(type="ApexClass", fullNames=[...])`

### If you're new to Cirra AI MCP

1. Start with `cirra_ai_init()`
2. Follow the 5-phase workflow
3. Generate code as strings
4. Deploy via `metadata_create`
5. Verify via `metadata_read`

### If you need to use CLI still

1. Original skill remains available at original path
2. Both skills can coexist
3. Choose by skill name: `sf-apex` (CLI) vs `sf-apex-cirra-ai` (MCP)

---

## Backward Compatibility

| Feature             | Compatibility                                     |
| ------------------- | ------------------------------------------------- |
| Generated Apex code | 100% compatible - same code, different deployment |
| 150-point scoring   | 100% compatible - same rules                      |
| Guardrails          | 100% compatible - same anti-patterns blocked      |
| Test patterns (PNB) | 100% compatible - same pattern                    |
| TAF support         | 100% compatible - same implementation             |
| Best practices      | 100% compatible - all still apply                 |

The ONLY difference is HOW code is deployed, not WHAT code is generated.

---

## Summary

This refactoring maintains all Apex expertise and best practices while replacing the CLI integration layer with Cirra AI MCP Server. The result is:

- **Same quality code generation**
- **Same scoring and validation**
- **Faster deployment** (direct API calls)
- **No file system dependency**
- **Fully programmatic** (no shell commands)
- **Cloud-native** ready

The sf-apex skill is now truly cloud-agnostic - it works wherever Cirra AI MCP Server is available.

---

## Version Information

- **Original**: sf-apex v1.1.0 (CLI-based)
- **Refactored**: sf-apex-cirra-ai v2.0.0 (MCP-based)
- **Author**: Jag Valaiyapathy
- **Refactor Date**: 2025-02-06
- **Refactor Agent**: Claude Code Agent
- **API Level**: Salesforce API 65.0
