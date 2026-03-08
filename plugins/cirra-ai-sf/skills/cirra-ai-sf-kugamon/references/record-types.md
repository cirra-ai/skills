# Kugamon CPQ Quote Record Types

## Querying Record Types

**IMPORTANT:** Record Type IDs are org-specific. Always query them dynamically:

```sql
SELECT Id, Name, DeveloperName
FROM RecordType
WHERE SObjectType = 'kugo2p__SalesQuote__c'
AND IsActive = true
```

## Available Record Types

### Renewal Quote

- **DeveloperName:** `Renewal` (query to get the org-specific Id)
- **When to use:** For renewal opportunities where existing customers are renewing their contracts
- **Typical scenarios:** Annual subscription renewals, multi-year contract renewals

### New Business Quote

- **DeveloperName:** `New_Business` (query to get the org-specific Id)
- **When to use:** For new business opportunities with prospects or new customers
- **Typical scenarios:** First-time sales, new logo acquisitions

### Expansion Quote

- **DeveloperName:** `Expansion` (query to get the org-specific Id)
- **When to use:** For expansion/upsell opportunities with existing customers
- **Typical scenarios:** Adding new products, increasing quantities, upgrading tiers

## Mapping Opportunity to Quote Record Types

**General rule:** Match the quote record type to the opportunity record type.

**Steps:**

1. Query the opportunity's `RecordType.Name`
2. Query `kugo2p__SalesQuote__c` record types (see query above)
3. Match by name:
   - Opportunity RecordType.Name = "Renewal" -> Quote DeveloperName = `Renewal`
   - Opportunity RecordType.Name = "New Business" -> Quote DeveloperName = `New_Business`
   - Opportunity RecordType.Name = "Expansion" -> Quote DeveloperName = `Expansion`

**If opportunity record type doesn't match these categories:** Ask the user which quote record type to use, or default to New Business if uncertain.
