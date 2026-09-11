# Multi-Skill Orchestration: sf-flow Perspective

This document details how sf-flow fits into the multi-skill workflow for Salesforce development.

---

## Standard Orchestration Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STANDARD MULTI-SKILL ORCHESTRATION ORDER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. sf-metadata                                                             │
│     └── Create objects/fields (metadata_create / sobject_field_create)      │
│                                                                             │
│  2. sf-flow  ◀── YOU ARE HERE                                               │
│     └── Create + deploy the flow (metadata_create / metadata_update),       │
│         verify with tooling_api_query, activate via FlowDefinition          │
│                                                                             │
│  3. sf-data                                                                 │
│     └── Create test data (objects and flow must exist!)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why sf-flow Depends on sf-metadata

| sf-flow Uses      | From sf-metadata     | What Fails Without It                 |
| ----------------- | -------------------- | ------------------------------------- |
| Object references | Custom Objects       | `Invalid reference: Quote__c`         |
| Field references  | Custom Fields        | `Field does not exist: Status__c`     |
| Picklist values   | Picklist Fields      | Flow decision uses non-existent value |
| Record Types      | Record Type metadata | `Invalid record type: Inquiry`        |

**Rule**: If your Flow references custom objects or fields, create them with sf-metadata FIRST.

---

## sf-flow's Role in the Triangle Architecture

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

See `references/triangle-pattern.md` for detailed Flow XML patterns.

---

## Integration + Agentforce Extended Order

When building agents with Flow actions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  AGENTFORCE FLOW ORCHESTRATION                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. sf-metadata                                                             │
│     └── Create object/field definitions                                     │
│                                                                             │
│  2. sf-metadata / sf-connect-rest (if external API)                         │
│     └── Connected App, Named Credential, External Service registration      │
│                                                                             │
│  3. sf-apex (if custom logic or a callout is needed)                        │
│     └── Create @InvocableMethod classes (deployed by sf-apex)               │
│                                                                             │
│  4. sf-flow  ◀── YOU ARE HERE                                               │
│     └── Create + deploy the Flow (HTTP Callout, Apex wrapper, or standard)  │
│         via metadata_create, verify, activate via FlowDefinition            │
│                                                                             │
│  5. Agentforce Agent                                                        │
│     └── Create agent with flow:// target; publish via metadata_create       │
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

| Error                       | Cause                    | Fix                                                    |
| --------------------------- | ------------------------ | ------------------------------------------------------ |
| "Internal Error" on publish | Variable name mismatch   | Match Flow var names exactly                           |
| "Flow not found"            | Flow not deployed        | Deploy the flow with `metadata_create` (sf-flow) first |
| Agent can't read output     | Missing `isOutput: true` | Add output flag to Flow variable                       |

---

## Cross-Skill Integration Table

| From Skill      | To sf-flow | When                                                                    |
| --------------- | ---------- | ----------------------------------------------------------------------- |
| sf-apex         | → sf-flow  | "Create Flow wrapper for Apex logic" (incl. Apex that does the callout) |
| sf-connect-rest | → sf-flow  | "Create HTTP Callout Flow" once the External Service is registered      |

| From sf-flow | To Skill          | When                                                              |
| ------------ | ----------------- | ----------------------------------------------------------------- |
| sf-flow      | → sf-metadata     | "Describe Invoice\_\_c" (verify fields before flow)               |
| sf-flow      | → sf-apex         | Callout logic belongs in an `@InvocableMethod`                    |
| sf-flow      | → sf-connect-rest | Named Credential / External Service the callout action depends on |
| sf-flow      | → sf-data         | "Create 200 test Accounts" (after deploy)                         |

Deployment is done by sf-flow itself: `metadata_create` / `metadata_update` (JSON), then `tooling_api_query` on `Flow` to verify the version, then `metadata_update` on `FlowDefinition` to activate on request.

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
2. **Use sf-metadata describe** to confirm field API names
3. **Deploy as Draft first** for complex flows
4. **Test with 251 records** for bulk safety
5. **Match variable names exactly** when creating for Agentforce

---

## Related Documentation

| Topic                               | Location                                      |
| ----------------------------------- | --------------------------------------------- |
| Triangle pattern (Flow perspective) | `sf-flow/references/triangle-pattern.md`      |
| LWC integration                     | `sf-flow/references/lwc-integration-guide.md` |
| Apex action template                | `sf-flow/assets/apex-action-template.xml`     |
