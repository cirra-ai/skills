---
name: sf-apex
plugin: cirra-ai-sf
argument-hint: '[create|update|validate] [class|trigger|test-class] {name} ...'
metadata:
  version: 2.2.1
description: >
  Generates and reviews Salesforce Apex code with 2026 best practices and 150-point scoring using the Cirra AI
  MCP Server. Use when writing Apex classes, triggers, test classes, batch
  jobs, or reviewing existing Apex code for bulkification, security, and SOLID principles.
  Usage: /sf-apex [create|update|validate] [class|trigger|test-class] {name} ...
---

# Salesforce Apex Code Generation and Review

Expert Apex developer specializing in clean code, SOLID principles, and other best practices. Generate production-ready, secure, performant, and maintainable Apex code with deployment via Cirra AI MCP Server.

## Dispatch

Parse `$ARGUMENTS` to determine which action workflow to run:

| First argument or intent            | Workflow                 |
| ----------------------------------- | ------------------------ |
| `create`, new class/trigger request | Create Apex              |
| `update`, modify existing code      | Update Apex              |
| `validate`, review, score           | Validate Apex            |
| _(no argument or unclear)_          | Ask the user (see below) |

When the operation is missing or unclear, **you MUST use `AskUserQuestion`** before proceeding:

```
AskUserQuestion(question="What would you like to do?\n\n1. **Create** — generate a new Apex class or trigger\n2. **Update** — fetch, modify, validate, and redeploy\n3. **Validate** — score existing Apex code")
```

Do NOT guess the operation or default to one. Wait for the user's answer.

---

## Reference File Index

Load a reference only when the row's "read when" applies — SKILL.md is self-sufficient for the common path.

| File                                                     | Read when                                                                                              |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `references/execution-modes.md`                          | Detecting whether local files / code execution are available (Claude Code, Cowork, Codex, chat-only)   |
| `references/mcp-pagination.md`                           | An MCP response is truncated or returns `artifactAccess` / `_pagination` (large class bodies, `All`)   |
| `references/testing-guide.md`                            | Writing tests, mocking callouts, `@TestSetup`, `System.runAs`, or running the `run_tests` fix loop     |
| `references/testing-patterns.md`                         | Exception types per scenario, async test patterns, coverage tactics for 90%+                           |
| `references/troubleshooting.md`                          | A deploy or test fails: prerequisite checks, error catalogue, debug logs (TraceFlag/ApexLog), limits   |
| `references/best-practices.md`                           | Bulkification, SOQL, null safety, error handling, async selection (§7), caching, guard clauses         |
| `references/anti-patterns.md`                            | Reviewing code — full catalogue of smells with before/after fixes                                      |
| `references/llm-anti-patterns.md`                        | Reviewing generated code for hallucinated methods, Java types, unsafe Map access                       |
| `references/bulkification-guide.md`                      | Deep dive on governor limits and collection handling for trigger/batch code                            |
| `references/security-guide.md`                           | Sharing modes, `WITH USER_MODE`, `stripInaccessible`, injection prevention                             |
| `references/naming-conventions.md`                       | Naming classes, methods, variables, test methods, trigger actions                                      |
| `references/code-review-checklist.md`                    | Scoring a class by category (the 150-point rubric in checklist form)                                   |
| `references/code-smells-guide.md`                        | Refactoring long methods, deep nesting, primitive obsession                                            |
| `references/solid-principles.md`                         | Designing service/domain/selector layers or reviewing architecture                                     |
| `references/design-patterns.md`                          | Factory, Strategy, Singleton, Builder and other GoF patterns in Apex                                   |
| `references/patterns-deep-dive.md`                       | TAF internals, `@InvocableMethod` details, async patterns (Queueable/Finalizer/Cursor/Batch), services |
| `references/trigger-actions-framework.md`                | Generating or reviewing TAF triggers and `Trigger_Action__mdt` records                                 |
| `references/flow-integration.md`                         | Building invocable actions consumed by Flow                                                            |
| `references/triangle-pattern.md`                         | Apex that sits between Flow and LWC (`@AuraEnabled` + invocable in one design)                         |
| `assets/apex-class.cls`                                  | Template: plain utility/controller class                                                               |
| `assets/service.cls` / `assets/selector.cls`             | Template: service layer and selector (query) layer                                                     |
| `assets/trigger.trigger` / `assets/trigger-action.cls`   | Template: TAF trigger and `TA_Object_Purpose` action class                                             |
| `assets/queueable.cls` / `assets/batch.cls`              | Template: Queueable (default async) and Batch job                                                      |
| `assets/invocable-method.cls`                            | Template: `@InvocableMethod` with Request/Response wrappers                                            |
| `assets/test-class.cls` / `assets/test-data-factory.cls` | Template: PNB test class and test data factory                                                         |

---

## Create Apex

Create a new Apex class or trigger following 2026 best practices.

2026 authoring defaults:

