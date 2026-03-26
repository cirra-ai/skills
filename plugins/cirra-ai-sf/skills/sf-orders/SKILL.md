---
name: sf-orders
plugin: cirra-ai-sf
argument-hint: '[order|return|case] ...'
metadata:
  version: 2.0.0
description: >
  Salesforce Order Management for managing orders, returns, and cases via the
  Cirra AI MCP Server. Use when users ask about order status, want to create
  return orders, send return labels, create or update support cases from returns,
  or manage the order-to-return-to-case lifecycle. Trigger for any mention of:
  order status, return order, return label, ReturnOrder, ReturnOrderLineItem,
  order management, RMA, shipping status, return request, case from return, or
  order-to-return workflows.
  Usage: /sf-orders [order|return|case] {details}
---

# Salesforce Order Management Expert

Manage orders, returns, and support cases in Salesforce using the Cirra AI MCP Server. Covers the full order-to-return-to-case lifecycle using standard Salesforce objects (Order, ReturnOrder, ReturnOrderLineItem, Case).

## Dispatch

Parse `$ARGUMENTS` to determine the operation:

| First argument or intent                  | Workflow                 |
| ----------------------------------------- | ------------------------ |
| `order`, order status, order details      | Order Status             |
| `return`, return order, RMA, return label | Return Management        |
| `case`, support case, case from return    | Case Management          |
| _(no argument or unclear)_                | Ask the user (see below) |

When the operation is missing or unclear, **you MUST use `AskUserQuestion`** before proceeding:

```
AskUserQuestion(question="What would you like to do?\n\n1. **Order** — query order status and details\n2. **Return** — create a return order or send a return label\n3. **Case** — create or update a support case")
```

Do NOT guess the operation or default to one. Wait for the user's answer.

---

## Core Responsibilities

1. **Order Status**: Query order details and line items
2. **Return Creation**: Create ReturnOrder with line items from an existing Order
3. **Return Label Email**: Send return shipping label to customer (flow preferred; Task fallback)
4. **Case Management**: Create and update support cases linked to returns

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

Use `sobject_describe` on each required object to verify it exists. Call `sobject_describe` for `Order`, `ReturnOrder`, and `Case`. If the call succeeds, the object is available; if it returns an error (object not found), the object is not available in this org.

Set capability flags:

- `HAS_ORDERS = true` if `sobject_describe(sObject="Order")` succeeds
- `HAS_RETURNS = true` if `sobject_describe(sObject="ReturnOrder")` succeeds
- `HAS_CASES = true` if `sobject_describe(sObject="Case")` succeeds (almost always true)

If ReturnOrder is missing, inform the user that return operations are unavailable because Order Management / Service Cloud is not enabled. The skill can still handle order status checks and general case management.

### Step 2: Check for return label infrastructure (if HAS_RETURNS = true)

Use `sobject_describe` on `ReturnOrder` and look for `LabelEmailSent__c` (Checkbox) and `LabelEmailSentDate__c` (DateTime).

- `HAS_LABEL_TRACKING = true` if both fields exist

Then check for the return label flow using `tooling_api_query`:

- sObject: `FlowDefinition`
- whereClause: `DeveloperName = 'Send_Return_Label_Email' AND ActiveVersionId != null`

- `HAS_RETURN_LABEL_FLOW = true` if the query returns a result with an active version

If the flow doesn't exist and the user needs email functionality, see `references/metadata-setup.md`.

### Capability Summary

| Operation               | Requires                                               |
| ----------------------- | ------------------------------------------------------ |
| Check Order Status      | HAS_ORDERS                                             |
| Create Return           | HAS_ORDERS + HAS_RETURNS                               |
| Email Return Label      | HAS_RETURNS (flow preferred; Task fallback if no flow) |
| Update Case Status      | HAS_CASES                                              |
| Create Case from Return | HAS_RETURNS + HAS_CASES                                |

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

For DML operations, use `sobject_dml` with `sObject`, `operation` (insert/update/delete/upsert), and `records` array. For delete operations, use `recordIds` (string array of IDs) instead of `records`.

**IMPORTANT — Resolved IDs**: When a lookup query accepts both an ID and a human-readable number (e.g., `Id OR OrderNumber`), always use the `Id` returned from the query result for all subsequent operations (DML, child queries, updates). Never pass raw user input (which may be a number, not an ID) into DML or relationship queries.

**IMPORTANT — Input format detection**: Before constructing a whereClause that accepts user input, detect whether the input is a Salesforce ID (15 or 18 alphanumeric characters) or a human-readable number/string. Using `Id = '{value}' OR SomeNumber = '{value}'` causes a `MALFORMED_ID` error when the value is not a valid ID format because Salesforce validates the Id field before evaluating the OR. Instead:

- If input matches a Salesforce ID pattern (15 or 18 alphanumeric chars): use `Id = '{value}'`
- Otherwise: use the number/name field only (e.g., `OrderNumber = '{value}'`)

---

## 1. Check Order Status

When a user asks about an order's status, shipping, or details:

### Query the order

The user may provide a Salesforce ID (15/18 chars) or an OrderNumber. Detect the input format (see Tool Usage Notes) and use the appropriate whereClause.

Use `soql_query`:

- sObject: `Order`
- fields: `["Id", "OrderNumber", "Status", "TotalAmount", "AccountId", "Account.Name", "EffectiveDate", "EndDate", "Description", "Type"]`
- whereClause: `Id = '{orderId}'` (if ID format) or `OrderNumber = '{orderId}'` (if number format)
- orderBy: `OrderNumber`
- groupBy: ``
- limit: `1`

### Query line items

