# sf-provisioning

Salesforce user and access provisioning skill for AI coding tools. Create users, grant or revoke capabilities, mirror an existing user's access, and onboard/offboard logins via the Cirra AI MCP Server — while enforcing the org's existing username/license/permission-set conventions.

## Features

- **Provision User**: Create a new user that matches the org's conventions (cloned from a comparable user)
- **Grant Capability**: Give an existing or new user a specific ability, reusing existing permission sets where possible
- **Revoke / Deactivate**: Remove a permission set, deactivate, or freeze a user with dependency checks
- **Mirror a User**: Create a new user with the same profile/locale and permission set assignments as a model user
- **Least-Privilege Defaults**: Surface (rather than silently add) any access broader than what was requested

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Usage

#### Installation

Invoke the unified skill:

```
/sf-provisioning
/sf-provisioning create-user Jane Doe, contractor
/sf-provisioning grant scratch-org access to jane@acme.com
/sf-provisioning mirror john@acme.com to jane@acme.com
```

#### In other tools

```
Skill: sf-provisioning
Request: "Set up a contractor login for Jane Doe with scratch-org access"
```

### Common Operations

| Operation        | Example Request                                         |
| ---------------- | ------------------------------------------------------- |
| Provision User   | "Create a contractor user for Jane Doe (jane@acme.com)" |
| Grant Capability | "Give jane@acme.com the ability to create scratch orgs" |
| Mirror Access    | "Set up Bob with the same access as Alice"              |
| Revoke           | "Remove the SFDX permission set from jane@acme.com"     |
| Offboard         | "Deactivate john@acme.com — he left the company"        |

## The Golden Rule

This skill always **discovers existing conventions before provisioning**:

- Username pattern, profile, license, alias, locale from comparable users
- Existing permission sets that already grant the requested capability (searched by `ObjectPermissions`, not by name)
- License seat availability before consuming a seat

This is enforced because a user that technically works but violates org naming/access conventions is a real defect, not a cosmetic one.

## Related Skills

| Skill          | When to Use                                                 |
| -------------- | ----------------------------------------------------------- |
| sf-permissions | Analyze, hierarchy, and "who has X?" questions about access |
| sf-metadata    | Create a new permission set when no existing one fits       |
| sf-audit       | Org-wide review of users, profiles, and permission sets     |
| sf-data        | Bulk user/role/permission-set-assignment queries            |

## Cirra AI MCP Tools — for developers

> This section is for Salesforce developers building integrations. Admins can skip it.

| Operation                      | MCP Tool                                      |
| ------------------------------ | --------------------------------------------- |
| Discover users / PS / licenses | `soql_query`                                  |
| Create user                    | `user_create` (prefer `template=`)            |
| Assign / remove PS             | `permission_set_assignments` (`add`/`remove`) |
| Update / deactivate user       | `user_update` / `sobject_dml` on `User`       |
| Create PS (last resort)        | `metadata_create(type="PermissionSet")`       |

## Execution Modes

| Mode                      | When                                              | Speed   |
| ------------------------- | ------------------------------------------------- | ------- |
| `mcp-plus-code-execution` | MCP + filesystem + code execution (Cowork, Codex) | Medium  |
| `mcp-core`                | MCP only, no filesystem (chat interfaces)         | Slowest |

Provisioning is a remote-only workflow: all operations target the connected org via the Cirra AI MCP Server. No SFDX project or CLI is required.

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce org
- A user with permissions to create users and assign permission sets (typically a System Administrator)

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
