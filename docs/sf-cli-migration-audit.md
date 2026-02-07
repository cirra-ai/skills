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
| Hook scripts (user-facing messages) | 7 | Fixed |
| SKILL.md mapping tables (old → new) | ~30 | Kept (intentional comparison) |
| docs/ CLI reference files | 6 | Deleted |
| docs/ supporting docs with CLI examples | ~200 | Fixed — replaced with MCP equivalents |
| examples/ with CLI commands | ~150 | Fixed — replaced with MCP equivalents |
| templates/ with CLI comments | ~100 | Fixed — replaced with MCP equivalents |
| CREDITS.md / migration docs | ~20 | Kept (attribution/history) |
| Agentforce testing scripts | 2 | Deleted (CLI-dependent) |

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

### CLI Reference Docs — Deleted

6 standalone CLI reference docs were deleted outright (their content was SF CLI command catalogs with no MCP equivalent structure):

- `cirra-ai-sf-soql/docs/cli-commands.md`
- `cirra-ai-sf-data/docs/sf-cli-data-commands.md`
- `cirra-ai-sf-lwc/docs/cli-commands.md`
- `cirra-ai-sf-metadata/docs/sf-cli-commands.md`
- `cirra-ai-sf-ai-agentforce-testing/docs/cli-commands.md`
- `cirra-ai-sf-ai-agentscript/docs/cli-guide.md`

### Example Files — Updated with MCP Equivalents

All CLI commands in example files replaced with Cirra AI MCP Server tool calls:

| File | Changes |
|---|---|
| `cirra-ai-sf-data/examples/relationship-query-examples.md` | 4 `sf data query` → `soql_query()` |
| `cirra-ai-sf-data/examples/crud-workflow-example.md` | 9 replacements (create/update/delete/query) |
| `cirra-ai-sf-data/examples/bulk-testing-example.md` | 6 replacements (import/tree/query) |
| `cirra-ai-sf-data/examples/cleanup-rollback-example.md` | 5 CLI commands replaced, section headers updated |
| `cirra-ai-sf-flow/examples/record-trigger-example.md` | 2 `sf data query` → `soql_query()` |
| `cirra-ai-sf-flow/examples/error-logging-example.md` | 2 replacements (deploy + query) |
| `cirra-ai-sf-metadata/examples/custom-object-example.md` | 2 `sf project deploy` → `metadata_create()` |
| `cirra-ai-sf-metadata/examples/permission-set-example.md` | 2 blocks replaced (deploy + assignment) |

### Template Files — Updated with MCP Equivalents

All CLI references in template comments replaced:

| File | Changes |
|---|---|
| `cirra-ai-sf-data/templates/cleanup/delete-by-created-date.apex` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/cleanup/delete-by-name.apex` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/bulk/bulk-insert-10000.apex` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/bulk/bulk-insert-500.apex` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/bulk/bulk-upsert-external-id.apex` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/soql/aggregate.soql` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/soql/child-to-parent.soql` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/soql/parent-to-child.soql` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/soql/polymorphic.soql` | CLI comments → MCP equivalents |
| `cirra-ai-sf-data/templates/soql/subquery.soql` | CLI comments → MCP equivalents |
| `cirra-ai-sf-soql/templates/optimization-patterns.soql` | CLI comments → MCP equivalents |

### Supporting Docs — Updated with MCP Equivalents

All CLI commands in supporting documentation replaced with Cirra AI MCP Server tool calls:

**sf-data docs:**

| File | Changes |
|---|---|
| `docs/anonymous-apex-guide.md` | Section header + CLI commands → MCP |
| `docs/bulk-operations-guide.md` | Decision matrix + 5 bash blocks → MCP |
| `docs/cleanup-rollback-guide.md` | Section header + bash block → MCP |
| `docs/orchestration.md` | 3 sections (apex, prerequisites, cleanup) → MCP |

**sf-flow docs:**

| File | Changes |
|---|---|
| `docs/flow-best-practices.md` | Table cell + prose → MCP |
| `docs/orchestration.md` | ASCII diagram + table cell → MCP |
| `docs/subflow-library.md` | 3 commands → MCP |
| `docs/testing-guide.md` | 7+ replacements including Quick Reference → MCP |
| `docs/transform-vs-loop-guide.md` | Section header + 2 commands → MCP |

**sf-metadata docs:**

