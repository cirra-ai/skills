---
name: cirra-ai-sf-kugamon
metadata:
  version: 1.1.0
description: >
  Kugamon CPQ quote management for Salesforce via Cirra AI MCP Server. Use when
  creating, verifying, or managing opportunities, quotes, and orders with the
  Kugamon package (kugo2p). Automatically detects whether the kuga_sub
  (Kugamon Subscriptions) package is installed and adapts the workflow accordingly.
  Handles renewal, new business, and expansion quotes with proper record type
  mapping, automatic line item population, and accurate amount field interpretation.
---

# cirra-ai-sf-kugamon: Kugamon CPQ Quote Management with Cirra AI

Expert Kugamon CPQ specialist. Create, verify, and manage Salesforce opportunities, quotes, and orders using the Kugamon package (kugo2p) via the Cirra AI MCP Server. Automatically adapts workflows based on whether the kuga_sub (Kugamon Subscriptions) package is installed.

## Execution modes

This skill supports four execution modes — see
`references/execution-modes.md` for detection logic and full details,
and `references/mcp-pagination.md` for handling large MCP responses.

All Kugamon operations go through MCP tools regardless of mode.

---

## Core Responsibilities

1. **Quote Creation**: Create Kugamon quotes from opportunities with proper record type mapping
2. **Line Item Management**: Handle product and service line separation with correct Renew field settings
3. **Consistency Checking**: Keep quotes and opportunity line items in sync
4. **Amount Interpretation**: Correctly interpret MRR, ARR, ACV, and TCV fields across subscription and non-subscription orgs

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

### Phase 2: Creating Opportunities and Line Items (If Needed)

#### Creating the Opportunity

**Required Fields:**

- `Name` — Opportunity name (e.g., "Starbucks - GenWatt Installation")
- `StageName` — Use "Qualification" by default when creating with a quote, or another appropriate stage
- `CloseDate` — Expected close date
- `AccountId` — Required for Kugamon (links to account)
- `Pricebook2Id` — Required if you plan to add products (use standard pricebook or custom)

**Recommended Optional Fields:**

- `Amount` — Total opportunity value (will be overridden by line item totals if products are added)
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
SELECT Id, Name, AccountId, Amount, StageName, CloseDate, Pricebook2Id, RecordType.Name,
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

- Compare `kugo2p__TotalAmount__c` (quote) to `kuga_sub__AnnualContractValueInitial__c` or `kuga_sub__TotalContractValue__c` (opportunity)
- Note: `Amount` field likely represents MRR, not annual value

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

- **If HAS_KUGA_SUB = true**: Check if subscription fields exist. Amount may be MRR while quote shows ACV.
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

---

## When to Load References

- **record-types.md**: When creating quotes to map correct record type
- **field-reference.md**: When troubleshooting field errors or understanding calculations
- **amount-fields-guide.md**: When amounts don't match or user questions field meanings
- **renew-field-guide.md**: When creating opportunity line items, or when ACV is double-counting recurring products

## Resources

- [Kugamon YouTube Channel](https://www.youtube.com/playlist?list=PL63Lb4qcQBZcTLAkBTdyn08bKpHVpy7fx) — Video tutorials and walkthroughs
