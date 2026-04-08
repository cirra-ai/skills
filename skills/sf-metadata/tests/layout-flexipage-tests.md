# Phase 1c: Page Layouts & Lightning Pages — Integration Tests

These tests exercise the sf-metadata skill's page layout and Lightning page
capabilities against a live Salesforce org via the Cirra AI MCP Server.

**Prerequisite:** Phase 0 smoke test TC-003 must PASS (metadata path functional).

---

## MCP Tools Exercised

| Tool                 | Operations                                                            |
| -------------------- | --------------------------------------------------------------------- |
| `page_layout_clone`  | Clone existing layout to new layout                                   |
| `page_layout_update` | JSON Patch add/remove/replace/move on sections, fields, related lists |
| `metadata_create`    | FlexiPage (App, Home, Record) creation                                |
| `metadata_update`    | FlexiPage region and component modifications                          |
| `metadata_read`      | Read FlexiPage and Layout metadata                                    |
| `metadata_delete`    | FlexiPage cleanup                                                     |
| `tooling_api_query`  | FlexiPage discovery by EntityDefinitionId                             |

---

## Classic Page Layouts (1c.1–1c.8)

### 1c.1 Clone Layout — Simple (Account)

- **Prompt**: Clone the standard Account page layout to "CirraTest Account Layout"
- **Expected**: `page_layout_clone` called, new layout created, original unchanged
- **Verify**: `metadata_read` returns layout sections and fields

### 1c.2 Update Layout — Add Fields to Section

- **Prompt**: Add AnnualRevenue and NumberOfEmployees to the Information section
- **Expected**: `page_layout_update` with `add` operation, fields in correct column
- **Known issue**: Fields already on layout cause error; adapt to available fields

### 1c.3 Update Layout — Add New Section

- **Prompt**: Add "Financial Details" two-column section after Information
- **Expected**: `page_layout_update`, new LayoutSection with `TwoColumnsTopToBottom` style
- **Verify**: `customLabel=true`, `detailHeading=true`, fields in both columns

### 1c.4 Update Layout — Add Related List with Column Config

- **Prompt**: Add Cases related list with CaseNumber, Subject, Status, Priority, CreatedDate
- **Expected**: `page_layout_update` targeting `relatedLists`, sort by CreatedDate Desc
- **Known issue**: Related list field names use `OBJECT.FIELD_REFERENCE` format

### 1c.5 Update Layout — Add Quick Actions

- **Prompt**: Add "New Case" and "Send Email" quick actions to action bar
- **Expected**: `page_layout_update` targeting `quickActionList`, sequential sortOrder

### 1c.6 Update Layout — Remove Fields and Reorder

- **Prompt**: Remove Fax field, move Phone to top of right column
- **Expected**: Patch includes `remove` op for Fax, `move` op for Phone

### 1c.7 Clone Layout — Custom Object (Case)

- **Prompt**: Clone default Case layout to "CirraTest Case Support Layout"
- **Expected**: `page_layout_clone`, settings preserved (Knowledge sidebar, assignment rules)

### 1c.8 Update Layout — Complex Multi-Operation Patch

- **Prompt**: Single operation: add section, add field, remove field, add related list
- **Expected**: Single `page_layout_update` call with 4+ patch operations

---

## Lightning Record Pages (1c.9–1c.12)

### 1c.9 Create Record Page — Simple (Account)

- **Prompt**: Create Lightning Record Page with header, two-column, highlights + detail + related lists
- **Expected**: `metadata_create` type=FlexiPage, type=RecordPage, sobjectType=Account
- **Template**: `flexipage:recordHomeTemplateDesktop`
- **Components**: `force:highlightsPanel`, `force:detailPanel`, `force:relatedListContainer`
- **Known issue**: Use `force:detailPanel` not `force:recordDetail`

### 1c.10 Create Record Page — With Tabs (Opportunity)

- **Prompt**: Create page with tabs: Details, Related, Activity; highlights + path
- **Expected**: `flexipage:tabset` with 3 tabs using Facets
- **Components**: `force:detailPanel`, `force:relatedListContainer`, `runtime_sales_activities:activityPanel`

### 1c.11 Create Record Page — With Visibility Rules (Case)

