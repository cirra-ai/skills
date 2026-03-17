---
name: cirra-ai-sf-kugamon
metadata:
  version: 1.2.0
description: >
  Kugamon CPQ quote and subscription management for Salesforce via Cirra AI MCP Server.
  Use when creating, verifying, or managing opportunities, quotes, orders, contracts,
  assets, subscriptions, or renewals with the Kugamon package (kugo2p). Automatically
  detects whether the kuga_sub (Kugamon Subscriptions) package is installed and adapts
  the workflow accordingly. Handles New, Expansion, and Renewal record types with proper
  record type mapping, automatic line item population, accurate amount field interpretation,
  and full Order Release lifecycle (Contract, Asset, Subscription, and Renewal Opportunity creation).
---

# cirra-ai-sf-kugamon: Kugamon CPQ Quote & Subscription Management with Cirra AI

Expert Kugamon CPQ and Subscription Management specialist. Create, verify, and manage Salesforce opportunities, quotes, orders, and the full Order Release lifecycle using the Kugamon package (kugo2p) via the Cirra AI MCP Server. Automatically adapts workflows based on whether the kuga_sub (Kugamon Subscriptions) package is installed.

## Core Responsibilities

1. **Quote Creation**: Create Kugamon quotes from opportunities with proper record type mapping
2. **Line Item Management**: Handle product and service line separation with correct Renew field settings
3. **Consistency Checking**: Keep quotes and opportunity line items in sync
4. **Amount Interpretation**: Correctly interpret MRR, ARR, ACV, and TCV fields across subscription and non-subscription orgs
5. **Subscription Management**: Manage the Order Release lifecycle — Contract creation, Asset creation, Subscription creation, and Renewal Opportunity generation across New, Expansion, and Renewal record types

---

## Workflow

### Phase 1: MCP Initialization & Package Detection

**FIRST**: Call `cirra_ai_init()` with no parameters:

```
cirra_ai_init()
```

- If a default org is configured, proceed immediately and confirm with the user:
  > "I've connected to **[org]**. Would you like me to use the defaults, or do you want to select different options?"
- If no default is configured, ask for the Salesforce user/alias before proceeding.

Do **not** ask for org details before calling `cirra_ai_init()`.

**THEN**: Detect the kuga_sub package by checking if `kuga_sub__Renew__c` exists on `OpportunityLineItem`:

```
sobject_describe(sObject="OpportunityLineItem")
```

Set a session flag:

- `HAS_KUGA_SUB = true` if the field exists
- `HAS_KUGA_SUB = false` if it does not

**This flag determines which workflow to follow throughout the entire process.**

**THEN**: If HAS_KUGA_SUB = true, detect Subscription Management:

```sql
SELECT Id, kuga_sub__InitiateOrderSubscriptionManagement__c
FROM kuga_sub__KugamonSettings__c
LIMIT 1
```

Set a second session flag:

- `HAS_SUB_MGMT = true` if `kuga_sub__InitiateOrderSubscriptionManagement__c` is NOT null
- `HAS_SUB_MGMT = false` if the field is null, the setting doesn't exist, or the query fails (a query failure means the object/field is not present in the org)

**This flag determines whether the Order Release lifecycle (Contracts, Assets, Subscriptions, Renewal Opportunities) is active.**

### Phase 2: Creating Opportunities and Line Items (If Needed)

#### Creating the Opportunity

**Required Fields:**

- `Name` — Opportunity name (e.g., "Starbucks - GenWatt Installation")
- `StageName` — Use "Qualification" by default when creating with a quote, or another appropriate stage
- `CloseDate` — Expected close date
- `AccountId` — Required for Kugamon (links to account)
- `Pricebook2Id` — Required if you plan to add products (use standard pricebook or custom)

**Recommended Optional Fields:**

- `Amount` — Total opportunity value (will be overridden by line item totals if products are added). **Note:** If `HAS_KUGA_SUB = true`, ignore the standard `Amount` field — it is a raw Qty × Price sum that does not factor Service Term and may include non-subscription products. Use `kuga_sub__OpportunityAmount__c` to read the true Opportunity Amount instead.
- `Type` — Opportunity type (e.g., "New Business", "Existing Business")
- `RecordTypeId` — Set to match quote type if known (New, Renewal, or Expansion)