| File | Changes |
|---|---|
| `docs/metadata-types-reference.md` | Section header + 6 commands → MCP |
| `docs/orchestration.md` | Best practices item + diagram → MCP |

**sf-apex resources:**

| File | Changes |
|---|---|
| `resources/anti-patterns.md` | Scanner run → MCP |
| `resources/patterns-deep-dive.md` | 2 commands → MCP |
| `resources/testing-patterns.md` | Test command → MCP |
| `resources/troubleshooting.md` | 15+ replacements → MCP |

**sf-lwc resources:**

| File | Changes |
|---|---|
| `resources/lms-guide.md` | 2 `sf project deploy` → `metadata_create()` |

**sf-soql docs:**

| File | Changes |
|---|---|
| `docs/soql-reference.md` | 5 `sf data query` commands → `soql_query()`, section renamed |
| `docs/anti-patterns.md` | `sf data query` → Tooling API |

**sf-ai-agentscript:**

| File | Changes |
|---|---|
| `VALIDATION.md` | Deploy + publish commands → MCP |
| `validation/README.md` | Quick start + tiers table → MCP |
| `resources/debugging-guide.md` | Diagnostic checklist → MCP |
| `resources/testing-guide.md` | `sf agent test run/validate` + CI/CD workflow → MCP |

**sf-ai-agentforce-testing docs:**

