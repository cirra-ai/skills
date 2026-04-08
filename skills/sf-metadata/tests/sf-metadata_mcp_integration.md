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

### Core metadata types

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

### Lightning Pages (FlexiPage)

4. **Create Lightning Record Page**
   - Tool: `metadata_create`
   - Type: `FlexiPage`
   - Payload: `type: RecordPage`, `sobjectType: Account`, `template: flexipage:recordHomeTemplateDesktop`
   - Components: `force:highlightsPanel`, `force:detailPanel`, `force:relatedListContainer`
   - Expect: validator `status: scored`, high score, page deployed.
5. **Create Lightning App Page**
   - Tool: `metadata_create`
   - Type: `FlexiPage`
   - Payload: `type: AppPage`, no `sobjectType`, `template: flexipage:defaultAppHomeTemplate`
   - Expect: validator `status: scored`, no schema issues about sobjectType.
6. **Create Lightning Home Page**
   - Tool: `metadata_create`
   - Type: `FlexiPage`
   - Payload: `type: HomePage`, no `sobjectType`, `template: home:desktopTemplate`
   - Regions: `top`, `bottomLeft`, `bottomRight`, `sidebar`
   - Expect: validator `status: scored`, page deployed.
7. **Update Lightning Page — add component**
   - Tool: `metadata_update`
   - Type: `FlexiPage`
   - Expect: validator `status: scored`, new component added, existing components preserved.
8. **Read Lightning Page**
   - Tool: `metadata_read`
   - Type: `FlexiPage`
   - Expect: validator `status: scored`, metadata_type = `FlexiPage`.

### Page Layouts

9. **Clone Page Layout**
   - Tool: `page_layout_clone`
   - Expect: new layout created, original layout unchanged.
   - Verify: `metadata_read` returns layout sections and fields.
10. **Update Page Layout — add fields**
    - Tool: `page_layout_update`
    - Patch op: `add`
    - Expect: fields added to correct section and column.
    - Verify: `metadata_read` shows new fields.
11. **Update Page Layout — multi-operation**
    - Tool: `page_layout_update`
    - Patch array with 4+ operations (add section, add field, remove field, add related list)
    - Expect: all changes applied in single call.

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
4. **FlexiPage with wrong component name**
   - Call validator with `componentName: force:recordDetail`.
   - Expect: `status: scored`, issue flagging wrong component name.
5. **FlexiPage with unsupported visibility operator**
   - Call validator with `operator: GREATER_THAN` in `visibilityRule`.
   - Expect: `status: scored`, critical issue about unsupported operator.
6. **FlexiPage RecordPage without sobjectType**
   - Call validator with `type: RecordPage`, no `sobjectType`.
   - Expect: `status: scored`, critical issue about missing sobjectType.
7. **Layout with invalid section style**
   - Call validator with `style: ThreeColumns`.
   - Expect: `status: scored`, issue about invalid style.
8. **Clone non-existent layout**
   - Tool: `page_layout_clone` with non-existent source.
   - Expect: error with actionable message.
9. **Duplicate FlexiPage name**
   - Tool: `metadata_create` with existing FlexiPage name.
   - Expect: `DUPLICATE_DEVELOPER_NAME` error.

## Org verification queries

Use these checks after positive scenarios:

- `tooling_api_query` for `CustomObject` by `DeveloperName`.
- `tooling_api_query` for `CustomField` by `EntityDefinition.QualifiedApiName`.
- `tooling_api_query` for `ValidationRule` by `ValidationName`.
- `tooling_api_query` for `FlexiPage` by `DeveloperName`.
- `metadata_read` for `Layout` by full name (e.g., `Account-CirraTest Account Layout`).

## Known limitations

These are Salesforce Metadata API constraints, not Cirra AI bugs:

- **Visibility rule operators**: Only `EQUAL` is supported for FlexiPage criteria.
- **`$Permission` syntax**: Not valid for visibility rule `leftValue`; use `$User` fields.
- **Home page regions**: `home:desktopTemplate` provides exactly 4 regions (top, bottomLeft, bottomRight, sidebar) — no true three-column layout.
- **Related list field names**: Use `OBJECT.FIELD_REFERENCE` format (e.g., `CASES.CASE_NUMBER`), not standard API names.
- **System field behaviors**: Fields like `IsClosedOnCreate` must use `Readonly` behavior; `Edit` is rejected.

## Optional cleanup

- Delete test artifacts in Setup UI or with metadata delete operation.
- Remove any temporary permission sets created for testing.
- Delete FlexiPages with `metadata_delete` (type: `FlexiPage`).
- Cloned layouts can be deleted via Setup UI (no `metadata_delete` for layouts).
