## ⚠️ Critical Lessons Learned (Metadata API Flows)

These lessons apply when creating or updating flows via `metadata_create` / `metadata_update` (JSON format). They are based on real-world failures and must be followed to avoid deployment errors.

### Lesson 1: Screen Field Names ARE Element References

Screen fields automatically create element references with their field name. Do **NOT** create a separate variable for screen fields — this causes a `Duplicate developer name` error.

```json
// WRONG: Don't create variable with same name as screen field
{ "screens": [{ "fields": [{ "name": "User_Input" }] }],
  "variables": [{ "name": "User_Input" }]  // DUPLICATE ERROR }

// CORRECT: Reference the screen field directly
{ "formulas": [{ "expression": "{!User_Input} & \" suffix\"" }] }
```

### Lesson 2: Collection DML — Cannot Use Both `object` and `inputReference`

When creating records from a collection using `inputReference`, do **NOT** include the `object` field. Define `objectType` on the variable instead.

```json
// WRONG:
{ "name": "Create_All", "object": "Account", "inputReference": "Var_Col" }

// CORRECT: objectType goes on the variable, not the create element
{ "variables": [{ "name": "Var_Col", "dataType": "SObject",
    "objectType": "Account", "isCollection": true }],
  "recordCreates": [{ "name": "Create_All", "inputReference": "Var_Col" }] }
```

### Lesson 3: Constants Cannot Be Collections

Flow constants cannot be collections or SObjects. Use a Decision + Counter Variable instead.

### Lesson 4: Read Current State Before Complex Updates

**ALWAYS** call `metadata_read` immediately before `metadata_update` for complex changes. Salesforce replaces the entire flow version on update — working with stale metadata will overwrite recent changes.

1. Call `metadata_read` to get current state
2. Analyze current elements and dependencies
3. Modify the retrieved metadata
4. Call `metadata_update` with complete state

### Lesson 5: All Element Names Must Be Globally Unique

Every element name in a Flow must be unique across **ALL** element types. Use prefixes to enforce this:

| Element Type  | Naming Convention | Example             |
| ------------- | ----------------- | ------------------- |
| Variables     | `Var_*`           | `Var_Account_Id`    |
| Formulas      | `Formula_*`       | `Formula_Full_Name` |
| Screens       | `Screen_*`        | `Screen_Welcome`    |
| Decisions     | `Decision_*`      | `Decision_Route`    |
| Assignments   | `Assign_*`        | `Assign_Defaults`   |
| Choices       | `Choice_*`        | `Choice_Option_A`   |
| Screen Fields | Descriptive       | `Account_Name`      |

### Lesson 6: Build Flows Iteratively, Not All At Once

- **Phase 1 — Shell**: `metadata_create` with minimal structure. Test: Does it open in Flow Builder?
- **Phase 2 — Basic Navigation**: Add first screen and routing. Test: Can you navigate through it?
- **Phase 3 — Core Logic**: Add record lookups and variables. Test: Does data flow correctly?
- **Phase 4 — Advanced Features**: Add formulas, loops, calculations. Test: Do calculations work?

**Red flags**: Creating 100+ line JSON on first attempt. Adding 5+ new element types at once. Not testing in Flow Builder between changes.

### Lesson 7: Collection DML Pattern — Build, Gather, Execute

Never create records one-by-one in a loop. Build a collection, then execute a single DML operation:

1. **Build_Record** — Assign field values to `Var_Current_Record` (single SObject variable)
2. **Add_To_Collection** — Use operator `Add` to append to the collection variable
3. **After loop exits** — Single `recordCreates` with `inputReference` pointing to the collection

Synchronous DML limit: 150 statements. Creating 10 records individually = 10 DML. Creating 10 records via collection = 1 DML.

### Lesson 8: `processMetadataValues` — Always Include Empty Array

Every Flow element **MUST** have a `processMetadataValues` property, even if it's an empty array. Without it, Salesforce may fail silently or discard the element.

```json
{ "name": "Element_Name", "processMetadataValues": [] }
```

### Lesson 8.5: Resource vs Node Elements — Property Rules

Flow elements split into two families. **Resources** (data containers) and **Nodes** (canvas/visual elements) do NOT accept the same properties. Mixing them up is one of the most common deploy-time failures (e.g. "The FlowFormula element doesn't accept a label property").

