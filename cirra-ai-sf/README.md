# cirra-ai-sf

Salesforce orchestrator plugin for Claude Cowork. Coordinates the individual Salesforce skills (Apex, Flow, Data, Metadata, Permissions, SOQL, Diagrams, and others) into a unified admin suite.

When installed, this plugin routes tasks to the appropriate skill based on context — e.g., Apex code reviews go to `cirra-ai-sf-apex`, data operations go to `cirra-ai-sf-data`, metadata queries go to `cirra-ai-sf-metadata`.

Each skill also works independently without the orchestrator.

## Skills

| Skill | Description |
| ----- | ----------- |
| [cirra-ai-sf-apex](skills/cirra-ai-sf-apex/README.md) | Create, update and review Apex classes and triggers |
| [cirra-ai-sf-flow](skills/cirra-ai-sf-flow/README.md) | Create, update and review flows |
| [cirra-ai-sf-data](skills/cirra-ai-sf-data/README.md) | SOQL queries, DML operations, test data factories |
| [cirra-ai-sf-lwc](skills/cirra-ai-sf-lwc/README.md) | Lightning Web Components development |
| [cirra-ai-sf-metadata](skills/cirra-ai-sf-metadata/README.md) | Metadata creation, org queries, permission set generation |
| [cirra-ai-sf-permissions](skills/cirra-ai-sf-permissions/README.md) | Permission Set analysis, "Who has X?" auditing |
| [cirra-ai-sf-soql](skills/cirra-ai-sf-soql/README.md) | Natural language to SOQL, query optimization |
| [cirra-ai-sf-diagram](skills/cirra-ai-sf-diagram/README.md) | Architecture diagrams (ERDs, OAuth, integrations) in Mermaid |

## Sample Prompts

- "Perform a thorough audit of the Apex classes and Flows in my Salesforce org. Use Cirra AI and the cirra-ai-sf plugin. Use the default org for Cirra AI. Please generate Word, HTML and Excel versions of the report."
- "I need a new custom object called Inspection\_\_c with fields for Status, Inspector, and Date. Then create an Apex trigger that auto-assigns inspectors based on region, a Screen Flow for field technicians to submit inspection results, and seed 50 test records so I can demo it. Do this in the default org for Cirra AI."
- "Review all Apex triggers in my org for bulkification issues and governor limit risks. For each issue found, suggest a fix and score the code. Do this in the default org for Cirra AI."
- "Analyze all my profiles and permission sets and recommend security fixes and cleanup."
- "Create an ERD diagram for my Sales Cloud data model including Account, Contact, Opportunity, and Lead."
- "Build a SOQL query that shows me all opportunities closing this quarter with amount over $100K."

## Model choice

For reports, analysis and simple metadata task the Sonnet model is a good and cost effective choice. For deeper thinking about how to best build new features or debug existing issues, the Opus model may be needed.

## Installation

For installation instructions and the full plugin catalog, see the [root README](../README.md).

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
