# cirra-ai-sf-apex Refactored Plugin - Complete File Index

## Project Overview

This project contains the refactored **sf-apex** Salesforce Apex code generation skill, migrated from Salesforce CLI to Cirra AI MCP Server. The original skill v1.1.0 (CLI-based) is now v2.0.0 (MCP-based).

**Key Achievement**: All Apex code generation and best practices are preserved, only the deployment mechanism changed from CLI to MCP.

---

## File Structure and Purpose

### Root Directory: `/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/`

```
sf-skills-cirra-ai/
├── README.md                           ← Start here: Quick start guide
├── INDEX.md                            ← This file
├── REFACTORING_SUMMARY.md              ← Detailed migration documentation
└── sf-apex/
    ├── exploded/                       ← Exploded layout (option 1)
    │   ├── .claude-plugin/
    │   │   └── plugin.json             ← MCP tools declaration
    │   └── skills/sf-apex/
    │       └── SKILL.md                ← Refactored skill doc (607 lines)
    └── skill/sf-apex/                  ← Flat layout (option 2)
        └── SKILL.md                    ← Identical copy of SKILL.md
```

---

## Detailed File Guide

### 1. **README.md** (Start Here)

**Location**: `/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/README.md`

**Purpose**: Quick start and overview
**Contains**:

- What changed (CLI → MCP)
- File locations for both layouts
- Directory structure
- Quick command comparison
- MCP tools overview
- Feature comparison table
- 5-phase workflow summary
- Installation steps
- Test scenarios
- Known limitations
- Migration guide

**Read First**: Yes - provides context for all other files

---

### 2. **REFACTORING_SUMMARY.md**

**Location**: `/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/REFACTORING_SUMMARY.md`

**Purpose**: Detailed migration and transformation documentation
**Contains**:

- Complete transformation mappings (CLI → MCP)
- Before/after code examples for all operations:
  - Deployment (`sf project deploy` → `metadata_create`)
  - Retrieval (`sf project retrieve` → `metadata_read`)
  - Discovery (`sf sobject describe` → `sobject_describe`)
- Removed operations (sf apex run, file templates)
- 5-phase workflow changes with specific details
- MCP tool mapping reference table
- Code generation patterns (unchanged)
- Benefits analysis
- Testing scenarios with full walkthrough
- File structure explanation
- Migration guide for existing users
- Backward compatibility notes
- Version information

**Read Second**: For deep understanding of what changed and why

---

### 3. **plugin.json** (MCP Configuration)

**Location**: `/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/sf-apex/exploded/.claude-plugin/plugin.json`

**Purpose**: Declares MCP tool requirements for the skill
**Contains**:

- Plugin name: `cirra-ai-sf-apex`
- Version: `2.0.0`
- Description
- Author metadata
- License: Apache-2.0
- Repository link
- Keywords (includes "cirra-ai", "metadata-api")
- Requirements:
  - `cirra_ai_team`: Team identifier
  - `sf_user`: Org user context
- MCP Tools (7 required):
  - `cirra_ai_init`
  - `soql_query`
  - `tooling_api_query`
  - `metadata_create`
  - `metadata_update`
  - `metadata_read`
  - `sobject_describe`
- Optional tools (3):
  - `metadata_delete`
  - `tooling_api_dml`
  - `sobjects_list`

**Critical**: This tells Claude Code which MCP tools are available

---

### 4. **SKILL.md** (Main Documentation - Two Identical Copies)

#### Copy 1: Exploded Layout

**Location**: `/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/sf-apex/exploded/skills/sf-apex/SKILL.md`

#### Copy 2: Flat Layout

**Location**: `/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/sf-apex/skill/sf-apex/SKILL.md`

**Purpose**: Complete skill documentation and usage guide
**Length**: 607 lines of comprehensive reference material
**Format**: Markdown with frontmatter YAML

**Sections Included**:

1. **Frontmatter (Lines 1-39)**
   - Skill name, version 2.0.0
   - Description with "Cirra AI MCP Server" emphasis
   - Metadata (author, scoring system)
   - Hook definitions (SessionStart, PostToolUse, PreToolUse)

2. **Core Responsibilities (Lines 45-50)**
   - Code generation
   - Code review
   - Validation & scoring
   - Metadata deployment

3. **Key Changes from CLI (Lines 54-69)**
   - What was removed (deploy, retrieve, anonymous Apex)
   - What was added (cirra_ai_init, metadata tools)