Use the Order `Id` from the query result above (not the raw user input).

Use `soql_query`:

- sObject: `OrderItem`
- fields: `["Id", "OrderId", "Product2.Name", "Quantity", "UnitPrice", "TotalPrice", "Description"]`
- whereClause: `OrderId = '{order.Id}'`
- orderBy: `CreatedDate ASC`
- groupBy: ``
- limit: `200`

### Present results

- Order Number, Status, Total Amount
- Account name
- Line items in table format (Product, Quantity, Unit Price, Total)
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
- whereClause: `Id = '{orderId}'` (if ID format) or `OrderNumber = '{orderId}'` (if number format)
- orderBy: ``
- groupBy: ``
- limit: `1`

**Step 2: Get order line items** (use the Order `Id` from Step 1, not raw user input).

Use `soql_query`:

- sObject: `OrderItem`
- fields: `["Id", "OrderId", "Product2Id", "Product2.Name", "Quantity", "UnitPrice", "TotalPrice"]`
- whereClause: `OrderId = '{order.Id}'`
- orderBy: `CreatedDate ASC`
- groupBy: ``
- limit: `200`

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
- recordIds: `["<return_order_id>"]`

### Verification

Query the created return order using `soql_query`:

- sObject: `ReturnOrder`
- fields: `["Id", "ReturnOrderNumber", "Status", "Description", "AccountId", "OrderId"]`
- whereClause: `Id = '{return_order_id}'`
- orderBy: ``
- groupBy: ``
- limit: `1`

Then query line items separately:

- sObject: `ReturnOrderLineItem`
- fields: `["Id", "Product2.Name", "QuantityReturned", "Description"]`
- whereClause: `ReturnOrderId = '{return_order_id}'`
- orderBy: ``
- groupBy: ``
- limit: `200`

Present results with the return order number, status, and a link to the record.

---

## 3. Email Return Label

When a user wants to send a return shipping label to a customer:

### Prerequisites

- `HAS_RETURNS` must be true
- The ReturnOrder must be in "Approved" or "Partially Fulfilled" status
- If `HAS_LABEL_TRACKING = true`, check that the label hasn't already been sent

### Validation

**Step 1: Verify the return order.**

Use `soql_query`:

- sObject: `ReturnOrder`
- fields: `["Id", "ReturnOrderNumber", "OrderId", "Status", "Description"]` (add `LabelEmailSent__c, LabelEmailSentDate__c` if `HAS_LABEL_TRACKING = true`)
- whereClause: `Id = '{returnOrderId}'` (if ID format) or `ReturnOrderNumber = '{returnOrderId}'` (if number format)
- orderBy: ``
- groupBy: ``
- limit: `1`

**Step 2: Business validation:**

- Status must be "Approved" or "Partially Fulfilled"
- If `LabelEmailSent__c = true`, reject: "Return label already sent on {date}"
- Validate email format

### Send the Label

If `HAS_RETURN_LABEL_FLOW = true`, the flow should be triggered. Since the Cirra AI MCP doesn't have a direct "run flow" tool, guide the user to trigger the flow manually or use `tooling_api_dml`.

If `HAS_LABEL_TRACKING = true` and the flow was triggered successfully, update the tracking fields:

Use `sobject_dml`:

- sObject: `ReturnOrder`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "{returnOrder.Id}",
      "LabelEmailSent__c": true,
      "LabelEmailSentDate__c": "<current_datetime_ISO>"
    }
  ]
  ```

If `HAS_RETURN_LABEL_FLOW = false`, create a Task record as a fallback so the label can be sent manually. Do **not** update `LabelEmailSent__c` — no email has actually been sent yet.

Use the ReturnOrder `Id` and `ReturnOrderNumber` from the Step 1 query result for all fields below.

Use `sobject_dml`:

- sObject: `Task`
- operation: `insert`
- records:
  ```json
  [
    {
      "Subject": "Send Return Label - {returnOrder.ReturnOrderNumber}",
      "Description": "Send return shipping label to {customerEmail} for return order {returnOrder.ReturnOrderNumber}",
      "Status": "Not Started",
      "Priority": "High",
      "WhatId": "{returnOrder.Id}",
      "ActivityDate": "<today>"
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
- whereClause: `Id = '{caseId}'` (if ID format) or `CaseNumber = '{caseId}'` (if number format)
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

Use the Case `Id` from the Step 1 query result (not the raw user input, which may be a CaseNumber).

Use `sobject_dml`:

- sObject: `Case`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "{case.Id}",
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
      "ParentId": "{case.Id}",
      "CommentBody": "Status changed from {previousStatus} to {newStatus}. Reason: {reason}",
      "IsPublished": false
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
- whereClause: `Id = '{returnOrderId}'` (if ID format) or `ReturnOrderNumber = '{returnOrderId}'` (if number format)
- orderBy: ``
- groupBy: ``
- limit: `1`

**Step 2: Get return line items** (use the ReturnOrder `Id` from Step 1, not raw user input).

Use `soql_query`:

- sObject: `ReturnOrderLineItem`
- fields: `["Id", "Product2Id", "Product2.Name", "QuantityReturned", "Description"]`
- whereClause: `ReturnOrderId = '{returnOrder.Id}'`
- orderBy: ``
- groupBy: ``
- limit: `200`

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

**Link the case back to the return order** (use the ReturnOrder `Id` from Step 1):

Use `sobject_dml`:

- sObject: `ReturnOrder`
- operation: `update`
- records:
  ```json
  [
    {
      "Id": "{returnOrder.Id}",
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

- Use the `sf-flow` skill to create a notification flow
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
