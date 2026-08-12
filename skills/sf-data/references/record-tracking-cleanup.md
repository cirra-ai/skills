## Record Tracking & Cleanup

### Cleanup Patterns

| Method     | Tool                                                                        | Best For         |
| ---------- | --------------------------------------------------------------------------- | ---------------- |
| By IDs     | `sobject_dml(operation="delete", records=[{"Id":"..."}])`                   | Known records    |
| By Pattern | Query with `whereClause="Name LIKE 'Test%'"` then delete returned IDs       | Test data        |
| By Date    | Query with `whereClause="CreatedDate >= TODAY AND Name LIKE 'Test%'"` first | Recent test data |

### Cleanup via SOQL (call after verifying records)

After inserting test records with `sobject_dml`, query to get IDs and provide cleanup:

```
soql_query(
  sObject="Account",
  fields=["Id"],
  whereClause="Name LIKE 'Test Account%'",
  sf_user="prod"
)
```

Then provide cleanup instruction:

```
sobject_dml(
  sObject="Account",
  operation="delete",
  records=[{"Id": "<ID1>"}, {"Id": "<ID2>"}],
  sf_user="prod"
)
```

---
