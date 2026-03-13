# Kugamon Subscription Management - Order Release Lifecycle

## Prerequisites

Subscription Management is active when ALL of the following are true:

1. The `kuga_sub` (Kugamon Subscriptions) package is installed
2. The Kugamon Settings custom setting `kuga_sub__InitiateOrderSubscriptionManagement__c` is NOT null

**Detection query:**

```sql
SELECT Id, kuga_sub__InitiateOrderSubscriptionManagement__c, kuga_sub__ExtendContractOnRenewal__c
FROM kuga_sub__KugamonSettings__c
LIMIT 1
```

## Record Types

Three Record Types exist on Opportunity, Kugamon Quote (`kugo2p__SalesQuote__c`), and Kugamon Order (`kugo2p__SalesOrder__c`):

| Record Type   | Purpose                                                | Contract Behavior                                |
| ------------- | ------------------------------------------------------ | ------------------------------------------------ |
| **New**       | Initial sale to an Account                             | Creates new Contract                             |
| **Expansion** | Additional products/services tied to existing Contract | Amends existing Contract                         |
| **Renewal**   | Extending an existing Contract                         | Extends or replaces Contract (setting-dependent) |

**Record Type inheritance:** The Record Type flows from Opportunity → Quote → Order. A New Opportunity produces New Quotes and New Orders.

## Configuration Fields That Control Behavior

### Asset Creation

- **Object:** `kugo2p__AdditionalProductDetail__c` (related to Product)
- **Field:** `kugo2p__CreateAsset__c`
- **Rule:** If this field is NOT null, an Asset is created when the Order Product Line is released
- **Applies to:** Order Product Lines only

### Subscription Creation

- **Object:** `Product2` (standard Product object)
- **Field:** `kuga_sub__CreateSubscription__c`
- **Rule:** If this field = True, a Subscription is created when the Order Service Line is released
- **Applies to:** Order Service Lines only

### Renewal Opportunity Line Item Creation

- **Object:** Order Service Line
- **Field:** `kuga_sub__Renew__c` (or equivalent Renew field)
- **Rule:** If this field = True, the service line is added as an Opportunity Line Item on the Renewal Opportunity
- **Applies to:** Order Service Lines only

### Contract Extension vs Replacement (Renewals only)

- **Object:** `kuga_sub__KugamonSettings__c`
- **Field:** `kuga_sub__ExtendContractOnRenewal__c`
- **Rule:** If True, the existing Contract is extended on Renewal. If False, a Replacement Contract is created.

## New Record Type - Detailed Behavior

### Trigger

A Kugamon Order with **New** Record Type is Released.

### Actions Performed

1. **Contract Creation**
   - A new Contract record is created and linked to the Account
   - This is the "master" Contract for this deal

2. **Asset Creation** (conditional per Product Line)
   - For EACH Order Product Line:
     - Query the related `kugo2p__AdditionalProductDetail__c` record
     - If `kugo2p__CreateAsset__c` is NOT null → Create an Asset record
     - If `kugo2p__CreateAsset__c` IS null → No Asset created for this line
   - Assets are linked to the new Contract

3. **Subscription Creation** (conditional per Service Line)
   - For EACH Order Service Line:
     - Query the related `Product2` record
     - If `kuga_sub__CreateSubscription__c` = True → Create a Subscription record
     - If `kuga_sub__CreateSubscription__c` = False → No Subscription created for this line
   - Subscriptions are linked to the new Contract

4. **Renewal Opportunity Creation** (conditional - requires at least one renewable line)
   - Check if ANY Order Service Lines have `kuga_sub__Renew__c` = True
   - If YES:
     - Create a future-dated Opportunity with **Renewal** Record Type
     - Populate Opportunity Line Items from all renewable service lines
   - If NO renewable lines exist → No Renewal Opportunity is created

### Verification Queries (Post-Release)

```sql
-- Check Contract was created
SELECT Id, ContractNumber, AccountId, Status, StartDate, EndDate
FROM Contract
WHERE AccountId = '<account_id>'
ORDER BY CreatedDate DESC
LIMIT 5

-- Check Assets were created
SELECT Id, Name, Product2Id, AccountId, Quantity
FROM Asset
WHERE AccountId = '<account_id>'
ORDER BY CreatedDate DESC
LIMIT 10

-- Check Renewal Opportunity was created
SELECT Id, Name, RecordType.Name, StageName, CloseDate, AccountId
FROM Opportunity
WHERE AccountId = '<account_id>'
AND RecordType.Name = 'Renewal'
ORDER BY CreatedDate DESC
LIMIT 5
```

## Expansion Record Type - Detailed Behavior

### Trigger

A Kugamon Order with **Expansion** Record Type is Released.

### Prerequisites

- The Order must have a **Contract Number** field populated (links to the existing Contract being expanded)
- The Order must have a **Renewal Opportunity Name** field populated (links to the existing Renewal Opportunity)

### Actions Performed

