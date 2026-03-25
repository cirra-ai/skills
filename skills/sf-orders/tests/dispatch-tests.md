# sf-orders dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## check order status by order number

- **Input**: `/sf-orders order ORD-00123`
- **Dispatch**: Check Order Status
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `link_build`
- **Should NOT call**: `sobject_dml`, `tooling_api_query`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Input "ORD-00123" is not a Salesforce ID pattern (not 15/18 alphanumeric chars), so the whereClause must use `OrderNumber = 'ORD-00123'` rather than `Id = ...`. Two `soql_query` calls are expected: one for the Order record, one for OrderItems. Results are presented in a table with a `link_build` record link.

---

## check order status by salesforce id

- **Input**: `/sf-orders order 8013g000001AbCdEfG`
- **Dispatch**: Check Order Status
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `link_build`
- **Should NOT call**: `sobject_dml`, `tooling_api_query`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Input is 18 alphanumeric characters, matching the Salesforce ID pattern. The whereClause must use `Id = '8013g000001AbCdEfG'` and must NOT use an `Id OR OrderNumber` form (which causes MALFORMED_ID errors). Two `soql_query` calls follow: Order then OrderItems using the resolved Id.

---

## create return order

- **Input**: `/sf-orders return ORD-00456 reason=Defective`
- **Dispatch**: Create Return Order
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`, `link_build`
- **Should NOT call**: `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: yes (must confirm which line item(s) to return if multiple exist)
- **Follow-up skills**: `sf-flow`

**Notes**: Full multi-step workflow — verify order, get OrderItems, present items for selection if more than one, validate return quantity, then perform three `sobject_dml` calls: insert ReturnOrder (Draft), insert ReturnOrderLineItem, update ReturnOrder to Submitted. Verification queries follow. Rollback via delete DML if ReturnOrderLineItem insert fails.

---

## email return label — flow path

- **Input**: `/sf-orders return label RO-00789 customer@example.com`
- **Dispatch**: Email Return Label
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`, `sobject_dml`
- **Should NOT call**: `soql_query` (for order lookup — not needed here)
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Capability check includes `tooling_api_query` on FlowDefinition to detect `Send_Return_Label_Email`. If `HAS_RETURN_LABEL_FLOW = true` and `HAS_LABEL_TRACKING = true`, a `sobject_dml` update sets `LabelEmailSent__c = true` and `LabelEmailSentDate__c`. If the return order status is not "Approved" or "Partially Fulfilled", the skill must reject with a clear error. If `LabelEmailSent__c` is already true, the skill must reject with the prior send date.

---

## update case status

- **Input**: `/sf-orders case 00001234 status=Escalated reason="Customer complaint"`
- **Dispatch**: Update Case Status
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`, `link_build`
- **Should NOT call**: `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: "00001234" is not a Salesforce ID, so whereClause uses `CaseNumber = '00001234'`. Two `sobject_dml` calls: one to update Case status, one to insert CaseComment with audit trail (because a reason was provided). Business rules must be applied: IsClosed check and status transition validation (New → Escalated is valid per the transition table).

---

## no arguments — default menu

- **Input**: `/sf-orders`
- **Dispatch**: (no-args menu)
- **Init required**: yes
- **Init timing**: after-menu
- **Path**: n/a
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`
- **Should NOT call**: `soql_query`, `sobject_dml`, `tooling_api_query`
- **Should ask user**: yes (present menu of available operations)
- **Menu options**: Check Order Status, Create Return Order, Email Return Label, Update Case Status, Create Case from Return
- **Follow-up skills**: `sf-flow`

**Notes**: When invoked with no arguments, `cirra_ai_init` is called first to detect the org and capabilities. The skill then presents the menu of operations keyed to what is available (e.g., return options only shown if `HAS_RETURNS = true`). User selection drives which workflow runs next.

---

## create case from return — return already has a case (edge case)

- **Input**: `/sf-orders case from return RO-00111`
- **Dispatch**: Create Case from Return
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should NOT call**: `sobject_dml`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Edge case — the ReturnOrder queried in Step 1 has `CaseId` already populated. The skill must reject immediately with "A case already exists for this return order. Case ID: {CaseId}" and must not proceed to create a duplicate Case or update the ReturnOrder. No `sobject_dml` calls should be made. The ReturnOrderLineItem query (Step 2) and the linked Order query (Step 4) should also be skipped since validation fails at Step 3.
