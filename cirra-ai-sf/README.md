# cirra-ai-sf

Salesforce development suite for Claude Code. Orchestrates Apex, Flow, and Data plugins with Cirra AI MCP Server.

## What's Included

| Plugin | What It Does |
|---|---|
| [cirra-ai-sf-apex](../cirra-ai-sf-apex/) | Apex code generation, review, and 150-point scoring |
| [cirra-ai-sf-flow](../cirra-ai-sf-flow/) | Flow creation, validation, and 110-point scoring |
| [cirra-ai-sf-data](../cirra-ai-sf-data/) | SOQL queries, DML operations, test data factories |

Each plugin works independently. Install this meta-plugin to get all three with coordinated orchestration.

## Installation

```bash
# Install the suite (all three plugins)
claude /plugin install github:cirra-ai/skills/cirra-ai-sf

# Or install individually
claude /plugin install github:cirra-ai/skills/cirra-ai-sf-apex
claude /plugin install github:cirra-ai/skills/cirra-ai-sf-flow
claude /plugin install github:cirra-ai/skills/cirra-ai-sf-data
```

## Requirements

- Cirra AI MCP Server
- Target Salesforce org (sandbox or production)
- Claude Code with skill plugins enabled

## License

MIT License. See LICENSE file.
