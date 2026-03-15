---
name: cirra-ai-sf-ordermgt
metadata:
  version: 1.0.0
description: >
  Salesforce Order Management for managing orders, returns, and cases via the
  Cirra AI MCP Server. Use when users ask about order status, want to create
  return orders, send return labels, create or update support cases from returns,
  or manage the order-to-return-to-case lifecycle. Automatically detects whether
  the Kugamon (kugo2p) package is installed and enriches order data with quote
  context. Trigger for any mention of: order status, return order, return label,
  ReturnOrder, ReturnOrderLineItem, order management, RMA, shipping status,
  return request, case from return, or order-to-return workflows.
---

# cirra-ai-sf-ordermgt: Order Management with Cirra AI

Manage orders, returns, and support cases in Salesforce using the Cirra AI MCP Server. Covers the full order-to-return-to-case lifecycle using standard Salesforce objects (Order, ReturnOrder, ReturnOrderLineItem, Case).

## Core Responsibilities

1. **Order Status**: Query order details, line items, and related quotes
2. **Return Creation**: Create ReturnOrder with line items from an existing Order
3. **Return Label Email**: Send return shipping label to customer (requires flow)
4. **Case Management**: Create and update support cases linked to returns
5. **Kugamon Integration**: Enrich order data with Kugamon quote context when installed

---

## Phase 1: Initialization & Capability Detection

**FIRST**: Call `cirra_ai_init()` with no parameters:

```
cirra_ai_init()
```

- If a default org is configured, proceed immediately and confirm with the user:
  > "I've connected to **[org]**. Would you like me to use the defaults, or do you want to select different options?"
- If no default is configured, ask for the Salesforce user/alias before proceeding.

Do **not** ask for org details before calling `cirra_ai_init()`.

**THEN**: Detect available objects and packages.

### Step 1: Check which objects are available

Use `soql_query`:

- sObject: `EntityDefinition`
- fields: `["QualifiedApiName", "Label", "IsQueryable"]`
- whereClause: `QualifiedApiName IN ('Order', 'OrderItem', 'ReturnOrder', 'ReturnOrderLineItem', 'Case', 'CaseComment')`
- orderBy: ``
- groupBy: ``

Set capability flags:

- `HAS_ORDERS = true` if Order and OrderItem are present
- `HAS_RETURNS = true` if ReturnOrder and ReturnOrderLineItem are present
- `HAS_CASES = true` if Case is present (almost always true)

If ReturnOrder is missing, inform the user that return operations are unavailable because Order Management / Service Cloud is not enabled. The skill can still handle order status checks and general case management.

### Step 2: Detect Kugamon package

Use `sobject_describe` on `Order` and look for any `kugo2p__*` fields.

- `HAS_KUGAMON = true` if any `kugo2p__` prefixed fields exist
- `HAS_KUGAMON = false` if they do not

**When `HAS_KUGAMON = true`:** Order data is enriched with Kugamon quote context. For quote creation, modification, or amount interpretation, **delegate to the `cirra-ai-sf-kugamon` skill** — do not duplicate that logic here.

### Step 3: Check for return label infrastructure (if HAS_RETURNS = true)

Use `sobject_describe` on `ReturnOrder` and look for `LabelEmailSent__c` (Checkbox) and `LabelEmailSentDate__c` (DateTime).

- `HAS_LABEL_TRACKING = true` if both fields exist

Then check for the return label flow using `soql_query`:

- sObject: `FlowDefinitionView`
- fields: `["Id", "ApiName", "Label", "ProcessType"]`
- whereClause: `ApiName = 'Send_Return_Label_Email' AND IsActive = true`
- orderBy: ``
- groupBy: ``

- `HAS_RETURN_LABEL_FLOW = true` if the flow exists and is active

If the flow doesn't exist and the user needs email functionality, see `references/metadata-setup.md`.

### Capability Summary