#### Creating Opportunity Line Items

**Check your HAS_KUGA_SUB flag before proceeding.**

##### If HAS_KUGA_SUB = true (Subscriptions package installed)

**CRITICAL:** Always set the `kuga_sub__Renew__c` field:

**Required Fields:**

- `OpportunityId` — The opportunity to attach to
- `PricebookEntryId` — Links to the product (required, not Product2Id directly)
- `Quantity` — Quantity to purchase (required, minimum 1)
- `kuga_sub__Renew__c` — **CRITICAL for revenue classification** (see references/renew-field-guide.md)

**Important Optional Fields:**

- `UnitPrice` — Override the pricebook price if needed
- `ServiceDate` — Start date for the service/product
- `kuga_sub__ServiceTerm__c` — Term length (e.g., 12, 24, 36)
- `kuga_sub__UnitofTerm__c` — Term unit ("Month" or "Year")

**Setting the Renew Field:**

- **For recurring products/services** (subscriptions, support contracts): Set `kuga_sub__Renew__c = true`
- **For one-time products** (hardware, implementation fees): Set `kuga_sub__Renew__c = false` (or omit, defaults to false)

**Why this matters:** The `Renew` field controls how Kugamon calculates revenue:

- When `Renew = false`: Product treated as non-recurring, amount goes to `kuga_sub__NonRecurringRevenue__c`
- When `Renew = true`: Product treated as recurring, amount goes to MRR/ARR fields

##### If HAS_KUGA_SUB = false (No subscriptions package)

**Required Fields:**

- `OpportunityId` — The opportunity to attach to
- `PricebookEntryId` — Links to the product (required, not Product2Id directly)
- `Quantity` — Quantity to purchase (required, minimum 1)

**Important Optional Fields:**

- `UnitPrice` — Override the pricebook price if needed
- `ServiceDate` — Start date for the service/product

**Note:** Without the kuga_sub package, Kugamon relies on `kugo2p__AdditionalProductDetail__c.kugo2p__Service__c` to determine whether line items become Quote Product Lines or Quote Service Lines.

### Phase 3: Discovery & Pre-Creation Checks

When a user requests quote creation, gather complete context.

**CRITICAL PRE-CREATION CHECKS:**

1. **Billing Address Validation:**

   ```sql
   SELECT Id, Name, BillingStreet, BillingCity, BillingState, BillingPostalCode, BillingCountry
   FROM Account
   WHERE Id = '<account_id>'
   ```

   - Verify ALL billing address fields are populated
   - If any field is missing, inform the user and ask for the complete billing address
   - DO NOT proceed until the billing address is complete

2. **Contact Validation:**

   ```sql
   SELECT Id, Name, Email, Phone
   FROM Contact
   WHERE AccountId = '<account_id>'
   AND Email != null
   LIMIT 10
   ```

   - Verify at least one contact exists for the account
   - Ask user which contact should be associated with the quote
   - DO NOT proceed until a contact is identified

**Query the full opportunity:**

##### If HAS_KUGA_SUB = true:

```sql
SELECT Id, Name, AccountId, Amount, kuga_sub__OpportunityAmount__c, StageName, CloseDate, Pricebook2Id, RecordType.Name,
       kuga_sub__MonthlyRecurringRevenue__c, kuga_sub__AnnualContractValueInitial__c,
       kuga_sub__TotalContractValue__c, kuga_sub__AnnualRecurringRevenueCommitted__c,
       kuga_sub__NonRecurringRevenue__c
FROM Opportunity
WHERE Id = '<opportunity_id>'
```

**If line items exist, verify Renew field is set correctly:**

```sql
SELECT Id, Product2.Name, Quantity, UnitPrice, TotalPrice,
       kuga_sub__Renew__c, kuga_sub__MRR__c, kuga_sub__ARR__c, kuga_sub__NonRecurringRevenue__c
FROM OpportunityLineItem
WHERE OpportunityId = '<opportunity_id>'
```