| Family                              | Element types                                                                                                                                                                                                                                                                     | Has `name` / `description` | Has `label` | Has `locationX` / `locationY` | Has `connector` |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | ----------- | ----------------------------- | --------------- |
| **Resources** (no canvas position)  | `formulas`, `variables`, `constants`, `textTemplates`, `choices`, `dynamicChoiceSets`                                                                                                                                                                                             | ✅                         | ❌          | ❌                            | ❌              |
| **Nodes** (visual, canvas elements) | `assignments`, `decisions`, `screens`, `loops`, `recordCreates`, `recordUpdates`, `recordDeletes`, `recordLookups`, `actionCalls`, `apexPluginCalls`, `subflows`, `waits`, `steps`, `transforms`, `collectionProcessors`, `orchestratedStages`, `customErrors`, `recordRollbacks` | ✅                         | ✅          | ✅                            | ✅ (most)       |
| **Hybrid resources** (own `label`)  | `stages`, `rules`, `exitRules`, `experimentPaths`, `scheduledPaths`, `screenActions`, `stageSteps`, `waitEvents`                                                                                                                                                                  | ✅                         | ✅          | ❌                            | varies          |

**General rule**: If you find yourself adding `label`, `locationX`, or `locationY` to a `formulas`, `variables`, `constants`, `textTemplates`, or `choices` entry, **stop** — those properties do not exist on those types and the deploy will fail with a metadata error.

**Common manifestation**:

```json
// WRONG — FlowFormula does not accept label
{ "formulas": [{ "name": "Is_Overdue", "label": "Is Overdue",
                  "dataType": "Boolean", "expression": "{!CloseDate} < TODAY()" }] }

// CORRECT — use `name` + `description` only; the formula has no canvas presence
{ "formulas": [{ "name": "Is_Overdue", "description": "True when CloseDate is in the past",
                  "dataType": "Boolean", "expression": "{!CloseDate} < TODAY()" }] }
```

If you need a human-readable label, put it on the node that _uses_ the formula (e.g. a Decision with `label: "Is the record overdue?"`), not on the formula itself.

The local validator (`validate_flow.py`) detects this class of error as a CRITICAL issue — run it before every deploy.

### Lesson 9: Empty Arrays for All Element Type Collections

Include **ALL** element type arrays in your flow metadata, even if empty. Missing arrays can cause silent failures, elements being deleted, or flows that won't save.

```json
{
  "assignments": [],
  "choices": [],
  "decisions": [],
  "formulas": [],
  "loops": [],
  "recordCreates": [],
  "recordDeletes": [],
  "recordLookups": [],
  "recordUpdates": [],
  "screens": [],
  "variables": [],
  "textTemplates": []
}
```

### Lesson 10: Connector Chains — Every Element Needs a Path

Every element (except the final one) must have a connector to the next element. Mental checklist for each element:

- Does it have a `connector`?
- If it's a decision, does it have a `defaultConnector`?
- Does the `targetReference` point to an existing element?
- Is this intentionally the final element (screen with `allowFinish: true`)?

### Flow Shell Template (JSON for `metadata_create`)

Always start with this complete template — include **ALL** empty arrays:

```json
{
  "fullName": "PLACEHOLDER",
  "label": "PLACEHOLDER",
  "apiVersion": 65,
  "processType": "Flow",
  "status": "Draft",
  "interviewLabel": "PLACEHOLDER {!$Flow.CurrentDateTime}",
  "environments": ["Default"],
  "processMetadataValues": [
    { "name": "BuilderType", "value": { "stringValue": "LightningFlowBuilder" } },
    { "name": "CanvasMode", "value": { "stringValue": "AUTO_LAYOUT_CANVAS" } }
  ],
  "start": {
    "locationX": 0,
    "locationY": 0,
    "connector": { "targetReference": "FIRST_ELEMENT" },
    "filters": [],
    "processMetadataValues": []
  },
  "assignments": [],
  "choices": [],
  "decisions": [],
  "formulas": [],
  "loops": [],
  "recordCreates": [],
  "recordDeletes": [],
  "recordLookups": [],
  "recordUpdates": [],
  "screens": [],
  "variables": [],
  "textTemplates": []
}
```

### Flow Element Types Reference

| Element Type   | Purpose               | Key Notes                                                                    |
| -------------- | --------------------- | ---------------------------------------------------------------------------- |
| Start          | Entry point           | Contains connector to first element; record-triggered adds filters/object    |
| Variables      | Store values          | Counter vars: `dataType` Number, `scale` 0. Collections: `isCollection` true |
| Screens        | User interface        | Fields auto-create element references — do NOT create duplicate variables    |
| Decisions      | Branching logic       | Must always include `defaultConnector`                                       |
| Record Lookups | Query Salesforce data | Use `storeOutputAutomatically: false` for security                           |
| Record Creates | Insert new records    | Use `inputReference` for collections — never combine with `object` field     |
| Assignments    | Set variable values   | Operators: `Assign`, `Add`, `AssignCount`                                    |
| Loops          | Iterate collections   | Auto-creates `currentItem_{LoopName}` variable                               |
| Formulas       | Computed values       | Use `{!VarName}` syntax to reference other elements                          |
