# Cirra AI Salesforce Skills

[![Author](https://img.shields.io/badge/Author-Cirra_AI-blue?logo=github)](https://github.com/cirra-ai)
![CI](https://github.com/cirra-ai/skills/actions/workflows/ci.yml/badge.svg)
![Package](https://github.com/cirra-ai/skills/actions/workflows/package-plugins.yml/badge.svg)

## Overview

This repository contains a collection of Salesforce admin *skills* for use with the [Cirra AI MCP Server](https://cirra.ai).

Skills are collections of pre-builts instructions, scripts, and resources. They can be installed into
your AI client to help it perform complex, time-consuming Salesforce admin tasks from simple prompts.

You don't need to be a developer to use these skills, and you don't need an IDE, CLI or sfdx project.

All you need is:

* A paid subscription to a compatible AI client. Currently the best options are:
  * [Claude Desktop](https://support.claude.com/en/articles/10065433-installing-claude-desktop) 
    (either in Chat, Cowork or Code mode)
  * [Claude Web](https://claude.ai/)
  * [OpenAI Codex](https://openai.com/codex/)
  * A growing collection of [AI development tools](https://agentskills.io/home#adoption)

* The [Cirra AI MCP Server](https://cirra.ai/products/salesforce-admin-mcp/)

The following skills are available or planned:

| Skill                                 | Description                                                                 |
| ------------------------------------- | --------------------------------------------------------------------------- |
| [cirra-ai-sf-apex](cirra-ai-sf-apex/) | Apex code generation, review, and 150-point scoring                         |
| [cirra-ai-sf-flow](cirra-ai-sf-flow/) | Flow creation, validation, and 110-point scoring                            |
| [cirra-ai-sf-data](cirra-ai-sf-data/) | SOQL queries, DML operations, test data factories, and 130-point validation |
| [cirra-ai-sf-lwc](cirra-ai-sf-lwc/)   | Lightning Web Components development skill                                  |
| sf-soql | Natural language → SOQL, query optimization |
| sf-metadata | Metadata gen & org queries |
| sf-data | SOQL & test data factories |
| sf-permissions | Permission Set analysis, "Who has X?" |
| [cirra-ai-sf-kugamon](cirra-ai-sf-kugamon/)   | Easily create opportunites, orders and quotes with [Kugamon](https://www.kugamon.com/)                                  |

The skills can either be installed individually, or as a bundle. See details for each AI platform below.

https://support.claude.com/en/articles/12512176-what-are-skills

## Installation

### Claude Cowork (desktop)

[Claude Cowork](https://support.claude.com/en/articles/13345190-getting-started-with-cowork) brings agentic capabilities to Claude Desktop for knowledge work beyond coding.

To install the plugin that wraps all the Cirra AI skills:

1. Make sure you have the Claude Desktop with [Claude Cowork](https://claude.com/product/cowork) installed.
2. Follow the instructions [here](https://support.claude.com/en/articles/13345190-getting-started-with-cowork#h_0f9e0998dd)

    * Click **Personal** and then the **+** icon
    * From the dropdown, select **Add marketplace from GitHub**
    * Enter `cirra-ai/skills` and click **Sync**

3. The end result should look something like this:

    <img src="docs/images/plugins-chooser.png" alt="Select a plugin" width="100%">

If you prefer to install skills individually you can also 
For more details on **Claude Cowork**, see [Getting started with Cowork](https://support.claude.com/en/articles/13345190-getting-started-with-cowork)

### Claude Code (desktop)

Claude Code on the desktop has a Local mode that is very similar to is very similar to is an agentic coding tool that is available in your terminal, IDE, desktop app, and browser.

1. Make sure you have the Claude Desktop with [Claude Cowork](https://claude.com/product/cowork) installed.

- [Claude Code](https://code.claude.com/docs)
- [Discover plugins](https://code.claude.com/docs/en/discover-plugins)

### Claude web (desktop or browser)

https://support.claude.com/en/articles/12512180-using-skills-in-claude

Skills are designed to be portable across AI clients -- see the [specification](https://agentskills.io/what-are-skills).

The repository
Each plugin combines skills, connectors, slash commands, and sub-agents into a single package.

<https://support.claude.com/en/articles/13345190-getting-started-with-cowork#h_0f9e0998dd>

Skills are smaller

The plugins are specifically designed for non-developers to use with various variations of Claude:

- [Claude Cowork](https://support.claude.com/en/articles/13345190-getting-started-with-cowork) in the [desktop app](https://support.claude.com/en/articles/10065433-installing-claude-desktop)
- Claude Code
  - In the [desktop app](https://code.claude.com/docs/en/desktop-quickstart)
  - In the [browser](https://code.claude.com/docs/en/claude-code-on-the-web) <https://claude.ai/code>
- Claude chat
  - In the [browser](https://claude.ai)
  - In the [desktop app](https://code.claude.com/docs/en/desktop-quickstart)

The skills should also work with other AI clients that support the [Agent Skills](https://agentskills.io/home) standard.

A skill includes instructions and best practices, as well as templates, scripts and assets.
No developer skills are required, and you don't need an IDE or Salesforce CLI are required.

[Claude Cowork](https://support.claude.com/en/articles/13345190-getting-started-with-cowork) brings agentic capabilities to Claude Desktop for knowledge work beyond coding.

Many of these plugins were adapted from corresponding skills in the <https://github.com/Jaganpro/sf-skills/> repository maintained by Jag Valaiyapathy, which in turn were based on various community contributions (see [CREDITS.md](./CREDITS.md))

## Available Plugins

| Plugin                                | Description                                                                  |
| ------------------------------------- | ---------------------------------------------------------------------------- |
| [cirra-ai-sf](cirra-ai-sf/)           | Orchestrator — coordinates the plugins below into a unified Salesforce suite |
| [cirra-ai-sf-apex](cirra-ai-sf-apex/) | Apex code generation, review, and 150-point scoring                          |
| [cirra-ai-sf-flow](cirra-ai-sf-flow/) | Flow creation, validation, and 110-point scoring                             |
| [cirra-ai-sf-data](cirra-ai-sf-data/) | SOQL queries, DML operations, test data factories, and 130-point validation  |
| [cirra-ai-sf-lwc](cirra-ai-sf-lwc/)   | Lightning Web Components development skill                                   |

More plugins (metadata, SOQL, permissions, Agent Script, and others) will be released incrementally -- stay tuned!

## Installation

### Claude Cowork

Alternatively, download a plugin zip from the [latest release](https://github.com/cirra-ai/skills/releases) and use **Upload plugin** to install it manually.

See the [Cowork plugins docs](https://support.claude.com/en/articles/13345190-getting-started-with-cowork#h_0f9e0998dd) for more details.

all the is in the [desktop app](https://support.claude.com/en/articles/10065433-installing-claude-desktop)

### Claude Code

First, make sure you have [Claude Code](https://claude.com/product/claude-code) installed.

See the [Claude Code plugins docs](https://docs.anthropic.com/en/docs/claude-code/plugins) for general setup, then:

```bash
# Add the marketplace (one-time)
/plugin marketplace add cirra-ai/skills

# Install the complete suite
/plugin install cirra-ai-sf-skills@cirra-ai

# Or install individual plugins
/plugin install cirra-ai-sf-apex@cirra-ai
```

## Requirements

- Cirra AI MCP Server
- Target Salesforce org (sandbox or production)
- [Claude Cowork](https://claude.com/product/cowork) or [Claude Code](https://claude.com/product/claude-code)

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for how to file issues, open pull requests, and run tests locally.

## License

See [LICENSE](LICENSE)

The plugins in this repository are designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. This repository and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