##### If HAS_KUGA_SUB = false:

```sql
SELECT Id, Name, AccountId, Amount, StageName, CloseDate, Pricebook2Id, RecordType.Name
FROM Opportunity
WHERE Id = '<opportunity_id>'
```

**Check for existing quotes (same for both):**

```sql
SELECT Id, Name, kugo2p__QuoteName__c, kugo2p__TotalAmount__c, kugo2p__IsPrimary__c
FROM kugo2p__SalesQuote__c
WHERE kugo2p__Opportunity__c = '<opportunity_id>'
```

### Phase 4: Create the Quote

**Prerequisites:** Billing address complete, contact identified.

Use only these createable fields:

- `RecordTypeId` — Match to opportunity type (see references/record-types.md)
- `kugo2p__Account__c` — Account lookup
- `kugo2p__Opportunity__c` — Opportunity lookup
- `kugo2p__QuoteName__c` — Quote name (user-specified or generated)
- `kugo2p__Pricebook2Id__c` — Pricebook lookup from opportunity
- `kugo2p__ContactBuying__c` — **REQUIRED** Buying contact lookup
- `kugo2p__ContactBilling__c` — Optional billing contact lookup
- `kugo2p__ContactShipping__c` — Optional shipping contact lookup
- `kugo2p__IsPrimary__c` — Set to true if no other primary quote exists
- `kugo2p__DateOfferValidThrough__c` — Expiration date (30 days from today if not specified)

**Never set these auto-managed fields:**

- `Name` (auto-generated quote number)
- `kugo2p__Status__c` (workflow-managed)
- `kugo2p__TotalAmount__c` (calculated)
- `kugo2p__SubtotalAmount__c` (calculated)

### Phase 5: Verification & Results

**CRITICAL: Query the newly created quote immediately:**

```sql
SELECT Id, Name, kugo2p__QuoteName__c, kugo2p__TotalAmount__c, kugo2p__SubtotalAmount__c,
       kugo2p__Status__c, kugo2p__IsPrimary__c, kugo2p__DateOfferValidThrough__c
FROM kugo2p__SalesQuote__c
WHERE Id = '<quote_id>'
```

**Check for auto-populated line items in BOTH sections:**

##### If HAS_KUGA_SUB = true:

**Quote Service Lines** (recurring services with `kuga_sub__Renew__c = true`):

```sql
SELECT Id, kugo2p__Line__c, kugo2p__ServiceName__c, kugo2p__Quantity__c,
       kugo2p__SalesPrice__c, kugo2p__TotalAmount__c
FROM kugo2p__SalesQuoteServiceLine__c
WHERE kugo2p__SalesQuote__c = '<quote_id>'
ORDER BY kugo2p__Line__c
```

**Quote Product Lines** (one-time products with `kuga_sub__Renew__c = false`):

```sql
SELECT Id, kugo2p__Line__c, kugo2p__Product__r.Name, kugo2p__Quantity__c,
       kugo2p__SalesPrice__c, kugo2p__TotalAmount__c
FROM kugo2p__SalesQuoteProductLine__c
WHERE kugo2p__SalesQuote__c = '<quote_id>'
ORDER BY kugo2p__Line__c
```

##### If HAS_KUGA_SUB = false:

**Quote Service Lines** (products with `kugo2p__Service__c = true`):

```sql
SELECT Id, kugo2p__Line__c, kugo2p__ServiceName__c, kugo2p__Quantity__c,
       kugo2p__SalesPrice__c, kugo2p__TotalAmount__c
FROM kugo2p__SalesQuoteServiceLine__c
WHERE kugo2p__SalesQuote__c = '<quote_id>'
ORDER BY kugo2p__Line__c
```

**Quote Product Lines** (products with `kugo2p__Service__c = false`):

