# sf-sandbox-manager

Salesforce sandbox and scratch org pool manager for AI coding tools. Check out clean environments, use them for tasks, and check them back in for recycling via the Cirra AI MCP Server.

## Features

- **Pool Management**: Track sandbox environments with checkout/checkin lifecycle
- **Sandbox Provisioning**: Create, refresh, and delete sandboxes via Tooling API
- **Scratch Org Support**: Create and manage scratch orgs via Salesforce CLI
- **Recommendation Engine**: Help users choose between sandbox types and scratch orgs
- **Auto-Setup**: Automatically creates the `Environment_Pool__c` tracking object on first use

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Usage

#### In Claude Code

Invoke the unified skill:

```
/sf-sandbox-manager
/sf-sandbox-manager checkout
/sf-sandbox-manager status
/sf-sandbox-manager recommend
```

#### In other tools

Invoke the skill:

```
Skill: sf-sandbox-manager
Request: "I need a clean sandbox for testing"
```

### Common Operations

| Operation          | Example Request                                        |
| ------------------ | ------------------------------------------------------ |
| Checkout           | "Get me a Developer sandbox for feature testing"       |
| Check In           | "I'm done with dev-sandbox-1, it's clean"              |
| Pool Status        | "Show me all environments and who's using them"        |
| Create Sandbox     | "Create a new Developer sandbox called 'qa-sprint42'"  |
| Create Scratch Org | "Spin up a scratch org for 7 days"                     |
| Delete             | "Decommission the old staging sandbox"                 |
| Recommend          | "Should I use a sandbox or scratch org for this task?" |
| Setup              | "Set up the environment pool tracking"                 |

## Related Skills

| Skill          | When to Use                                           |
| -------------- | ----------------------------------------------------- |
| sf-metadata    | Create custom objects/fields in a checked-out sandbox |
| sf-data        | Populate test data after checkout                     |
| sf-permissions | Audit permissions on the pool tracking object         |
| sf-apex        | Develop Apex in a checked-out scratch org             |

## Cirra AI MCP Tools — for developers

> This section is for Salesforce developers building integrations. Admins can skip it.

| Operation            | MCP Tool                                      |
| -------------------- | --------------------------------------------- |
| Query pool           | `soql_query(sObject="Environment_Pool__c")`   |
| Update pool record   | `sobject_dml(sObject="Environment_Pool__c")`  |
| Create sandbox       | `tooling_api_dml(sObject="SandboxInfo")`      |
| Query sandbox status | `tooling_api_query(sObject="SandboxProcess")` |
| Switch connection    | `sf_connection_manage()`                      |

## Execution Modes

| Mode                      | Sandbox | Scratch Org   | Speed   |
| ------------------------- | ------- | ------------- | ------- |
| `sfdx-repo`               | Full    | Full          | Fastest |
| `cli`                     | Full    | Full          | Fast    |
| `mcp-plus-code-execution` | Full    | Limited       | Medium  |
| `mcp-core`                | Full    | Not supported | Slowest |

All sandbox pool operations go through MCP tools regardless of mode. The mode
determines whether scratch org CLI commands are available.

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce production org (for sandbox management)
- Salesforce CLI (optional, for scratch org support)

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
