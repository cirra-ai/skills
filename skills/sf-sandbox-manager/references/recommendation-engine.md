# Recommendation Engine

Full decision tree for choosing the right Salesforce environment type.

## Decision Tree

```
START
 │
 ├─ Need production data?
 │    ├─ Full copy of all data → FULL COPY SANDBOX
 │    ├─ Subset / sample data → PARTIAL COPY SANDBOX
 │    └─ No data needed (schema only) → continue
 │
 ├─ Need installed packages or complex org config?
 │    ├─ Yes + can wait 30+ min → DEVELOPER SANDBOX
 │    └─ Yes + need it now → SCRATCH ORG (if using 2GP/unlocked packages)
 │
 ├─ Duration?
 │    ├─ Short (< 7 days) → SCRATCH ORG
 │    ├─ Long (> 30 days) → DEVELOPER SANDBOX
 │    └─ Medium (7–30 days) → either (prefer scratch for isolation)
 │
 └─ CONSTRAINTS (override all above):
      ├─ No CLI available → SANDBOX only
      ├─ No Dev Hub enabled → SANDBOX only
      ├─ Sandbox limit reached → SCRATCH ORG only
      └─ Non-technical user → prefer SANDBOX (simpler UX)
```

## Simplified Questions (Non-Technical Users)

For users who don't know Salesforce terminology, ask plain-language questions.

### Question 1: Data needs

```
AskUserQuestion(question="Will you need real customer data from production in this environment?")
```

**If yes:**

```
AskUserQuestion(question="Do you need all the data or just a sample?\n\n1. **All data** — exact copy of production\n2. **Sample** — a representative subset")
```

- All data → **Full Copy Sandbox**
- Sample → **Partial Copy Sandbox**

**If no:** proceed to Question 2.

### Question 2: Duration

```
AskUserQuestion(question="How long will you need this environment?\n\n1. **A few days** — quick testing or a single feature\n2. **A few weeks** — sprint-length work\n3. **Ongoing** — long-running project or permanent test environment")
```

- A few days + CLI available → **Scratch Org**
- A few days + no CLI → **Developer Sandbox**
- A few weeks → **Developer Sandbox** (or Scratch Org if CLI available and user prefers disposable)
- Ongoing → **Developer Sandbox**

### Question 3 (optional): Performance needs

Only ask if duration answer is "a few weeks" or "ongoing":

```
AskUserQuestion(question="Will you be working with large amounts of data (tens of thousands of records)?\n\n1. **Yes** — need room for bulk data\n2. **No** — just a handful of test records")
```

- Yes → **Developer Pro Sandbox** (1 GB vs 200 MB)
- No → **Developer Sandbox**

## Full Matrix (Technical Users)

For users who use Salesforce jargon, present the full decision matrix.

### Gather Requirements

```
AskUserQuestion(question="Help me narrow down the right environment:\n\n1. Do you need production data? (full/partial/none)\n2. Do you need installed managed packages?\n3. How long do you need it? (days/weeks/months)\n4. Do you have the Salesforce CLI available?\n5. Is this for CI/CD or manual testing?")
```

### Decision Rules

| Requirement                   | → Recommendation        |
| ----------------------------- | ----------------------- |
| Production data (full)        | Full Copy Sandbox       |
| Production data (partial)     | Partial Copy Sandbox    |
| Managed packages + long-term  | Developer Sandbox       |
| Managed packages + short-term | Scratch Org (2GP)       |
| No data + < 7 days + CLI      | Scratch Org             |
| No data + > 30 days           | Developer Sandbox       |
| No data + 7–30 days           | Either (prefer scratch) |
| Large data volume testing     | Developer Pro Sandbox   |
| CI/CD pipeline                | Scratch Org             |
| No CLI available              | Any Sandbox type        |
| No Dev Hub                    | Any Sandbox type        |

## Constraint Detection

The skill should automatically detect these constraints before making a recommendation:

### 1. CLI Availability (execution mode)

Detected during initialization. If `mcp-core` or `mcp-plus-code-execution`, scratch orgs are not available.

### 2. Dev Hub Status

If CLI is available, check:

```bash
sf org display --target-dev-hub --json
```

If no Dev Hub is configured, scratch orgs cannot be created.

### 3. Sandbox Limits

Query existing sandboxes:

```
tooling_api_query(
  sObject="SandboxInfo",
  fields=["Id", "SandboxName", "LicenseType"],
  whereClause="",
  limit=200
)
```

Compare count against org edition limits (see `sandbox-types-guide.md`).

### 4. Org Edition

```
soql_query(
  sObject="Organization",
  fields=["OrganizationType", "Name"],
  whereClause="",
  limit=1
)
```

Different editions have different sandbox and scratch org limits.

## Recommendation Output Format

```
**Recommendation: Developer Sandbox**

Based on your requirements:
- You don't need production data ✓
- You need the environment for 2+ weeks ✓
- Installed packages need to be available ✓

A Developer sandbox copies the schema from production (no data), provisions in
minutes, and persists until you no longer need it.

**Alternative**: If you only needed it for a few days and had the Salesforce CLI,
a scratch org would be faster to provision and fully disposable.

Ready to create one? Use `/sf-sandbox-manager create` to get started.
```
