# cirra-ai-sf-diagram

Salesforce architecture diagram generation skill for Claude Cowork and Claude Code. Create Mermaid diagrams for OAuth flows, data models (ERDs), integration sequences, system landscapes, and role hierarchies.

## Features

- **OAuth Flows**: Authorization Code, JWT Bearer, PKCE, Client Credentials, Device Flow
- **Data Models (ERD)**: Object relationships with color coding by type
- **Integration Sequences**: API callouts, event-driven flows
- **System Landscapes**: High-level architecture diagrams
- **Role Hierarchies**: User hierarchies, profile/permission structures
- **Dual Output**: Mermaid + ASCII fallback for every diagram

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Usage

#### In Claude Cowork or Claude Code

Use the pre-built command

```
/create-diagram
```

#### In other tools

Invoke the skill:

```
Skill: cirra-ai-sf-diagram
Request: "Create a JWT Bearer OAuth flow diagram"
```

### Common Operations

| Operation   | Example Request                                       |
| ----------- | ----------------------------------------------------- |
| OAuth Flow  | "Create a JWT Bearer OAuth flow diagram"              |
| ERD         | "Create an ERD for Account, Contact, and Opportunity" |
| Integration | "Diagram our Salesforce to SAP integration"           |
| Landscape   | "Create a system architecture diagram"                |
| Hierarchy   | "Visualize our role hierarchy"                        |
| Agentforce  | "Create flow diagram for FAQ Agent"                   |

## Related Skills

| Skill                   | When to Use                                        |
| ----------------------- | -------------------------------------------------- |
| cirra-ai-sf-metadata    | Get real object/field definitions for ERD diagrams |
| cirra-ai-sf-permissions | Get permission data for hierarchy visualizations   |

## Cirra AI MCP Tools (for org discovery)

| Operation       | MCP Tool                                    |
| --------------- | ------------------------------------------- |
| Describe Object | `sobject_describe(sObject)`                 |
| Record Counts   | `soql_query(fields=["COUNT(Id)"])`          |
| Custom Objects  | `tooling_api_query(sObject="CustomObject")` |

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server (optional - only needed for org-connected ERDs)

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
