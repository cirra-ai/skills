## Apex Integration

Call Apex `@InvocableMethod` classes from Flow for complex business logic.

### Flow Pattern (XML reference — deploy as JSON)

> The XML below shows the structural pattern. When deploying via `metadata_create`, translate to the equivalent JSON object.

```xml
<actionCalls>
    <name>Process_Record</name>
    <actionName>RecordProcessor</actionName>
    <actionType>apex</actionType>
    <inputParameters>
        <name>recordId</name>
        <value><elementReference>var_RecordId</elementReference></value>
    </inputParameters>
    <outputParameters>
        <assignToReference>var_IsSuccess</assignToReference>
        <name>isSuccess</name>
    </outputParameters>
    <faultConnector>
        <targetReference>Handle_Error</targetReference>
    </faultConnector>
</actionCalls>
```

### Documentation

| Resource                    | Location                                                                            |
| --------------------------- | ----------------------------------------------------------------------------------- |
| Apex Action Template        | `assets/apex-action-template.xml`                                                   |
| Apex @InvocableMethod Guide | [sf-apex/references/flow-integration.md](../sf-apex/references/flow-integration.md) |
| Triangle Architecture       | [references/triangle-pattern.md](references/triangle-pattern.md)                    |

### ⚠️ Flows for Agentforce

**When creating Flows for Agentforce agents:**

- sf-flow (this skill) creates the validated Flow metadata (JSON)
- sf-flow deploys via Cirra AI metadata_create tool
- **Action Definition registration required** (see below)
- Only THEN can agents use `flow://FlowName` targets

**Variable Name Matching**: When creating Flows for Agentforce agents:

- Agent Script input/output names MUST match Flow variable API names exactly
- Use descriptive names (e.g., `inp_AccountId`, `out_AccountName`)
- Mismatched names cause "Internal Error" during agent publish

### Output Variable Naming for Agentforce

Use `out_` prefix for output variables to distinguish them in Action Definition schema:

```xml
<variables>
    <name>out_CaseSubject</name>
    <dataType>String</dataType>
    <isOutput>true</isOutput>
</variables>
<variables>
    <name>out_CaseStatus</name>
    <dataType>String</dataType>
    <isOutput>true</isOutput>
</variables>
```

### Formula Expression Limitations in Flows

Flow formulas have more limited function support than formula fields. The table below applies to **formula variables and formula elements within the flow**, NOT to `filterFormula` entry conditions:

| Function                  | In `filterFormula` (entry conditions) | In flow formulas/variables | Alternative for flow formulas          |
| ------------------------- | ------------------------------------- | -------------------------- | -------------------------------------- |
| `ISNEW()` / `ISCHANGED()` | ✅ Supported                          | ❌ Not supported           | Use `$Record__Prior` comparisons       |
| `BLANKVALUE()`            | ✅ Supported                          | ❌ Not supported           | Use Decision element or `IF()`         |
| `CASESAFEID()`            | ❌ Not supported                      | ❌ Not supported           | ID variables handle this automatically |

### filterFormula Gotchas

- **`ISPICKVAL(field, value)`** — the second argument must be a **literal string** (the API name of the picklist value). Passing a field reference or variable as the second argument causes a formula compile error — if you need to compare two fields, use `=` instead.
- For picklist equality in entry conditions, prefer the simpler `TEXT({!$Record.Field}) = "Value"` or `ISPICKVAL({!$Record.Field}, "Value")`.
- **`filterFormula` and `emailSimple` body** do not support cross-object relationship traversal — use only direct `$Record` field references (e.g., `{!$Record.Status}`) in these contexts. Relationship paths like `$Record.Owner.Name` work in flow formulas and assignments but cause deploy errors in `filterFormula`/`emailSimple`.

### Action Definition Registration (REQUIRED)

> **CRITICAL**: Creating a Flow is NOT sufficient for Agentforce. The Flow must be registered as an Action Definition.

**Registration Workflow:**

1. **Deploy Flow** to target org via sf-flow + Cirra AI metadata_create
2. Navigate to **Setup > Agentforce > Action Definitions**
3. Click **"New Action"**, select **"Flow"** as target type
4. Choose your deployed Flow from the list
5. **Map input/output variables** - these become the action's schema
6. Configure planner flags:
   - `is_displayable`: Can LLM show output to user?
   - `is_used_by_planner`: Can LLM use output for decisions?
7. **Save** the Action Definition

```
Flow Created  →  Deployed to Org  →  Action Definition Created  →  Agent Can Use
     ↑               ↑                        ↑                         ↑
   sf-flow  Cirra AI            Setup > Agentforce         @actions.MyAction
```

**Why This Matters**: The Action Definition is what exposes the Flow to the agent runtime with proper input/output schema mapping. Without it, `@actions.FlowName` will fail with `ValidationError: Tool target 'FlowName' is not an action definition`.

| Direction             | Pattern                                             |
| --------------------- | --------------------------------------------------- |
| sf-flow → sf-metadata | "Describe Invoice\_\_c" (verify fields before flow) |
| sf-flow → Cirra AI    | Deploy with validation via metadata_create          |
| sf-flow → sf-data     | "Create 200 test Accounts" (test data after deploy) |
