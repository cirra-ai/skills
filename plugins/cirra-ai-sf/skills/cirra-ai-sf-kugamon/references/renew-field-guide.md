# Understanding the Renew Field in Kugamon CPQ

## Overview

The `kuga_sub__Renew__c` field on OpportunityLineItem is critical for proper revenue classification in Kugamon CPQ. It determines whether a product/service is treated as recurring or non-recurring.

## Field Behavior

### When Renew = true

- Product is treated as a **recurring subscription**
- Revenue flows to:
  - `kuga_sub__MRR__c` (Monthly Recurring Revenue)
  - `kuga_sub__ARR__c` (Annual Recurring Revenue)
- `kuga_sub__NonRecurringRevenue__c` = 0

### When Renew = false (or null)

- Product is treated as **non-recurring/one-time**
- Revenue flows to:
  - `kuga_sub__NonRecurringRevenue__c`
- MRR and ARR remain 0

## Revenue Roll-Ups to Opportunity

### Opportunity Line Item Fields (Source)

- `kuga_sub__MRR__c` - Monthly recurring amount
- `kuga_sub__ARR__c` - Annual recurring amount (typically MRR × 12)
- `kuga_sub__NonRecurringRevenue__c` - One-time amount

### Opportunity Roll-Up Fields (Calculated)

1. **Monthly Recurring Revenue** (`kuga_sub__MonthlyRecurringRevenue__c`)
   - Roll-up sum of all line item MRR values

2. **Annual Recurring Revenue (Committed)** (`kuga_sub__AnnualRecurringRevenueCommitted__c`)
   - Roll-up sum of all line item ARR values

3. **Non-Recurring Revenue** (`kuga_sub__NonRecurringRevenue__c`)
   - Roll-up sum of all line item non-recurring revenue

4. **Annual Contract Value (Initial)** (`kuga_sub__AnnualContractValueInitial__c`)
   - **FORMULA:** `NonRecurringRevenue + AnnualRecurringRevenueCommitted`
   - This is where double-counting occurs if Renew is set incorrectly!

## Common Mistake: Double-Counting

### The Problem

When a recurring product has `Renew = false`:

- The line item populates BOTH `kuga_sub__ARR__c` AND `kuga_sub__NonRecurringRevenue__c`
- This causes the ACV formula to count the product twice

### Example of Wrong Configuration

```
OpportunityLineItem: "Annual Support Contract"
- UnitPrice: $2,000/month
- kuga_sub__Renew__c: false  ❌ WRONG!
- kuga_sub__MRR__c: $2,000
- kuga_sub__ARR__c: $24,000
- kuga_sub__NonRecurringRevenue__c: $24,000  ❌ Should be $0!

Rolls up to Opportunity:
- ARR: $24,000 ✓
- Non-Recurring: $24,000 ❌ Should be $0
- ACV: $24,000 + $24,000 = $48,000 ❌ DOUBLE-COUNTED!
```

### Example of Correct Configuration

```
OpportunityLineItem: "Annual Support Contract"
- UnitPrice: $2,000/month
- kuga_sub__Renew__c: true  ✓ CORRECT!
- kuga_sub__MRR__c: $2,000
- kuga_sub__ARR__c: $24,000
- kuga_sub__NonRecurringRevenue__c: $0  ✓ Correct!

Rolls up to Opportunity:
- ARR: $24,000 ✓
- Non-Recurring: $0 ✓
- ACV: $0 + $24,000 = $24,000 ✓ CORRECT!
```

## Best Practices

### When Creating Opportunity Line Items

**Always explicitly set the Renew field:**

```javascript
// For recurring products (subscriptions, support, services)
{
  "Product2Id": "01txxx",
  "Quantity": 1,
  "UnitPrice": 2000,
  "kuga_sub__Renew__c": true  // REQUIRED for recurring!
}

// For one-time products (hardware, implementation, licenses)
{
  "Product2Id": "01txxx",
  "Quantity": 1,
  "UnitPrice": 15000,
  "kuga_sub__Renew__c": false  // or omit (defaults to false)
}
```

### Product Types Guide

| Product Type          | Renew Setting | Examples                           |
| --------------------- | ------------- | ---------------------------------- |
| Subscriptions         | `true`        | SaaS licenses, recurring services  |
| Support Contracts     | `true`        | Standard Support, Premium Support  |
| Hardware              | `false`       | Servers, equipment, devices        |
| Implementation        | `false`       | Setup fees, onboarding, training   |
| Professional Services | `false`       | Consulting hours (unless retainer) |
| One-time Licenses     | `false`       | Perpetual software licenses        |
| Recurring Retainers   | `true`        | Monthly consulting retainers       |

## Troubleshooting

### Symptom: ACV Higher Than Expected

1. **Query the opportunity:**

```sql
SELECT kuga_sub__NonRecurringRevenue__c,
       kuga_sub__AnnualRecurringRevenueCommitted__c,
       kuga_sub__AnnualContractValueInitial__c
FROM Opportunity
WHERE Id = '<opp_id>'
```

2. **If NonRecurring + ARR ≠ ACV**, there's a data issue elsewhere
3. **If NonRecurring seems too high**, check line items:

```sql
SELECT Id, Product2.Name, kuga_sub__Renew__c,
       kuga_sub__MRR__c, kuga_sub__ARR__c,
       kuga_sub__NonRecurringRevenue__c
FROM OpportunityLineItem
WHERE OpportunityId = '<opp_id>'
```

4. **Look for products with ALL of:**
   - `kuga_sub__Renew__c = false`
   - `kuga_sub__MRR__c > 0` or `kuga_sub__ARR__c > 0`
   - `kuga_sub__NonRecurringRevenue__c > 0`

5. **Fix by updating the line item:**

```javascript
{
  "Id": "00kxxx",
  "kuga_sub__Renew__c": true
}
```

The Non-Recurring Revenue will automatically recalculate to $0 via Kugamon's automation.

## Technical Details

### Why Does This Happen?

Kugamon CPQ has automation (likely workflow rules or process builder) that:

1. Calculates MRR and ARR based on product pricing and term
2. Populates NonRecurringRevenue based on the Renew field
3. When Renew = false: NonRecurringRevenue = line total
4. When Renew = true: NonRecurringRevenue = 0

The automation runs AFTER record save, so you can't directly control NonRecurringRevenue - you must control it via the Renew field.

### Why Not Just Update NonRecurringRevenue Directly?

Attempting to update `kuga_sub__NonRecurringRevenue__c` directly on the line item will be overridden by Kugamon's automation. The Renew field is the "source of truth" that drives the calculation.
