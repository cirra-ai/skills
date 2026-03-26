# sf-metadata MCP integration protocol (actual org)

## Prerequisites

- Cirra AI MCP server is connected and authenticated.
- A target Salesforce org and `sf_user` alias are available.
- Contributor has permission to create/update metadata in the org.

## Reusable LLM prompt

Use this prompt as-is for each scenario:

```text
Use the sf-metadata skill.
1) Run cirra_ai_init first.
2) Validate the metadata payload with the skill MCP validator.
3) If validation is scored and acceptable, run metadata_create or metadata_update.
4) Return the validator response and deployment result.
```

## Positive scenarios

1. **Create Custom Object**
   - Tool: `metadata_create`
   - Type: `CustomObject`
   - Expect: validator `status: scored`, high score, object created.
2. **Create Custom Field with description**
   - Tool: `metadata_create`
   - Type: `CustomField`
   - Expect: validator `status: scored`, no critical schema issue.
3. **Update Validation Rule**
   - Tool: `metadata_update`
   - Type: `ValidationRule`
   - Expect: validator `status: scored`, deployment update succeeds.

## Negative scenarios

1. **Unsupported tool**
   - Call validator with `tool: soql_query`.
   - Expect: `status: error`.
2. **Non-target metadata type**
   - Call validator with `type: Flow`.
   - Expect: `status: skipped`.
3. **Missing metadata payload**
   - Call validator with empty `metadata` array.
   - Expect: `status: error`.

## Org verification queries

Use these checks after positive scenarios:

- `tooling_api_query` for `CustomObject` by `DeveloperName`.
- `tooling_api_query` for `CustomField` by `EntityDefinition.QualifiedApiName`.
- `tooling_api_query` for `ValidationRule` by `ValidationName`.

## Optional cleanup

- Delete test artifacts in Setup UI or with metadata delete operation.
- Remove any temporary permission sets created for testing.
