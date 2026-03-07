# cirra-ai-sf-audit

Run a comprehensive Salesforce org audit that inventories and evaluates all major metadata categories: Apex classes, Apex triggers, Flows, Process Builders, Workflow Rules, LWC components, custom objects and fields, validation rules, Profiles, and Permission Sets. Generates Word, Excel, and HTML reports.

## Features

- **Complete org inventory**: Counts and catalogs every component across all metadata categories
- **Code quality scoring**: 150-point Apex, 110-point Flow, 165-point LWC, and 120-point Metadata rubrics (from domain skills)
- **Trigger review**: Inventories Apex triggers and flags anti-patterns (logic in trigger body, missing bulkification)
- **Permission audit**: Inventories Profiles, Permission Sets, and PSGs; detects overly broad permissions, orphaned PS, and outdated PSGs
- **Data model audit**: Scores custom objects against the metadata rubric and flags cross-object issues
- **Validation rule review**: Inventories rules and flags missing descriptions, hardcoded IDs, and missing bypass mechanisms
- **Legacy automation inventory**: Catalogs active Workflow Rules and Process Builders with migration priorities
- **Automation overlap detection**: Identifies objects with multiple automation types active (triggers, flows, PBs, workflow rules)
- **Report generation**: Word (.docx), Excel (.xlsx), and HTML reports with per-component scores and findings
- **Actionable summary**: Overall health score, components needing attention, findings by severity, migration priorities
- **Incremental audits**: Re-score only components that changed since the last audit, carrying forward unchanged scores
- **Three execution modes**: Works with local SFDX repos (fastest), Salesforce CLI, or MCP-only (cloud environments)

## Installation

For full installation instructions (Claude Cowork, OpenAI Codex, browser), see the [root README](../../README.md).

## Quick Start

### In Claude Cowork or Claude Code

Use the pre-built command:

```
/audit-org
```

### In OpenAI Codex or other tools

```
Skill: cirra-ai-sf-audit
Request: "Audit my Salesforce org"
```

### Incremental Audit

To update a previous audit (only re-scores changed components):

```
Audit my Salesforce org. Previous audit is at ~/audits/2026-01/audit_output/
```

## Execution Modes

| Mode        | When                                  | Speed   |
| ----------- | ------------------------------------- | ------- |
| `sfdx-repo` | Working directory is an SFDX project  | Fastest |
| `cli`       | Salesforce CLI installed and authed   | Fast    |
| `cloud`     | MCP-only (Cowork, cloud environments) | Slowest |

The skill auto-detects the best available mode. In `sfdx-repo` mode, metadata
is read directly from disk with no API calls for body retrieval. In `cli` mode,
bulk retrieval uses the Salesforce CLI. In `cloud` mode, everything goes through
MCP with cursor pagination.

## Cross-Skill Integration

| Related Skill           | When to Use                                         |
| ----------------------- | --------------------------------------------------- |
| cirra-ai-sf-apex        | Fix or review Apex classes/triggers in the audit    |
| cirra-ai-sf-flow        | Fix or review Flows found in the audit              |
| cirra-ai-sf-lwc         | Fix or review LWC components found in the audit     |
| cirra-ai-sf-permissions | Fix permission or Profile issues found in the audit |
| cirra-ai-sf-metadata    | Fix data model issues found in the audit            |
| cirra-ai-sf-data        | Query or update data after fixing issues            |
| cirra-ai-sf-diagram     | Visualize architecture or permission hierarchies    |

## Requirements

- Claude Cowork, Claude Code, OpenAI Codex, or another tool with skill support
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The skill and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