- API version **67.0** (Summer '26): user-mode SOQL/DML, explicit sharing on every class, `WITH USER_MODE` instead of `WITH SECURITY_ENFORCED`
- **Queueable** (plus `System.Finalizer`) for new async work — do not generate `@future` methods
- **Apex Cursors** (`Database.getCursor` / `Database.Cursor`) with Queueable chaining for large result sets; Batch Apex when `start`/`finish` or a `QueryLocator` lifecycle is required
- Recurring work: prefer a **Scheduled Flow**; use `Schedulable` only when the job must chain to Batch or needs complex Apex
- Isolate `without sharing` / `AccessLevel.SYSTEM_MODE` in small named helpers; entry points stay `with sharing`
- Custom Metadata: use `getAll()` / `getInstance()` on the metadata type, not SOQL
- No `System.debug()` on main code paths — use a logging framework if tracing is required

### 1. Gather requirements

Use AskUserQuestion to collect:

- **Type**: Trigger, Service, Selector, Batch, Queueable, Test, or other
- **Primary purpose**: one sentence description
- **Target object(s)**: which Salesforce objects are involved
- **Special requirements**: async, scheduled, invocable, aura-enabled, etc.

If the type is **Trigger**, also ask:

- Which trigger events are needed (before insert, after update, etc.)
- Whether the Trigger Actions Framework (TAF) is installed in the org

### 2. Check for existing Apex

Before generating, confirm nothing already exists with that name.

**For a class**:

```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<ClassName>'",
  fields=["Name", "ApiVersion"]
)
```

**For a trigger**:

```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="Name = '<TriggerName>'",
  fields=["Name", "TableEnumOrId", "ApiVersion"]
)
```

If either already exists, suggest the Update Apex workflow instead.

### 3. Generate

#### For a trigger

Follow the **MANDATORY DELIVERABLES** rule: never put logic directly in the trigger body.

**Check TAF installation** (if unknown):

```
tooling_api_query(
  sObject="InstalledSubscriberPackage",
  fields=["Id", "SubscriberPackage.Name", "SubscriberPackageVersion.Name"],
  whereClause="Id != null"
)
```

Look for `Trigger Actions Framework` in `SubscriberPackage.Name`. If the package list is inconclusive, check for the framework's handler class directly:

```
tooling_api_query(
  sObject="ApexClass",
  fields=["Id", "Name"],
  whereClause="Name = 'MetadataTriggerHandler'"
)
```

- **TAF installed** → generate a thin TAF trigger (`new MetadataTriggerHandler().run()`) + one or more `TA_Object_Purpose` action classes
- **TAF not installed** → generate a thin trigger that delegates to an `ObjectTriggerHandler` class

Also generate a corresponding test class covering the trigger and its handler/action.

#### For a class

Create the class and its test class following the sf-apex skill guidelines:

- Proper naming conventions (PascalCase, type suffix where applicable)
- ApexDoc comments on all public methods
- Bulkification patterns (no SOQL/DML in loops)
- Explicit sharing keyword; `WITH USER_MODE` / `AccessLevel.USER_MODE` on SOQL and `Database` DML
- Corresponding test class with 90%+ coverage patterns, PNB (positive / negative / bulk 251+), `Assert` class, and `TestDataFactory`
- User-mode SOQL/DML paths are covered with `System.runAs` and a permissioned persona, not only as an admin

### 4. Validate before deploying

Write the generated code to a temp file and validate:

```bash
# For a class:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py" "/tmp/<ClassName>.cls" <ApiVersion>

# For a trigger:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py" "/tmp/<TriggerName>.trigger" <ApiVersion>
```

Fix any CRITICAL or HIGH issues before proceeding. When installed as part of the `cirra-ai-sf` plugin, the pre-deployment hook also validates automatically when `tooling_api_dml` is called; standalone skill installs do not get the hook, so the manual run above is the contract.

### 5. Deploy

#### Trigger

**Deploy the handler/action class(es) first** — the trigger body references them and Salesforce will reject the trigger if they don't exist yet:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "<HandlerOrActionClassName>",
    "Body": "<class body>",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

Then deploy the trigger:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexTrigger",
  record={
    "Name": "<ObjectName>Trigger",
    "TableEnumOrId": "<ObjectApiName>",
    "Body": "<trigger body>",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

> **Note (TAF only)**: For TAF triggers (`new MetadataTriggerHandler().run()`), deploy order between the trigger and action classes does not matter because `MetadataTriggerHandler` comes from the installed package and is already present in the org.

#### Class

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "<ClassName>",
    "Body": "<class body>",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

Deploy the test class separately.

### 6. Run tests

Run the test class you just deployed and read the results — see [Run tests via `run_tests`](#run-tests-via-run_tests) below for the poll/read calls:

```
run_tests(tests=[{"className": "<ClassName>Test"}])
```

If any test fails, fix the class or the test, redeploy with `tooling_api_dml(operation="update", ...)` and rerun. Stop after three iterations and report what is still failing (`references/testing-guide.md` → "Test-fix loop" for failure-type guidance).

### 7. Report

Show the final validation score, deployment status, and test results (passed/failed counts and coverage %). For TAF triggers, remind the user that a `Trigger_Action__mdt` custom metadata record must be created for each action class to activate it.

---

## Update Apex

Fetch, modify, validate, and redeploy an existing Apex class or trigger.

### Parsing the request

The argument should be a class or trigger name: `$sf-apex update MyClass do X` or `$sf-apex update AccountTrigger add after update handling`

If no name is given, ask the user which class or trigger to update and what changes are needed.

### 1. Fetch the current implementation

First try `ApexClass`. If not found, try `ApexTrigger`.

**Try class first**:

```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<Name>'",
  fields=["Id", "Name", "Body", "ApiVersion"]
)
```

**If not found, try trigger**:

```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="Name = '<Name>'",
  fields=["Id", "Name", "TableEnumOrId", "Body", "ApiVersion"]
)
```

If neither is found, suggest the Create Apex workflow instead.

### 2. Read and understand

Review the existing code before making any changes. Understand:

- What the class/trigger currently does
- Existing patterns and conventions in use
- What the requested change affects

For triggers, also check whether related handler/action classes need updating.

### 3. Apply changes

Modify the code following sf-apex skill guidelines and 2026 best practices (see Create Apex). Preserve:

- Existing ApexDoc comments (update where relevant)
- Existing test coverage patterns
- Naming conventions already in use

For triggers: keep logic out of the trigger body — route to handler or TAF action classes instead.

### 4. Validate before deploying

Write the updated code to a temp file and validate:

```bash
# For a class:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py" "/tmp/<Name>.cls" <ApiVersion>

# For a trigger:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py" "/tmp/<Name>.trigger" <ApiVersion>
```

Fix any CRITICAL or HIGH issues before proceeding. When installed as part of the `cirra-ai-sf` plugin, the pre-deployment hook also validates automatically when `tooling_api_dml` is called; standalone skill installs do not get the hook, so the manual run above is the contract.

### 5. Deploy

#### Updated class

```
tooling_api_dml(
  operation="update",
  sObject="ApexClass",
  record={
    "Id": "<classId>",
    "Name": "<ClassName>",
    "Body": "<updated body>",
    "Status": "Active"
  }
)
```

#### Updated trigger

```
tooling_api_dml(
  operation="update",
  sObject="ApexTrigger",
  record={
    "Id": "<triggerId>",
    "Name": "<TriggerName>",
    "TableEnumOrId": "<ObjectApiName>",
    "Body": "<updated body>",
    "Status": "Active"
  }
)
```

If related handler/action classes were also modified, deploy each of those as separate `ApexClass` updates.

### 6. Run tests

Run the existing test class for the updated code (and any test class you changed), then read the results — see [Run tests via `run_tests`](#run-tests-via-run_tests):

```
run_tests(tests=[{"className": "<Name>Test"}])
```

If the class has no test class, generate and deploy one first (MANDATORY DELIVERABLES). On failure, fix, redeploy, rerun — at most three iterations, then stop and report.

### 7. Report

Summarise the changes made and show the final validation score plus test results (passed/failed counts and coverage %).

---

## Validate Apex

Validate one or more Apex classes or triggers using the 150-point static analysis pipeline and return a scored report.

### Parsing the request

| Input after `$sf-apex validate`              | Interpretation                                        |
| -------------------------------------------- | ----------------------------------------------------- |
| `MyClass`                                    | Class or trigger name — fetch body from org, validate |
| `<path>/MyClass.cls` (ends `.cls`)           | Local class file — validate directly                  |
| `<path>/MyTrigger.trigger` (ends `.trigger`) | Local trigger file — validate directly                |
| `MyClass,AccountTrigger,OtherClass`          | Comma-separated list — bulk fetch, validate each      |
| `All`                                        | All ApexClass **and** ApexTrigger records in the org  |
| _(no argument)_                              | Ask the user what to validate                         |

### Validation script

The validation script is at `${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py`. Locate it with:

```bash
# $CLAUDE_PLUGIN_ROOT is set by Claude Code. Other hosts: see references/execution-modes.md.
# If not set, find the script:
find ~/.claude/plugins -name "validate_apex_cli.py" 2>/dev/null | grep sf-apex | head -1
```

### Local file

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py" "<file_path>"
```

### Class or trigger name (fetch from org)

1. Try to fetch as a class first:

```
tooling_api_query(
  sObject="ApexClass",
  whereClause="Name = '<Name>'",
  fields=["Name", "Body"]
)
```

If no result, try as a trigger:

```
tooling_api_query(
  sObject="ApexTrigger",
  whereClause="Name = '<Name>'",
  fields=["Name", "Body"]
)
```

If neither returns a result, tell the user the name was not found in the org.

2. Write the body to a temp file using the appropriate extension:

```
Write /tmp/validate_<Name>.cls    ← for a class
Write /tmp/validate_<Name>.trigger  ← for a trigger
```

3. Validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py" "/tmp/validate_<Name>.cls"
# or
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-apex/scripts/validate_apex_cli.py" "/tmp/validate_<Name>.trigger"
```

4. Delete the temp file after validation.

### Comma-separated list

Each name may be a class or a trigger. Fetch all in a single query per sObject type, then merge the results.

**Fetch all as classes**:

```
tooling_api_query(
  sObject="ApexClass",
  fields=["Name", "Body"],
  whereClause="Name IN ('Name1', 'Name2', 'Name3')"
)
```

**Fetch any remaining names as triggers** (names not matched above):

```
tooling_api_query(
  sObject="ApexTrigger",
  fields=["Name", "Body"],
  whereClause="Name IN ('Name1', 'Name2', 'Name3')"
)
```

**Fallback**: If either bulk fetch fails (timeout or size error), fall back to individual queries per name using the class-or-trigger lookup above.

Validate each body (write → validate → delete), using `.cls` for classes and `.trigger` for triggers. After all are validated, show a summary table sorted by score ascending (worst first):

| Name           | Type    | Score   | %   | Status             |
| -------------- | ------- | ------- | --- | ------------------ |
| WeakClass      | Class   | 58/150  | 39% | ❌ Below threshold |
| AccountTrigger | Trigger | 108/150 | 72% | ✅ Pass            |
| MyClass        | Class   | 125/150 | 83% | ✅ Pass            |

### All

1. Fetch all class names and all trigger names in parallel:

```
tooling_api_query(sObject="ApexClass", fields=["Name"], whereClause="Id != null", limit=500)
tooling_api_query(sObject="ApexTrigger", fields=["Name"], whereClause="Id != null", limit=200)
```

2. Fetch bodies in batches of 50 (large bodies can make bigger batches fail):

```
tooling_api_query(
  sObject="ApexClass",
  fields=["Name", "Body"],
  whereClause="Name IN (<50 names>)"
)
```

Repeat with `ApexTrigger` for trigger names.

**Backoff strategy**: If a batch of 50 fails (timeout or response size error), retry with 20 names, then 10, then fall back to individual queries for that batch.

3. Validate each body (write → validate → delete), using `.cls` or `.trigger` extension as appropriate.
4. Show the summary table (classes and triggers together) sorted by score ascending.
5. Highlight any below 105/150 (70%) as requiring attention.

---

## Execution modes

This skill supports four execution modes — see
`references/execution-modes.md` for detection logic and full details,
`references/mcp-pagination.md` for handling large MCP responses, and
[`../../shared/references/cirra-mcp-tools.md`](../../shared/references/cirra-mcp-tools.md)
for the authoritative Cirra AI MCP tool signatures used in this skill.

All Apex operations go through MCP tools regardless of mode. The mode
determines whether local tooling (filesystem, code execution) is
available for post-processing and how large query results are retrieved.

---

## Core Responsibilities

1. **Code Generation**: Create Apex classes, triggers (TAF), tests, async jobs from requirements
2. **Code Review**: Analyze existing Apex for best practices violations with actionable fixes
3. **Validation & Scoring**: Score code against 8 categories (0-150 points)
4. **Deployment**: Deploy Apex classes and triggers via `tooling_api_dml` (Tooling API). Use `metadata_create`/`metadata_update` only for non-Apex metadata (Custom Objects, fields, etc.)
5. **Test Execution**: Run the delivered test classes with `run_tests`, read `ApexTestResult` / `ApexCodeCoverageAggregate`, and iterate on failures (max 3 rounds)

---

## Fast Path (Simple Requests)

For simple, self-contained requests (utility class, hello-world, single-method class, quick test), bypass the detailed requirements/design elaboration and full scoring from Phases 1-3 while still performing initialization and mandatory guardrails, then generate + deploy:

1. Call `cirra_ai_init()` (Phase 1 init; always required)
2. Generate the code as a string
3. Run mandatory guardrail checks (anti-patterns only — skip full 150-point scoring)
4. Deploy via `tooling_api_dml`
5. Verify deployment
6. Run the test class with `run_tests` and report pass/fail + coverage

**Use the fast path when**: the request is explicit, the class is self-contained, and there are no ambiguous requirements to clarify.

**Use the full 5-phase workflow when**: the request involves multiple classes, triggers, complex business logic, integrations, or underspecified requirements.

---

## Workflow (5-Phase Pattern)

### Phase 1: Requirements Gathering & MCP Initialization

**FIRST**: Call `cirra_ai_init()` with no parameters:

```
cirra_ai_init()
```

- If a default org is configured, proceed immediately and confirm with the user:
  > "I've connected to **[org]**. Would you like me to use the defaults, or do you want to select different options?"
- If no default is configured, ask for the Salesforce user/alias before proceeding.

Do **not** ask for org details before calling `cirra_ai_init()`.

**Then**, if the request is underspecified, ask concise follow-up questions covering:

- Class type (Trigger, Service, Selector, Batch, Queueable, Test, Controller)
- Primary purpose (one sentence)
- Target object(s)
- Test requirements

**Then**:

1. Check existing code: `tooling_api_query(sObject="ApexClass", fields=["Id", "Name"], whereClause="Name LIKE '%Account%'")`
2. Check for existing Trigger Actions Framework: `tooling_api_query(sObject="ApexClass", fields=["Id", "Name"], whereClause="Name LIKE 'TA_%'")`
3. Keep an internal checklist for requirements, generation, validation, deployment, and testing

---

### Phase 2: Design & Template Selection

**Select template** (for reference - code is generated as strings):

| Class Type        | Reference Template                |
| ----------------- | --------------------------------- |
| Trigger           | Standard TAF trigger pattern      |
| Trigger Action    | TA_ObjectName_Purpose naming      |
| Service           | Service layer pattern             |
| Selector          | Selector pattern for queries      |
| Batch             | Batch Apex pattern                |
| Queueable         | Queueable/async pattern           |
| Test              | Test class with PNB patterns      |
| Test Data Factory | Factory pattern for test data     |
| Standard Class    | Standard utility/controller class |

**Template-Free Design**: Generate Apex code directly as strings following naming conventions and patterns. No file system templates needed.

---

### Phase 3: Code Generation/Review

**For Generation**:

1. Generate Apex code as a STRING (not saved to file system)
2. Apply naming conventions (see best practices section)
3. Include ApexDoc comments
4. Generate corresponding test class as STRING
5. Validate code against guardrails (see below)

**For Review**:

1. Fetch the code from the org — the validator only reads local files and never talks to the org: `tooling_api_query(sObject="ApexClass", fields=["Id", "Name", "Body", "ApiVersion"], whereClause="Name = '<ClassName>'")` (or `whereClause="Id = '<classId>'"`)
2. Write `Body` to a temp file and score it: `python3 scripts/validate_apex_cli.py /tmp/<ClassName>.cls <ApiVersion>` (`.trigger` for triggers)
3. Analyze against best practices and generate improvement report with specific fixes
4. For bulk review, fetch bodies with `whereClause="Name IN ('Class1', 'Class2', 'Class3')"` (or `whereClause="Id != null"` in batches of 50 for the whole org), write each to its own file and validate each — the Validate Apex workflow above has the batching and backoff rules

**Run Validation**:

```
Score: XX/150 ⭐⭐⭐⭐ Rating
├─ Bulkification: XX/25
├─ Security: XX/25
├─ Testing: XX/25
├─ Architecture: XX/20
├─ Clean Code: XX/20
├─ Error Handling: XX/15
├─ Performance: XX/10
└─ Documentation: XX/10
```

---

### ⛔ GENERATION GUARDRAILS (MANDATORY)

**BEFORE generating ANY Apex code, VERIFY no anti-patterns are introduced.**

If ANY of these patterns would be generated, **STOP and ask the user**:

> "I noticed [pattern]. This will cause [problem]. Should I:
> A) Refactor to use [correct pattern]
> B) Proceed anyway (not recommended)"

| Anti-Pattern                  | Detection                                                   | Impact                                                                                     |
| ----------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| SOQL inside loop              | `for(...) { [SELECT...] }`                                  | Governor limit failure (100 SOQL)                                                          |
| DML inside loop               | `for(...) { insert/update }`                                | Governor limit failure (150 DML)                                                           |
| Missing sharing               | `class X {` without keyword                                 | Security violation                                                                         |
| Hardcoded ID                  | 15/18-char ID literal                                       | Deployment failure                                                                         |
| Empty catch                   | `catch(e) { }`                                              | Silent failures                                                                            |
| String concatenation in SOQL  | `'SELECT...WHERE Name = \'' + var`                          | SOQL injection                                                                             |
| Test without assertions       | `@IsTest` method with no `Assert.*`                         | False positive tests                                                                       |
| Java types in Apex            | `ArrayList`, `HashMap`, `int`, `boolean`                    | Compile error — use `List`, `Map`, `Integer`, `Boolean`                                    |
| Non-existent Apex methods     | `.size()` on SObject, `.get()` on non-Map                   | Compile error — verify API before using                                                    |
| Wrong Map initialization      | `new Map{'key' => val}` (curly-brace syntax)                | Compile error — use `new Map<K,V>()` then `.put()`                                         |
| `@future` in new code         | `@future` / `@future(callout=true)`                         | Cannot chain, cannot call from Batch, primitives only — use Queueable + `System.Finalizer` |
| `System.debug()` on main path | `System.debug(` outside tests / temporary diagnostics       | Log noise, CPU cost, leaks data — use a logging framework or remove before deploy          |
| Custom metadata via SOQL      | `[SELECT ... FROM X__mdt]`                                  | Counts against SOQL limits — use `X__mdt.getAll()` / `getInstance()`                       |
| Unhandled partial DML         | `Database.update(records, false)` with no `SaveResult` loop | Silent partial failures — iterate `Database.SaveResult`, log/raise per failed record       |

**DO NOT generate anti-patterns even if explicitly requested.** Ask user to confirm the exception with documented justification.

### ✅ MANDATORY DELIVERABLES

**Every Apex generation MUST include these artifacts.** Do NOT deliver a class or trigger without the corresponding items below.

#### 1. Triggers MUST have a helper class

Never put business logic directly in a trigger body. Always extract logic into a separate handler/helper class:

- **If TAF is installed** → generate the trigger (`new MetadataTriggerHandler().run()`) + one or more `TA_Object_Purpose` action classes
- **If TAF is NOT installed** → generate a thin trigger that delegates to a handler class (e.g., `AccountTriggerHandler`) containing all logic

The trigger file should contain only routing; the helper class holds the logic. This is non-negotiable regardless of how simple the logic seems.

#### 2. Unit tests for ALL generated Apex

Every class **and** every trigger (including its helper/handler) MUST have a corresponding test class delivered in the same response. The test class MUST include at minimum the PNB pattern:

- **P**ositive — happy-path test
- **N**egative — error/exception test
- **B**ulk — 251+ records test

If the generated code includes both a trigger + helper class, the test class should cover both (trigger fires correctly, helper logic works in isolation).

Do NOT defer test generation to a later step or offer it as optional. Tests are part of the deliverable, not follow-up work.

---

### Phase 4: Metadata Deployment

**Step 1: Generate Code String**
Generate Apex code as a STRING with full ApexDoc comments and validation.

**Step 2: Deploy via Cirra AI MCP**

> **Validation**: When installed as part of the `cirra-ai-sf` plugin, a
> `PreToolUse` hook (`pre-mcp-validate.py`, registered in the plugin's
> `hooks/hooks.json`) runs before every `metadata_create` / `metadata_update`
> / `tooling_api_dml` call and surfaces critical issues (SOQL/DML in loops,
> injection). **Standalone skill installs do not get this hook** — run
> `python3 scripts/validate_apex_cli.py <file>` manually before deploying.

> **IMPORTANT**: Apex classes MUST be deployed via `tooling_api_dml`, NOT `metadata_create`.
> The Metadata API does not support the `body`/`Body` field for `ApexClass`. Use the
> Tooling API pattern below — note `Name` (not `fullName`) and `Body` (capital B).

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "AccountService",
    "Body": "[YOUR APEX CODE STRING HERE]",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

**Step 3: Verify Deployment**

```
tooling_api_query(
  sObject="ApexClass",
  fields=["Id", "Name", "Status"],
  whereClause="Name = 'AccountService'"
)
```

**Step 4: Test Execution** — run the test class and read results (full call sequence in [Run tests via `run_tests`](#run-tests-via-run_tests)):

```
run_tests(tests=[{"className": "AccountServiceTest"}])
```

Poll `ApexTestQueueItem` for the returned job id, then read `ApexTestResult` and `ApexCodeCoverageAggregate`. Fix and redeploy on failure (max 3 iterations).

**Error Handling**: If `tooling_api_dml` returns an error:

- `REQUIRED_FIELD_MISSING` for `ApexClass` → ensure required fields like `Status` and `ApiVersion` are populated on insert or update
- `INVALID_TYPE` for `ApexClass` → verify the `sObject` name is exactly `ApexClass` (case-sensitive) and that you are calling the Tooling API, not the Metadata or REST sObjects endpoint
- `NOT_FOUND` → typically occurs when updating or deleting with an `Id` that does not exist or is not visible in the current org; query first to verify the `Id` and context
- `DUPLICATE_VALUE` → a class with that `Name` already exists; query for the existing Id and use `operation="update"` instead
- Compilation errors → read the error message, fix the Apex code string, and retry the `tooling_api_dml` call
- Do **not** fall back to `metadata_create` for Apex classes — it does not support the `Body` field

---

### Phase 5: Documentation & Testing Guidance

**Completion Summary**:

```
✓ Apex Code Complete: [ClassName]
  Type: [type] | API: 67.0
  Deployment: VIA CIRRA AI MCP (tooling_api_dml)
  Test Class: [TestClassName]
  Validation: PASSED (Score: XX/150)
  Tests: X passed / Y failed (run_tests job <jobId>) | Coverage: NN%

Next Steps: verify via tooling_api_query, monitor logs (references/troubleshooting.md)
```

If tests could not be run (tool unavailable, org restriction), say so explicitly: `Tests: not run — <reason>`. Never report coverage you did not read from `ApexCodeCoverageAggregate`.

---

## Best Practices (150-Point Scoring)

| Category           | Points | Key Rules                                                                        |
| ------------------ | ------ | -------------------------------------------------------------------------------- |
| **Bulkification**  | 25     | NO SOQL/DML in loops; collect first, operate after; test 251+ records            |
| **Security**       | 25     | `WITH USER_MODE`; bind variables; `with sharing`; `Security.stripInaccessible()` |
| **Testing**        | 25     | 90%+ coverage; Assert class; positive/negative/bulk tests; Test Data Factory     |
| **Architecture**   | 20     | TAF triggers; Service/Domain/Selector layers; SOLID; dependency injection        |
| **Clean Code**     | 20     | Meaningful names; self-documenting; no `!= false`; single responsibility         |
| **Error Handling** | 15     | Specific before generic catch; no empty catch; custom business exceptions        |
| **Performance**    | 10     | Monitor with `Limits`; cache expensive ops; scope variables; async for heavy     |
| **Documentation**  | 10     | ApexDoc on classes/methods; meaningful params                                    |

**Thresholds**: ✅ 90+ (Deploy) | ⚠️ 70-89 (Review) | ❌ <70 (Block - fix required). Findings use one five-level severity scale — `CRITICAL` > `HIGH` > `MODERATE` > `LOW` > `INFO` (Salesforce Code Analyzer ordering) — shared with sf-audit; fix every `CRITICAL`/`HIGH` finding before deploying regardless of score.

**Exemption for trivial classes**: Simple utility classes, hello-world examples, and single-purpose test helpers are exempt from the <70 block threshold. Score them for informational purposes but do not block deployment. The guardrail anti-pattern checks (SOQL in loops, missing sharing, etc.) still apply regardless of complexity.

---

## Trigger Actions Framework (TAF)

### Quick Reference

**When to Use**: If TAF package is installed in target org

**Check Installation**:

```
tooling_api_query(
  sObject="InstalledSubscriberPackage",
  fields=["Id", "SubscriberPackage.Name", "SubscriberPackageVersion.Name"],
  whereClause="Id != null"
)
```

Look for `Trigger Actions Framework` in `SubscriberPackage.Name`. If the package list is inconclusive, check for the framework's handler class directly:

```
tooling_api_query(
  sObject="ApexClass",
  fields=["Id", "Name"],
  whereClause="Name = 'MetadataTriggerHandler'"
)
```

**Trigger Pattern** (one per object):

```apex
trigger AccountTrigger on Account (before insert, after insert, before update, after update, before delete, after delete, after undelete) {
    new MetadataTriggerHandler().run();
}
```

**Action Class** (one per behavior):

```apex
public class TA_Account_SetDefaults implements TriggerAction.BeforeInsert {
    public void beforeInsert(List<Account> newList) {
        for (Account acc : newList) {
            if (acc.Industry == null) {
                acc.Industry = 'Other';
            }
        }
    }
}
```

**Deploy Action Class**:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "TA_Account_SetDefaults",
    "Body": "[GENERATED APEX CODE]",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

**⚠️ CRITICAL**: TAF triggers do NOTHING without `Trigger_Action__mdt` records! Each action class needs a corresponding Custom Metadata record (deploy manually or via separate metadata deployment).

**Fallback**: If TAF is NOT installed, use standard trigger pattern (non-TAF).

---

## Async Decision Matrix

**Queueable is the default.** Reach for something else only when the row says so.

| Scenario                                                                                                                   | Use                                                                                                                                                     |
| -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Any async work: callouts, heavy logic, chaining                                                                            | `Queueable` (`implements Queueable, Database.AllowsCallouts`) — supports complex state, chaining, job Id                                                |
| Delay, or de-duplicate the same job                                                                                        | `Queueable` + `AsyncOptions` (`MinimumQueueableDelayInMinutes` up to 10 minutes, `DuplicateSignature`) passed to `System.enqueueJob`                    |
| Delay longer than 10 minutes                                                                                               | `System.scheduleBatch()`                                                                                                                                |
| Large result set without Batch overhead                                                                                    | `Queueable` + `Database.Cursor` (`Database.getCursor`, `cursor.fetch(position, Math.min(200, remaining))`, re-enqueue with position)                    |
| Guaranteed cleanup / retry / logging after a job                                                                           | `System.Finalizer` attached with `System.attachFinalizer` inside `execute`                                                                              |
| Needs the `QueryLocator` start → execute → finish lifecycle (millions of rows, `Database.Stateful`, org-wide reprocessing) | `Batch Apex` (max 5 concurrent jobs)                                                                                                                    |
| Recurring schedule                                                                                                         | **Scheduled Flow** (declarative, no code) — `Schedulable` only when the schedule must enqueue Apex that Flow cannot express                             |
| Long-running callout from LWC/Visualforce                                                                                  | `Continuation` (up to 3 callouts per transaction, run in parallel)                                                                                      |
| `@future`                                                                                                                  | **Legacy — do not generate.** No chaining, no complex parameters, no job Id, no Finalizer. Migrate to `Queueable` when touching existing `@future` code |

Chained Queueables must guard depth (`AsyncInfo.hasMaxStackDepth()` / `AsyncOptions.MaximumQueueableStackDepth`) and must never enqueue from a loop. Full examples: `references/best-practices.md` §7 and `references/patterns-deep-dive.md` → Async Patterns.

---

## Modern Apex Features (API 67.0)

- **Null coalescing**: `value ?? defaultValue`
- **Safe navigation**: `record?.Field__c`
- **User mode**: `WITH USER_MODE` in SOQL; `AccessLevel.USER_MODE` on `Database` DML (defaults at 67.0+)
- **Assert class**: `Assert.areEqual()`, `Assert.isTrue()`
- **Apex Cursors**: `Database.getCursor(query)` / `Database.getCursorWithBinds(...)` then `cursor.fetch(position, count)` — up to 50 million rows; combine with Queueable chaining instead of new Batch jobs when a `QueryLocator` lifecycle is not required
- **Queueable delay / dedup**: `AsyncOptions` (delay up to 10 minutes, `DuplicateSignature`)
- **Finalizers**: `System.Finalizer` attached with `System.attachFinalizer` for guaranteed post-job cleanup

**Breaking Change (API 62.0)**: Cannot modify Set while iterating - throws `System.FinalException`

---

## Flow Integration (@InvocableMethod)

Apex classes can be called from Flow using `@InvocableMethod`. This pattern enables complex business logic, DML, callouts, and integrations from declarative automation.

### Quick Pattern

```apex
public with sharing class RecordProcessor {

    @InvocableMethod(label='Process Record' category='Custom')
    public static List<Response> execute(List<Request> requests) {
        List<Response> responses = new List<Response>();
        for (Request req : requests) {
            Response res = new Response();
            res.isSuccess = true;
            res.processedId = req.recordId;
            responses.add(res);
        }
        return responses;
    }

    public class Request {
        @InvocableVariable(label='Record ID' required=true)
        public Id recordId;
    }

    public class Response {
        @InvocableVariable(label='Is Success')
        public Boolean isSuccess;
        @InvocableVariable(label='Processed ID')
        public Id processedId;
    }
}
```

**Deploy via Cirra AI**:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "RecordProcessor",
    "Body": "[YOUR INVOCABLE METHOD CODE]",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

---

## Testing Best Practices

### The 3 Test Types (PNB Pattern)

Every feature needs:

1. **Positive**: Happy path test
2. **Negative**: Error handling test
3. **Bulk**: 251+ records test

**Example**:

```apex
@IsTest
static void testPositive() {
    Account acc = new Account(Name = 'Test', Industry = 'Tech');
    insert acc;
    Assert.areEqual('Tech', [SELECT Industry FROM Account WHERE Id = :acc.Id].Industry);
}

@IsTest
static void testNegative() {
    try {
        insert new Account(); // Missing Name
        Assert.fail('Expected DmlException');
    } catch (DmlException e) {
        Assert.isTrue(e.getMessage().contains('REQUIRED_FIELD_MISSING'),
            'Expected REQUIRED_FIELD_MISSING but got: ' + e.getMessage());
    }
}

@IsTest
static void testBulk() {
    List<Account> accounts = new List<Account>();
    for (Integer i = 0; i < 251; i++) {
        accounts.add(new Account(Name = 'Bulk ' + i));
    }
    insert accounts;
    Assert.areEqual(251, [SELECT COUNT() FROM Account]);
}
```

**Deploy Test Class**:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "AccountServiceTest",
    "Body": "[YOUR TEST CLASS CODE]",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

---

## Common Exception Types

When writing test classes, use these specific exception types:

| Exception Type         | When to Use                   |
| ---------------------- | ----------------------------- |
| `DmlException`         | Insert/update/delete failures |
| `QueryException`       | SOQL query failures           |
| `NullPointerException` | Null reference access         |
| `ListException`        | List operation failures       |
| `LimitException`       | Governor limit exceeded       |
| `CalloutException`     | HTTP callout failures         |

---

## Cirra AI MCP Server Integration

### Required Initialization

**ALWAYS start with**:

```
cirra_ai_init()
```

Call with no parameters — uses the default org. If a default is configured, confirm with the user before proceeding. If no default is configured, ask for the Salesforce user/alias.

This initializes the connection to Cirra AI MCP Server and provides access to all Salesforce metadata operations.

### API Routing — Which Tool for Which Metadata Type

Different metadata types require different APIs. Using the wrong one causes silent failures or missing fields:

| Metadata Type                 | Correct Tool      | Why                                                 |
| ----------------------------- | ----------------- | --------------------------------------------------- |
| `ApexClass`, `ApexTrigger`    | `tooling_api_dml` | Metadata API does not support `Body` field for Apex |
| `Flow`                        | `metadata_create` | Tooling API's `Flow` object is read-only            |
| `LightningComponentBundle`    | `metadata_create` | Requires Base64-encoded sources in metadata format  |
| `CustomObject`, `CustomField` | `metadata_create` | Standard Metadata API types                         |
| `PermissionSet`               | `metadata_create` | Standard Metadata API type                          |
| `ValidationRule`              | `metadata_create` | Standard Metadata API type                          |
| Data records (Account, etc.)  | `sobject_dml`     | REST API for record-level CRUD (not metadata)       |

### MCP Tools Mapping

| Operation           | MCP Tool            | Example                                                                                                                            |
| ------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Query Apex code     | `tooling_api_query` | `tooling_api_query(sObject="ApexClass", fields=["Id","Name","Body"], whereClause="Name = 'AccountService'")`                       |
| Query metadata      | `tooling_api_query` | `tooling_api_query(sObject="ApexTrigger", fields=["Id","Name","TableEnumOrId"], whereClause="TableEnumOrId = 'Account'")`          |
| Deploy class        | `tooling_api_dml`   | `tooling_api_dml(operation="insert", sObject="ApexClass", record={"Name":"MyClass","Body":"...","Status":"Active"})`               |
| Update class        | `tooling_api_dml`   | `tooling_api_dml(operation="update", sObject="ApexClass", record={"Id":"...","Name":"MyClass","Body":"...","Status":"Active"})`    |
| List classes        | `tooling_api_query` | `tooling_api_query(sObject="ApexClass", fields=["Id","Name","ApiVersion"], whereClause="NamespacePrefix = null", limit=500)`       |
| Retrieve class body | `tooling_api_query` | `tooling_api_query(sObject="ApexClass", fields=["Id","FullName","Name","Body","Metadata"], whereClause="Id = '<classId>'")`        |
| Describe object     | `sobject_describe`  | `sobject_describe(sObject="Account")`                                                                                              |
| Delete class        | `tooling_api_dml`   | `tooling_api_dml(operation="delete", sObject="ApexClass", recordId="<classId>")`                                                   |
| Run tests           | `run_tests`         | `run_tests(tests=[{"className":"AccountServiceTest"}])` → job id                                                                   |
| Test results        | `tooling_api_query` | `tooling_api_query(sObject="ApexTestResult", fields=["MethodName","Outcome","Message"], whereClause="AsyncApexJobId = '<jobId>'")` |

### Run tests via `run_tests`

`run_tests` is asynchronous: it enqueues the run and returns a job id. Always run the test class after every deploy (Create step 6, Update step 6, Phase 4 step 4).

**1. Start the run** (one or more classes; `testMethods` narrows to specific methods):

```
run_tests(tests=[{"className": "<ClassName>Test"}])
```

Org-wide alternative when coverage for a production deploy matters: `run_tests(testLevel="RunLocalTests", category=["Apex"])` — warn the user that this can take minutes on a large org.

**2. Poll until finished** — repeat (waiting ~10–15 s between calls) until every row's `Status` is `Completed`, `Failed`, or `Aborted`:

```
tooling_api_query(
  sObject="ApexTestQueueItem",
  fields=["Id", "Status", "ApexClass.Name", "ExtendedStatus"],
  whereClause="ParentJobId = '<jobId>'"
)
```

**3. Read results**:

```
tooling_api_query(
  sObject="ApexTestResult",
  fields=["MethodName", "Outcome", "Message", "StackTrace", "RunTime"],
  whereClause="AsyncApexJobId = '<jobId>'"
)
```

**4. Read coverage** for the class under test (not the test class):

```
tooling_api_query(
  sObject="ApexCodeCoverageAggregate",
  fields=["ApexClassOrTrigger.Name", "NumLinesCovered", "NumLinesUncovered"],
  whereClause="ApexClassOrTrigger.Name = '<ClassName>'"
)
```

Coverage % = `NumLinesCovered / (NumLinesCovered + NumLinesUncovered) × 100`.

**5. Report and iterate**: show `X passed / Y failed`, each failure's `MethodName` + `Message` + first `StackTrace` line, and the coverage %. If anything failed (or coverage is below 75% for code headed to production), fix the class or the test, redeploy via `tooling_api_dml(operation="update", ...)`, and rerun from step 1. **Maximum three iterations** — then stop, report what still fails, and ask the user how to proceed. Failure-type → fix guidance lives in `references/testing-guide.md` → "Test-fix loop".

### Apex Class / Trigger DML Format

Use `tooling_api_dml` for all Apex class and trigger create/update/delete operations:

**Create class**:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexClass",
  record={
    "Name": "ClassName",
    "Body": "public class ClassName { ... }",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

**Update class** (Id, Name, Body, Status are all required):

> **IMPORTANT**: The `Name` field is required in `tooling_api_dml` update payloads even though you are updating an existing record. Omitting it causes `Missing or invalid 'Name' field` error.

```
tooling_api_dml(
  operation="update",
  sObject="ApexClass",
  record={
    "Id": "<classId>",
    "Name": "ClassName",
    "Body": "public class ClassName { ... }",
    "Status": "Active"
  }
)
```

**Create trigger**:

```
tooling_api_dml(
  operation="insert",
  sObject="ApexTrigger",
  record={
    "Name": "AccountTrigger",
    "TableEnumOrId": "Account",
    "Body": "trigger AccountTrigger on Account (before insert, after insert) { ... }",
    "Status": "Active",
    "ApiVersion": "67.0"
  }
)
```

**Update trigger** (Id, TableEnumOrId, Name, Body, Status all required):

```
tooling_api_dml(
  operation="update",
  sObject="ApexTrigger",
  record={
    "Id": "<triggerId>",
    "Name": "AccountTrigger",
    "TableEnumOrId": "Account",
    "Body": "trigger AccountTrigger on Account (...) { ... }",
    "Status": "Active"
  }
)
```

### Query Examples

**Find all Apex classes**:

```
tooling_api_query(
  sObject="ApexClass",
  fields=["Id", "Name", "ApiVersion", "Status"],
  whereClause="Id != null",
  limit=500
)
```

**Find test results for a class**:

```
tooling_api_query(
  sObject="ApexTestResult",
  fields=["MethodName", "Outcome", "Message", "StackTrace", "TestTimestamp"],
  whereClause="ApexClass.Name = 'AccountServiceTest'",
  orderBy="TestTimestamp DESC",
  limit=10
)
```

(`ApexTestResult` has no `TestClassName` field — filter on the `ApexClass.Name` relationship, or on `AsyncApexJobId` for a specific `run_tests` job.)

**Find triggers on Account**:

```
tooling_api_query(
  sObject="ApexTrigger",
  fields=["Id", "Name", "Status", "ApiVersion"],
  whereClause="TableEnumOrId = 'Account'"
)
```

**Query with SOQL (not metadata)**:

```
soql_query(
  sObject="Account",
  fields=["Id", "Name", "Industry"],
  whereClause="Industry = 'Technology'",
  limit=10
)
```

---

## Cross-MCP Tool Integration

| MCP Tool            | Use Case                             | Example                                                                                                                                       |
| ------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `sobject_describe`  | Discover object/fields before coding | `sobject_describe(sObject="Invoice__c")` → get field names, types, CRUD                                                                       |
| `soql_query`        | Test code behavior after deploy      | `soql_query(sObject="Account", fields=["Id","Name","Industry"], whereClause="Id IN ('001...', '001...')")` — literals only, no bind variables |
| `tooling_api_query` | Check existing Apex classes          | `tooling_api_query(sObject="ApexClass", fields=["Id","Name"], whereClause="Name LIKE 'Account%'")`                                            |
| `tooling_api_query` | Retrieve class body for review       | `tooling_api_query(sObject="ApexClass", fields=["Id","FullName","Name","Body","Metadata"], whereClause="Id = '<classId>'")`                   |
| `tooling_api_dml`   | Deploy new Apex classes/triggers     | `tooling_api_dml(operation="insert", sObject="ApexClass", record={"Name":"MyClass","Body":"...","Status":"Active"})`                          |
| `tooling_api_dml`   | Update existing Apex code            | `tooling_api_dml(operation="update", sObject="ApexClass", record={"Id":"...","Name":"MyClass","Body":"...","Status":"Active"})`               |
| `tooling_api_dml`   | Perform DML on metadata objects      | `tooling_api_dml(operation="update", sObject="ApexClass", record={...})`                                                                      |
| `run_tests`         | Execute tests after deploy           | `run_tests(tests=[{"className":"MyClassTest"}])` → poll `ApexTestQueueItem`, read `ApexTestResult`                                            |

---

## Field-Level Security & CRUD Checks

Before generating code that accesses fields, use `sobject_describe`:

```
sobject_describe(sObject="Account")
→ Returns: fields[], CRUD permissions, sharing rules
```

In generated code, use:

```apex
// For CRUD/FLS checking
List<String> fieldsToRead = new List<String>{ 'Name', 'Industry' };
Map<String, Schema.SObjectField> fieldMap = Schema.Account.getSObjectType().getDescribe().fields.getMap();

for (String field : fieldsToRead) {
    if (!fieldMap.get(field).getDescribe().isAccessible()) {
        throw new SecurityException('Field ' + field + ' is not accessible');
    }
}
```

Or use `Security.stripInaccessible()`:

```apex
List<Account> accounts = [SELECT Id, Name, Industry FROM Account LIMIT 100];
accounts = (List<Account>) Security.stripInaccessible(AccessType.READABLE, accounts);
```

---

---

## Glossary of MCP Terms

- **MCP**: Model Context Protocol - allows the agent to access external applications like Salesforce
- **Cirra AI**: AI assistant that provides the Salesforce Admin MCP server
- **Metadata API**: Programmatic interface to deploy/retrieve Apex, triggers, config
- **Tooling API**: Query and update (via DML) metadata objects like ApexClass, ApexTrigger, ApexTestResult
- **ApexClass**: Apex class metadata object (stored in Salesforce)
- **ApexTrigger**: Apex trigger metadata object (stored in Salesforce)
- **ApexTestResult**: Test execution result metadata object (one row per test method per run; filter on `AsyncApexJobId`)
- **ApexTestQueueItem**: Per-class status row for a `run_tests` job (filter on `ParentJobId`)
- **ApexCodeCoverageAggregate**: Covered / uncovered line counts per class or trigger

---

## Apex Class MCP Patterns

**Always obtain explicit approval before creating, updating, or deleting a class or trigger.**

### List all classes

```
tooling_api_query(sObject="ApexClass", fields=["Id","Name","NamespacePrefix","ApiVersion","IsValid","Status","ManageableState"], whereClause="Id != null", limit=500)
```

### Retrieve class body (for review or edit)

```
tooling_api_query(sObject="ApexClass", fields=["Id","FullName","Name","NamespacePrefix","Body","Metadata"], whereClause="Id = '<classId>'")
```

Do **not** use `metadata_read` for ApexClass — it does not return the class body.

### Create a class

```
tooling_api_dml(operation="insert", sObject="ApexClass", record={"Name": "MyClass", "Body": "public class MyClass { ... }", "Status": "Active", "ApiVersion": "67.0"})
```

Offer to create a test class alongside. Verify referenced fields/objects exist before creating.

### Update a class

```
tooling_api_dml(operation="update", sObject="ApexClass", record={"Id": "<classId>", "Name": "MyClass", "Body": "...", "Status": "Active"})
```

### Delete a class

```
tooling_api_dml(operation="delete", sObject="ApexClass", recordId="<classId>")
```

Before deleting: check for references in other Apex classes, triggers, LWC, and flows. List references and offer to handle them first.

## Apex Trigger MCP Patterns

### List all triggers

```
tooling_api_query(sObject="ApexTrigger", fields=["Id","Name","NamespacePrefix","TableEnumOrId","ApiVersion","IsValid","Status","ManageableState"], whereClause="Id != null", limit=500)
```

### Retrieve trigger body

```
tooling_api_query(sObject="ApexTrigger", fields=["Id","FullName","Name","NamespacePrefix","TableEnumOrId","Body","Metadata"], whereClause="Id = '<triggerId>'")
```

### Create a trigger

```
tooling_api_dml(operation="insert", sObject="ApexTrigger", record={"Name": "AccountTrigger", "TableEnumOrId": "Account", "Body": "trigger AccountTrigger on Account (...) { ... }", "Status": "Active", "ApiVersion": "67.0"})
```

Suggest creating a helper class and test class alongside. Verify referenced fields/objects exist first.

### Update a trigger

```
tooling_api_dml(operation="update", sObject="ApexTrigger", record={"Id": "<triggerId>", "TableEnumOrId": "Account", "Name": "AccountTrigger", "Body": "...", "Status": "Active"})
```

### Delete a trigger

```
tooling_api_dml(operation="delete", sObject="ApexTrigger", recordId="<triggerId>")
```

---

## Cross-Skill Integration

| Related Skill | When to Use                                              |
| ------------- | -------------------------------------------------------- |
| sf-flow       | Create a Flow that calls `@InvocableMethod`              |
| sf-lwc        | Create an LWC that calls `@AuraEnabled` controllers      |
| sf-data       | SOQL authoring, field coverage, and test data            |
| sf-metadata   | Describe objects/fields before coding; non-Apex metadata |
| sf-audit      | Org-wide Apex/Flow/LWC audit                             |

---

## Dependencies

### Cirra AI MCP Server tools

#### Required

- cirra_ai_init
- soql_query
- tooling_api_query
- tooling_api_dml
- run_tests (run the delivered test classes after every deploy)

#### Optional

- sobject_describe
- metadata_create (for non-Apex metadata only)
- metadata_update (for non-Apex metadata only)
- metadata_read
- metadata_delete
- sobjects_list

---

## Notes

- **API Version**: Deploy with 67.0 by default. If the org runs an older release, match the org's API version: `soql_query(sObject="Organization", fields=["Id", "InstanceName"], whereClause="Id != null")` — the org's current API version is the highest `ApiVersion` accepted by the Tooling API; when unsure, deploy at the version of the newest existing class (`tooling_api_query(sObject="ApexClass", fields=["ApiVersion"], whereClause="NamespacePrefix = null", orderBy="ApiVersion DESC", limit=1)`)
- **API 67.0 behavior changes** (Summer '26 — [release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_apex.htm&release=262&type=5)): database operations default to **user mode** (not system mode); classes without a sharing declaration default to **`with sharing`** (previously `without sharing`); **`WITH SECURITY_ENFORCED` is removed** — classes at 67.0+ that use it do not compile, use `WITH USER_MODE` instead; DML/SOQL inside trigger bodies also runs in user mode unless system mode is explicit. Keep declaring sharing mode explicitly and prefer `WITH USER_MODE` — code that intentionally needs system-mode access must say `without sharing` / `AccessLevel.SYSTEM_MODE` explicitly at 67.0. **These changes are versioned per class**: a class pinned at ApiVersion 66.0 or earlier keeps the old semantics and still compiles with `WITH SECURITY_ENFORCED` — do not report existing older classes as broken. When updating such a class, keep its ApiVersion unless asked to raise it; migrate `WITH SECURITY_ENFORCED` to `WITH USER_MODE` (available since API 58.0) whenever touching the code, and always before raising ApiVersion to 67.0. Pass the class's ApiVersion to the validator so this check applies at the right severity
- **Invocable action parameters**: custom Apex classes used as invocable action parameters must have a visible no-argument constructor (global for packaged classes); API calls validate this from version 66.0
- **TAF Optional**: Prefer TAF when package is installed, use standard trigger pattern as fallback
- **2026 async**: Generate Queueable + Finalizer, not `@future`. Prefer Apex Cursors + Queueable over new Batch jobs unless start/finish or a `QueryLocator` is required. Prefer Scheduled Flow over `Schedulable`
- **Scoring**: Block deployment if score < 70% (exempt trivial/test classes — see scoring thresholds)
- **MCP Initialization**: ALWAYS call `cirra_ai_init` first
- **Code as String**: Generate all Apex as strings, deploy via `tooling_api_dml`
- **No Local Files**: Apex code is NOT saved to local file system - lives only in Salesforce org via Tooling API
- **Org-wide audit**: Use `/sf-audit` for a full org audit
- **Validation hook**: When the `cirra-ai-sf` plugin is installed, a plugin-level `PreToolUse` hook runs for Apex-related metadata operations (for example `ApexClass` and `ApexTrigger`), independent of the active skill. Standalone skill installs do not get this hook — use `python scripts/validate_apex_cli.py ...` for on-demand checks in either case.
