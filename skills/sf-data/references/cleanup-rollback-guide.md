# Cleanup and Rollback Guide

Strategies for test data isolation and cleanup.

The Apex patterns below run inside deployed test classes (sf-apex +
`run_tests`); Cirra cannot execute anonymous Apex. From a conversation,
clean up with the MCP calls in "Cleanup via Cirra AI MCP".

## Savepoint/Rollback Pattern

Best for synchronous test isolation.

```apex
// Create savepoint BEFORE any DML
Savepoint sp = Database.setSavepoint();

try {
    // Create test data
    List<Account> accounts = TestDataFactory_Account.create(100);

    // Run your tests
    Test.startTest();
    MyClass.processAccounts(accounts);
    Test.stopTest();

    // Assert results
    System.assertEquals(expected, actual);

} finally {
    // Always rollback
    Database.rollback(sp);
}
```

**Limitations:**

- Does not roll back async operations
- Maximum 5 savepoints per transaction

## Cleanup by Name Pattern

```apex
String pattern = 'Test%';

DELETE [SELECT Id FROM Opportunity WHERE Name LIKE :pattern];
DELETE [SELECT Id FROM Contact WHERE LastName LIKE :pattern];
DELETE [SELECT Id FROM Account WHERE Name LIKE :pattern];
```

**Order matters:** Delete children before parents.

## Cleanup by Date

```apex
DateTime startTime = DateTime.now().addHours(-1);

DELETE [
    SELECT Id FROM Account
    WHERE CreatedDate >= :startTime
    AND Name LIKE 'Test%'
];
```

## Cleanup via Cirra AI MCP

```
# Query IDs to delete (raise limit or paginate for more than 200)
soql_query(sObject="Account", fields=["Id"], whereClause="Name LIKE 'Test%'")

# Delete up to 200 records per call
sobject_dml(
  operation="delete",
  sObject="Account",
  recordIds=["001xx...", "001yy...", ...]
)

# More than 200 records: one Bulk API job (see bulk-operations-guide.md)
bulk_dml(
  operation="delete",
  sObject="Account",
  recordIds=["001xx...", "001yy...", ...]
)
```

`delete` sends rows to the Recycle Bin. `bulk_dml(operation="hardDelete")`
skips it — only with the Bulk API Hard Delete permission and explicit user
approval.

## Best Practices

1. **Track created IDs** - Store in Set<Id>
2. **Delete in order** - Children first, parents last
3. **Use test prefixes** - 'Test', 'BulkTest'
4. **Preview before delete** - Verify records first
5. **Use @isTest** - Auto-rollback in tests
