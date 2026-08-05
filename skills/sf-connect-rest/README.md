# sf-connect-rest

Salesforce Connect REST API skill for AI coding tools. Reach org capabilities that have no dedicated tool — named credentials, custom domains, Experience Cloud site publishing, Agentforce data libraries, Files, Chatter, and more — via the Cirra AI MCP Server.

## Features

- **Find the Resource**: Turn "Cirra can't do X" into the exact documented Connect REST resource, method, and request shape — or a clear statement that no such resource exists.
- **Core Resources**: Named credentials, custom domains, and org and user settings that do not round-trip cleanly through the Metadata API.
- **Experience Cloud**: Site information, audiences, moderation, and site publishing — the step that has no Metadata API equivalent.
- **Agentforce**: Data libraries and prompt templates.
- **Safe writes**: Every POST, PATCH, PUT, and DELETE shows the exact method, path, and body and waits for explicit approval.
- **Error decoding**: Distinguishes a Chatter rate-limit 503 from an outage, and a permission 403 from a malformed request.

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Usage

### 1. Invoke the skill

```
Skill: sf-connect-rest
Request: "List the named credentials in this org"
```

Or in CLIs:

```
/sf-connect-rest list the named credentials in this org
/sf-connect-rest publish the partner community site
/sf-connect-rest Cirra can't reach custom domains — how do I list them
```

### 2. Paths are looked up, never guessed

The skill consults the official Connect REST API reference for the exact path and HTTP method before calling anything, and confirms the resource exists at your org's API version. If the resource isn't in the documentation, it says so rather than probing candidate paths.

### 3. Reads are free, writes are gated

`GET` runs without ceremony. Any write shows you the exact request first and waits for approval — the passthrough has no dry-run.

### Common Operations

| Operation              | Example Request                                           |
| ---------------------- | --------------------------------------------------------- |
| List named credentials | "List the named credentials in this org"                  |
| Publish a site         | "Publish the partner community site"                      |
| Inspect org settings   | "Show the org's custom domains"                           |
| Agentforce resources   | "List the Agentforce data libraries"                      |
| Capability gap         | "Cirra can't reach X — is there a Connect REST resource?" |

## Related Skills

| Skill         | When to Use                                                        |
| ------------- | ------------------------------------------------------------------ |
| sf-cms        | CMS authoring and delivery — use the purpose-built tools instead   |
| sf-metadata   | The capability is Metadata API rather than Connect REST            |
| sf-data       | Record data — use SOQL and DML, which enforce field-level access   |
| sf-help-fetch | Reading a Salesforce Help article to confirm a resource or setting |

## Cirra AI MCP Tools — for developers

> This section is for Salesforce developers building integrations. Admins can skip it.

| Operation                 | MCP Tool                                                 |
| ------------------------- | -------------------------------------------------------- |
| Any Connect REST resource | `connect_rest` (`method`, `path`, `queryParams`, `body`) |
| CMS content and delivery  | `cms_content`, `cms_delivery`                            |
| Setup record links        | `link_build`                                             |

Paths are relative to `/services/data/vXX.X/connect/` — the version prefix is added automatically. Only Connect REST resources are reachable: paths outside `/connect/` are rejected, because the record-facing tools enforce field-level access checks that a general passthrough would bypass.

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce org
- Web access, in practice, to look up resource paths in the Connect REST API reference

## License

Cirra AI License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