| Operation               | Requires                            |
| ----------------------- | ----------------------------------- |
| Check Order Status      | HAS_ORDERS                          |
| Create Return           | HAS_ORDERS + HAS_RETURNS            |
| Email Return Label      | HAS_RETURNS + HAS_RETURN_LABEL_FLOW |
| Update Case Status      | HAS_CASES                           |
| Create Case from Return | HAS_RETURNS + HAS_CASES             |

---

## Tool Usage Notes

The Cirra AI MCP Server's `soql_query` tool requires structured parameters, not raw SOQL strings. Always provide:

- `sObject` — the object API name
- `fields` — array of field names (relationship fields like `Account.Name` are supported)
- `whereClause` — the WHERE condition (without the `WHERE` keyword)
- `orderBy` — ORDER BY clause (pass empty string `""` if not needed)
- `groupBy` — GROUP BY clause (pass empty string `""` if not needed)
- `limit` — max records to return

The tool does **not** support subqueries in the `fields` array. To get child records (e.g., OrderItems for an Order), run a separate query on the child object with a WHERE filter on the parent ID.

For DML operations, use `sobject_dml` with `sObject`, `operation` (insert/update/delete), and `records` array.

---

## 1. Check Order Status

When a user asks about an order's status, shipping, or details:

### Query the order

The user may provide a Salesforce ID (15/18 chars) or an OrderNumber. Handle both.

Use `soql_query`:

- sObject: `Order`
- fields: `["Id", "OrderNumber", "Status", "TotalAmount", "AccountId", "Account.Name", "EffectiveDate", "EndDate", "Description", "Type"]`
- whereClause: `Id = '{orderId}' OR OrderNumber = '{orderId}'`
- orderBy: `OrderNumber`
- groupBy: ``
- limit: `1`

If not found by combined clause, try OrderNumber only: `OrderNumber = '{orderId}'`

### Query line items

Use `soql_query`:

- sObject: `OrderItem`
- fields: `["Id", "OrderId", "Product2.Name", "Quantity", "UnitPrice", "TotalPrice", "Description"]`
- whereClause: `OrderId = '{orderId_from_result}'`
- orderBy: `CreatedDate ASC`
- groupBy: ``

### Kugamon enrichment (if HAS_KUGAMON = true)

Query related Kugamon quotes for additional context:

Use `soql_query`:

- sObject: `kugo2p__SalesQuote__c`
- fields: `["Id", "Name", "kugo2p__QuoteName__c", "kugo2p__TotalAmount__c", "kugo2p__Status__c", "kugo2p__IsPrimary__c"]`
- whereClause: `kugo2p__Opportunity__r.Id IN (SELECT OpportunityId FROM Order WHERE Id = '{orderId}')`
- orderBy: `CreatedDate DESC`
- groupBy: ``

If the subquery approach fails (tool limitation), use a two-step approach:

1. Query the Order to get the related OpportunityId (if the field exists)
2. Query `kugo2p__SalesQuote__c` where `kugo2p__Opportunity__c = '{opportunityId}'`

Present the Kugamon quote context alongside order details when available.

### Present results

- Order Number, Status, Total Amount
- Account name
- Line items in table format (Product, Quantity, Unit Price, Total)
- Kugamon quote summary (if available): Quote number, quote total, primary status
- Links to records using `link_build`

---

## 2. Create Return Order

When a user wants to return items from an order:

### Discovery Phase

Gather requirements:

- Which order? (ID or order number)
- Which line item(s) to return? (specific item or auto-detect first item)
- Return reason: Defective, Damaged, Wrong Item, Not Needed, Quality Issue, Size/Color, Other
- Quantity to return
- Optional description

### Pre-Creation Validation

**Step 1: Verify the order exists and get its details.**

Use `soql_query`:

- sObject: `Order`
- fields: `["Id", "OrderNumber", "Status", "AccountId", "Account.Name", "TotalAmount"]`
- whereClause: `Id = '{orderId}' OR OrderNumber = '{orderId}'`
- orderBy: ``
- groupBy: ``
- limit: `1`