```sql
SELECT Id, kugo2p__Line__c, kugo2p__Product__r.Name, kugo2p__Quantity__c,
       kugo2p__SalesPrice__c, kugo2p__TotalAmount__c
FROM kugo2p__SalesQuoteProductLine__c
WHERE kugo2p__SalesQuote__c = '<quote_id>'
ORDER BY kugo2p__Line__c
```

**Amount Field Interpretation:**

If subscription fields exist (any `kuga_sub__*` fields present on opportunity):

- **Ignore the standard `Amount` field** — it is a raw Qty × Price sum that does not factor Service Term and may include non-subscription products
- **Use `kuga_sub__OpportunityAmount__c` for the true Opportunity Amount**
- Compare `kugo2p__TotalAmount__c` (quote) to `kuga_sub__AnnualContractValueInitial__c` or `kuga_sub__TotalContractValue__c` (opportunity)

If subscription fields do NOT exist:

- Compare `kugo2p__TotalAmount__c` (quote) to `Amount` (opportunity)

**Always show all amount fields** in summary to provide complete picture.

**Present results with:**

- Quote number (actual `Name` field value)
- Quote total and comparison to opportunity amounts
- Auto-populated line items in BOTH sections (Product Lines and Service Lines) in table format
- Direct links to quote and opportunity records
- Status and primary quote indicator

---

## Consistency Checking and Synchronization

**CRITICAL:** Whenever updating quotes OR opportunity line items, ALWAYS check for consistency and synchronize both sides unless explicitly told not to.

### When to Check Consistency

1. After creating a new quote
2. After updating quote line items (service lines or product lines)
3. After updating opportunity line items
4. When user explicitly requests quote or opportunity updates

### What to Check

Compare the following between Quote Lines and Opportunity Line Items:

##### If HAS_KUGA_SUB = true:

**For Service Lines (recurring):**

- Service/Product match (`kugo2p__ServiceName__c` vs `Product2.Name`)
- Quantity (`kugo2p__Quantity__c` vs `Quantity`)
- Unit Price (`kugo2p__SalesPrice__c` vs `UnitPrice`)
- Start Date (`kugo2p__DateServiceStart__c` vs `ServiceDate`)
- End Date (`kugo2p__DateServiceEnd__c` vs calculated from ServiceDate + Term)
- Term (`kugo2p__ServiceTerm__c` vs `kuga_sub__ServiceTerm__c`)

**For Product Lines (one-time):**

- Product match (`kugo2p__Product__r.Name` vs `Product2.Name`)
- Quantity (`kugo2p__Quantity__c` vs `Quantity`)
- Unit Price (`kugo2p__SalesPrice__c` vs `UnitPrice`)

##### If HAS_KUGA_SUB = false:

**For Service Lines:**

- Service/Product match (`kugo2p__ServiceName__c` vs `Product2.Name`)
- Quantity (`kugo2p__Quantity__c` vs `Quantity`)
- Unit Price (`kugo2p__SalesPrice__c` vs `UnitPrice`)
- Start Date (`kugo2p__DateServiceStart__c` vs `ServiceDate`)

**For Product Lines:**

- Product match (`kugo2p__Product__r.Name` vs `Product2.Name`)
- Quantity (`kugo2p__Quantity__c` vs `Quantity`)
- Unit Price (`kugo2p__SalesPrice__c` vs `UnitPrice`)

### Synchronization Rules

**DEFAULT BEHAVIOR:** When updating either quotes or opportunities, automatically update BOTH sides to maintain consistency.

**When updating Quote Lines:**

1. Check if corresponding Opportunity Line Items exist
2. If they exist, update them to match the quote
3. Update: ServiceDate, Quantity, UnitPrice (if changed)
4. DO NOT update: Product2Id (requires delete/recreate)

**When updating Opportunity Line Items:**

1. Check if corresponding Quote Lines exist
2. If they exist, update them to match the opportunity
3. Update: Quantity, SalesPrice, DateServiceStart (if changed)
4. For Service changes: Delete old line and create new one (Kugamon restriction)

**Exception:** Only skip synchronization if user explicitly says:

- "only update the quote"
- "don't update the opportunity"
- "skip opportunity sync"

