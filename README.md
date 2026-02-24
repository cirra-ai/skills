# Cirra AI Salesforce Skills

[![Author](https://img.shields.io/badge/Author-Cirra_AI-blue?logo=github)](https://github.com/cirra-ai)
![CI](https://github.com/cirra-ai/skills/actions/workflows/ci.yml/badge.svg)
![Package](https://github.com/cirra-ai/skills/actions/workflows/package-plugins.yml/badge.svg)

## Overview

This repository contains Salesforce admin skills for use with the [Cirra AI MCP Server](https://cirra.ai).

These skills help your AI client:

1. Perform complex Salesforce admin tasks more reliably with detailed guidance, examples and validation scripts
2. Perform multi-step and long-running Salesforce admin tasks independently. Instead of entering prompts one at a time, describe an outcome, step away, and come back to finished work — formatted documents, organized files, and more.

Examples:

- 'Generate a comprehensive report of my org and highlight possible improvements'
- 'Audit my Apex, LWC and flows to ensure they meet best practices'
- 'Fix the top priority issues found in the report you just generated'
- 'Generate descriptions and help texts for all the custom fields'
- 'Analyze all my profiles and permission sets and recommend security fixes and cleanup'

The skills in this repository are designed for agentic AI tools like **Claude Cowork** and **OpenAI Codex**, but also make standard Claude and ChatGPT more capable. They are compatible with **Claude Code** and other developer tools.

To learn more about skills see [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills) and [agentskills.io](https://agentskills.io/home#adoption).

## Skills

All skills are bundled in the `cirra-ai-sf` plugin. They can also be installed individually as skill-only zip files.

The following skills are available or planned:

| Skill                                                               | Description                                                                             |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [cirra-ai-sf-apex](skills/cirra-ai-sf-apex/README.md)               | Create, update and review Apex classes and triggers                                     |
| [cirra-ai-sf-flow](skills/cirra-ai-sf-flow/README.md)               | Create, update and review flows. Includes porting from Process Builders                 |
| [cirra-ai-sf-data](skills/cirra-ai-sf-data/README.md)               | SOQL queries, DML operations, test data factories, and pre-flight SOQL validation       |
| [cirra-ai-sf-lwc](skills/cirra-ai-sf-lwc/README.md)                 | Lightning Web Components development                                                    |
| [cirra-ai-sf-audit](skills/cirra-ai-sf-audit/README.md)             | Full org audit across Apex, Flows, and LWC with scored reports                          |
| [cirra-ai-sf-metadata](skills/cirra-ai-sf-metadata/README.md)       | Metadata creation, org queries, permission set generation                               |
| [cirra-ai-sf-permissions](skills/cirra-ai-sf-permissions/README.md) | Permission Set analysis, hierarchy viewer, "Who has X?" auditing                        |
| [cirra-ai-sf-diagram](skills/cirra-ai-sf-diagram/README.md)         | Salesforce architecture diagrams (ERDs, OAuth flows, integrations) in Mermaid           |
| `cirra-ai-sf-kugamon` (coming soon)                         | Easily create opportunities, orders and quotes with [Kugamon](https://www.kugamon.com/) |

The skills can either be installed individually, or as a bundle. See details for each AI platform below.

To learn more about skills see [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)

## Installation

First, sign up for a free trial of the [Cirra AI MCP Server](https://cirra.ai/free-trial/) if you have not already.

Then, navigate to [cirra-ai.github.io/skills](https://skills.cirra.ai/) for a full install guide and downloadable packages.

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for how to file issues, open pull requests, and run tests locally.

## License

See [LICENSE](LICENSE)

The plugins in this repository are designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. This repository and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
