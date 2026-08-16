# sf-cms

Salesforce CMS skill for AI coding tools. Create, update, clone, publish, and search managed content in enhanced CMS workspaces, administer workspaces and channels, and verify what is actually live on a delivery channel or Experience Cloud site — via the Cirra AI MCP Server.

## Features

- **Create and Publish**: Author managed content into the right workspace with the right content type, then publish it to a channel as a separate, separately-approved step.
- **Update Content**: Edit existing content through its variant (the editable unit in enhanced CMS workspaces), with a before/after plan shown for approval.
- **Verify Delivery**: Answer "what is live?" and "why isn't this showing on the site?" with a four-step diagnosis instead of a bare "not found".
- **Find Content**: Search managed content across workspaces and folders.
- **Workspace and Channel**: List, create, update, and delete CMS spaces and channels, with the destructive cases called out before approval.
- **Taxonomy**: Read and set taxonomy term associations on content.

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Usage

### 1. Invoke the skill

```
Skill: sf-cms
Request: "Add a news article about the Q3 launch to the Marketing workspace"
```

Or in CLIs:

```
/sf-cms create a news article "Q3 launch" in the Marketing workspace
/sf-cms publish the Q3 launch article to the Partner Portal channel
/sf-cms delivery what content is live on the customer portal
/sf-cms why isn't the Q3 launch article showing on the site
```

### 2. Discovery happens automatically

The skill will:

- Connect to your org via `cirra_ai_init()`
- List the CMS workspaces and channels rather than guessing IDs
- Read the content type from the Metadata API and model the body on existing content
- Present the full plan and wait for your approval before any write

### 3. Publishing is always a separate approval

Creating or updating content never makes it live. The skill asks again before publishing — naming the channels the workspace is connected to, since publish itself takes no channel and goes live on all of them — and then verifies through the delivery API rather than trusting the authoring response.

### Common Operations

| Operation       | Example Request                                        |
| --------------- | ------------------------------------------------------ |
| Create content  | "Add a news article about the Q3 launch"               |
| Update content  | "Update the Q3 launch article headline"                |
| Publish         | "Publish the Q3 launch article to the Partner Portal"  |
| Verify delivery | "What content is live on the customer portal?"         |
| Troubleshoot    | "Why isn't the Q3 launch article showing on the site?" |
| Search          | "Find CMS content mentioning pricing"                  |
| Channel setup   | "Create a CMS channel for the partner site"            |

## Related Skills

| Skill           | When to Use                                                               |
| --------------- | ------------------------------------------------------------------------- |
| sf-metadata     | Create or inspect a `ManagedContentType` — content types are Metadata API |
| sf-connect-rest | DAM providers, search indexing, folder sharing, legacy CMS workspaces     |
| sf-permissions  | Diagnose CMS workspace access after a permission-shaped failure           |

## Cirra AI MCP Tools — for developers

> This section is for Salesforce developers building integrations. Admins can skip it.

| Operation                      | MCP Tool                                                             |
| ------------------------------ | -------------------------------------------------------------------- |
| Discover workspaces / channels | `cms_content` (`list_spaces`, `list_channels`)                       |
| Discover content types         | `metadata_list` / `metadata_read` (`ManagedContentType`)             |
| Search content                 | `cms_content` (`search`)                                             |
| Create / clone content         | `cms_content` (`create`, `clone`)                                    |
| Edit / remove content          | `cms_content` (`update`, `delete`) — operates on a variant           |
| Publish / unpublish            | `cms_content` (`publish`, `unpublish`) — unpublish takes variant IDs |
| Read what is live              | `cms_delivery`                                                       |
| CMS resources without a tool   | `connect_rest`                                                       |

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce org using enhanced CMS workspaces

## License

Cirra AI License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
