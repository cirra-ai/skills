# cirra-ai-sf-audit

Run a full Salesforce org audit across Apex, Flows, LWC, Permissions, and Metadata. Scores all components against quality rubrics, audits the permission model for security risks, evaluates the data model against best practices, and generates Word, Excel, and HTML reports.

## Features

- **Org-wide audit**: Collects and scores every Apex class, active Flow, and LWC component in the org
- **Permission audit**: Inventories Permission Sets and Groups, detects overly broad permissions, orphaned PS, and outdated PSGs
- **Data model audit**: Scores custom objects against a 120-point metadata rubric and flags cross-object issues
- **Scoring rubrics**: 150-point Apex, 110-point Flow, 165-point LWC, and 120-point Metadata rubrics (from the domain skills)
- **Report generation**: Word (.docx), Excel (.xlsx), and HTML reports with per-component scores and permission findings
- **Actionable summary**: Overall health score, components needing attention, permission findings by severity, top issues per domain

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

## Cross-Skill Integration

| Related Skill           | When to Use                                      |
| ----------------------- | ------------------------------------------------ |
| cirra-ai-sf-apex        | Fix or review Apex classes found in the audit    |
| cirra-ai-sf-flow        | Fix or review Flows found in the audit           |
| cirra-ai-sf-lwc         | Fix or review LWC components found in the audit  |
| cirra-ai-sf-permissions | Fix permission issues found in the audit         |
| cirra-ai-sf-metadata    | Fix data model issues found in the audit         |
| cirra-ai-sf-data        | Query or update data after fixing issues         |
| cirra-ai-sf-diagram     | Visualize architecture or permission hierarchies |

## Requirements

- Claude Cowork, Claude Code, OpenAI Codex, or another tool with skill support
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The skill and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
