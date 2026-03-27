# sf-orders dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## check order status by order number

- **Input**: `/sf-orders order ORD-00123`
- **Dispatch**: Order Status
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
- **Dispatch**: Order Status
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
- **Dispatch**: Return Management
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
- **Dispatch**: Return Management
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`, `sobject_dml`
- **Should NOT call**: `link_build`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Capability check includes `tooling_api_query` on FlowDefinition to detect `Send_Return_Label_Email`. If `HAS_RETURN_LABEL_FLOW = true` and `HAS_LABEL_TRACKING = true`, a `sobject_dml` update sets `LabelEmailSent__c = true` and `LabelEmailSentDate__c`. If the return order status is not "Approved" or "Partially Fulfilled", the skill must reject with a clear error. If `LabelEmailSent__c` is already true, the skill must reject with the prior send date.

---

## update case status

- **Input**: `/sf-orders case 00001234 status=Escalated reason="Customer complaint"`
- **Dispatch**: Case Management
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
- **Init timing**: before-menu (init needed for capability detection before presenting menu)
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
- **Dispatch**: Case Management
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

---

## create case from return — happy path

- **Input**: `/sf-orders case from return RO-00222`
- **Dispatch**: Case Management
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`, `link_build`
- **Should NOT call**: `tooling_api_dml`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Happy path for creating a case from a return order (existing edge case test covers the duplicate rejection). Should query ReturnOrder, ReturnOrderLineItem, and linked Order, then create a Case via `sobject_dml` and link it back to the ReturnOrder. Priority is derived from return reason (Defective → High). "RO-00222" is not a Salesforce ID — use `ReturnOrderNumber` in the whereClause.

---

## return with single line item auto-detect

- **Input**: `/sf-orders return ORD-00789`
- **Dispatch**: Return Management
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`, `link_build`
- **Should NOT call**: `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: yes (need return reason and quantity; may skip line item selection if only one exists)
- **Follow-up skills**: `sf-flow`

**Notes**: `return` keyword routes to Create Return Order. No line item or reason specified — must ask for reason and quantity. Per SKILL.md: "If there's only one item, or the user says 'auto-detect', use the first item." Should query OrderItems and if only one exists, auto-select it but still ask for return reason.

---

## natural language — I need to return an item

- **Input**: `/sf-orders I need to return a defective item from order ORD-00345`
- **Dispatch**: Return Management
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`, `link_build`
- **Should NOT call**: `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: yes (which specific item to return if multiple exist)
- **Follow-up skills**: `sf-flow`

**Notes**: Natural language with "return" intent and "defective" reason. Should route to Create Return Order. The reason (Defective) is embedded in the request. "ORD-00345" is not a Salesforce ID — use `OrderNumber` in whereClause. Should still ask which line item if multiple exist.

---

## case with invalid status transition

- **Input**: `/sf-orders case 00005678 status=Working`
- **Dispatch**: Case Management
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `fast`
- **First tool**: `cirra_ai_init`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should NOT call**: `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: If the case is currently in "Escalated" status, transitioning to "Working" is valid per the status transition table. But if the case is "Closed", the transition to "Working" is invalid (closed cases cannot be reopened). The skill must query the case first, check `IsClosed`, and reject with an appropriate error if the case is closed. This tests the business rule validation path.

---

## email return label — task fallback path

- **Input**: `/sf-orders return label RO-00999 customer@test.com`
- **Dispatch**: Return Management
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`, `sobject_dml`
- **Should NOT call**: `link_build`
- **Should ask user**: no
- **Follow-up skills**: `sf-flow`

**Notes**: Tests the fallback path when `HAS_RETURN_LABEL_FLOW = false`. The `tooling_api_query` on FlowDefinition returns no active flow. Should fall back to creating a Task record via `sobject_dml` with high priority. Must NOT update `LabelEmailSent__c` since no email was actually sent — only the flow path updates that field.