---

## Key Object Reference

See references/field-reference.md for complete field details.

| Object       | API Name                           | Purpose            |
| ------------ | ---------------------------------- | ------------------ |
| Quote        | `kugo2p__SalesQuote__c`            | Main quote record  |
| Service Line | `kugo2p__SalesQuoteServiceLine__c` | Recurring services |
| Product Line | `kugo2p__SalesQuoteProductLine__c` | One-time products  |

---

## Common Issues

**Quote total doesn't match opportunity Amount:**

- **If HAS_KUGA_SUB = true**: Ignore the standard `Amount` field (raw Qty × Price, unreliable). Compare quote to `kuga_sub__OpportunityAmount__c` or `kuga_sub__AnnualContractValueInitial__c` instead.
- **If HAS_KUGA_SUB = false**: Quote total should match the sum of all opportunity line item totals.

**Line items not auto-populating:**
Verify opportunity has products/line items and pricebook matches. Check BOTH `kugo2p__SalesQuoteProductLine__c` and `kugo2p__SalesQuoteServiceLine__c`.

- **If HAS_KUGA_SUB = false**: Also verify products have corresponding records in `kugo2p__AdditionalProductDetail__c` with `kugo2p__Service__c` properly set.

**Cannot create quote — missing billing address:**
Query account billing fields, inform user which fields are missing, update the account, then proceed.

**Cannot create quote — no contact exists:**
Query contacts for the account, request contact information, create the contact, then proceed.

**ACV is double-counting recurring products (HAS_KUGA_SUB = true only):**
Update line items to set `kuga_sub__Renew__c = true` for recurring services/subscriptions. See references/renew-field-guide.md.

**kuga_sub fields don't exist / "No such column" errors:**
Set `HAS_KUGA_SUB = false` and follow the non-subscription workflow. The Kugamon CPQ package still works without kuga_sub.

**Quote and opportunity line items are out of sync:**
Follow the Consistency Checking workflow above. Always update BOTH sides unless explicitly told not to.

**Order Release did not create expected Assets/Subscriptions/Renewal Opportunity:**

1. Check Subscription Management is active: Query `kuga_sub__KugamonSettings__c` for `kuga_sub__InitiateOrderSubscriptionManagement__c` — must be NOT null
2. Assets not created: Check if Order Product Lines' corresponding `kugo2p__AdditionalProductDetail__c.kugo2p__CreateAsset__c` is NOT null
3. Subscriptions not created: Check if Order Service Lines' corresponding `Product2.kuga_sub__CreateSubscription__c` = True
4. Renewal Opportunity not created: Check if any Order Service Lines have `kuga_sub__Renew__c` = True
5. For Expansion Orders: Verify the Order has `Contract Number` and `Renewal Opportunity Name` populated
6. For Renewal Orders: Verify the Order has `Contract Number` populated

**Renewal Order created a new Contract instead of extending (or vice versa):**
Check `kuga_sub__ExtendContractOnRenewal__c` in KugamonSettings. True = extend Contract; False = create replacement Contract.

---

## Order Release Lifecycle (Subscription Management)

**PREREQUISITE:** `HAS_SUB_MGMT = true` (Kugamon Subscription Management is active)

When a Kugamon Order is Released, the system triggers different behaviors depending on the Order's Record Type. The Record Type on the Order inherits from the parent Opportunity/Quote Record Type. See references/subscription-management.md for full details.

**Key configuration fields that control behavior:**

| Object                               | Field                                              | Controls                                                    |
| ------------------------------------ | -------------------------------------------------- | ----------------------------------------------------------- |
| `kuga_sub__KugamonSettings__c`       | `kuga_sub__InitiateOrderSubscriptionManagement__c` | Enables Subscription Mgmt (must be NOT null)                |
| `kuga_sub__KugamonSettings__c`       | `kuga_sub__ExtendContractOnRenewal__c`             | True = extend Contract on renewal; False = replace          |
| `kugo2p__AdditionalProductDetail__c` | `kugo2p__CreateAsset__c`                           | If NOT null, Asset created on Order Product Line release    |
| `Product2`                           | `kuga_sub__CreateSubscription__c`                  | If True, Subscription created on Order Service Line release |
| Order Service Line                   | `kuga_sub__Renew__c`                               | If True, generates Renewal Opportunity Line Item            |
| `kugo2p__SalesOrder__c`              | Contract Number                                    | Links to existing Contract (required for Expansion/Renewal) |
| `kugo2p__SalesOrder__c`              | Renewal Opportunity Name                           | Links to existing Renewal Opp (used by Expansion)           |

