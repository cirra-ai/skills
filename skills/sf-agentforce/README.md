# sf-agentforce

Standard Agentforce platform skill for Setup UI-based agent building, PromptTemplate metadata, Einstein Models API, GenAiFunction/GenAiPlugin setup, and custom Lightning types.

> **For code-first Agent Script DSL development**, use a dedicated Agent Script skill instead.

## Features

- **Agent Builder**: Creating and configuring agents via Setup UI / Agentforce Builder
- **GenAiFunction**: Metadata XML for registering Flow, Apex, and Prompt Template actions
- **GenAiPlugin**: Grouping multiple GenAiFunctions into reusable action sets
- **PromptTemplate**: Einstein Prompt Builder templates for AI-generated content
- **Models API**: Native LLM access in Apex via `aiplatform.ModelsAPI`
- **Custom Lightning Types**: LightningTypeBundle for custom agent action UIs
- **100-Point Scoring**: Quality assurance across 6 categories
- **Three execution modes**: Works with local SFDX repos (fastest), Salesforce CLI, or MCP-only (cloud environments)

## What This Skill Does NOT Cover

| Area                                     | Use Instead        |
| ---------------------------------------- | ------------------ |
| Agent Script DSL (`.agent` files)        | Agent Script skill |
| Agent testing & coverage                 | Out of scope       |
| Flow creation for actions                | sf-flow            |
| Apex InvocableMethod classes for actions | sf-apex            |

## Installation

For full installation instructions (Claude Cowork, OpenAI Codex, browser), see the [root README](../../README.md).

## Quick Start

### In Claude Cowork or Claude Code

```
/sf-agentforce
/sf-agentforce create GenAiFunction for my Apex discount calculator
/sf-agentforce validate MyAgent
```

### In OpenAI Codex or other tools

```
Skill: sf-agentforce
Request: "Create a PromptTemplate for case summarization"
```

## Execution Modes

| Mode        | When                                  | Speed   |
| ----------- | ------------------------------------- | ------- |
| `sfdx-repo` | Working directory is an SFDX project  | Fastest |
| `cli`       | Salesforce CLI installed and authed   | Fast    |
| `cloud`     | MCP-only (Cowork, cloud environments) | Slowest |

The skill auto-detects the best available mode. In `sfdx-repo` mode, GenAiFunction/GenAiPlugin/PromptTemplate XML is read directly from disk. In `cli` mode, `sf agent` commands manage agent lifecycle and `sf project deploy start` handles metadata. In `cloud` mode, everything goes through MCP tools.

## Requirements

| Requirement | Value                                              |
| ----------- | -------------------------------------------------- |
| API Version | **Per feature** (see breakdown below; 66.0+ ideal) |
| Licenses    | Agentforce, Einstein Generative AI                 |
| sf CLI      | v2.x with agent commands                           |

**API version breakdown**

- Models API (Apex `aiplatform.ModelsAPI`): **61.0+**
- Custom Lightning Types (`LightningTypeBundle`): **64.0+**
- Full Agentforce Builder workflow as described here: **66.0+** (recommended)

## Scoring System (100 Points)

| Category              | Points | Focus                                                       |
| --------------------- | ------ | ----------------------------------------------------------- |
| Agent Configuration   | 20     | System instructions, welcome/error messages, agent user set |
| Topic & Action Design | 25     | Clear descriptions, proper scope, capability text           |
| Metadata Quality      | 20     | Valid GenAiFunction/GenAiPlugin XML, target types           |
| Integration Patterns  | 15     | Orchestration order, dependency management                  |
| PromptTemplate Usage  | 10     | Variable bindings, template types, prompt quality           |
| Deployment Readiness  | 10     | Validation passes, dependencies deployed first              |

**Minimum Score**: 80 (80%) for deployment

## Documentation

| Document                                                                     | Description                                         |
| ---------------------------------------------------------------------------- | --------------------------------------------------- |
| [SKILL.md](SKILL.md)                                                         | Entry point — full skill reference                  |
| [references/prompt-templates.md](references/prompt-templates.md)             | PromptTemplate metadata and Einstein Prompt Builder |
| [references/models-api.md](references/models-api.md)                         | Einstein Models API (`aiplatform.ModelsAPI`)        |
| [references/custom-lightning-types.md](references/custom-lightning-types.md) | LightningTypeBundle for custom agent UIs            |
| [references/cli-commands.md](references/cli-commands.md)                     | `sf agent` CLI command reference                    |

## Cross-Skill Integration

| Related Skill  | When to Use                                       |
| -------------- | ------------------------------------------------- |
| sf-apex        | Create @InvocableMethod for agent actions         |
| sf-flow        | Create Autolaunched Flows for agent actions       |
| sf-metadata    | Deploy custom objects BEFORE agents               |
| sf-lwc         | Create screen components for custom Lightning UIs |
| sf-permissions | Review permission sets for agent users            |

## Orchestration Order

```
sf-metadata → sf-apex → sf-flow → sf-agentforce → deploy
```

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The skill and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
