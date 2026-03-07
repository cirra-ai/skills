# cirra-ai-sf-lwc MCP Integration Test Protocol

## Prerequisites

- Access to a Salesforce org authenticated in Cirra AI MCP.
- Cirra AI MCP server running with metadata tools enabled.
- This repository checked out locally.
- Python test environment available (`pytest`).

## Reusable LLM Prompt

Use this prompt in contributor testing sessions:

> "Generate and deploy an LWC bundle named `c/integrationTestCard` using `metadata_create` with type `LightningComponentBundle`. Include minimal valid `html`, `js`, `css`, and `meta.xml` content. After deployment, run validation and report score and issues."

## Positive Scenarios

1. **Valid deploy payload**
   - Tool: `metadata_create`
   - Type: `LightningComponentBundle`
   - Expected: validator result includes `status: scored` and numeric score.
2. **Valid update payload**
   - Tool: `metadata_update`
   - Same component with small text change.
   - Expected: validator result includes `status: scored`.
3. **Resource-list payload**
   - Provide `lwcResources` array with at least one `.html` resource.
   - Expected: validator extracts HTML and returns scored output.

## Negative Scenarios

1. **Unsupported tool**
   - Tool: `soql_query`.
   - Expected: `status: error` with unsupported tool message.
2. **Wrong metadata type**
   - Tool: `metadata_create`, type `CustomObject`.
   - Expected: `status: skipped`.
3. **Missing body/content**
   - Tool: `metadata_create` with empty metadata content.
   - Expected: `status: error` indicating missing/empty payload.

## Org Verification Queries

After successful create/update, run one or more:

- `tooling_api_query` on `LightningComponentBundle` filtered by `DeveloperName`.
- `metadata_read` for `LightningComponentBundle` and full name `c/integrationTestCard`.

## Optional Cleanup

- Remove temporary test bundle with `metadata_delete` for `LightningComponentBundle`.
- Re-run validation to confirm no stale test artifacts remain in org.