4. **Workflow: 5-Phase Pattern (Lines 73-143)**
   - **Phase 1**: Requirements gathering + MCP initialization
   - **Phase 2**: Design & template selection
   - **Phase 3**: Code generation/review with guardrails
   - **Phase 4**: Metadata deployment (new MCP approach)
   - **Phase 5**: Documentation & testing guidance

5. **Generation Guardrails (Lines 122-145)**
   - 7 mandatory anti-patterns to prevent
   - SOQL in loops, DML in loops, hardcoded IDs, etc.
   - Instructions on when to stop and ask user

6. **Best Practices: 150-Point Scoring (Lines 179-193)**
   - Bulkification (25 pts)
   - Security (25 pts)
   - Testing (25 pts)
   - Architecture (20 pts)
   - Clean Code (20 pts)
   - Error Handling (15 pts)
   - Performance (10 pts)
   - Documentation (10 pts)
   - Scoring thresholds

7. **Trigger Actions Framework (TAF) (Lines 202-238)**
   - When to use TAF
   - TAF trigger pattern
   - TAF action class pattern
   - Deployment via metadata_create
   - Custom Metadata requirements
   - Fallback to standard triggers

8. **Async Decision Matrix (Lines 241-250)**
   - When to use @future, Queueable, Batch, Schedulable

9. **Modern Apex Features (Lines 255-265)**
   - API 65.0 features
   - Null coalescing, safe navigation, WITH USER_MODE

10. **Flow Integration (@InvocableMethod) (Lines 268-309)**
    - Quick pattern with example
    - Deployment via metadata_create
    - Reference templates

11. **Testing Best Practices (Lines 312-348)**
    - PNB pattern (Positive, Negative, Bulk)
    - Example test methods
    - Deployment of test classes

12. **Common Exception Types (Lines 357-383)**
    - DmlException, QueryException, etc.
    - When to use each type

13. **Cirra AI MCP Server Integration (Lines 386-464)**
    - Required initialization
    - MCP Tools mapping table (with CLI comparison)
    - Metadata API format for classes and triggers
    - Query examples (ApexClass, test results, triggers)
    - SOQL queries with binding

14. **Cross-MCP Tool Integration (Lines 467-480)**
    - Tool use cases and examples
    - sobject_describe, soql_query, metadata operations

15. **Field-Level Security & CRUD (Lines 483-505)**
    - Using sobject_describe for field discovery
    - CRUD/FLS checking patterns in code
    - Security.stripInaccessible() usage

16. **Limitations & Workarounds (Lines 508-520)**
    - Features not supported (anonymous Apex, local files)
    - Workarounds for each limitation

17. **Glossary of MCP Terms (Lines 523-531)**
    - MCP, Cirra AI, Metadata API, Tooling API definitions

18. **Dependencies (Lines 534-537)**
    - Optional Cirra AI tools for enhanced workflow

19. **Notes & License (Lines 540-554)**
    - API version, TAF, scoring, MCP requirements
    - License and attribution
    - Refactoring attribution

**Both SKILL.md files are IDENTICAL** - use whichever layout matches your installation:

- **Exploded**: If skill installed as separate directory structure
- **Flat**: If skill installed in consolidated location

---

## Usage Guide by File

### For Quick Understanding

1. Start: `README.md` (5 min read)
2. Deep dive: `REFACTORING_SUMMARY.md` (10 min read)

### For Deployment Operations

1. Reference: `SKILL.md` → "Phase 4: Metadata Deployment" (lines 363-408)
2. Tool examples: `SKILL.md` → "MCP Tools Mapping" table (lines 415-432)

### For Code Generation

1. Guardrails: `SKILL.md` → "Generation Guardrails" (lines 122-145)
2. Patterns: `SKILL.md` → "TAF", "Testing", "Flow Integration" sections

### For Testing

1. Workflow: `README.md` → "Testing the Refactored Skill"
2. Detailed: `REFACTORING_SUMMARY.md` → "Testing the Refactored Skill"

### For Troubleshooting

1. Limitations: `SKILL.md` → "Limitations & Workarounds" (lines 508-520)
2. MCP setup: `plugin.json` → Required tools declaration

---

## Installation Instructions

### Choose Layout (Both Work Identically)

**Option A: Exploded Layout**

```
Copy entire directory:
/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/sf-apex/exploded/
to: ~/.claude/plugins/cirra-ai-sf-apex/

Structure becomes:
~/.claude/plugins/cirra-ai-sf-apex/
├── .claude-plugin/
│   └── plugin.json
└── skills/sf-apex/
    └── SKILL.md
```