| File | Changes |
|---|---|
| `docs/connected-app-setup.md` | **Deleted** — dead doc (users don't set up Connected Apps) |
| `docs/eca-setup-guide.md` | **Deleted** — dead doc (users don't set up ECAs) |
| `docs/agent-api-reference.md` | `sf data query --use-tooling-api` + auth table → MCP; ECA refs removed |
| `docs/agentic-fix-loop.md` | `sf agent test run/results/validate/publish` → MCP |
| `docs/coverage-analysis.md` | `sf agent test run/results/create` + CI/CD → MCP |
| `docs/test-spec-guide.md` | `sf agent test create` → MCP |

**sf-ai-agentforce-testing resources:**

| File | Changes |
|---|---|
| `resources/test-spec-reference.md` | 6 sections rewritten → MCP |
| `resources/agentic-fix-loops.md` | ASCII diagram + 6 command replacements → MCP |

**sf-ai-agentforce-testing templates (YAML):**

| File | Changes |
|---|---|
| `templates/basic-test-spec.yaml` | Comment line → MCP |
| `templates/standard-test-spec.yaml` | 3 comment lines → MCP |
| `templates/comprehensive-test-spec.yaml` | Comment line → MCP |
| `templates/escalation-tests.yaml` | Comment line → MCP |
| `templates/guardrail-tests.yaml` | Comment line → MCP |

## Known Limitations — Cannot Replace with MCP

### 1. Agentforce Testing CLI Scripts — Removed

Two scripts that shelled out to `sf agent test` CLI commands have been **deleted** since Claude Cowork cannot run SF CLI:

- `run-automated-tests.py` — Orchestrated `sf agent test list/create/run` via subprocess
- `test-fix-loop.sh` — Ran `sf agent test run` in a bash loop

**Replaced by:** The SKILL.md documents equivalent operations via Cirra AI Tooling API (`tooling_api_query(AiEvaluationDefinition)`, `tooling_api_dml(create, AiEvaluationRun)`, etc.).

**Also deleted (make direct HTTP calls to Agent Runtime API — cannot work in Cowork's sandbox):**

- `multi_turn_test_runner.py` — Multi-turn test orchestrator using urllib to call Agent Runtime API directly
- `agent_api_client.py` — Pure Python HTTP client for Agent Runtime API sessions/messages

**Also deleted (OAuth setup docs — users don't set up OAuth apps; Cirra AI handles auth automatically):**

- `docs/eca-setup-guide.md` — External Client App setup instructions (dead doc)
- `docs/connected-app-setup.md` — Connected App setup instructions (dead doc)

**Also deleted (validation tests for removed scripts):**

- `validation/scenarios/tier1_api_client/` — Tests for deleted agent_api_client.py
- `validation/scenarios/tier2_test_runner/` — Tests for deleted multi_turn_test_runner.py
- `validation/scenarios/tier4_negative/` — Tests importing from deleted scripts
- `validation/scenarios/tier5_live_api/` — Live API tests importing from deleted scripts

**Kept (CLI-independent):**

- `generate-test-spec.py` — Parses .agent files, generates YAML (no CLI or HTTP invocation)
- `parse-agent-test-results.py` — Parses test output (no CLI or HTTP invocation)

**Still not available via MCP:** `sf agent preview` (interactive UI-only feature) and `sf agent generate test-spec` (interactive CLI-only). Agent Runtime API proxy is a desired enhancement (see JIRA PLTFRM ticket).

### 2. `@salesforce/sfdx-lwc-jest` npm Package

**Files:** `cirra-ai-sf-lwc/resources/jest-testing.md`

This is an **npm package name** used for LWC unit testing, not a CLI command. It runs locally and is unrelated to org connectivity. No change needed.

### 3. `sf agent validate` — No MCP Equivalent

Agent validation is performed locally by the IDE/LSP. References in docs annotated with explanatory notes rather than replaced.

### 4. `sf agent preview` — UI-Only Feature

Interactive agent preview is a browser-based UI feature with no API/MCP equivalent. References in docs annotated as "UI-only, not available via MCP."

## CLI → MCP Mapping Reference

The following mapping was applied consistently across all files:

| SF CLI Command | Cirra AI MCP Tool |
|---|---|
| `sf org login web` / `sf org display` | `cirra_ai_init()` |
| `sf data query --query "..."` | `soql_query(query="...")` |
| `sf data query --use-tooling-api` | `tooling_api_query(sobjectType="...", whereClause="...")` |
| `sf data create record` | `sobject_dml(operation="insert", sobjectType="...", records=[...])` |
| `sf data update record` | `sobject_dml(operation="update", sobjectType="...", records=[...])` |
| `sf data delete record` | `sobject_dml(operation="delete", sobjectType="...", records=[...])` |
| `sf data import/upsert/delete bulk` | `sobject_dml(operation="...", sobjectType="...", records=[...])` |
| `sf project deploy start` | `metadata_create(type="...", fullName="...", metadata={...})` |
| `sf project retrieve start` | `metadata_read(type="...", fullName="...")` |
| `sf sobject describe` | `sobject_describe(sobjectType="...")` |
| `sf sobject list` | `sobjects_list()` |
| `sf org assign permset` | `sobject_dml(operation="insert", sobjectType="PermissionSetAssignment", ...)` |
| `sf agent test create` | `tooling_api_dml(operation="create", sobjectType="AiEvaluationDefinition", ...)` |
| `sf agent test run` | `tooling_api_dml(operation="create", sobjectType="AiEvaluationRun", ...)` |
| `sf agent test results` | `tooling_api_query(sobjectType="AiEvaluationResult", ...)` |
| `sf agent test list` | `tooling_api_query(sobjectType="AiEvaluationDefinition", ...)` |
| `sf agent publish` | `metadata_create(type="GenAiPlannerBundle", ...)` |
| `sf agent activate` | `metadata_update(type="GenAiPlannerBundle", ...)` |
| `--target-org <alias>` | `orgAlias="..."` parameter |

## Intentionally Preserved References

The following files intentionally retain SF CLI references and should NOT be modified:

- **SKILL.md mapping tables** — Show "SF CLI Command → Cirra AI Tool" comparisons (educational)
- **CREDITS.md files** — Attribution to sf CLI team and docs
- **REFACTORING_SUMMARY.md, INDEX.md, README2.md** — Document the migration itself
- **plugin.json changelog entries** — Historical record of migration
- **`@salesforce/sfdx-lwc-jest`** — npm package name, runs locally via Node.js

## Migration Status: COMPLETE

All actionable SF CLI references have been remediated. The migration covered:
- **6 plugin.json** descriptions aligned
- **1 marketplace.json** updated
- **6 README.md** files updated
- **5 hook scripts** fixed (CLI messages → MCP)
- **5 hook scripts** cleaned (dead code removal)
- **4 CLI/HTTP-dependent scripts** deleted (2 CLI + 2 Agent Runtime API)
- **8 CLI reference/OAuth docs** deleted (6 CLI + 2 OAuth setup)
- **4 validation test tiers** deleted (tests for removed scripts)
- **8 example files** updated with MCP equivalents
- **11 template files** updated with MCP equivalents
- **~40 supporting docs/resources** updated with MCP equivalents
- **5 YAML templates** updated with MCP equivalents
