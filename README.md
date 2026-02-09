# Cirra AI Salesforce Plugins

![CI](https://github.com/cirra-ai/skills/actions/workflows/ci.yml/badge.svg)
![Package](https://github.com/cirra-ai/skills/actions/workflows/package-plugins.yml/badge.svg)

Salesforce development plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Claude Cowork](https://docs.anthropic.com/en/docs/cowork). Each plugin adds domain-specific skills, templates, and validation hooks powered by the Cirra AI MCP Server.

## Available Plugins

| Plugin | Description |
|---|---|
| [cirra-ai-sf](cirra-ai-sf/) | Orchestrator — coordinates the plugins below into a unified Salesforce suite |
| [cirra-ai-sf-apex](cirra-ai-sf-apex/) | Apex code generation, review, and 150-point scoring |
| [cirra-ai-sf-flow](cirra-ai-sf-flow/) | Flow creation, validation, and 110-point scoring |
| [cirra-ai-sf-data](cirra-ai-sf-data/) | SOQL queries, DML operations, test data factories, and 130-point validation |

More plugins (LWC, metadata, SOQL, permissions, Agent Script, and others) are being restored incrementally — see the `skills_v2` branch for the full catalog.

## Installation

### Claude Cowork

1. Open **Plugins** in the left sidebar and click **Browse plugins**
2. From the dropdown, select **Add marketplace from GitHub**
3. Enter `cirra-ai/skills` and confirm
4. Browse the Cirra AI marketplace and install the plugins you need

Alternatively, download a plugin zip from the [latest release](https://github.com/cirra-ai/skills/releases) and use **Upload plugin** to install it manually.

See the [Cowork plugins docs](https://docs.anthropic.com/en/docs/cowork/plugins) for more details.

### Claude Code

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
- Claude Code or Claude Cowork with plugins enabled

## Contributing

We welcome contributions! Please read [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for how to file issues, open pull requests, and run tests locally.

## License

MIT License — see [LICENSE](LICENSE) for details.

The plugins in this repository are designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. This repository and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