**Option B: Flat Layout**

```
Copy entire directory:
/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/sf-apex/skill/
to: ~/.claude/plugins/

Structure becomes:
~/.claude/plugins/sf-apex/
└── sf-apex/
    └── SKILL.md
```

### Prerequisites

- Cirra AI MCP Server access (configured)
- Claude Code with skill support
- Salesforce org with Apex API 65.0+

### Activation

Once installed, invoke with:

```
User: @cirra-ai-sf-apex Generate a service class for Account
```

---

## MCP Tool Requirements

### Must Have (7 Required)

1. **cirra_ai_init** - Initialize connection
2. **metadata_create** - Deploy new code
3. **metadata_update** - Update existing code
4. **metadata_read** - Retrieve code
5. **tooling_api_query** - Query metadata
6. **soql_query** - Query data
7. **sobject_describe** - Get schema

### Should Have (3 Optional)

1. **metadata_delete** - Delete code
2. **tooling_api_dml** - Metadata DML
3. **sobjects_list** - List objects

---

## Version History

### v2.0.0 (Current - MCP-Based)

- **Released**: 2025-02-06
- **Base**: Original sf-apex v1.1.0
- **Changes**: Replaced CLI with Cirra AI MCP Server
- **Status**: Production-ready
- **Location**: `/sessions/lucid-loving-albattani/mnt/outputs/sf-skills-cirra-ai/`

### v1.1.0 (Original - CLI-Based)

- **Location**: `/sessions/lucid-loving-albattani/mnt/.local-plugins/marketplaces/sf-skills/sf-apex/`
- **Status**: Still available, can coexist with v2.0.0
- **Note**: Uses `sf project deploy`, `sf project retrieve`, etc.

---

## Key Differences Summary

| Aspect           | v1.1.0 (CLI)                      | v2.0.0 (MCP)          |
| ---------------- | --------------------------------- | --------------------- |
| Deployment       | `sf project deploy`               | `metadata_create()`   |
| Retrieval        | `sf project retrieve`             | `metadata_read()`     |
| Schema discovery | `sf sobject describe`             | `sobject_describe()`  |
| Metadata query   | `sf data query --use-tooling-api` | `tooling_api_query()` |
| File system      | Uses force-app/                   | No file I/O           |
| Anonymous Apex   | `sf apex run`                     | Not supported         |
| Initialization   | CLI auth                          | `cirra_ai_init()`     |
| Code generation  | Identical                         | Identical             |
| Scoring          | Identical                         | Identical             |
| Best practices   | Identical                         | Identical             |

---

## Document Cross-References

### README.md references:

- REFACTORING_SUMMARY.md (for detailed changes)
- SKILL.md sections (for specific operations)
- plugin.json (MCP tools)

### REFACTORING_SUMMARY.md references:

- Original SKILL.md (CLI version)
- MCP tool examples (in this document)
- Testing scenarios

### SKILL.md references:

- Best practices documentation (inline)
- Resource guides (references only, not included)
- Cross-skill integration (optional)

### plugin.json references:

- MCP tool registry
- Cirra AI team configuration

---

## Support and Questions

### For Quick Help

- README.md: Overview and common questions
- MCP tool examples in SKILL.md sections

### For Technical Details

- REFACTORING_SUMMARY.md: Transformation details
- SKILL.md: Complete reference

### For Specific Operations

- Deployment: SKILL.md Phase 4
- Code retrieval: SKILL.md MCP Tools Mapping
- Testing: README.md or REFACTORING_SUMMARY.md

---

## License

Apache-2.0 License
Copyright (c) 2024-2025 Jag Valaiyapathy

**Refactored for Cirra AI MCP Server by Claude Agent (2025)**

---

## Final Checklist

When using this refactored skill, verify:

- [ ] Cirra AI MCP Server is configured
- [ ] All 7 required tools are available
- [ ] SKILL.md is readable (choice of exploded or flat layout)
- [ ] plugin.json is in .claude-plugin/ directory
- [ ] User can invoke with @cirra-ai-sf-apex
- [ ] cirra_ai_init() is called first in workflow
- [ ] Code is generated as strings (not files)
- [ ] Deployment uses metadata_create()
- [ ] Verification uses metadata_read()

---

**Last Updated**: 2025-02-06
**Files Created**: 4 (1 README + 1 Summary + 1 plugin.json + 2 SKILL.md copies)
**Total Lines**: ~1000+ of documentation
**Status**: Complete and ready for use
