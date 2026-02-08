# cirra-ai-sf

Salesforce admin suite for Claude Cowork and Claude Code. Orchestrates Apex, Flow, and Data plugins with Cirra AI MCP Server.

## What's Included

| Plugin | What It Does |
|---|---|
| [cirra-ai-sf-apex](../cirra-ai-sf-apex/) | Apex code generation, review, and 150-point scoring |
| [cirra-ai-sf-flow](../cirra-ai-sf-flow/) | Flow creation, validation, and 110-point scoring |
| [cirra-ai-sf-data](../cirra-ai-sf-data/) | SOQL queries, DML operations, test data factories |

Each plugin works independently. Install this meta-plugin to get all three with coordinated orchestration.

## Installation

### Claude Code

Add the Cirra AI marketplace, then install the full suite or individual skills:

```bash
# Step 1: Add the marketplace (one-time)
/plugin marketplace add cirra-ai/skills

# Step 2: Install the complete suite
/plugin install cirra-ai-sf-skills@cirra-ai

# Or install individual skills
/plugin install cirra-ai-sf-apex@cirra-ai
/plugin install cirra-ai-sf-flow@cirra-ai
/plugin install cirra-ai-sf-data@cirra-ai
```

### Claude Cowork

1. Download the plugin zip from the [latest release](https://github.com/cirra-ai/skills/releases)
   - **Full suite**: download `cirra-ai-sf-skills.zip`
   - **Individual skill**: download e.g. `cirra-ai-sf-apex.zip`
2. In Cowork, click **Plugins** in the left sidebar
3. Click **Upload plugin**
4. Select the downloaded zip file

## Requirements

- Cirra AI MCP Server
- Target Salesforce org (sandbox or production)
- Claude Code or Claude Cowork with plugins enabled

## License

MIT License. See LICENSE file.
