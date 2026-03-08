# Kugamon CPQ Field Reference

## Opportunity Fields

### Required Fields

| Field API Name | Type      | Description         | Default/Notes                                |
| -------------- | --------- | ------------------- | -------------------------------------------- |
| `Name`         | Text(120) | Opportunity name    | Required for creation                        |
| `StageName`    | Picklist  | Current stage       | Use "Qualification" when creating with quote |
| `CloseDate`    | Date      | Expected close date | Required for creation                        |

### Strongly Recommended Fields

| Field API Name | Type               | Description     | Default/Notes                             |
| -------------- | ------------------ | --------------- | ----------------------------------------- |
| `AccountId`    | Lookup(Account)    | Related account | Required for Kugamon CPQ to work properly |
| `Pricebook2Id` | Lookup(Pricebook2) | Price book      | Required if adding opportunity products   |

### Optional but Useful Fields

| Field API Name | Type               | Description             | Default/Notes                                               |
| -------------- | ------------------ | ----------------------- | ----------------------------------------------------------- |
| `Amount`       | Currency           | Total opportunity value | Auto-calculated from line items if products exist           |
| `Type`         | Picklist           | Opportunity type        | E.g., "New Business", "Existing Business"                   |
| `RecordTypeId` | Lookup(RecordType) | Record type             | Map to quote record type (New/Renewal/Expansion)            |
| `ContactId`    | Lookup(Contact)    | Primary contact         | Optional, use OpportunityContactRole for full relationships |

### Kugamon Subscription Fields (Calculated)

All these are **read-only calculated fields** - do not set them manually:

| Field API Name                                 | Description      | Calculation                         |
| ---------------------------------------------- | ---------------- | ----------------------------------- |
| `kuga_sub__MonthlyRecurringRevenue__c`         | MRR              | Roll-up sum from line items         |
| `kuga_sub__AnnualRecurringRevenueCommitted__c` | ARR              | Roll-up sum from line items         |
| `kuga_sub__AnnualRecurringRevenueForecast__c`  | ARR forecast     | MRR × 12                            |
| `kuga_sub__NonRecurringRevenue__c`             | One-time revenue | Roll-up sum from line items         |
| `kuga_sub__AnnualContractValueInitial__c`      | ACV              | NonRecurring + ARR                  |
| `kuga_sub__TotalContractValue__c`              | TCV              | Net amount from primary quote/order |

## OpportunityLineItem Fields

### Required Fields

| Field API Name       | Type                   | Description             | Default/Notes                                                |
| -------------------- | ---------------------- | ----------------------- | ------------------------------------------------------------ |
| `OpportunityId`      | Lookup(Opportunity)    | Parent opportunity      | Required                                                     |
| `PricebookEntryId`   | Lookup(PricebookEntry) | Product pricebook entry | Required - links to product via pricebook                    |
| `Quantity`           | Number(10,2)           | Quantity                | Required, minimum 1                                          |
| `kuga_sub__Renew__c` | Checkbox               | Is this recurring?      | **CRITICAL**: Defaults to false. Set true for subscriptions! |

### Important Optional Fields

| Field API Name | Type     | Description           | Default/Notes                              |
| -------------- | -------- | --------------------- | ------------------------------------------ |
| `UnitPrice`    | Currency | Unit price override   | Optional - uses pricebook price if omitted |
| `ServiceDate`  | Date     | Service start date    | Optional                                   |
| `Discount`     | Percent  | Discount percentage   | Optional                                   |
| `Description`  | Text     | Line item description | Optional                                   |

### Kugamon Subscription Fields

| Field API Name                | Type     | Description          | Default/Notes                           |
| ----------------------------- | -------- | -------------------- | --------------------------------------- |
| `kuga_sub__ServiceTerm__c`    | Number   | Contract term length | E.g., 12, 24, 36                        |
| `kuga_sub__UnitofTerm__c`     | Picklist | Term unit            | "Month" or "Year"                       |
| `kuga_sub__DateServiceEnd__c` | Date     | Service end date     | Auto-calculated from ServiceDate + Term |

### Kugamon Calculated Fields (Read-Only)

These are **populated by Kugamon automation** based on `kuga_sub__Renew__c`:

| Field API Name                     | Description               | When Renew=true       | When Renew=false      |
| ---------------------------------- | ------------------------- | --------------------- | --------------------- |
| `kuga_sub__MRR__c`                 | Monthly recurring revenue | Calculated from price | 0                     |
| `kuga_sub__ARR__c`                 | Annual recurring revenue  | MRR × 12              | 0                     |
| `kuga_sub__NonRecurringRevenue__c` | One-time revenue          | 0                     | Total line amount     |
| `kuga_sub__Service__c`             | Is this a service?        | Formula field         | Formula field         |
| `kuga_sub__NetAmount__c`           | Net amount                | Total after discounts | Total after discounts |

## Quote Fields (kugo2p**SalesQuote**c)

### Required Fields for Creation

| Field API Name           | Type                | Description         | Default/Notes                          |
| ------------------------ | ------------------- | ------------------- | -------------------------------------- |
| `kugo2p__Account__c`     | Lookup(Account)     | Related account     | Required                               |
| `kugo2p__Opportunity__c` | Lookup(Opportunity) | Related opportunity | Required                               |
| `RecordTypeId`           | Lookup(RecordType)  | Quote record type   | Map to opp type: New/Renewal/Expansion |

### Optional but Recommended Fields

