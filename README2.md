# sf-apex Plugin Refactored for Cirra AI MCP Server

This directory contains the refactored **sf-apex** plugin that uses Cirra AI MCP Server instead of Salesforce CLI for all metadata operations.

## Quick Start

### What Changed

- Removed: Salesforce CLI dependencies (`sf project deploy`, `sf project retrieve`, etc.)
- Added: Cirra AI MCP Server tools (`metadata_create`, `metadata_update`, `metadata_read`)
- Result: Cloud-native, fully programmatic Apex code generation and deployment

### File Locations

#### Plugin Configuration

- **Plugin JSON**: `/exploded/.claude-plugin/plugin.json`
  - Declares MCP tool requirements
  - Version 2.0.0 (MCP-based)
  - 7 required tools + 3 optional

#### Skill Documentation

Two identical locations for different installation patterns:

1. **Exploded Layout**
   - `/sf-apex/exploded/skills/sf-apex/SKILL.md`
   - Use when skill is installed as separate directory

2. **Flat Layout**
   - `/sf-apex/skill/sf-apex/SKILL.md`
   - Alternative installation pattern

Both files contain identical refactored documentation.

## Directory Structure

```
sf-skills-cirra-ai/
├── README.md (this file)
├── REFACTORING_SUMMARY.md (detailed migration guide)
└── sf-apex/
    ├── exploded/
    │   ├── .claude-plugin/
    │   │   └── plugin.json
    │   └── skills/sf-apex/
    │       └── SKILL.md
    └── skill/sf-apex/
        └── SKILL.md
```

## Key Changes Overview

### Old (CLI-Based)

```bash
# File system operations
force-app/main/default/classes/AccountService.cls

# Deploy
sf project deploy --source-dir force-app/main/default/classes/

# Retrieve
sf project retrieve --metadata ApexClass:AccountService

# Describe
sf sobject describe --sobject Account
```

### New (MCP-Based)

```apex
// Generate as string
String apexCode = "public class AccountService { ... }";

// Deploy
metadata_create(type="ApexClass", metadata=[{
  "fullName": "AccountService",
  "apiVersion": "65.0",
  "status": "Active",
  "body": apexCode
}])

// Retrieve
metadata_read(type="ApexClass", fullNames=["AccountService"])

// Describe
sobject_describe(sObject="Account")
```

## MCP Tools Used

### Required (Must Have)

1. **cirra_ai_init** - Initialize Cirra AI MCP connection
2. **metadata_create** - Deploy new Apex classes/triggers
3. **metadata_update** - Update existing Apex code
4. **metadata_read** - Retrieve Apex code from org
5. **tooling_api_query** - Query metadata objects (ApexClass, ApexTestResult, etc.)
6. **soql_query** - Standard SOQL queries with binding
7. **sobject_describe** - Discover object schema and fields

### Optional (Nice to Have)

1. **metadata_delete** - Remove Apex classes from org
2. **tooling_api_dml** - Create/update metadata via DML (TAF Custom Metadata)
3. **sobjects_list** - List all objects in org

## Feature Comparison

| Feature                 | CLI Version       | MCP Version           | Status        |
| ----------------------- | ----------------- | --------------------- | ------------- |
| Apex code generation    | Yes               | Yes                   | ✅ Identical  |
| Service/Selector layers | Yes               | Yes                   | ✅ Identical  |
| TAF triggers            | Yes               | Yes                   | ✅ Identical  |
| Test classes (PNB)      | Yes               | Yes                   | ✅ Identical  |
| 150-point scoring       | Yes               | Yes                   | ✅ Identical  |
| Security best practices | Yes               | Yes                   | ✅ Identical  |
| Bulkification rules     | Yes               | Yes                   | ✅ Identical  |
| Code deployment         | CLI (force-app/)  | MPC (metadata_create) | ✅ Refactored |
| Code retrieval          | CLI (sf retrieve) | MCP (metadata_read)   | ✅ Refactored |
| Anonymous Apex          | sf apex run       | Not supported         | ❌ Removed    |
| Local file I/O          | Yes (force-app/)  | No                    | ✅ Improved   |

## Workflow Phases (Unchanged Core)

### Phase 1: Requirements

- Gather class type, purpose, target object
- Initialize MCP: `cirra_ai_init(cirra_ai_team="...", sf_user="...")`
- Query existing code: `tooling_api_query(...)`

### Phase 2: Design

- Select template pattern (TAF, Service, Batch, Test, etc.)
- Plan code structure and dependencies

### Phase 3: Generation

- Generate Apex code as STRING
- Validate against guardrails (no SOQL in loops, no hardcoded IDs, etc.)
- Score against 150-point rubric

### Phase 4: Deployment (REFACTORED)

- Deploy via `metadata_create(type="ApexClass", metadata=[...])`
- Verify with `metadata_read(type="ApexClass", fullNames=[...])`
- Query test results: `tooling_api_query(sObject="ApexTestResult")`

### Phase 5: Documentation

- Summary with score and next steps
- Test execution recommendations

## Best Practices Maintained

