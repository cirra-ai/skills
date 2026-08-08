## Test Data Creation via Cirra AI MCP

Instead of running Apex factories, use `sobject_dml` directly:

**Example: Create 201 Accounts (crossing batch boundary)**

The MCP server enforces a 200-record limit per call. Split into batches:

```
// Batch 1: records 1-200
sobject_dml(
  sObject="Account",
  operation="insert",
  records=[
    {"Name": "Test Account 1", "Industry": "Technology"},
    {"Name": "Test Account 2", "Industry": "Finance"},
    // ... up to 200 records
  ],
  sf_user="prod"
)

// Batch 2: record 201
sobject_dml(
  sObject="Account",
  operation="insert",
  records=[
    {"Name": "Test Account 201", "Industry": "Retail"}
  ],
  sf_user="prod"
)
```

**Distributed Test Data** (Hot/Warm/Cold scoring):

```
sobject_dml(
  sObject="Lead",
  operation="insert",
  records=[
    // 50 Hot leads
    {"FirstName": "Hot", "LastName": "Lead1", "Company": "TechCo", "Industry": "Technology", "NumberOfEmployees": 1500},
    // 100 Warm leads
    {"FirstName": "Warm", "LastName": "Lead51", "Company": "FinCo", "Industry": "Finance", "NumberOfEmployees": 500},
    // 101 Cold leads
    {"FirstName": "Cold", "LastName": "Lead151", "Company": "RetailCo", "Industry": "Retail", "NumberOfEmployees": 50}
  ],
  sf_user="prod"
)
```

---
