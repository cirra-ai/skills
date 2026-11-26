# cirra-ai-sf

Salesforce admin plugin for Claude, for use with the [Cirra AI MCP Server](https://cirra.ai). It bundles 14 Salesforce skills (Apex, Flow, Data/SOQL, Metadata, Permissions, Diagrams, and others) and connects Claude to the Cirra AI MCP Server, which works in the Salesforce org you connect.

When installed, this plugin routes tasks to the appropriate skill based on context — e.g., Apex code reviews go to `sf-apex`, data operations go to `sf-data`, metadata queries go to `sf-metadata`.

Each skill also works independently without the orchestrator.

## What's included

- **14 skills**, listed below. They load in Claude Chat, Claude Cowork and Claude Code.
- **The Cirra AI MCP Server** at `https://mcp.cirra.ai/mcp`. You sign in with a Cirra AI account; if you have not connected a Salesforce org yet, you are asked to connect one.
- **A validation hook** (Claude Cowork and Claude Code only). Before Claude calls `metadata_create`, `metadata_update`, `tooling_api_dml`, `soql_query` or `sobject_dml`, a local Python script checks the request and adds findings for Claude to act on. It does not stop the call.

## Skills

| Skill                                               | Description                                                                                                                          |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| [sf-apex](skills/sf-apex/README.md)                 | Create, update and review Apex classes and triggers                                                                                  |
| [sf-flow](skills/sf-flow/README.md)                 | Create, update and review flows. Includes porting from Process Builders                                                              |
| [sf-data](skills/sf-data/README.md)                 | SOQL queries, DML and Bulk API 2.0 operations, test data patterns, and pre-flight SOQL validation                                    |
| [sf-lwc](skills/sf-lwc/README.md)                   | Lightning Web Components development                                                                                                 |
| [sf-audit](skills/sf-audit/README.md)               | Full org audit across Apex, Flows, and LWC with scored reports                                                                       |
| [sf-metadata](skills/sf-metadata/README.md)         | Metadata creation, org queries, permission set generation                                                                            |
| [sf-permissions](skills/sf-permissions/README.md)   | Permission Set analysis, hierarchy viewer, "Who has X?" auditing                                                                     |
| [sf-diagram](skills/sf-diagram/README.md)           | Salesforce architecture diagrams (ERDs, OAuth flows, integrations) in Mermaid                                                        |
| [sf-kugamon](skills/sf-kugamon/README.md)           | Kugamon CPQ quote management — create, verify, and manage opportunities, quotes, and orders with [Kugamon](https://www.kugamon.com/) |
| [sf-orders](skills/sf-orders/README.md)             | Order management — orders, returns, cases, and the order-to-return lifecycle                                                         |
| [sf-help-fetch](skills/sf-help-fetch/README.md)     | Read Salesforce documentation headlessly — Help articles, Knowledge Articles, developer.salesforce.com docs, and release info        |
| [sf-provisioning](skills/sf-provisioning/README.md) | User and access provisioning — create users, grant or revoke capabilities, mirror access, offboard logins                            |
| [sf-cms](skills/sf-cms/README.md)                   | Salesforce CMS content — author, publish, and verify what is live on a delivery channel                                              |
| [sf-connect-rest](skills/sf-connect-rest/README.md) | Connect REST API access for capabilities with no dedicated tool — named credentials, custom domains, site publishing                 |

## Sample Prompts

- "Perform a thorough audit of the Apex classes and Flows in my Salesforce org. Use Cirra AI and the cirra-ai-sf plugin. Use the default org for Cirra AI. Please generate Word, HTML and Excel versions of the report."
- "I need a new custom object called Inspection\_\_c with fields for Status, Inspector, and Date. Then create an Apex trigger that auto-assigns inspectors based on region, a Screen Flow for field technicians to submit inspection results, and seed 50 test records so I can demo it. Do this in the default org for Cirra AI."
- "Review all Apex triggers in my org for bulkification issues and governor limit risks. For each issue found, suggest a fix and score the code. Do this in the default org for Cirra AI."
- "Analyze all my profiles and permission sets and recommend security fixes and cleanup."
- "Create an ERD diagram for my Sales Cloud data model including Account, Contact, Opportunity, and Lead."
- "Build a SOQL query that shows me all opportunities closing this quarter with amount over $100K."

## What data it sends

- **To the Cirra AI MCP Server (`mcp.cirra.ai`).** Each tool call sends its arguments — for example a SOQL query, record values, or metadata — to Cirra AI, which runs it against the Salesforce org you connected and returns the result to Claude. Salesforce data passes through Cirra AI's infrastructure and may appear briefly in transient operational logs and short-lived response caches. See the [Cirra AI Privacy Policy](https://cirra.ai/legal/privacy-policy/).
- **To Salesforce documentation sites (`sf-help-fetch` only).** The skill sends the documentation URL, topic ID or Salesforce instance name you ask about to `help.salesforce.com`, `developer.salesforce.com`, `zd-ht-prod.zoominsoftware.io` and `api.status.salesforce.com`. It sends no data from your org.
- **To the npm registry (`sf-lwc` only, optional).** If Claude runs the optional Salesforce SLDS linter, `npx` downloads `@salesforce-ux/slds-linter` from the npm registry. Your component files are linted on your machine and are not uploaded.
- **Nowhere else.** The validation hook runs on your machine and makes no network calls. Reports and files that skills such as `sf-audit` create are saved in your own workspace.

## Model choice

For reports, analysis and simple metadata tasks the Sonnet model is a good and cost effective choice. For deeper thinking about how to best build new features or debug existing issues, the Opus model may be needed.

## Installation

For installation instructions and the full plugin catalog, see the [root README](../README.md).

## Requirements

- Claude Chat, Claude Cowork, or Claude Code
- A Cirra AI account — start with a [free trial](https://cirra.ai/free-trial/)
- A Salesforce org

## Support

- Documentation: [docs.cirra.ai](https://docs.cirra.ai)
- Contact: [support@cirra.ai](mailto:support@cirra.ai)
- [Privacy Policy](https://cirra.ai/legal/privacy-policy/) · [Terms of Service](https://cirra.ai/legal/tos/)

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
