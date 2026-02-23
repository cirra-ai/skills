# cirra-ai-sf-audit

Run a full Salesforce org audit across Apex, Flows, and LWC. Scores all components against quality rubrics and generates Word, Excel, and HTML reports.

## Features

- **Org-wide audit**: Collects and scores every Apex class, active Flow, and LWC component in the org
- **Scoring rubrics**: 150-point Apex, 110-point Flow, and 165-point LWC rubrics (from the domain skills)
- **Report generation**: Word (.docx), Excel (.xlsx), and HTML reports with per-component scores
- **Actionable summary**: Overall health score, components needing attention, top issues per domain

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

| Related Skill    | When to Use                                   |
| ---------------- | --------------------------------------------- |
| cirra-ai-sf-apex | Fix or review Apex classes found in the audit  |
| cirra-ai-sf-flow | Fix or review Flows found in the audit         |
| cirra-ai-sf-lwc  | Fix or review LWC components found in the audit |
| cirra-ai-sf-data | Query or update data after fixing issues       |

## Requirements

- Claude Cowork, Claude Code, OpenAI Codex, or another tool with skill support
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The skill and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
