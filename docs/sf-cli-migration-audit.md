# SF CLI to Cirra AI MCP Server — Migration Audit

This document tracks the identification and remediation of Salesforce CLI (`sf CLI` / `sfdx`) references across the Cirra AI skills repository. The goal is to ensure all user-facing instructions reference Cirra AI MCP Server tools instead of the Salesforce CLI.

## Audit Methodology

### Step 1: plugin.json Description Alignment

Cross-referenced each `cirra-ai-*/.claude-plugin/plugin.json` description against the original in `sf-skills/` to ensure descriptions match the original's detail level with "using Cirra AI MCP Server" appended.

**Files updated:**
- `cirra-ai-sf-lwc/.claude-plugin/plugin.json` — Was extremely terse, restored SLDS 2 validation, 140-point scoring, dark mode, accessibility
- `cirra-ai-sf-flow/.claude-plugin/plugin.json` — Restored "Winter '26 best practices" and "Use when..." guidance
- `cirra-ai-sf-ai-agentforce-testing/.claude-plugin/plugin.json` — Restored multi-turn conversations, scoring, auto-fix details
- `cirra-ai-sf-data/.claude-plugin/plugin.json` — Restored "Use when" pattern
- `cirra-ai-sf-metadata/.claude-plugin/plugin.json` — Restored specific use cases
- `cirra-ai-sf-ai-agentscript/.claude-plugin/plugin.json` — Restored 100-point scoring, three-phase model

### Step 2: Full-Text Search for CLI References

Ran `grep` for patterns: `sf CLI`, `sfdx`, `Salesforce CLI`, `sf org`, `sf data`, `sf project`, `sf sobject`, `--target-org`, `sf apex`, `sf agent`.

Found **700+ matches** across the codebase, categorized below.

### Step 3: Triage by Category

| Category | Count | Action |
|---|---|---|
| marketplace.json | 3 | Fixed |
| README requirements/descriptions | 12 | Fixed |
| Hook scripts (user-facing messages) | 7 | Fixed where possible |
| SKILL.md mapping tables (old → new) | ~30 | Kept (intentional comparison) |
| docs/ CLI reference files | ~200 | Known — see Remaining Work |
| examples/ with CLI commands | ~150 | Known — see Remaining Work |
| templates/ with CLI comments | ~100 | Known — see Remaining Work |
| CREDITS.md / migration docs | ~20 | Kept (attribution/history) |
| Agentforce testing scripts | ~50 | Cannot replace — see Limitations |

## Changes Made

### marketplace.json

| Before | After |
|---|---|
| `"Salesforce DevOps automation using sf CLI v2"` | `"Salesforce DevOps automation using Cirra AI MCP Server"` |
| `"tags": ["salesforce", "deployment", "ci-cd", "sfdx"]` | `"tags": ["salesforce", "deployment", "ci-cd", "cirra-ai"]` |
| `"keywords": ["deploy", "sfdx", ...]` | `"keywords": ["deploy", "metadata-api", ...]` |

### README Files

All `cirra-ai-*/README.md` files updated:

| Change | Files |
|---|---|
| `sf CLI v2` → `Cirra AI MCP Server` in Requirements | apex, data, flow, lwc, agentforce-testing |
| `SF CLI v2+ with agent commands` → `Cirra AI MCP Server` | agentscript |
| `CRUD Operations via sf CLI` → `via Cirra AI MCP Server` | data |
| `Run agent tests via sf CLI` → `via Cirra AI MCP Server` | agentforce-testing |
| `CLI deployment` → `MCP deployment` | agentscript |
| `sf CLI Commands Wrapped` table → `Cirra AI MCP Tools` table | data |
| `sf agent validate/deploy` → metadata_create/metadata_read | agentscript |
| Added `Copyright (c) 2026 Cirra AI, Inc.` | All 6 READMEs |

### Hook Scripts — Fixed

| Script | Before | After |
|---|---|---|
| `cirra-ai-sf-soql/hooks/scripts/post-tool-validate.py:145` | `Run 'sf org login web' to enable live analysis` | `Use cirra_ai_init to connect to your org for live analysis` |
| `cirra-ai-sf-data/hooks/scripts/post-write-validate.py:191` | `No org connected - run: sf org login web` | `No org connected - use cirra_ai_init to connect` |
| `cirra-ai-sf-flow/hooks/scripts/validate_flow.py:1736` | `ALWAYS use sf-deploy skill for consistent deployment` | `ALWAYS use metadata_create via Cirra AI MCP Server for deployment` |
| `cirra-ai-sf-metadata/hooks/scripts/generate_permission_set.py:306` | `sf project deploy start --source-dir ...` | `Use metadata_create(type='PermissionSet', ...) via Cirra AI MCP Server` |
| `cirra-ai-sf-metadata/hooks/scripts/generate_permission_set.py:309` | `sf org assign permset --name ...` | `Use sobject_dml to insert PermissionSetAssignment` |

### Dead Code Removal — Salesforce Code Analyzer & Live Query Plan

The `code_analyzer` Python module (including `code_analyzer.scanner`, `code_analyzer.score_merger`, and `code_analyzer.live_query_plan`) was never ported from the original sf-skills repo. All imports always failed with `ImportError`, producing only "not available" output messages. This dead code has been **completely removed** from 5 hook scripts:

