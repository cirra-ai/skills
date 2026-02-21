# cirra-ai-sf-permissions

Salesforce permission analysis and auditing skill for Claude Cowork and Claude Code. Analyze Permission Set hierarchies, find "who has access to X?", audit user permissions, and identify security risks via the Cirra AI MCP Server.

## Features

- **Hierarchy Viewer**: Visualize all PS/PSG in an org as structured trees
- **Permission Detector**: Find which PS/PSG grant a specific permission
- **User Analyzer**: Show all permissions assigned to a specific user
- **Security Audit**: Identify overly broad permissions and security risks
- **Permission Set Creation**: Generate and deploy Permission Sets

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Usage

#### In Claude Cowork or Claude Code

Use the pre-built command

```
/analyze-permissions
```

#### In other tools

Invoke the skill:

```
Skill: cirra-ai-sf-permissions
Request: "Who has delete access to the Account object?"
```

### Common Operations

| Operation | Example Request |
| --------- | ------------------------------------------------------- |
| Hierarchy | "Show the permission set hierarchy in my org" |
| Who Has X? | "Who has edit access to Account.AnnualRevenue?" |
| User Analysis | "What permissions does john@company.com have?" |
| Security Audit | "Find all permission sets with ModifyAllData" |
| PS Creation | "Create a read-only permission set for contractors" |

## Related Skills

| Skill | When to Use |
| -------------------- | -------------------------------------------------------- |
| cirra-ai-sf-metadata | Create permission sets and manage metadata |
| cirra-ai-sf-diagram | Visualize permission hierarchies as Mermaid diagrams |
| cirra-ai-sf-data | Query user assignments in bulk |

## Cirra AI MCP Tools

| Operation | MCP Tool |
| --------- | ------------------------------------------ |
| Query PS/PSG | `soql_query(sObject="PermissionSet")` |
| Query Permissions | `soql_query(sObject="ObjectPermissions")` |
| Tooling Queries | `tooling_api_query(sObject, fields)` |
| Create PS | `metadata_create(type="PermissionSet")` |

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
