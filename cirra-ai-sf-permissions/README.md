# sf-permissions v1.0.0

Salesforce Permission Set analysis, visualization, and auditing via Cirra AI MCP tools.

Based on [sf-permissions in Jaganpro/sf-skills](https://github.com/Jaganpro/sf-skills/tree/main/sf-permissions)

## What's Changed

- Removed Python scripts and sf CLI dependency
- Fully refactored to use Cirra AI MCP tools (soql*query, tooling_api_query, metadata_read, permission_set*\* tools)
- Added Cirra AI parameter format guidance to avoid common validation errors
- Streamlined workflows for org audits, access detection, and user analysis

## Requirements

- Cirra AI MCP connector (configured via .mcp.json)

## Capabilities

- Full org permission audit (PS, PSG, hierarchy, risk flags)
- "Who has access to X?" detection (objects, fields, Apex, custom permissions)
- User permission analysis
- Permission Set management (create, update, assign)
- Agentforce agent access configuration
