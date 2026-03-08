# Kugamon CPQ Quote Record Types

## Available Record Types

### Renewal Quote

- **Record Type ID:** `012Ho000001bKaoIAE`
- **When to use:** For renewal opportunities where existing customers are renewing their contracts
- **Typical scenarios:** Annual subscription renewals, multi-year contract renewals

### New Business Quote

- **Record Type ID:** `012Ho000001bKakIAE`
- **When to use:** For new business opportunities with prospects or new customers
- **Typical scenarios:** First-time sales, new logo acquisitions

### Expansion Quote

- **Record Type ID:** `012Ho000001bKajIAE`
- **When to use:** For expansion/upsell opportunities with existing customers
- **Typical scenarios:** Adding new products, increasing quantities, upgrading tiers

## Mapping Opportunity to Quote Record Types

**General rule:** Match the quote record type to the opportunity record type.

**Example mappings:**

- Opportunity RecordType.Name = "Renewal" → Quote RecordTypeId = `012Ho000001bKaoIAE`
- Opportunity RecordType.Name = "New Business" → Quote RecordTypeId = `012Ho000001bKakIAE`
- Opportunity RecordType.Name = "Expansion" → Quote RecordTypeId = `012Ho000001bKajIAE`

**If opportunity record type doesn't match these categories:** Ask the user which quote record type to use, or default to New Business if uncertain.
