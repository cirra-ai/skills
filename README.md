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

These skills are designed for agentic AI tools like **Claude Cowork** and **OpenAI Codex**, but also make standard Claude and ChatGPT more capable. They are compatible with **Claude Code** and other developer tools.

To learn more about skills see [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills) and [agentskills.io](https://agentskills.io/home#adoption).

## Skills

All skills are bundled in the `cirra-ai-sf` plugin. They can also be installed individually as skill-only zip files.

The following skills are available or planned:

| Skill                                                                            | Description                                                                             |
| -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [cirra-ai-sf-apex](cirra-ai-sf/skills/cirra-ai-sf-apex/README.md)               | Create, update and review Apex classes and triggers                                     |
| [cirra-ai-sf-flow](cirra-ai-sf/skills/cirra-ai-sf-flow/README.md)               | Create, update and review flows. Includes porting from Process Builders                 |
| [cirra-ai-sf-data](cirra-ai-sf/skills/cirra-ai-sf-data/README.md)               | SOQL queries, DML operations, test data factories, and pre-flight SOQL validation       |
| [cirra-ai-sf-lwc](cirra-ai-sf/skills/cirra-ai-sf-lwc/README.md)                 | Lightning Web Components development                                                    |
| [cirra-ai-sf-metadata](cirra-ai-sf/skills/cirra-ai-sf-metadata/README.md)       | Metadata creation, org queries, permission set generation                               |
| [cirra-ai-sf-permissions](cirra-ai-sf/skills/cirra-ai-sf-permissions/README.md) | Permission Set analysis, hierarchy viewer, "Who has X?" auditing                        |
| [cirra-ai-sf-diagram](cirra-ai-sf/skills/cirra-ai-sf-diagram/README.md)         | Salesforce architecture diagrams (ERDs, OAuth flows, integrations) in Mermaid           |
| [cirra-ai-sf-kugamon](cirra-ai-sf-kugamon/)                                     | Easily create opportunities, orders and quotes with [Kugamon](https://www.kugamon.com/) |

The skills can either be installed individually, or as a bundle. See details for each AI platform below.

To learn more about skills see [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)

## Installation

First, sign up for a free trial of the [Cirra AI MCP Server](https://cirra.ai/free-trial/) if you have not already.

Downloads and a full install guide are available at **[cirra-ai.github.io/skills](https://cirra-ai.github.io/skills/)**.

### Claude Cowork or Claude Code (desktop)

1. Install [Claude Cowork](https://claude.com/product/cowork) if you haven't already.
2. Open the Claude Desktop app and select the **Cowork** tab.
3. Click **Plugins** in the left sidebar.
4. Click **Personal** and then the **+** icon.
5. Select **Add marketplace from GitHub**.
6. Enter `cirra-ai/skills` and click **Sync** — then install **cirra-ai-sf**.
7. You may need to restart the app to see the skills.

You can also upload the plugin zip directly, or install individual skills.

### OpenAI Codex

1. Install [OpenAI Codex](https://openai.com/codex/) if you haven't already.
2. In a new thread, say "Install the skills from the `cirra-ai/skills` GitHub repo".
3. This will use the built-in `skill-installer` skill to download and install the latest skills.
4. You may need to restart the app to see the skills.

### Claude web or desktop

1. Download the skill zip you want from [cirra-ai.github.io/skills](https://cirra-ai.github.io/skills/).
2. Go to [Settings → Capabilities](https://claude.ai/settings/capabilities).
3. Scroll down to **Skills** and click **+ Add**.
4. Upload the skill zip you downloaded.

### Claude Code (CLI)

Install from the marketplace:

```
/plugin marketplace add cirra-ai/skills
/plugin install cirra-ai-sf@cirra-ai
```

Or install from a downloaded zip:

```
/plugin install path/to/cirra-ai-sf.zip
```

See [discover-plugins](https://code.claude.com/docs/en/discover-plugins) for details.

### ChatGPT

ChatGPT does not support skills directly. We recommend using Codex instead.

However, if you only have access to ChatGPT you can still use the skills by downloading an individual skill zip and adding it to a chat that has the **Cirra AI** app enabled. Note that neither Agent mode nor Custom GPTs support custom MCP apps at this time.

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for how to file issues, open pull requests, and run tests locally.

## License

See [LICENSE](LICENSE)

The plugins in this repository are designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. This repository and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
