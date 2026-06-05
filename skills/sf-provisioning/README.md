# sf-provisioning

Salesforce user and access provisioning skill for AI coding tools. Create users, grant and revoke capabilities, mirror access from existing users, and offboard logins — while enforcing the org's existing conventions (username pattern, profile, license, permission sets) via the Cirra AI MCP Server.

## Features

- **Provision User**: Onboard a new user with the right license, profile, locale, and permission sets — discovered from comparable existing users, not invented.
- **Grant Capability**: Enable a specific ability (scratch org creation, API access, a feature, an object) by finding the existing permission set that already grants it.
- **Revoke / Deactivate**: Narrow revoke of a permission set, or deactivate/freeze a user for offboarding (with dependency checks).
- **Mirror a User**: Create a new user with the same access as an existing one — profile, license, locale, and every permission set assignment.

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Quick Start

### 1. Invoke the skill

```
Skill: sf-provisioning
Request: "Create a contractor user for Jane Doe with scratch-org access"
```

Or in CLIs:

```
/sf-provisioning create-user Jane Doe contractor
/sf-provisioning grant scratch-org access to jane@cirra.ai
/sf-provisioning mirror access from john@cirra.ai to jane@cirra.ai
/sf-provisioning deactivate john@cirra.ai
```

### 2. Discovery happens automatically

The skill will:

- Connect to your org via `cirra_ai_init()`
- Query comparable existing users to read off your org's username pattern, profile, license, and permission set conventions
- Find the existing permission set that grants the requested capability (instead of creating a new one)
- Present the full plan and wait for your approval before any write

### 3. Review results

After approval, the skill creates the user, assigns permission sets, verifies the result, and reports a compact table with a direct setup-record link.

## Common Operations

| Operation            | Example Request                                         |
| -------------------- | ------------------------------------------------------- |
| Provision contractor | "Create a contractor user for Jane Doe"                 |
| Grant capability     | "Give jane@cirra.ai the ability to create scratch orgs" |
| Mirror access        | "Give Jane the same access as John"                     |
| Revoke a permission  | "Remove the SFDX permission set from jane@cirra.ai"     |
| Offboard             | "Deactivate john@cirra.ai — he left the company"        |

## Related Skills

| Skill          | When to Use                                                   |
| -------------- | ------------------------------------------------------------- |
| sf-permissions | Analyze "who has X access?", visualize PS/PSG hierarchies     |
| sf-metadata    | Create a new permission set when none exists for a capability |
| sf-audit       | Org-wide review of users, profiles, and permission sets       |

## Cirra AI MCP Tools — for developers

> This section is for Salesforce developers building integrations. Admins can skip it.

| Operation                      | MCP Tool                                              |
| ------------------------------ | ----------------------------------------------------- |
| Discover users / PS / licenses | `soql_query`                                          |
| Create user                    | `user_create` (prefer `template=` to clone)           |
| Assign / remove PS             | `permission_set_assignments` (`add` / `remove`)       |
| Update user fields             | `user_update` / `sobject_dml` on `User`               |
| Create permission set          | `metadata_create(type="PermissionSet")` (last resort) |

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce org

## License

Cirra AI License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