| Field API Name                     | Type               | Description       | Default/Notes                      |
| ---------------------------------- | ------------------ | ----------------- | ---------------------------------- |
| `kugo2p__QuoteName__c`             | Text               | Quote name        | Descriptive name for the quote     |
| `kugo2p__Pricebook2Id__c`          | Lookup(Pricebook2) | Pricebook         | Should match opportunity pricebook |
| `kugo2p__IsPrimary__c`             | Checkbox           | Is primary quote? | Set to true if first/primary quote |
| `kugo2p__DateOfferValidThrough__c` | Date               | Expiration date   | Default: 30 days from today        |

### Auto-Managed Fields (Never Set These)

| Field API Name              | Description  | Notes                                            |
| --------------------------- | ------------ | ------------------------------------------------ |
| `Name`                      | Quote number | Auto-generated (e.g., SQ-251108-0000010)         |
| `kugo2p__Status__c`         | Quote status | Workflow-managed (Draft/Sent/Won/Lost/Cancelled) |
| `kugo2p__TotalAmount__c`    | Total amount | Calculated from line items                       |
| `kugo2p__SubtotalAmount__c` | Subtotal     | Calculated from line items                       |
| `kugo2p__NetAmount__c`      | Net amount   | Total after discounts/taxes                      |

## Quote Line Item Object (kugo2p**SalesQuoteServiceLine**c)

### Key Fields

| Field API Name           | Type     | Description                   |
| ------------------------ | -------- | ----------------------------- |
| `kugo2p__SalesQuote__c`  | Lookup   | Parent quote                  |
| `kugo2p__Service__c`     | Lookup   | Product/service reference     |
| `kugo2p__ServiceName__c` | Text     | Product/service name          |
| `kugo2p__Line__c`        | Formula  | Line number with HTML link    |
| `kugo2p__Quantity__c`    | Number   | Quantity                      |
| `kugo2p__SalesPrice__c`  | Currency | Unit price                    |
| `kugo2p__TotalAmount__c` | Currency | Line total (Quantity × Price) |

## Field Interdependencies

### Opportunity Product Requirements

To add products to an opportunity:

1. Opportunity must have `Pricebook2Id` set
2. Product must have a `PricebookEntry` in that pricebook
3. Use `PricebookEntryId` (not `Product2Id`) when creating line item

### Quote Creation Requirements

To create a valid Kugamon quote:

1. Opportunity must exist with `Pricebook2Id`
2. Opportunity should have products (line items)
3. Quote `RecordTypeId` should match opportunity type
4. Quote `kugo2p__Pricebook2Id__c` should match opportunity pricebook

### Revenue Calculation Dependencies

For proper revenue calculations:

1. Set `kuga_sub__Renew__c` correctly on line items
2. For recurring products: Set `ServiceTerm` and `UnitofTerm`
3. Kugamon automation will populate MRR/ARR/NonRecurring fields
4. These roll up to opportunity-level fields
5. ACV is calculated as NonRecurring + ARR

## Common Mistakes

### ❌ Wrong: Using Product2Id directly

```javascript
{
  "OpportunityId": "006xxx",
  "Product2Id": "01txxx",  // WRONG - will fail
  "Quantity": 1
}
```

### ✅ Correct: Using PricebookEntryId

```javascript
{
  "OpportunityId": "006xxx",
  "PricebookEntryId": "01uxxx",  // CORRECT
  "Quantity": 1
}
```

### ❌ Wrong: Omitting Renew for recurring products

```javascript
{
  "OpportunityId": "006xxx",
  "PricebookEntryId": "01uxxx",
  "Quantity": 1,
  "UnitPrice": 2000
  // Missing kuga_sub__Renew__c - will default to false!
}
```

### ✅ Correct: Setting Renew for recurring products

```javascript
{
  "OpportunityId": "006xxx",
  "PricebookEntryId": "01uxxx",
  "Quantity": 1,
  "UnitPrice": 2000,
  "kuga_sub__Renew__c": true  // CORRECT - marks as recurring
}
```

## Quick Reference Examples

### Creating an Opportunity

```javascript
{
  "Name": "Acme Corp - Annual Subscription",
  "AccountId": "001xxx",
  "StageName": "Qualification",
  "CloseDate": "2025-12-31",
  "Pricebook2Id": "01sxxx",
  "RecordTypeId": "012xxx"
}
```

### Creating a Recurring Line Item

```javascript
{
  "OpportunityId": "006xxx",
  "PricebookEntryId": "01uxxx",
  "Quantity": 1,
  "UnitPrice": 2000,
  "kuga_sub__Renew__c": true,
  "kuga_sub__ServiceTerm__c": 12,
  "kuga_sub__UnitofTerm__c": "Month"
}
```

### Creating a One-Time Line Item

```javascript
{
  "OpportunityId": "006xxx",
  "PricebookEntryId": "01uxxx",
  "Quantity": 1,
  "UnitPrice": 15000,
  "kuga_sub__Renew__c": false
}
```

### Creating a Quote

```javascript
{
  "RecordTypeId": "012Ho000001bKakIAE",
  "kugo2p__Account__c": "001xxx",
  "kugo2p__Opportunity__c": "006xxx",
  "kugo2p__QuoteName__c": "Q4 2025 Quote",
  "kugo2p__Pricebook2Id__c": "01sxxx",
  "kugo2p__IsPrimary__c": true,
  "kugo2p__DateOfferValidThrough__c": "2025-12-31"
}
```
