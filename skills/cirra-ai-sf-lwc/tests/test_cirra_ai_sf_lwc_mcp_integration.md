# cirra-ai-sf-lwc MCP Integration Test Protocol

## Test Summary (Last Run: 2026-03-07)

| #   | Test                                      | Result | Details                                         |
| --- | ----------------------------------------- | ------ | ----------------------------------------------- |
| 1   | Valid deploy (Base64 + lwc/ prefix paths) | PASS   | Created successfully via metadata_create        |
| 2   | Verify in org via Tooling API query       | PASS   | LightningComponentBundle found by DeveloperName |
| 3   | Deploy with empty lwcResources            | PASS   | API accepted (no validator block — see note)    |
| 4   | Deploy without lwcResources key           | PASS   | API accepted (created empty bundle)             |
| 5   | Cleanup                                   | PASS   | All test bundles deleted                        |

## Prerequisites

- Access to a Salesforce org authenticated in Cirra AI MCP.
- Cirra AI MCP server running with metadata tools enabled.
- This repository checked out locally.
- Python test environment available (`pytest`).

## Reusable LLM Prompt

Use this prompt in contributor testing sessions:

> "Generate and deploy an LWC bundle named `c/integrationTestCard` using `metadata_create` with type `LightningComponentBundle`. Include minimal valid `html`, `js`, and `css` resources with Base64-encoded sources. Set `apiVersion`, `isExposed`, and `targets` on the bundle (do NOT include a `meta.xml` resource — it is auto-generated). After deployment, run validation and report score and issues."

## Positive Scenarios

1. **Valid deploy payload**
   - Tool: `metadata_create`
   - Type: `LightningComponentBundle`
   - **Important**: `source` values must be **Base64-encoded**, and `filePath` must use
     the `lwc/<componentName>/` prefix (e.g., `lwc/integrationTestCard/integrationTestCard.html`).
     Do NOT include a `*.js-meta.xml` resource — it is auto-generated.
   - Expected: validator result includes `status: scored` and numeric score.

   Example payload:

   ```python
   metadata_create(
       type="LightningComponentBundle",
       metadata=[{
           "fullName": "integrationTestCard",
           "apiVersion": 62,
           "isExposed": True,
           "masterLabel": "integrationTestCard",
           "description": "MCP integration test component",
           "targets": {"target": ["lightning__AppPage"]},
           "lwcResources": {"lwcResource": [
               {"filePath": "lwc/integrationTestCard/integrationTestCard.html",
                "source": "<Base64-encoded HTML>"},
               {"filePath": "lwc/integrationTestCard/integrationTestCard.js",
                "source": "<Base64-encoded JS>"},
               {"filePath": "lwc/integrationTestCard/integrationTestCard.css",
                "source": "<Base64-encoded CSS>"}
           ]}
       }]
   )
   ```

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
   - Tool: `metadata_create` with empty `lwcResources` array or no `lwcResources` key.
   - **Known behavior**: The Metadata API accepts empty bundles without error (creates an
     empty LightningComponentBundle). The LWC validator does not currently block this.
     This is a gap — consider adding a pre-flight check for empty payloads.

## Org Verification Queries

After successful create/update, run one or more:

- `tooling_api_query` on `LightningComponentBundle` filtered by `DeveloperName`.
- `metadata_read` for `LightningComponentBundle` and full name `c/integrationTestCard`.

## Optional Cleanup

- Remove temporary test bundle with `metadata_delete` for `LightningComponentBundle`.
- Re-run validation to confirm no stale test artifacts remain in org.

## Key Insights from Testing

1. **Base64 encoding required**: LWC `source` values must be Base64-encoded. Plain text sources cause `UNKNOWN_EXCEPTION` errors from the Metadata API.
2. **filePath prefix**: Must use `lwc/<componentName>/` prefix (e.g., `lwc/myComp/myComp.js`), not just the filename.
3. **No meta.xml resource**: The `*.js-meta.xml` is auto-generated from the bundle-level properties (`apiVersion`, `isExposed`, `targets`). Including it manually causes conflicts.
4. **Empty bundles accepted**: The API does not reject empty `lwcResources`. The validator should catch this as an error but currently does not.