| Script | What was removed |
|---|---|
| `cirra-ai-sf-apex/hooks/scripts/post-tool-validate.py` | Code Analyzer scanning, Live Query Plan analysis, ScoreMerger score merging, CA output section, CA violations in issues list |
| `cirra-ai-sf-flow/hooks/scripts/post-tool-validate.py` | Code Analyzer scanning, CA deduction calculations, CA output section, CA violations in issues list |
| `cirra-ai-sf-lwc/hooks/scripts/post-tool-validate.py` | Code Analyzer scanning for .js files, CA output section |
| `cirra-ai-sf-soql/hooks/scripts/post-tool-validate.py` | Live Query Plan analysis phase, live plan output section |
| `cirra-ai-sf-data/hooks/scripts/post-write-validate.py` | `run_live_plan_analysis()` function, live plan output in report formatter |

Also updated:

- `cirra-ai-sf-apex/resources/bulkification-guide.md` — Replaced dead "See Also" link to `code_analyzer/live_query_plan.py` with `soql_query` via Cirra AI MCP Server

**Impact:** Function names were updated to reflect the removal (`validate_apex_with_ca` → `validate_apex`, `validate_flow_with_ca` → `validate_flow`). All validation hook scripts now only run their custom scoring and any available local linters (e.g., SLDS Linter for LWC, LLM Pattern Validator for Apex).

## Known Limitations — Cannot Replace with MCP

### 2. Agentforce Testing CLI Scripts — Removed

Two scripts that shelled out to `sf agent test` CLI commands have been **deleted** since Claude Cowork cannot run SF CLI:

- `run-automated-tests.py` — Orchestrated `sf agent test list/create/run` via subprocess
- `test-fix-loop.sh` — Ran `sf agent test run` in a bash loop

**Replaced by:** The SKILL.md already documents equivalent operations via Cirra AI Tooling API (`tooling_api_query(AiEvaluationDefinition)`, `tooling_api_dml(create, AiEvaluationRun)`, etc.), and the multi-turn test runner (`multi_turn_test_runner.py`) provides API-based testing without any CLI dependency.

**Kept (CLI-independent):**

- `multi_turn_test_runner.py` — Direct Agent Runtime API calls (no CLI needed)
- `agent_api_client.py` — Pure Python HTTP client for Agent Runtime API
- `generate-test-spec.py` — Parses .agent files, generates YAML (no CLI invocation)
- `parse-agent-test-results.py` — Parses test output (no CLI invocation)

**Still not available via MCP:** `sf agent preview` (interactive UI-only feature) and `sf agent generate test-spec` (interactive CLI-only).

### 3. `@salesforce/sfdx-lwc-jest` npm Package

**Files:** `cirra-ai-sf-lwc/resources/jest-testing.md`, `cirra-ai-sf-lwc/docs/cli-commands.md`

This is an **npm package name** used for LWC unit testing, not a CLI command. It runs locally and is unrelated to org connectivity. No change needed.

## Remaining Work — Doc/Example/Template Files

The following doc, example, and template files still contain sf CLI command examples. These are inherited from the original sf-skills repo and serve as reference material. They are **not user-facing instructions** (users interact with SKILL.md, not these support files), but should be updated in a future pass for consistency:

### Full CLI Reference Docs (consider removing or rewriting)

- `cirra-ai-sf-soql/docs/cli-commands.md`
- `cirra-ai-sf-data/docs/sf-cli-data-commands.md`
- `cirra-ai-sf-lwc/docs/cli-commands.md`
- `cirra-ai-sf-metadata/docs/sf-cli-commands.md`
- `cirra-ai-sf-ai-agentforce-testing/docs/cli-commands.md`
- `cirra-ai-sf-ai-agentscript/docs/cli-guide.md`

### Example Files with CLI Commands

- `cirra-ai-sf-data/examples/` — crud-workflow, bulk-testing, cleanup-rollback, relationship-queries
- `cirra-ai-sf-flow/examples/` — error-logging, record-trigger
- `cirra-ai-sf-metadata/examples/` — custom-object, permission-set

### Template Files with CLI Comments

- `cirra-ai-sf-data/templates/` — bulk inserts, cleanup scripts, SOQL templates
- `cirra-ai-sf-soql/templates/` — optimization patterns

### Supporting Docs with CLI Examples

- `cirra-ai-sf-data/docs/` — bulk-operations-guide, cleanup-rollback-guide, anonymous-apex-guide, orchestration
- `cirra-ai-sf-flow/docs/` — testing-guide, subflow-library, transform-vs-loop-guide, flow-best-practices
- `cirra-ai-sf-metadata/docs/` — metadata-types-reference, orchestration
- `cirra-ai-sf-apex/resources/` — troubleshooting, testing-patterns, patterns-deep-dive
- `cirra-ai-sf-lwc/resources/` — lms-guide
- `cirra-ai-sf-ai-agentscript/` — VALIDATION.md, validation/README.md, resources/debugging-guide

### Intentionally Kept (No Action Needed)

- **SKILL.md mapping tables** — Show "SF CLI Command → Cirra AI Tool" comparisons (educational)
- **CREDITS.md files** — Attribution to sf CLI team and docs
- **REFACTORING_SUMMARY.md, INDEX.md, README2.md** — Document the migration itself
- **plugin.json changelog entries** — Historical record of migration
