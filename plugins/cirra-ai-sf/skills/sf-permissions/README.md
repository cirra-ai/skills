# sf-permissions

Salesforce permission analysis and management skill for AI coding tools. Analyze Permission Set hierarchies, find "who has access to X?", audit user permissions, identify security risks, and create, update, assign and clone Permission Sets and Profiles via the Cirra AI MCP Server.

## Features

- **Hierarchy Viewer**: Visualize all PS/PSG in an org as structured trees
- **Permission Detector**: Find which PS/PSG grant a specific permission
- **User Analyzer**: Show all permissions assigned to a specific user
- **Security Audit**: Identify overly broad permissions and security risks
- **Permission Set Lifecycle**: Create, update (JSON Patch), clone, delete and assign Permission Sets
- **Profile Management**: Inspect, patch and clone Profiles
- **Agent Access**: Grant and audit Agentforce agent visibility

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Usage

#### Installation

Invoke the unified skill:

```
/sf-permissions
/sf-permissions audit
/sf-permissions analyze Account delete access
```

#### In other tools

Invoke the skill:

```
Skill: sf-permissions
Request: "Who has delete access to the Account object?"
```

### Common Operations

| Operation      | Example Request                                     |
| -------------- | --------------------------------------------------- |
| Hierarchy      | "Show the permission set hierarchy in my org"       |
| Who Has X?     | "Who has edit access to Account.AnnualRevenue?"     |
| User Analysis  | "What permissions does john@company.com have?"      |
| Security Audit | "Find all permission sets with ModifyAllData"       |
| PS Creation    | "Create a read-only permission set for contractors" |
| PS Update      | "Add delete access to Opportunity on Sales_Admin"   |
| Assignment     | "Give jane@company.com the Sales_Admin PS"          |
| Profile        | "What does the Custom Sales User profile grant?"    |

## Related Skills

| Skill           | When to Use                                          |
| --------------- | ---------------------------------------------------- |
| sf-metadata     | Create permission sets and manage metadata           |
| sf-diagram      | Visualize permission hierarchies as Mermaid diagrams |
| sf-data         | Query user assignments in bulk                       |
| sf-provisioning | Create users, mirror a user's access, offboard       |

## Cirra AI MCP Tools — for developers

> This section is for Salesforce developers building integrations. Admins can skip it.

| Operation          | MCP Tool                                                                                                         |
| ------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Query PS/PSG       | `soql_query` on `PermissionSet` / `PermissionSetGroup` / `PermissionSetGroupComponent` (`fields`, `whereClause`) |
| Query permissions  | `soql_query` on `ObjectPermissions` / `FieldPermissions` / `SetupEntityAccess`                                   |
| Tooling queries    | `tooling_api_query` (`sObject`, `fields`, `whereClause`) — e.g. `PermissionSet.Type`                             |
| Read PS metadata   | `metadata_read(type="PermissionSet", fullNames=[...])`                                                           |
| Create PS          | `metadata_create(type="PermissionSet", metadata=[{fullName, label, ...}])`                                       |
| Change PS contents | `permission_set_update(permissionSet=..., patch=[...])` — JSON Patch over object/field/system/class/tab access   |
| Assign / remove PS | `permission_set_assignments(operation="add", permissionSets=[...], users=[...])` — or `operation="remove"`       |
| Delete PS          | `metadata_delete(type="PermissionSet", fullNames=[...])`                                                         |
| Profiles           | `profile_describe(profile, permissionTypes, sObject)` / `profile_update(profile, patch)` / `profile_clone`       |

Full signatures: [`shared/references/cirra-mcp-tools.md`](../../shared/references/cirra-mcp-tools.md).

## Execution Modes

| Mode                      | When                                              | Speed   |
| ------------------------- | ------------------------------------------------- | ------- |
| `sfdx-repo`               | Working directory is an SFDX project              | Fastest |
| `cli`                     | Salesforce CLI installed and authed               | Fast    |
| `mcp-plus-code-execution` | MCP + filesystem + code execution (Cowork, Codex) | Medium  |
| `mcp-core`                | MCP only, no filesystem (chat interfaces)         | Slowest |

All permission operations go through MCP tools regardless of mode. The
mode determines how large responses (e.g. PermissionSet/PSG datasets)
are handled.

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