1. **Contract Amendment**
   - The existing Contract (referenced by Order's `Contract Number`) is amended
   - NO new Contract is created

2. **Asset Creation** (conditional per Product Line)
   - Same conditional logic as New
   - Assets are assigned to the Order's `Contract Number` (the existing Contract)

3. **Subscription Creation** (conditional per Service Line)
   - Same conditional logic as New
   - Subscriptions are assigned to the Order's `Contract Number` (the existing Contract)

4. **Add Lines to Existing Renewal Opportunity** (conditional per Service Line)
   - NO new Renewal Opportunity is created
   - For EACH renewable Order Service Line (where `kuga_sub__Renew__c` = True):
     - An Opportunity Line Item is added to the existing Renewal Opportunity (referenced by Order's `Renewal Opportunity Name`)

### Key Difference from New

- Contract is amended, not created
- All new Assets/Subscriptions are linked to the EXISTING Contract
- Renewal Opportunity Line Items are ADDED to the EXISTING Renewal Opportunity (not a new one)

## Renewal Record Type - Detailed Behavior

### Trigger

A Kugamon Order with **Renewal** Record Type is Released.

### Prerequisites

- The Order must have a **Contract Number** field populated (links to the Contract being renewed)

### Behavior Fork: Extend vs Replace

Query the Kugamon Setting to determine which path:

```sql
SELECT kuga_sub__ExtendContractOnRenewal__c
FROM kuga_sub__KugamonSettings__c
LIMIT 1
```

### Path A: Extend Contract (ExtendContractOnRenewal = True)

1. **Contract Extension**
   - The existing Contract (referenced by Order's `Contract Number`) is amended/extended
   - NO new Contract is created

2. **Asset Creation** (conditional per Product Line)
   - Same conditional logic as New
   - Assets are linked to the extended Contract

3. **Subscription Creation** (conditional per Service Line)
   - Same conditional logic as New
   - Subscriptions are linked to the extended Contract

4. **Replacement Renewal Opportunity** (conditional)
   - If any Order Service Lines have `kuga_sub__Renew__c` = True:
     - A new future-dated Renewal Opportunity REPLACES the previous one
     - Populated with Opportunity Line Items from renewable service lines

### Path B: Replace Contract (ExtendContractOnRenewal = False)

1. **Existing Contract Amendment**
   - The original Contract is amended/closed

2. **Replacement Contract Creation**
   - A brand new Contract is created
   - This becomes the new "master" Contract

3. **Asset Creation** (conditional per Product Line)
   - Same as New Record Type behavior
   - Assets linked to the new Replacement Contract

4. **Subscription Creation** (conditional per Service Line)
   - Same as New Record Type behavior
   - Subscriptions linked to the new Replacement Contract

5. **Renewal Opportunity Creation** (conditional)
   - Same as New Record Type behavior
   - A new future-dated Renewal Opportunity is created
   - Populated with Opportunity Line Items from renewable service lines

## Complete Decision Matrix

| Scenario              | Contract           | Assets                                              | Subscriptions                                | Renewal Opp                          |
| --------------------- | ------------------ | --------------------------------------------------- | -------------------------------------------- | ------------------------------------ |
| **New**               | Create new         | Create if AdditionalProductInfo.CreateAsset != null | Create if Product2.CreateSubscription = True | Create new if any lines Renew = True |
| **Expansion**         | Amend existing     | Create & assign to existing Contract                | Create & assign to existing Contract         | Add lines to existing Renewal Opp    |
| **Renewal (Extend)**  | Extend existing    | Create                                              | Create                                       | Create replacement Renewal Opp       |
| **Renewal (Replace)** | Create replacement | Create (same as New)                                | Create (same as New)                         | Create new (same as New)             |

## Troubleshooting Order Release

### Assets Not Created

1. Verify `kugo2p__AdditionalProductDetail__c` exists for the Product
2. Check that `kugo2p__CreateAsset__c` is NOT null on that record
3. Query: `SELECT Id, kugo2p__CreateAsset__c FROM kugo2p__AdditionalProductDetail__c WHERE kugo2p__Product__c = '<product_id>'`

### Subscriptions Not Created

1. Verify `kuga_sub__CreateSubscription__c` = True on the Product2 record
2. Query: `SELECT Id, Name, kuga_sub__CreateSubscription__c FROM Product2 WHERE Id = '<product_id>'`

### Renewal Opportunity Not Created

1. Verify at least one Order Service Line has `kuga_sub__Renew__c` = True
2. Check that Subscription Management is active (KugamonSettings.InitiateOrderSubscriptionManagement != null)

### Expansion Order Not Linking Correctly

1. Verify the Order has `Contract Number` populated
2. Verify the Order has `Renewal Opportunity Name` populated
3. If either is missing, the Expansion behaviors for that area will not execute

### Wrong Contract Behavior on Renewal

1. Check `kuga_sub__ExtendContractOnRenewal__c` in KugamonSettings
2. True = extend existing Contract (no new one)
3. False = create replacement Contract
