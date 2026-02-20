# Multi-Skill Orchestration: cirra-ai-sf-flow Perspective

This document details how cirra-ai-sf-flow fits into the multi-skill workflow for Salesforce development.

---

## Standard Orchestration Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STANDARD MULTI-SKILL ORCHESTRATION ORDER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. cirra-ai-sf-metadata                                                    │
│     └── Create object/field definitions (LOCAL files)                       │
│                                                                             │
│  2. cirra-ai-sf-flow  ◀── YOU ARE HERE                                     │
│     └── Create flow definitions (LOCAL files)                               │
│                                                                             │
│  3. cirra-ai-sf-deploy                                                      │
│     └── Deploy all metadata (REMOTE)                                        │
│                                                                             │
│  4. cirra-ai-sf-data                                                        │
│     └── Create test data (REMOTE - objects must exist!)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why cirra-ai-sf-flow Depends on cirra-ai-sf-metadata

| cirra-ai-sf-flow Uses | From cirra-ai-sf-metadata | What Fails Without It                 |
| --------------------- | ------------------------- | ------------------------------------- |
| Object references     | Custom Objects            | `Invalid reference: Quote__c`         |
| Field references      | Custom Fields             | `Field does not exist: Status__c`     |
| Picklist values       | Picklist Fields           | Flow decision uses non-existent value |
| Record Types          | Record Type metadata      | `Invalid record type: Inquiry`        |

**Rule**: If your Flow references custom objects or fields, create them with cirra-ai-sf-metadata FIRST.

---

## cirra-ai-sf-flow's Role in the Triangle Architecture

Flow acts as the **orchestrator** in the Flow-LWC-Apex triangle:

```
                    ┌─────────────────────┐
                    │       FLOW          │◀── YOU ARE HERE
                    │  (Orchestrator)     │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     │
┌─────────────────┐   ┌─────────────────┐           │
│   LWC Screen    │   │  Apex Invocable │           │
│   Component     │   │     Action      │           │
└────────┬────────┘   └────────┬────────┘           │
         │    @AuraEnabled     │                     │
         └──────────┬──────────┘                     │
                    ▼                                │
         ┌─────────────────────┐                     │
         │   Apex Controller   │─────────────────────┘
         └─────────────────────┘   Results back to Flow
```

See `docs/triangle-pattern.md` for detailed Flow XML patterns.

---

## Integration + Agentforce Extended Order

When building agents with Flow actions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AGENTFORCE FLOW ORCHESTRATION                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. cirra-ai-sf-metadata                                                    │
│     └── Create object/field definitions                                     │
│                                                                             │
│  2. cirra-ai-sf-connected-apps (if external API)                            │
│     └── Create OAuth Connected App                                          │
│                                                                             │
│  3. cirra-ai-sf-integration (if external API)                               │
│     └── Create Named Credential + External Service                          │
│                                                                             │
│  4. cirra-ai-sf-apex (if custom logic needed)                               │
│     └── Create @InvocableMethod classes                                     │
│                                                                             │
│  5. cirra-ai-sf-flow  ◀── YOU ARE HERE                                     │
│     └── Create Flow (HTTP Callout, Apex wrapper, or standard)               │
│                                                                             │
│  6. cirra-ai-sf-deploy                                                      │
│     └── Deploy all metadata                                                 │
│                                                                             │
│  7. cirra-ai-sf-ai-agentforce                                               │
│     └── Create agent with flow:// target                                    │
│                                                                             │
│  8. cirra-ai-sf-deploy                                                      │
│     └── Publish agent (metadata_create via Cirra AI MCP)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Flows for Agentforce: Critical Requirements

When creating Flows that will be called by Agentforce agents:

### 1. Variable Name Matching

Agent Script input/output names MUST match Flow variable API names exactly:

```xml
<!-- Flow variable -->
<variables>
    <name>inp_AccountId</name>
    <dataType>String</dataType>
    <isInput>true</isInput>
</variables>
```

```yaml
# Agent Script action - names must match!
actions:
  - name: GetAccountDetails
    target: flow://Get_Account_Details
    inputs:
      - name: inp_AccountId # Must match Flow variable name
        source: slot
```

### 2. Flow Requirements for Agents

| Requirement                  | Why                                              |
| ---------------------------- | ------------------------------------------------ |
| Autolaunched or Screen Flow  | Record-triggered flows cannot be called directly |
| `isInput: true` for inputs   | Agent needs to pass values                       |
| `isOutput: true` for outputs | Agent needs to read results                      |
| Descriptive variable names   | Agent uses these in responses                    |

### 3. Common Integration Errors

| Error                       | Cause                    | Fix                                                 |
| --------------------------- | ------------------------ | --------------------------------------------------- |
| "Internal Error" on publish | Variable name mismatch   | Match Flow var names exactly                        |
| "Flow not found"            | Flow not deployed        | cirra-ai-sf-deploy before cirra-ai-sf-ai-agentforce |
| Agent can't read output     | Missing `isOutput: true` | Add output flag to Flow variable                    |

---

## Cross-Skill Integration Table

| From Skill                | To cirra-ai-sf-flow | When                                        |
| ------------------------- | ------------------- | ------------------------------------------- |
| cirra-ai-sf-ai-agentforce | → cirra-ai-sf-flow  | "Create Autolaunched Flow for agent action" |
| cirra-ai-sf-apex          | → cirra-ai-sf-flow  | "Create Flow wrapper for Apex logic"        |
| cirra-ai-sf-integration   | → cirra-ai-sf-flow  | "Create HTTP Callout Flow"                  |

| From cirra-ai-sf-flow | To Skill               | When                                                |
| --------------------- | ---------------------- | --------------------------------------------------- |
| cirra-ai-sf-flow      | → cirra-ai-sf-metadata | "Describe Invoice\_\_c" (verify fields before flow) |
| cirra-ai-sf-flow      | → cirra-ai-sf-deploy   | "Deploy flow with checkOnly"                        |
| cirra-ai-sf-flow      | → cirra-ai-sf-data     | "Create 200 test Accounts" (after deploy)           |

---

## Deployment Order for Flow Dependencies

When deploying Flows that reference Apex or LWC:

```
1. APEX CLASSES        (if @InvocableMethod called)
   └── Deploy first

2. LWC COMPONENTS      (if used in Screen Flow)
   └── Deploy second

3. FLOWS               ◀── Deploy LAST
   └── References deployed Apex/LWC
```

---

## Best Practices

1. **Always verify objects exist** before creating Flow references
2. **Use cirra-ai-sf-metadata describe** to confirm field API names
3. **Deploy as Draft first** for complex flows
4. **Test with 251 records** for bulk safety
5. **Match variable names exactly** when creating for Agentforce

---

## Related Documentation

| Topic                               | Location                                              |
| ----------------------------------- | ----------------------------------------------------- |
| Triangle pattern (Flow perspective) | `cirra-ai-sf-flow/docs/triangle-pattern.md`           |
| LWC integration                     | `cirra-ai-sf-flow/docs/lwc-integration-guide.md`      |
| Apex action template                | `cirra-ai-sf-flow/templates/apex-action-template.xml` |
| cirra-ai-sf-ai-agentforce           | `cirra-ai-sf-ai-agentforce/SKILL.md`                  |
