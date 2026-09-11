# CRUD Workflow Example

Complete end-to-end example of data operations using sf-data skill.

## Scenario

Create a Deal Desk workflow test environment with:

- Accounts with varying revenue tiers
- Contacts as decision makers
- Opportunities at different stages

## Phase 1: Discovery (sf-metadata)

```
Skill(skill="sf-metadata")
Request: "Describe object Account - show required fields and picklist values"
```

**Response shows:**

- Required: Name
- Picklists: Industry, Type, Rating

## Phase 2: Create Records (sf-data)

### Cirra AI MCP - Single Record

```
sobject_dml(
  operation="insert",
  sObject="Account",
  records=[{"Name": "Enterprise Corp", "Industry": "Technology", "AnnualRevenue": 5000000}]
)
```

**Output:**

```json
{
  "status": 0,
  "result": {
    "id": "001XXXXXXXXXXXX",
    "success": true
  }
}
```

### Cirra AI MCP - Query Created Record

```
soql_query(
  sObject="Account",
  fields=["Id", "Name", "Industry", "AnnualRevenue"],
  whereClause="Name = 'Enterprise Corp'"
)
```

## Phase 3: Update Records

### Update Single Record

```
sobject_dml(
  operation="update",
  sObject="Account",
  records=[{"Id": "001XXXXXXXXXXXX", "Rating": "Hot", "Type": "Customer - Direct"}]
)
```

### Verify Update

```
soql_query(
  sObject="Account",
  fields=["Id", "Name", "Rating", "Type"],
  whereClause="Id = '001XXXXXXXXXXXX'"
)
```

## Phase 4: Create Related Records

### Create Contact for Account

```
sobject_dml(
  operation="insert",
  sObject="Contact",
  records=[{"FirstName": "John", "LastName": "Smith", "AccountId": "001XXXXXXXXXXXX", "Title": "CTO"}]
)
```

### Create Opportunity

```
sobject_dml(
  operation="insert",
  sObject="Opportunity",
  records=[{"Name": "Enterprise Deal", "AccountId": "001XXXXXXXXXXXX", "StageName": "Prospecting", "CloseDate": "2025-03-31", "Amount": 250000}]
)
```

## Phase 5: Query Relationships

### Parent-to-Child (Subquery)

```
soql_query(
  sObject="Account",
  fields=["Id", "Name", "(SELECT Id, Name, Title FROM Contacts)", "(SELECT Id, Name, Amount, StageName FROM Opportunities)"],
  whereClause="Name = 'Enterprise Corp'"
)
```

If the server rejects a subquery in `fields`, run two queries instead: the
parent, then the children filtered by `AccountId IN (...)`.

### Child-to-Parent (Dot Notation)

```
soql_query(
  sObject="Contact",
  fields=["Id", "Name", "Account.Name", "Account.Industry"],
  whereClause="Account.Name = 'Enterprise Corp'"
)
```

## Phase 6: Delete Records

### Delete in Correct Order

Children first, then parents:

```
# Delete Opportunities
sobject_dml(operation="delete", sObject="Opportunity", recordIds=["006XXXXXXXXXXXX"])

# Delete Contacts
sobject_dml(operation="delete", sObject="Contact", recordIds=["003XXXXXXXXXXXX"])

# Delete Account
sobject_dml(operation="delete", sObject="Account", recordIds=["001XXXXXXXXXXXX"])
```

Delete takes `recordIds` (a string array), never `records`. For more than
200 IDs use `bulk_dml(operation="delete", ...)`.

## Apex Test-Class Alternative

Cirra cannot run anonymous Apex. When the hierarchy must be built inside a
test transaction, hand this to **sf-apex** as a test class (or `@testSetup`
method) and run it with `run_tests`:

```apex
// Inside an @isTest method: create the complete hierarchy in one transaction
Account acc = new Account(
    Name = 'Enterprise Corp',
    Industry = 'Technology',
    AnnualRevenue = 5000000
);
insert acc;

Contact con = new Contact(
    FirstName = 'John',
    LastName = 'Smith',
    AccountId = acc.Id,
    Title = 'CTO'
);
insert con;

Opportunity opp = new Opportunity(
    Name = 'Enterprise Deal',
    AccountId = acc.Id,
    ContactId = con.Id,
    StageName = 'Prospecting',
    CloseDate = Date.today().addDays(90),
    Amount = 250000
);
insert opp;

System.debug('Created hierarchy: Account=' + acc.Id + ', Contact=' + con.Id + ', Opp=' + opp.Id);
```

Execute:

```
run_tests(tests=[{"className": "DealDeskDataTest"}])
```

For persistent demo data, stay with the `sobject_dml` calls above — or
`bulk_dml` once the set grows past 200 records.

## Validation Score

```
Score: 125/130 ⭐⭐⭐⭐⭐ Excellent
├─ Query Efficiency: 25/25 (indexed fields, no N+1)
├─ Bulk Safety: 23/25 (single records OK for demo)
├─ Data Integrity: 20/20 (all required fields)
├─ Security & FLS: 20/20 (no PII exposed)
├─ Test Patterns: 12/15 (single record demo)
├─ Cleanup & Isolation: 15/15 (proper delete order)
└─ Documentation: 10/10 (fully documented)
```
