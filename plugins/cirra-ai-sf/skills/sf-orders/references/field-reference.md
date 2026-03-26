# Order Management Field Reference

## Order Object (Standard)

### Key Fields

| Field API Name  | Type               | Description           | Notes                      |
| --------------- | ------------------ | --------------------- | -------------------------- |
| `Id`            | ID                 | Salesforce record ID  | 15 or 18 character format  |
| `OrderNumber`   | Auto Number        | Human-readable number | e.g., "00000100"           |
| `Status`        | Picklist           | Order status          | Draft, Activated, etc.     |
| `TotalAmount`   | Currency           | Total order value     | Calculated from line items |
| `AccountId`     | Lookup(Account)    | Related account       | Required                   |
| `EffectiveDate` | Date               | Order start date      | Required for activation    |
| `EndDate`       | Date               | Order end date        | Optional                   |
| `Type`          | Picklist           | Order type            | Optional                   |
| `Description`   | Text Area          | Order description     | Optional                   |
| `Pricebook2Id`  | Lookup(Pricebook2) | Price book            | Required for order items   |
| `ContractId`    | Lookup(Contract)   | Related contract      | Optional                   |

## OrderItem Object (Standard)

### Key Fields

| Field API Name     | Type                   | Description       | Notes                            |
| ------------------ | ---------------------- | ----------------- | -------------------------------- |
| `Id`               | ID                     | Record ID         |                                  |
| `OrderId`          | Lookup(Order)          | Parent order      | Required                         |
| `Product2Id`       | Lookup(Product2)       | Product reference | Required                         |
| `PricebookEntryId` | Lookup(PricebookEntry) | Pricebook entry   | Required for creation            |
| `Quantity`         | Number                 | Quantity ordered  | Required, min 1                  |
| `UnitPrice`        | Currency               | Unit price        | Required                         |
| `TotalPrice`       | Currency               | Line total        | Calculated: Quantity x UnitPrice |
| `Description`      | Text                   | Line description  | Optional                         |
| `ServiceDate`      | Date                   | Service date      | Optional                         |

## ReturnOrder Object (Standard — requires Service Cloud)

### Key Fields

| Field API Name      | Type            | Description             | Notes                                                |
| ------------------- | --------------- | ----------------------- | ---------------------------------------------------- |
| `Id`                | ID              | Record ID               |                                                      |
| `ReturnOrderNumber` | Auto Number     | Human-readable number   | Auto-generated                                       |
| `OrderId`           | Lookup(Order)   | Original order          | Required                                             |
| `AccountId`         | Lookup(Account) | Related account         | Required                                             |
| `Status`            | Picklist        | Return status           | See status-transitions.md                            |
| `Description`       | Text Area       | Return description      | Optional                                             |
| `CaseId`            | Lookup(Case)    | Related support case    | Standard field, may not be available in all editions |
| `ReturnedById`      | Lookup(User)    | User who created return | Auto-populated                                       |

### Optional Custom Fields (for label tracking)

| Field API Name          | Type     | Description                      | Default |
| ----------------------- | -------- | -------------------------------- | ------- |
| `LabelEmailSent__c`     | Checkbox | Whether return label was emailed | false   |
| `LabelEmailSentDate__c` | DateTime | When the label email was sent    | null    |

## ReturnOrderLineItem Object (Standard)

### Key Fields

| Field API Name     | Type                | Description            | Notes                    |
| ------------------ | ------------------- | ---------------------- | ------------------------ |
| `Id`               | ID                  | Record ID              |                          |
| `ReturnOrderId`    | Lookup(ReturnOrder) | Parent return order    | Required                 |
| `OrderItemId`      | Lookup(OrderItem)   | Original order item    | Required                 |
| `Product2Id`       | Lookup(Product2)    | Product being returned | Required                 |
| `QuantityReturned` | Number              | Quantity returned      | Required, min 1          |
| `Description`      | Text                | Return reason/notes    | Optional                 |
| `ReasonCode`       | Picklist            | Return reason code     | Optional (org-dependent) |

## Case Object (Standard)

### Key Fields for Order Management

| Field API Name | Type               | Description     | Notes                           |
| -------------- | ------------------ | --------------- | ------------------------------- |
| `Id`           | ID                 | Record ID       |                                 |
| `CaseNumber`   | Auto Number        | Case number     | Auto-generated                  |
| `Subject`      | Text               | Case subject    | Required                        |
| `Description`  | Text Area          | Case details    |                                 |
| `Status`       | Picklist           | Case status     | New, Working, Escalated, Closed |
| `Priority`     | Picklist           | Case priority   | Low, Medium, High, Critical     |
| `Origin`       | Picklist           | Case origin     | Web, Phone, Email               |
| `Type`         | Picklist           | Case type       |                                 |
| `AccountId`    | Lookup(Account)    | Related account |                                 |
| `OwnerId`      | Lookup(User/Queue) | Case owner      |                                 |
| `IsClosed`     | Boolean            | Is case closed? | Read-only, derived from Status  |

### CaseComment Object

| Field API Name | Type         | Description          | Notes          |
| -------------- | ------------ | -------------------- | -------------- |
| `ParentId`     | Lookup(Case) | Parent case          | Required       |
| `CommentBody`  | Text Area    | Comment text         | Required       |
| `IsPublished`  | Boolean      | Visible to customer? | Default: false |

## Object Relationships

```
Account
  └── Order
  │     └── OrderItem (Product2)
  │           └── ReturnOrderLineItem
  └── ReturnOrder (→ Order)
  │     └── ReturnOrderLineItem (→ OrderItem)
  │     └── Case (via CaseId)
  └── Case
        └── CaseComment
```

## ID Prefix Reference

| Prefix | Object      |
| ------ | ----------- |
| `001`  | Account     |
| `006`  | Opportunity |
| `800`  | Order       |
| `802`  | OrderItem   |
| `801`  | ReturnOrder |
| `500`  | Case        |