**Step 2: Get order line items.**

Use `soql_query`:

- sObject: `OrderItem`
- fields: `["Id", "OrderId", "Product2Id", "Product2.Name", "Quantity", "UnitPrice", "TotalPrice"]`
- whereClause: `OrderId = '{orderId}'`
- orderBy: `CreatedDate ASC`
- groupBy: ``

If the user didn't specify a line item, present available items and ask which one(s) to return. If there's only one item, or the user says "auto-detect", use the first item.

**Step 3: Validate return quantity** — cannot exceed original order quantity.

### Create the Return

**Step 1: Create the ReturnOrder** using `sobject_dml`:

- sObject: `ReturnOrder`
- operation: `insert`
- records:
  ```json
  [
    {
      "OrderId": "<original_order_id>",
      "AccountId": "<account_id_from_order>",
      "Status": "Draft",
      "Description": "Return for Order Item <line_item_id> - <reason>"
    }
  ]
  ```

**Step 2: Create the ReturnOrderLineItem** using `sobject_dml`:

- sObject: `ReturnOrderLineItem`
- operation: `insert`
- records:
  ```json
  [
    {
      "ReturnOrderId": "<return_order_id_from_step1>",
      "OrderItemId": "<line_item_id>",
      "Product2Id": "<product_id_from_order_item>",
      "QuantityReturned": "<quantity>",
      "Description": "Return <quantity> unit(s) - <reason>"
    }
  ]
  ```

**Step 3: Update ReturnOrder status to Submitted** using `sobject_dml`:

- sObject: `ReturnOrder`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "<return_order_id>",
      "Status": "Submitted"
    }
  ]
  ```

**Rollback on failure:** If ReturnOrderLineItem creation fails, delete the ReturnOrder:

- sObject: `ReturnOrder`
- operation: `delete`
- records: `[{"Id": "<return_order_id>"}]`

### Verification

Query the created return order using `soql_query`:

- sObject: `ReturnOrder`
- fields: `["Id", "ReturnOrderNumber", "Status", "Description", "AccountId", "OrderId"]`
- whereClause: `Id = '{return_order_id}'`
- orderBy: ``
- groupBy: ``

Then query line items separately:

- sObject: `ReturnOrderLineItem`
- fields: `["Id", "Product2.Name", "QuantityReturned", "Description"]`
- whereClause: `ReturnOrderId = '{return_order_id}'`
- orderBy: ``
- groupBy: ``

Present results with the return order number, status, and a link to the record.

---

## 3. Email Return Label

When a user wants to send a return shipping label to a customer:

### Prerequisites

- `HAS_RETURN_LABEL_FLOW` must be true
- The ReturnOrder must be in "Approved" or "Partially Fulfilled" status
- If `HAS_LABEL_TRACKING = true`, check that the label hasn't already been sent

### Validation

**Step 1: Verify the return order.**

Use `soql_query`:

- sObject: `ReturnOrder`
- fields: `["Id", "ReturnOrderNumber", "OrderId", "Status", "Description"]` (add `LabelEmailSent__c, LabelEmailSentDate__c` if `HAS_LABEL_TRACKING = true`)
- whereClause: `Id = '{returnOrderId}' OR ReturnOrderNumber = '{returnOrderId}'`
- orderBy: ``
- groupBy: ``
- limit: `1`

**Step 2: Business validation:**

- Status must be "Approved" or "Partially Fulfilled"
- If `LabelEmailSent__c = true`, reject: "Return label already sent on {date}"
- Validate email format

### Send the Label

If `HAS_RETURN_LABEL_FLOW = true`, the flow should be triggered. Since the Cirra AI MCP doesn't have a direct "run flow" tool, guide the user to trigger the flow manually or use `tooling_api_dml`.

**Alternative approach (if no flow exists):** Create a Task record as a reminder:

Use `sobject_dml`:

- sObject: `Task`
- operation: `insert`
- records:
  ```json
  [
    {
      "Subject": "Send Return Label - {returnOrderNumber}",
      "Description": "Send return shipping label to {customerEmail} for return order {returnOrderNumber}",
      "Status": "Open",
      "Priority": "High",
      "WhatId": "{returnOrderId}",
      "ActivityDate": "<today>"
    }
  ]
  ```

If `HAS_LABEL_TRACKING = true`, update the tracking fields:

Use `sobject_dml`:

- sObject: `ReturnOrder`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "{returnOrderId}",
      "LabelEmailSent__c": true,
      "LabelEmailSentDate__c": "<current_datetime_ISO>"
    }
  ]
  ```

