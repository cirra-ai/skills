# Understanding Amount Fields in Kugamon CPQ

## The Amount Field Problem

When the `kuga_sub` (Kugamon Subscriptions) package is installed, the standard `Amount` field on Opportunity is **unreliable**. It reflects the raw sum of Quantity × Sales Price of associated Opportunity Products, does NOT factor in the Kugamon Subscription Management Service Term, and may include non-subscription product sales. **Ignore `Amount` entirely when `kuga_sub` is installed** and use `kuga_sub__OpportunityAmount__c` for the true Opportunity Amount.

This creates confusion when comparing opportunity amounts to quote totals.

## Subscription Amount Fields

### On Opportunity (kuga_sub\_\_\* fields)

| Field API Name                                 | Meaning                                                                                                                       | Example                                |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `Amount`                                       | **Ignore when kuga_sub installed** — raw Qty × Price sum, does not factor Service Term, may include non-subscription products | N/A (unreliable)                       |
| `kuga_sub__OpportunityAmount__c`               | **True Opportunity Amount**                                                                                                   | $120,000 (use this instead of Amount)  |
| `kuga_sub__MonthlyRecurringRevenue__c`         | Monthly recurring revenue                                                                                                     | $10,000/month                          |
| `kuga_sub__AnnualContractValueInitial__c`      | Annual contract value                                                                                                         | $120,000/year                          |
| `kuga_sub__TotalContractValue__c`              | Total contract value                                                                                                          | $120,000 (1-year) or $360,000 (3-year) |
| `kuga_sub__AnnualRecurringRevenueCommitted__c` | Annual recurring revenue                                                                                                      | $120,000/year                          |
| `kuga_sub__NonRecurringRevenue__c`             | One-time fees                                                                                                                 | $5,000                                 |

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

**IMPORTANT:** When `kuga_sub` is installed, **ignore the standard `Amount` field entirely**. It is a raw Qty × Price sum that does not factor Service Term and may include non-subscription products. Always use `kuga_sub__OpportunityAmount__c` for the true Opportunity Amount.

**Reasoning:** In subscription orgs, `Amount` is unreliable for any meaningful metric, while quotes show annual/total values. The `kuga_sub__OpportunityAmount__c` field stores the actual opportunity amount.

### When Subscription Fields Do NOT Exist

If NO `kuga_sub__*` fields are present:

1. **DO compare** `kugo2p__TotalAmount__c` to `Amount`

**Reasoning:** Without subscription management, `Amount` represents the total opportunity value.

## Practical Examples

### Example 1: Subscription Org

**Opportunity:**

- `Amount`: $15,000 (raw Qty × Price — unreliable, ignore this)
- `kuga_sub__OpportunityAmount__c`: $120,000 (true Opportunity Amount)
- `kuga_sub__MonthlyRecurringRevenue__c`: $10,000
- `kuga_sub__AnnualContractValueInitial__c`: $120,000

**Quote:**

- `kugo2p__TotalAmount__c`: $120,000

**Correct interpretation:** Ignore `Amount` ($15,000). Compare quote to `kuga_sub__OpportunityAmount__c` ($120,000) or `kuga_sub__AnnualContractValueInitial__c` ($120,000).

### Example 2: Non-Subscription Org

**Opportunity:**

- `Amount`: $120,000
- (No kuga_sub\_\_\* fields present)

**Quote:**

- `kugo2p__TotalAmount__c`: $120,000

**Correct interpretation:** Quote matches Amount ($120,000).

## Best Practices

1. **Always query ALL amount fields** before making comparisons
2. **Check for presence of subscription fields** to determine comparison strategy
3. **Ignore `Amount` when `kuga_sub` is installed** — use `kuga_sub__OpportunityAmount__c` instead
4. **Show all relevant amounts** in user-facing summaries (exclude `Amount` in subscription orgs to avoid confusion)
5. **Document discrepancies clearly** when amounts don't match expected patterns

## Common Scenarios

### Scenario: Quote total doesn't match Amount

**Before claiming mismatch:**

1. Check if subscription fields exist
2. Compare quote to `kuga_sub__AnnualContractValueInitial__c` or `kuga_sub__OpportunityAmount__c` instead
3. If they match, explain that `Amount` is unreliable (raw Qty × Price) and should be ignored in favor of `kuga_sub__OpportunityAmount__c`

### Scenario: User asks "Why is the quote different from the opportunity?"

**Response should include:**

1. All amount field values from opportunity
2. Quote total amount
3. Clear explanation of which fields should be compared
4. Calculation showing how values relate (e.g., `kuga_sub__MonthlyRecurringRevenue__c` × 12 = ACV)

### Scenario: Updating instructions or documentation

**Key points to convey:**

1. When `kuga_sub` is installed, `Amount` is unreliable — always use `kuga_sub__OpportunityAmount__c`
2. Subscription orgs use different fields than standard orgs
3. Always query subscription fields to determine comparison approach