### New Record Type — Order Release

1. **Create Contract** — New Contract linked to the Account
2. **Create Assets** (conditional) — For each Order Product Line where `kugo2p__AdditionalProductDetail__c.kugo2p__CreateAsset__c` is NOT null
3. **Create Subscriptions** (conditional) — For each Order Service Line where `Product2.kuga_sub__CreateSubscription__c` = True
4. **Create Renewal Opportunity** (conditional) — Future-dated Renewal Opportunity if any Service Lines have `kuga_sub__Renew__c` = True, populated with Opportunity Line Items

### Expansion Record Type — Order Release

**Prerequisites:** Order must have `Contract Number` and `Renewal Opportunity Name` populated.

1. **Amend existing Contract** — Contract referenced by Order's `Contract Number` is amended (NOT a new Contract)
2. **Create Assets** (conditional) — Assigned to the existing Contract
3. **Create Subscriptions** (conditional) — Assigned to the existing Contract
4. **Add lines to existing Renewal Opportunity** — Renewable Service Lines added as Opportunity Line Items to the existing Renewal Opportunity

### Renewal Record Type — Order Release

**Prerequisites:** Order must have `Contract Number` populated.

**If `ExtendContractOnRenewal` = True:**

1. **Extend existing Contract** — Amend/extend the existing Contract
2. **Create Assets** (conditional)
3. **Create Subscriptions** (conditional)
4. **Create Replacement Renewal Opportunity** (conditional) — New future-dated Renewal Opportunity replaces the previous one

**If `ExtendContractOnRenewal` = False:**

1. **Amend existing Contract** — Original Contract amended/closed
2. **Create Replacement Contract** — Brand new Contract created
3. **Create Assets** (conditional) — Same behavior as New
4. **Create Subscriptions** (conditional) — Same behavior as New
5. **Create Renewal Opportunity** (conditional) — Same behavior as New

### Record Type Behavior Matrix

| Action               | New                     | Expansion                     | Renewal (Extend)                | Renewal (Replace)       |
| -------------------- | ----------------------- | ----------------------------- | ------------------------------- | ----------------------- |
| Create Contract      | Yes (new)               | No (amend)                    | No (extend)                     | Yes (replacement)       |
| Create Assets        | Conditional\*           | Conditional\* (to Contract)   | Conditional\*                   | Conditional\*           |
| Create Subscriptions | Conditional\*\*         | Conditional\*\* (to Contract) | Conditional\*\*                 | Conditional\*\*         |
| Create Renewal Opp   | Conditional\*\*\* (new) | No (add lines)                | Conditional\*\*\* (replacement) | Conditional\*\*\* (new) |

- \* Asset condition: `kugo2p__AdditionalProductDetail__c.kugo2p__CreateAsset__c` is NOT null
- \*\* Subscription condition: `Product2.kuga_sub__CreateSubscription__c` = True
- \*\*\* Renewal Opp condition: Order Service Line `kuga_sub__Renew__c` = True

---

## When to Load References

- **record-types.md**: When creating quotes to map correct record type
- **field-reference.md**: When troubleshooting field errors or understanding calculations
- **amount-fields-guide.md**: When amounts don't match or user questions field meanings
- **renew-field-guide.md**: When creating opportunity line items, or when ACV is double-counting recurring products

## Resources

- [Kugamon YouTube Channel](https://www.youtube.com/playlist?list=PL63Lb4qcQBZcTLAkBTdyn08bKpHVpy7fx) — Video tutorials and walkthroughs
