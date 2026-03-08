# Understanding Amount Fields in Kugamon CPQ

## The Amount Field Problem

In Salesforce orgs with subscription management (like Kugamon), the standard `Amount` field on Opportunity can represent **different values** depending on configuration:

- Monthly Recurring Revenue (MRR)
- Annual Recurring Revenue (ARR)
- Total Contract Value (TCV)
- Annual Contract Value (ACV)

This creates confusion when comparing opportunity amounts to quote totals.

## Subscription Amount Fields

### On Opportunity (kuga_sub\_\_\* fields)

| Field API Name                                 | Meaning                   | Example                                |
| ---------------------------------------------- | ------------------------- | -------------------------------------- |
| `Amount`                                       | **May be MRR or ACV**     | $10,000 (could be monthly or annual)   |
| `kuga_sub__MonthlyRecurringRevenue__c`         | Monthly recurring revenue | $10,000/month                          |
| `kuga_sub__AnnualContractValueInitial__c`      | Annual contract value     | $120,000/year                          |
| `kuga_sub__TotalContractValue__c`              | Total contract value      | $120,000 (1-year) or $360,000 (3-year) |
| `kuga_sub__AnnualRecurringRevenueCommitted__c` | Annual recurring revenue  | $120,000/year                          |
| `kuga_sub__NonRecurringRevenue__c`             | One-time fees             | $5,000                                 |

### On Quote (kugo2p\_\_\* fields)

| Field API Name              | Meaning                                                       |
| --------------------------- | ------------------------------------------------------------- |
| `kugo2p__TotalAmount__c`    | Total quote amount (typically annual or total contract value) |
| `kugo2p__SubtotalAmount__c` | Subtotal before discounts/taxes                               |

## Comparison Rules

### When Subscription Fields Exist

If ANY `kuga_sub__*` fields are present on the opportunity:

1. **Do NOT compare** `kugo2p__TotalAmount__c` to `Amount`
2. **DO compare** `kugo2p__TotalAmount__c` to:
   - `kuga_sub__AnnualContractValueInitial__c` (preferred), OR
   - `kuga_sub__TotalContractValue__c` (if ACV not available)

**Reasoning:** In subscription orgs, `Amount` is often configured to show MRR, while quotes show annual/total values.

### When Subscription Fields Do NOT Exist

If NO `kuga_sub__*` fields are present:

1. **DO compare** `kugo2p__TotalAmount__c` to `Amount`

**Reasoning:** Without subscription management, `Amount` represents the total opportunity value.

## Practical Examples

### Example 1: Subscription Org (MRR in Amount field)

**Opportunity:**

- `Amount`: $10,000
- `kuga_sub__MonthlyRecurringRevenue__c`: $10,000
- `kuga_sub__AnnualContractValueInitial__c`: $120,000

**Quote:**

- `kugo2p__TotalAmount__c`: $120,000

**Correct interpretation:** Quote matches the Annual Contract Value ($120,000), not the Amount field ($10,000 MRR).

### Example 2: Subscription Org (ACV in Amount field)

**Opportunity:**

- `Amount`: $120,000
- `kuga_sub__MonthlyRecurringRevenue__c`: $10,000
- `kuga_sub__AnnualContractValueInitial__c`: $120,000

**Quote:**

- `kugo2p__TotalAmount__c`: $120,000

**Correct interpretation:** Quote matches both Amount and ACV ($120,000).

### Example 3: Non-Subscription Org

**Opportunity:**

- `Amount`: $120,000
- (No kuga_sub\_\_\* fields present)

**Quote:**

- `kugo2p__TotalAmount__c`: $120,000

**Correct interpretation:** Quote matches Amount ($120,000).

## Best Practices

1. **Always query ALL amount fields** before making comparisons
2. **Check for presence of subscription fields** to determine comparison strategy
3. **Show all relevant amounts** in user-facing summaries
4. **Never assume** what `Amount` represents - let the data guide you
5. **Document discrepancies clearly** when amounts don't match expected patterns

## Common Scenarios

### Scenario: Quote total doesn't match Amount

**Before claiming mismatch:**

1. Check if subscription fields exist
2. Compare quote to `kuga_sub__AnnualContractValueInitial__c` instead
3. If they match, explain that Amount shows MRR while quote shows ACV

### Scenario: User asks "Why is the quote different from the opportunity?"

**Response should include:**

1. All amount field values from opportunity
2. Quote total amount
3. Clear explanation of which fields should be compared
4. Calculation showing how values relate (e.g., MRR × 12 = ACV)

### Scenario: Updating instructions or documentation

**Key points to convey:**

1. Field interpretation depends on org configuration
2. Subscription orgs use different fields than standard orgs
3. Always query subscription fields to determine comparison approach