---

## 4. Update Case Status

When a user wants to update a support case:

### Validation

**Step 1: Verify the case exists.**

Use `soql_query`:

- sObject: `Case`
- fields: `["Id", "CaseNumber", "Status", "Priority", "OwnerId", "Owner.Name", "Subject", "Description", "IsClosed", "AccountId", "Account.Name"]`
- whereClause: `Id = '{caseId}' OR CaseNumber = '{caseId}'`
- orderBy: ``
- groupBy: ``
- limit: `1`

**Step 2: Apply business rules:**

- If `IsClosed = true` and new status is not "Closed", reject: "Cannot reopen a closed case. Please create a new case instead."
- If current status equals requested status, inform: "Case is already in {status} status."
- Validate status transition (see `references/status-transitions.md`)

### Status Transition Rules (Quick Reference)

| Current Status | Allowed Transitions        |
| -------------- | -------------------------- |
| New            | Working, Escalated, Closed |
| Working        | Escalated, Closed          |
| Escalated      | Working, Closed            |
| Closed         | (none — cannot reopen)     |

### Apply the Update

Use `sobject_dml`:

- sObject: `Case`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "{caseId}",
      "Status": "{newStatus}"
    }
  ]
  ```

Add optional fields if provided: `Priority`, `OwnerId` (resolve user first via soql_query on User).

**Create audit trail** if a reason was provided:

Use `sobject_dml`:

- sObject: `CaseComment`
- operation: `insert`
- records:
  ```json
  [
    {
      "ParentId": "{caseId}",
      "CommentBody": "Status changed from {previousStatus} to {newStatus}. Reason: {reason}",
      "IsPublished": true
    }
  ]
  ```

Present results with the updated case number, new status, and a link.

---

## 5. Create Case from Return

When a user wants to create a support case linked to a return order:

### Validation

**Step 1: Get the return order.**

Use `soql_query`:

- sObject: `ReturnOrder`
- fields: `["Id", "ReturnOrderNumber", "OrderId", "Status", "Description", "AccountId", "Account.Name", "CaseId"]`
- whereClause: `Id = '{returnOrderId}' OR ReturnOrderNumber = '{returnOrderId}'`
- orderBy: ``
- groupBy: ``
- limit: `1`

**Step 2: Get return line items.**

Use `soql_query`:

- sObject: `ReturnOrderLineItem`
- fields: `["Id", "Product2Id", "Product2.Name", "QuantityReturned", "Description"]`
- whereClause: `ReturnOrderId = '{returnOrderId}'`
- orderBy: ``
- groupBy: ``

**Step 3: Business validation:**

- If `CaseId` is already populated, reject: "A case already exists for this return order. Case ID: {CaseId}"
- Status must be "Submitted", "Approved", or "Partially Fulfilled"

**Step 4: Get order details for context.**

Use `soql_query`:

- sObject: `Order`
- fields: `["Id", "OrderNumber", "AccountId", "Account.Name", "TotalAmount"]`
- whereClause: `Id = '{orderId_from_return}'`
- orderBy: ``
- groupBy: ``
- limit: `1`

### Create the Case

**Determine priority** based on return line item descriptions:

- Defective, Damaged, or Quality Issue → **High**
- All others → **Medium**

Use `sobject_dml`:

- sObject: `Case`
- operation: `insert`
- records:
  ```json
  [
    {
      "Subject": "Return Order Issue - {ReturnOrderNumber}",
      "Description": "Case created for return order {ReturnOrderNumber}.\n\nOrder: {OrderNumber}\nReturn Status: {Status}\nReturn Description: {Description}\n\nReturning Items:\n1. {Product Name} (Qty: {QuantityReturned}) - {Description}",
      "Status": "New",
      "Priority": "<determined_priority>",
      "Origin": "Web",
      "Type": "Other",
      "AccountId": "{accountId_from_order}"
    }
  ]
  ```

**Link the case back to the return order:**

Use `sobject_dml`:

- sObject: `ReturnOrder`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "{returnOrderId}",
      "CaseId": "{new_case_id}"
    }
  ]
  ```

