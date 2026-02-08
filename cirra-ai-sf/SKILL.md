---
name: cirra-ai-sf
description: >
  Salesforce development suite — orchestrates Apex, Flow, and Data plugins
  with Cirra AI MCP Server. Use when the user needs cross-domain Salesforce
  work spanning code, flows, and data operations.
license: MIT
metadata:
  version: '1.0.0'
  author: 'Cirra AI'
---

# cirra-ai-sf: Salesforce Development Suite

Orchestrates three independent Salesforce plugins into a unified development workflow. Each plugin works standalone; this meta-skill coordinates them when all three are active.

## Sub-Plugins

| Plugin | Domain | Scoring |
|---|---|---|
| **cirra-ai-sf-apex** | Apex classes, triggers, tests, batch jobs | 150 points / 8 categories |
| **cirra-ai-sf-flow** | Record-triggered, screen, autolaunched, scheduled flows | 110 points / 6 categories |
| **cirra-ai-sf-data** | SOQL queries, DML operations, test data factories | Pass/fail pre-flight checks |

Each plugin includes its own MCP deployment validator — no cross-plugin dependencies.

## Routing Rules

When a user request arrives, route to the appropriate plugin:

| Request Type | Route To | Examples |
|---|---|---|
| Write/review Apex code | cirra-ai-sf-apex | "Create a trigger handler", "Review this Apex class" |
| Create/validate a Flow | cirra-ai-sf-flow | "Build a record-triggered flow", "Score this flow XML" |
| Query/insert/update data | cirra-ai-sf-data | "Query all Accounts", "Create 200 test records" |
| Mixed (code + data) | Both | "Deploy the trigger and create test data" |

## Orchestration Order

When building a complete feature:

```
1. cirra-ai-sf-metadata  →  Create custom objects/fields (if needed)
2. cirra-ai-sf-apex      →  Deploy Apex classes/triggers
   cirra-ai-sf-flow      →  Deploy Flows (parallel with Apex if independent)
3. cirra-ai-sf-data      →  Create test data, verify with SOQL
```

Objects and fields must exist before code that references them can be deployed.

## Validation Flow

Each plugin validates its own domain independently:

- **cirra-ai-sf-data**: Pre-flight checks on `soql_query` / `sobject_dml` params (missing sObject, PII detection, syntax errors) — pass/fail
- **cirra-ai-sf-apex**: 150-point scoring on `metadata_create` / `metadata_update` for ApexClass/ApexTrigger — delegates to ApexValidator
- **cirra-ai-sf-flow**: 110-point scoring on `metadata_create` / `metadata_update` for Flow/FlowDefinition — delegates to EnhancedFlowValidator

No plugin needs to import from another plugin's codebase.

## Prerequisites

**CRITICAL**: Call `cirra_ai_init()` once per session before using any Cirra AI MCP tools.

```python
cirra_ai_init(sf_user="your-username")
```

## Related Skills

These plugins complement the core three but are independent:

| Skill | Purpose |
|---|---|
| cirra-ai-sf-metadata | Custom objects, fields, Permission Sets |
| cirra-ai-sf-lwc | Lightning Web Components |
| cirra-ai-sf-soql | Advanced SOQL optimization |
| cirra-ai-sf-ai-agentscript | Agentforce agent authoring |
