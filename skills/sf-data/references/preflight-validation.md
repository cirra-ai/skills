## Pre-Flight Validation (Sandboxed Environments)

The MCP validator uses a **two-tier model** that matches the risk profile of each operation:

- **Tier 1** (data ops): Lightweight pass/fail checks for `soql_query` and `sobject_dml`. No scoring — just catches structural errors and PII before executing. Running an inefficient query interactively is fine; governor limits protect you.
- **Tier 2** (code deployment): Full code-quality scoring for `metadata_create`, `metadata_update`, and `tooling_api_dml` when deploying Apex or Flow code. Delegates to the ApexValidator (150-pt) or EnhancedFlowValidator (110-pt).

### How to run

```bash
python scripts/mcp_validator_cli.py input.json
python scripts/mcp_validator_cli.py --format report input.json
echo '{"tool":"soql_query","params":{...}}' | python scripts/mcp_validator_cli.py
```

### Tier 1: Data Parameter Checks (soql_query, sobject_dml)

Simple pass/fail. No score — just errors and warnings.

```json
{
  "tool": "sobject_dml",
  "params": {
    "sObject": "Account",
    "operation": "insert",
    "records": [
      { "Name": "Test Account 1", "Industry": "Technology" },
      { "Name": "Test Account 2", "Industry": "Finance" }
    ],
    "sf_user": "prod"
  }
}
```

**What Tier 1 checks:**

| Check                                                       | Tool        | Severity |
| ----------------------------------------------------------- | ----------- | -------- |
| Missing `sObject`                                           | Both        | Error    |
| Missing `sf_user`                                           | Both        | Error    |
| Invalid DML `operation`                                     | sobject_dml | Error    |
| Empty records array                                         | sobject_dml | Error    |
| Update/delete missing `Id`                                  | sobject_dml | Error    |
| Upsert missing externalIdField                              | sobject_dml | Error    |
| PII in record values                                        | sobject_dml | Warning  |
| Inconsistent fields                                         | sobject_dml | Warning  |
| SOQL syntax errors (`==`, unbalanced parens, double quotes) | soql_query  | Warning  |

**Output:**

```json
{
  "tier": "data_params",
  "tool": "sobject_dml",
  "status": "pass",
  "errors": [],
  "warnings": []
}
```

### Tier 2: Code Deployment Scoring (metadata_create, metadata_update, tooling_api_dml)

Full code quality scoring when deploying Apex or Flow code. Extracts the `body` from the metadata payload and delegates to the appropriate validator.

```json
{
  "tool": "metadata_create",
  "params": {
    "type": "ApexClass",
    "metadata": [
      {
        "fullName": "AccountService",
        "apiVersion": "65.0",
        "status": "Active",
        "body": "public with sharing class AccountService {\n    public static List<Account> getByIndustry(String industry) {\n        return [SELECT Id, Name FROM Account WHERE Industry = :industry LIMIT 1000];\n    }\n}"
      }
    ],
    "sf_user": "prod"
  }
}
```

**What Tier 2 checks:**

| Metadata Type  | Validator             | Max Score | Key Checks                                         |
| -------------- | --------------------- | --------- | -------------------------------------------------- |
| ApexClass      | ApexValidator         | 150       | SOQL-in-loops, DML-in-loops, sharing, naming, docs |
| ApexTrigger    | ApexValidator         | 150       | Bulkification, error handling, security            |
| Flow           | EnhancedFlowValidator | 110       | DML-in-loops, fault paths, naming, governance      |
| FlowDefinition | EnhancedFlowValidator | 110       | Performance, error handling, security              |
| Other types    | — (skipped)           | —         | Non-code metadata passes through without scoring   |

**Output:**

```json
{
  "tier": "code_deployment",
  "tool": "metadata_create",
  "metadata_type": "ApexClass",
  "validator": "ApexValidator",
  "status": "scored",
  "score": 145,
  "max_score": 150,
  "rating": "Excellent (5/5)",
  "issues": [...]
}
```

---
