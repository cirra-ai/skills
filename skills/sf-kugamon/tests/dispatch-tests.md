# sf-kugamon dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## quote — create quote for an opportunity

- **Input**: `/sf-kugamon quote for opportunity 006Xx000001abcdEAA`
- **Dispatch**: Quote Creation
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`
- **Should NOT call**: `sobject_create` (that tool is for metadata, not data records)
- **Should ask user**: yes (confirm org if default is set; select billing contact from account contacts)
- **Menu options**: n/a
- **Follow-up skills**: `sf-kugamon`

**Notes**: Full quote creation path. After `cirra_ai_init`, the skill detects kuga_sub via `sobject_describe` on `OpportunityLineItem`. It then runs pre-creation checks (billing address and contact validation via `soql_query`), queries the opportunity, checks for existing quotes, and creates the quote via `sobject_dml` with `operation: "insert"`. If HAS_KUGA_SUB is true, also queries `kuga_sub__KugamonSettings__c` to set HAS_SUB_MGMT.

---

## order — release order and trigger subscription lifecycle

- **Input**: `/sf-kugamon order release 801Xx000001abcdEAA`
- **Dispatch**: Order Release Lifecycle
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`
- **Should NOT call**: `sobject_create` (metadata tool, not for data records)
- **Should ask user**: no
- **Menu options**: n/a
- **Follow-up skills**: `sf-kugamon`

**Notes**: Targets the Order Release Lifecycle workflow. Requires HAS_SUB_MGMT = true. The skill checks `kuga_sub__KugamonSettings__c` for `kuga_sub__InitiateOrderSubscriptionManagement__c`, then manages Contract creation/amendment, Asset creation, Subscription creation, and Renewal Opportunity generation based on the Order's Record Type (New, Expansion, or Renewal). `sobject_dml` with `operation: "update"` is used to set the order to Released status.

---

## contract — check and manage an existing contract

- **Input**: `/sf-kugamon contract 800Xx000001abcdEAA check status`
- **Dispatch**: Order Release Lifecycle
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should NOT call**: `sobject_create`, `sobject_dml`
- **Should ask user**: no
- **Menu options**: n/a
- **Follow-up skills**: `sf-kugamon`

**Notes**: Routes to the Order Release Lifecycle workflow for contract management. The skill queries `kuga_sub__KugamonSettings__c` to confirm Subscription Management is active, then retrieves the Contract record and linked Order details via `soql_query`. No mutations expected for a status check; the skill should report Contract state, associated Assets, Subscriptions, and whether `kuga_sub__ExtendContractOnRenewal__c` affects future renewal behavior.

---

## renewal — create renewal quote from existing subscription

- **Input**: `/sf-kugamon renewal opportunity 006Xx000009zzzzEAA`
- **Dispatch**: Quote Creation
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`
- **Should NOT call**: `sobject_create` (metadata tool, not for data records)
- **Should ask user**: yes (confirm contact and billing address before quote creation)
- **Menu options**: n/a
- **Follow-up skills**: `sf-kugamon`

**Notes**: Renewal quotes follow the same Quote Creation workflow but require RecordTypeId mapped to the Renewal record type (see references/record-types.md). The skill must set `kugo2p__IsPrimary__c` appropriately, check for existing quotes on the opportunity, and verify the Order's `Contract Number` field is populated before Order Release. With HAS_KUGA_SUB = true, line items should have `kuga_sub__Renew__c = true` for recurring services.

---

## subscription — inspect subscription records and MRR/ARR fields

- **Input**: `/sf-kugamon subscription for account 001Xx000003abcdEAA`
- **Dispatch**: Subscription Management
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should NOT call**: `sobject_create`, `sobject_dml`
- **Should ask user**: no
- **Menu options**: n/a
- **Follow-up skills**: `sf-kugamon`

**Notes**: Routes to Subscription Management. The skill verifies HAS_KUGA_SUB = true (kuga_sub package present) and HAS_SUB_MGMT = true before querying subscription records. Reads `kuga_sub__MonthlyRecurringRevenue__c`, `kuga_sub__AnnualRecurringRevenueCommitted__c`, and `kuga_sub__TotalContractValue__c` fields from the Opportunity. Reports all amount fields; instructs user to ignore the raw `Amount` field and use `kuga_sub__OpportunityAmount__c` as the true opportunity value.

---

## no arguments — user provides no hint

- **Input**: `/sf-kugamon`
- **Dispatch**: (none — present menu)
- **Init required**: yes
- **Init timing**: before-menu (init needed before presenting menu — SKILL.md says "do not ask for org details before calling cirra_ai_init")
- **Path**: n/a
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none)`
- **Should call**: `cirra_ai_init`, `sobject_describe`
- **Should NOT call**: `sobject_create`, `sobject_dml`
- **Should ask user**: yes (no context provided; skill must ask what the user wants to do)
- **Menu options**: Create a quote, Manage an order/contract, Check subscriptions/renewals, Verify quote consistency, Troubleshoot line items or amounts
- **Follow-up skills**: `sf-kugamon`

**Notes**: With no arguments, the skill calls `cirra_ai_init` first, then presents a menu of options. Package detection via `sobject_describe` on `OpportunityLineItem` can run after the user selects an action, or speculatively in parallel. The menu should reflect the five core responsibilities listed in SKILL.md.

---

## edge case — kuga_sub package not installed (HAS_KUGA_SUB = false)

- **Input**: `/sf-kugamon quote for opportunity 006Xx000001xxxxxEAA`
- **Dispatch**: Quote Creation
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(none)`
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `sobject_dml`
- **Should NOT call**: `sobject_create` (metadata tool, not for data records)
- **Should ask user**: yes (confirm contact for quote; warn user that kuga_sub fields are absent)
- **Menu options**: n/a
- **Follow-up skills**: `sf-kugamon`

**Notes**: Edge case where `sobject_describe` on `OpportunityLineItem` returns no `kuga_sub__Renew__c` field, setting HAS_KUGA_SUB = false. The skill must NOT query `kuga_sub__KugamonSettings__c`, must NOT reference any `kuga_sub__*` fields on Opportunity or OpportunityLineItem, and must use the standard `Amount` field (not `kuga_sub__OpportunityAmount__c`) for amount comparisons. Quote creation still uses `sobject_dml` with `operation: "insert"` (not `sobject_create`, which is for metadata). Line item routing to service vs. product lines falls back to `kugo2p__AdditionalProductDetail__c.kugo2p__Service__c`. Any "No such column" errors on kuga_sub fields should trigger this fallback path rather than failing.
