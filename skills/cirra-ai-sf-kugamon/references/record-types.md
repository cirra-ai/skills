# Kugamon CPQ Record Types

## Querying Record Types

**IMPORTANT:** Record Type IDs are org-specific. Always query them dynamically:

```sql
SELECT Id, Name, DeveloperName
FROM RecordType
WHERE SObjectType = 'kugo2p__SalesQuote__c'
AND IsActive = true
```

Record Types exist on three objects: Opportunity, Kugamon Quote (`kugo2p__SalesQuote__c`), and Kugamon Order (`kugo2p__SalesOrder__c`). The Record Type flows from Opportunity → Quote → Order.

## Available Record Types

### New Business Quote

- **DeveloperName:** `New_Business` (query to get the org-specific Id)
- **When to use:** For new business opportunities with prospects or new customers
- **Typical scenarios:** First-time sales, new logo acquisitions
- **Order Release behavior:** Creates Contract, Assets, Subscriptions, and Renewal Opportunity (see subscription-management.md)

### Expansion Quote

- **DeveloperName:** `Expansion` (query to get the org-specific Id)
- **When to use:** For expansion/upsell opportunities with existing customers tied to an existing Contract
- **Typical scenarios:** Adding new products, increasing quantities, upgrading tiers
- **Order Release behavior:** Amends existing Contract, creates Assets/Subscriptions assigned to that Contract, adds lines to existing Renewal Opportunity (see subscription-management.md)

### Renewal Quote

- **DeveloperName:** `Renewal` (query to get the org-specific Id)
- **When to use:** For renewal opportunities where existing customers are renewing their contracts
- **Typical scenarios:** Annual subscription renewals, multi-year contract renewals
- **Order Release behavior:** Extends or replaces Contract depending on KugamonSettings.ExtendContractOnRenewal (see subscription-management.md)

## Mapping Opportunity to Quote/Order Record Types

**General rule:** Match the quote/order record type to the opportunity record type.

**Steps:**

1. Query the opportunity's `RecordType.Name`
2. Query `kugo2p__SalesQuote__c` record types (see query above)
3. Match by name:
   - Opportunity RecordType.Name = "Renewal" -> Quote DeveloperName = `Renewal`
   - Opportunity RecordType.Name = "New Business" -> Quote DeveloperName = `New_Business`
   - Opportunity RecordType.Name = "Expansion" -> Quote DeveloperName = `Expansion`

**If opportunity record type doesn't match these categories:** Ask the user which quote record type to use, or default to New Business if uncertain.

## Record Type Lifecycle Summary

| Record Type   | Opportunity        | Quote           | Order           | Order Release Creates                                            |
| ------------- | ------------------ | --------------- | --------------- | ---------------------------------------------------------------- |
| **New**       | Initial deal       | New quote       | New order       | Contract + Assets + Subscriptions + Renewal Opp                  |
| **Expansion** | Upsell/cross-sell  | Expansion quote | Expansion order | Amends Contract + Assets + Subscriptions + adds to Renewal Opp   |
| **Renewal**   | Contract extension | Renewal quote   | Renewal order   | Extends/replaces Contract + Assets + Subscriptions + Renewal Opp |

## Key Differences by Record Type

### New

- No prior Contract required
- Creates a brand new Contract
- Creates a future-dated Renewal Opportunity (if renewable lines exist)

### Expansion

- **Requires:** Existing Contract (Order must have Contract Number populated)
- **Requires:** Existing Renewal Opportunity (Order must have Renewal Opportunity Name populated)
- Amends (does not create) the Contract
- Adds lines to (does not create) the Renewal Opportunity

### Renewal

- **Requires:** Existing Contract (Order must have Contract Number populated)
- Behavior depends on `kuga_sub__ExtendContractOnRenewal__c` setting:
  - **True:** Extends the existing Contract, creates replacement Renewal Opportunity
  - **False:** Creates a replacement Contract (behaves like New for downstream records)