All 2025 best practices are preserved:

- **Bulkification** (25 pts): No SOQL/DML in loops, bulk test 251+ records
- **Security** (25 pts): WITH USER_MODE, binding, with sharing, FLS checks
- **Testing** (25 pts): 90%+ coverage, PNB patterns, Test Data Factory
- **Architecture** (20 pts): TAF triggers, Service/Domain/Selector layers, SOLID
- **Clean Code** (20 pts): Meaningful names, self-documenting, no `!= false`
- **Error Handling** (15 pts): Specific catches, no empty catch blocks
- **Performance** (10 pts): Monitor Limits, cache expensive ops, async for heavy work
- **Documentation** (10 pts): ApexDoc comments, meaningful parameters

Scoring thresholds remain:

- ✅ 90+ points: Deploy
- ⚠️ 67-89 points: Review required
- ❌ <67 points: Blocked - fix required

## Installation

### Prerequisites

- Cirra AI MCP Server access
- Salesforce org with Apex API enabled
- Claude Code with skill support

### Steps

1. Copy the skill to your Claude plugins directory
2. Use either `exploded` or `skill` layout (both work identically)
3. Invoke with skill name: `cirra-ai-sf-apex`

### Invoke Examples

```
User: Create a service class for Account processing using cirra-ai-sf-apex

Claude will:
1. Call cirra_ai_init()
2. Query existing code with tooling_api_query()
3. Generate code as string
4. Deploy with metadata_create()
5. Verify with metadata_read()
```

## Testing the Refactored Skill

### Test 1: Class Generation and Deployment

```
Request: Generate a bulkified Account service class

Expected:
- cirra_ai_init() called
- tooling_api_query() finds existing AccountService (or not)
- Code generated with proper bulkification
- metadata_create() deploys class
- metadata_read() verifies deployment
- Score >= 90 points
```

### Test 2: Trigger with TAF

```
Request: Create a TAF trigger for Account with SetDefaults action

Expected:
- Check TAF installation via tooling_api_query()
- Generate AccountTrigger.trigger
- Generate TA_Account_SetDefaults.cls
- Both deployed via metadata_create()
- Score >= 90 points
```

### Test 3: Code Review

```
Request: Review my existing AccountService class for improvements

Expected:
- metadata_read() retrieves AccountService code
- Analyzed against 150-point rubric
- Issues reported with fixes
- Suggestions for improvement
```

## Known Limitations

| Limitation                     | Reason                             | Workaround                                      |
| ------------------------------ | ---------------------------------- | ----------------------------------------------- |
| Anonymous Apex (`sf apex run`) | MCP doesn't support code execution | Generate test class, deploy via metadata_create |
| Local file templates           | No file I/O in MCP                 | Patterns in SKILL.md guide code generation      |
| Directory watching             | No file system access              | Generate strings, deploy to org                 |

## Migration from CLI Version

If you're currently using the CLI-based sf-apex skill:

1. **All generated code stays the same** - No Apex syntax changes
2. **Deployment method changes** - Use metadata_create instead of sf project deploy
3. **Retrieval method changes** - Use metadata_read instead of sf project retrieve
4. **Both skills can coexist** - Choose which one to use per task

Example migration:

```
OLD: sf project deploy --source-dir force-app/main/default/classes/AccountService.cls
NEW: metadata_create(type="ApexClass", metadata=[{ "fullName": "AccountService", "body": "[CODE]" }])
```

## Documentation Files

### In This Directory

1. **README.md** (this file)
   - Overview and quick start

2. **REFACTORING_SUMMARY.md**
   - Detailed transformation mappings
   - Before/after examples
   - Benefits analysis
   - Migration guide

### In SKILL.md (Both Locations)

Complete reference for:

- 5-phase workflow
- 150-point scoring rules
- All MCP tool usage
- Code generation patterns
- Best practices
- Apex 65.0 features
- TAF setup and patterns
- Testing patterns (PNB)
- Security guidelines
- Bulkification rules

## Version Information

- **Skill Name**: cirra-ai-sf-apex
- **Version**: 2.0.0 (MCP-based)
- **API Level**: Salesforce 65.0
- **Author**: Jag Valaiyapathy
- **Refactored**: 2025-02-06
- **License**: Apache-2.0

## Original CLI Version

The original sf-apex plugin (v1.1.0) is still available at:
`/sessions/lucid-loving-albattani/mnt/.local-plugins/marketplaces/sf-skills/sf-apex/`

## Support & Questions

Refer to:

1. **SKILL.md** - Complete documentation (both locations have identical content)
2. **REFACTORING_SUMMARY.md** - Migration and transformation details
3. **MCP Tool Mapping** section in SKILL.md - Tool usage examples

## Next Steps

1. **To use this skill**: Copy to your Claude plugins directory
2. **To understand changes**: Read REFACTORING_SUMMARY.md
3. **To deploy code**: Follow Phase 4 in SKILL.md
4. **To review code**: Use metadata_read() to retrieve existing code

---

**Note**: Both SKILL.md files are identical. Use whichever layout matches your installation pattern.