- **Prompt**: Create page with visibility-rule-gated rich text for Status=Escalated
- **Expected**: `visibilityRule` with criteria using EQUAL operator
- **Known issue**: Only EQUAL operator is supported; use `richTextValue` property (not `markup`)

### 1c.12 Create Record Page — Dynamic Actions (Contact)

- **Prompt**: Create page with dynamic actions enabled on highlights panel
- **Expected**: `enableActionsConfiguration: true`, action list configured

---

## Lightning App Pages (1c.13–1c.14)

### 1c.13 Create App Page — Single Region (Dashboard)

- **Prompt**: Create single-column app page with rich text header, report chart, list view
- **Expected**: type=AppPage, no sobjectType
- **Template**: `flexipage:defaultAppHomeTemplate`, region name: `main`

### 1c.14 Create App Page — Multi-Region with Tabs (Console)

- **Prompt**: Create two-column app page with tabset (Pipeline + Recent Accounts) + sidebar
- **Expected**: `flexipage:tabset` in main, rich text in sidebar

---

## Lightning Home Pages (1c.15–1c.16)

### 1c.15 Create Home Page — Simple

- **Prompt**: Create home page with assistant, tasks list view, report chart
- **Expected**: type=HomePage, no sobjectType
- **Template**: `home:desktopTemplate`, regions: top, bottomLeft, bottomRight, sidebar

### 1c.16 Create Home Page — Rich with Visibility Rules

- **Prompt**: Create three-column home page with visibility rule on performance chart
- **Expected**: Adapted to 4-region template (top, bottomLeft, bottomRight, sidebar)
- **Known issue**: `$Permission` syntax not supported; use `$User` fields. Only EQUAL operator works.

---

## Lightning Page Updates (1c.17–1c.20)

### 1c.17 Update Record Page — Add Component

- **Prompt**: Add Chatter feed to bottom of main column
- **Expected**: `metadata_update`, `forceChatter:recordFeedContainer` added, existing components preserved

### 1c.18 Update Record Page — Add Visibility Rule

- **Prompt**: Add visibility rule to path assistant (Amount > 50000)
- **Expected**: Adapted to EQUAL operator (e.g., StageName EQUAL "Closed Won")
- **Known issue**: GREATER_THAN operator unsupported

### 1c.19 Update App Page — Add Tab

- **Prompt**: Add third "Cases" tab to existing tabset
- **Expected**: `metadata_read` first to discover structure, then `metadata_update`

### 1c.20 Update Home Page — Replace Component

- **Prompt**: Replace sidebar report chart with Cases list view
- **Expected**: `metadata_read` first, chart removed, list view added in same position

---

## Error/Edge Cases (1c.21–1c.23)

### 1c.21 Clone Non-Existent Layout

- **Prompt**: Clone "NonExistent Layout" on Account
- **Expected**: `page_layout_clone` returns actionable error

### 1c.22 Invalid JSON Patch Path

- **Prompt**: Add field at `/layoutSections/99/layoutColumns/0/layoutItems/-`
- **Expected**: Error returned, layout unchanged
- **Known issue**: Error is generic JS runtime error, not a user-friendly message

### 1c.23 Duplicate FlexiPage Name

- **Prompt**: Create FlexiPage with same name as 1c.9
- **Expected**: `DUPLICATE_DEVELOPER_NAME` error, existing page unchanged

---

## Test Artifacts Created

| Type           | Name                          | Object      |
| -------------- | ----------------------------- | ----------- |
| Page Layout    | CirraTest Account Layout      | Account     |
| Page Layout    | CirraTest Case Support Layout | Case        |
| Lightning Page | CirraTest_Account_Record_Page | Account     |
| Lightning Page | CirraTest_Opp_Record_Page     | Opportunity |
| Lightning Page | CirraTest_Case_Record_Page    | Case        |
| Lightning Page | CirraTest_Contact_Record_Page | Contact     |
| Lightning Page | CirraTest_Dashboard_App_Page  | —           |
| Lightning Page | CirraTest_Sales_Console_Page  | —           |
| Lightning Page | CirraTest_Home_Page           | —           |
| Lightning Page | CirraTest_Sales_Home_Page     | —           |
