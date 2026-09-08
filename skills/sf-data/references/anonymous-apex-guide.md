# Apex Data Scripts (test classes and sf-apex)

**The Cirra AI MCP Server cannot execute anonymous Apex.** Every Apex snippet
in this guide — and every factory in `assets/factories/` — only runs as a
**deployed Apex test class** (created and deployed through **sf-apex**,
executed with `run_tests`) or inside other Apex that sf-apex deploys. Do not
present these scripts as something sf-data can run. For seeding, transforming
or deleting org data from a conversation, use `sobject_dml` (up to 200
records) or `bulk_dml` (more) — see `bulk-operations-guide.md`.

## When Apex is still the right tool

- Test classes that need data built in the test transaction (`@testSetup`,
  `Test.startTest()` / `Test.stopTest()` governor-limit isolation)
- Trigger and flow unit tests that assert on side effects in the same
  transaction
- Logic that must run as Apex (savepoints, `Database.rollback`, complex
  branching per record) — hand it to sf-apex as a class or batch job

## The MCP equivalents

```
# Insert records (up to 200 per call)
sobject_dml(operation="insert", sObject="Account", records=[
  {"Name": "Test Account 1", "Industry": "Technology"}
])

# Insert thousands of records (one Bulk API job)
bulk_dml(operation="insert", sObject="Account", records=[...])

# Read records
soql_query(sObject="Account", fields=["Id", "Name"], whereClause="Name LIKE 'Test%'")

# Run the deployed test class that uses a factory
run_tests(tests=[{"className": "AccountTriggerTest"}])
```

## Common patterns (inside a test class)

### Bulk data creation

```apex
@isTest
static void insertsInBulk() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 500; i++) {
        accounts.add(new Account(
            Name = 'Test Account ' + i,
            Industry = 'Technology'
        ));
    }
    Test.startTest();
    insert accounts;
    Test.stopTest();
    System.assertEquals(500, [SELECT COUNT() FROM Account WHERE Name LIKE 'Test Account %']);
}
```

### Data transformation

```apex
List<Account> accounts = [
    SELECT Id, Name, Industry
    FROM Account
    WHERE Name LIKE 'Old%'
];

for (Account acc : accounts) {
    acc.Name = acc.Name.replace('Old', 'New');
}

update accounts;
```

Outside a test class, do the same with `bulk_query` (read) and
`bulk_dml(operation="update")` (write).

### Testing trigger logic

```apex
// Setup test data
Account acc = new Account(Name = 'Trigger Test');
insert acc;

// Force trigger to fire
acc.Industry = 'Technology';
update acc;

// Verify results
acc = [SELECT Id, Field__c FROM Account WHERE Id = :acc.Id];
System.assertNotEquals(null, acc.Field__c);
```

## Error handling

```apex
try {
    insert accounts;
} catch (DmlException e) {
    for (Integer i = 0; i < e.getNumDml(); i++) {
        System.debug('Row ' + e.getDmlIndex(i) + ': ' + e.getDmlMessage(i));
    }
}
```

## Apex governor limits (synchronous)

| Limit        | Value     |
| ------------ | --------- |
| SOQL Queries | 100       |
| DML Rows     | 10,000    |
| CPU Time     | 10,000 ms |
| Heap Size    | 6 MB      |

`bulk_dml` is not subject to these — Bulk API jobs run outside the Apex
transaction limits (triggers still run per 200-record chunk).

## Best practices

1. **Keep test data in the test** — `@testSetup` data is rolled back
   automatically; no cleanup needed.
2. **Use factories from `assets/factories/`** as the starting point for
   sf-apex test classes; adapt required fields to the org.
3. **Assert, don't debug** — `System.assert*` proves behaviour; `System.debug`
   only logs it.
4. **Idempotent scripts** — any Apex that sf-apex deploys for a one-off data
   fix should be safe to re-run.