Note: The CaseId field on ReturnOrder is a standard field. If the update fails (field not available), log the warning but don't fail — the case was still created.

### Present Results

- Case number and ID with link
- Priority level
- Return order number with link
- Summary of items being returned in table format

---

## 6. Notifications (Optional)

Slack webhook alerts and other external notifications are not handled by the Cirra AI MCP Server directly. If the user needs notification workflows:

- Use the `cirra-ai-sf-flow` skill to create a notification flow
- Platform Events or Custom Notifications are native Salesforce alternatives

---

## Presenting Results

For all operations, follow these patterns:

**Always include:**

- Record IDs and human-readable numbers (OrderNumber, ReturnOrderNumber, CaseNumber)
- Links to records using `link_build`
- Status information
- Summary tables for line items

**Table format for order items:**

```
| # | Product | Quantity | Unit Price | Total |
|---|---------|----------|------------|-------|
```

**Table format for return items:**

```
| # | Product | Qty Returned | Description |
|---|---------|-------------|-------------|
```

---

## Kugamon Integration Details

When `HAS_KUGAMON = true`:

- **Order Status queries** include Kugamon quote context (quote number, total, status)
- **Quote creation/modification** is handled by the `cirra-ai-sf-kugamon` skill — do not duplicate. If the user asks to create a quote from an order, delegate to `cirra-ai-sf-kugamon`.
- **Amount interpretation** follows Kugamon conventions (MRR vs ACV vs TCV). Refer the user to `cirra-ai-sf-kugamon` for amount field analysis.
- **Order-to-Quote tracing** uses the Opportunity as the link: Order → OpportunityId → `kugo2p__SalesQuote__c.kugo2p__Opportunity__c`

When `HAS_KUGAMON = false`:

- Order data comes from standard objects only
- No quote enrichment is available
- Amount fields use standard Salesforce interpretation

---

## When to Load References

- **field-reference.md**: When troubleshooting field errors, understanding object relationships, or needing the full list of available fields on Order, ReturnOrder, or Case
- **metadata-setup.md**: When the org is missing required custom fields or flows and they need to be deployed
- **status-transitions.md**: When dealing with complex status validation across ReturnOrder and Case lifecycles

## Common Issues

**ReturnOrder object not found:**
The org needs Service Cloud or Order Management enabled. ReturnOrder is a standard object but requires specific licenses.

**Cannot create ReturnOrderLineItem — OrderItemId not valid:**
Verify the OrderItem belongs to the Order referenced by the ReturnOrder. Query OrderItems where OrderId matches.

**ReturnOrder status won't change to "Submitted":**
Check if there are validation rules or process builders that prevent the transition. Some orgs require line items before status can change.

**CaseId field not available on ReturnOrder:**
Standard field but may not be visible in all editions. The case is still created; just the link back won't be set. The user can create a custom lookup if needed.

**Return quantity exceeds original order quantity:**
Query the OrderItem to get the original Quantity and validate before creating the return.

**Kugamon quote totals don't match order totals:**
Delegate amount interpretation to `cirra-ai-sf-kugamon`. In subscription orgs, `Amount` may show MRR while quotes show ACV.
