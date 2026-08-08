---
name: sf-flow
plugin: cirra-ai-sf
argument-hint: '[create|update|validate] {FlowName} ...'
metadata:
  version: 2.3.2
description: >
  Creates and validates Salesforce flows with 110-point scoring and Winter '26 best practices
  using Cirra AI MCP Server. Use when building record-triggered flows, screen flows,
  autolaunched flows, scheduled flows, or reviewing existing flow performance.
  Usage: /sf-flow [create|update|validate] {FlowName} ...
---

# Salesforce Flow Development and Review

Expert Salesforce Flow Builder with deep knowledge of best practices, bulkification, and Winter '26 (API 65.0) metadata. Create production-ready, performant, secure, and maintainable flows using Cirra AI MCP Server for deployment.

## Dispatch

Parse `$ARGUMENTS` to determine the action:

| First argument or intent       | Workflow                 |
| ------------------------------ | ------------------------ |
| `create`, new flow request     | Create Flow              |
| `update`, modify existing flow | Update Flow              |
| `validate`, review, score      | Validate Flow            |
| _(no argument or unclear)_     | Ask the user (see below) |

When the operation is missing or unclear, **you MUST use `AskUserQuestion`** before proceeding:

```
AskUserQuestion(question="What would you like to do?\n\n1. **Create** — generate a new Flow\n2. **Update** — fetch, modify, validate, and redeploy\n3. **Validate** — score an existing Flow")
```

Do NOT guess the operation or default to one. Wait for the user's answer.

---

## Approval Processes: Choose the Engine First

When a request is to build an approval (e.g. "create an approval process", "require approval before X", "deal/discount approval", "gate a stage until approved"), do NOT start building until the **engine** is decided:

| Engine                                        | Build with                                                                                                  | Use when                                                                                                                                                                 |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Flow Approval Orchestration** (recommended) | this skill (`processType` Orchestrator, record-triggered) + the Setup approval wizard for the approval step | Default. Salesforce's active investment; native record-change auto-trigger; Approval Trace audit log; recall/reassign; Apex-extensible; free (no orchestration credits). |
| **Legacy (classic) Approval Process**         | `sf-metadata` (`ApprovalProcess` metadata type)                                                             | Simple single-step manager approvals; need built-in **delegate approver**; org already standardized on classic.                                                          |

**If the user has not explicitly named the engine, ASK (one question) and recommend Flow Approval Orchestration.** Do not default silently.

```
AskUserQuestion(question="Build this as a **Flow Approval Orchestration** (recommended — record-change auto-trigger, audit trace, Salesforce's strategic direction) or a **legacy Approval Process** (simpler, built-in delegate approver)?")
```

**Set expectations up front (true for BOTH engines):**

- An approval process cannot _prevent_ a field transition by itself. To gate (e.g. block `Closed Won` until approved) you ALSO need a **validation rule** keyed off either a custom "approved" flag (set by a final-approval field update / background step) or `PRIORVALUE(StageName)`.
- Auto-trigger on record change is **native** to Flow record-triggered orchestrations; classic needs a separate record-triggered auto-submit flow.
- The orchestration's **approval step** subtype does not reliably round-trip through the Metadata API — assemble that step in the Setup approval wizard / Flow Builder. Build the supporting **approver screen flow** and **background field-update flow** with this skill, then wire them in the wizard.

### Minimize metadata round-trips

- **Read before update** for any element the API replaces wholesale (`Layout`, `ApprovalProcess`, `StandardValueSet`, `Flow`): fetch current → change the one field → send the complete payload. A partial payload silently drops siblings.
- **Use exact metadata element names** — do not infer them from the Setup UI label. Known mismatches: `recordEditability` (NOT `recordEditabilityType`); the "Submit for Approval" standard button is `Submit` inside `excludeButtons`; OpportunityStage values are governed by `won`/`closed`/`forecastCategory`, not just `label`.
- **Batch** field/criteria reads into one `soql_query` / `metadata_read` instead of one call per item.
- Prefer the surgical tool where one exists (`page_layout_update` / `permission_set_update` JSON-Patch) over a full `metadata_update` rebuild.

---

## Action Workflow: Create Flow

Create a new Flow following Winter '26 best practices.

### Step 1. Gather requirements

Use AskUserQuestion to collect:

- **Flow type**: Record-Triggered, Screen, Autolaunched, Scheduled, or Platform Event-Triggered
- **Trigger object** (if record-triggered): which Salesforce object
- **Trigger event** (if record-triggered): before save, after save, or both
- **Primary purpose**: one sentence description
- **Special requirements**: subflows, invocable actions, external callouts, etc.

### Step 2. Check for existing flow

Before generating, confirm the flow doesn't already exist:

```
metadata_list(
  type="Flow",
  sf_user="<sf_user>"
)
```

If it exists, suggest running with `update <FlowApiName>` instead.

### Step 3. Generate

Create the flow XML following the sf-flow skill guidelines (see Workflow Design section below):

- Proper API naming conventions (snake_case with descriptive prefix)
- Fault paths on all DML and callout elements
- Bulkification patterns (no DML or SOQL in loops)
- Description and labels on all elements
- `runInMode="SystemModeWithoutSharing"` only where justified

### Step 4. Validate before deploying — REQUIRED, MANUAL

> **This step is not optional and is not automated.** Skipping it has shipped Flows with broken email actions, missing fault paths, and `InvalidDraft` states that only surface at runtime. A skill-scoped `PreToolUse` hook (`scripts/pre-mcp-validate.py`) ships with this skill, but **it is not wired up in every runtime environment** — until you confirm the hook is registered for your host, treat the manual step below as the contract.

Write the generated metadata to a temp file (`/tmp/<FlowApiName>.flow-meta.xml` for XML, `/tmp/<FlowApiName>.flow.json` for JSON), then run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-flow/scripts/validate_flow_cli.py" "/tmp/<FlowApiName>.flow-meta.xml"
```

Fix any **CRITICAL** or **HIGH** issues before deploying — including missing `faultConnector` on `actionCalls`, `recordCreates`, `recordUpdates`, `recordDeletes`, `recordLookups`, `apexPluginCalls`, and `waits` with callouts. A score below 80% (88/110) is a hard stop unless you explicitly state in your response why the deployment is going ahead anyway.

**Self-check before every `metadata_create` / `metadata_update` / `tooling_api_dml` call on a Flow.** Answer these four questions out loud (in your reasoning) before invoking the tool:

1. Did I write the Flow metadata to a file?
2. Did I run `validate_flow_cli.py` on that file?
3. Did the validator output appear in my context, with a score and an issue list?
4. Are all CRITICAL/HIGH issues resolved?

If you cannot answer "yes" to all four, do not call the deployment tool. Stop, run the validator, and resume.

**Default fault-routing rule for every Flow.** Every element that can fault at runtime needs a `faultConnector`: every `actionCalls` (email, callout, invocable Apex), every `recordCreates` / `recordUpdates` / `recordDeletes` / `recordLookups`, every `apexPluginCalls`, and every `waits` involving a callout. Routing the fault to a no-op terminal element is acceptable; routing it to the success path is not (it hides failures).

### Step 5. Deploy

```
metadata_create(
  type="Flow",
  metadata=[{"fullName": "<FlowApiName>", "label": "<Flow Label>", "apiVersion": 65, "processType": "<ProcessType>", "status": "Draft", ...}]
)
```

### Step 6. Report

Show the final validation score and deployment status.

---

## Action Workflow: Update Flow

Fetch, modify, validate, and redeploy an existing Salesforce Flow.

### Parsing the request

The argument should be a flow API name: `update Auto_Lead_Assignment do X`

If no flow name is given, ask the user which flow to update and what changes are needed.

### Step 1. Fetch the current implementation

```
metadata_read(
  type="Flow",
  fullNames=["<FlowApiName>"],
  sf_user="<sf_user>"
)
```

If the flow is not found, suggest running with `create` instead.

### Step 2. Read and understand

Review the existing flow XML before making any changes. Understand:

- Flow type and trigger configuration
- Existing element names and labels
- What the requested change affects

### Step 3. Apply changes

Modify the flow following sf-flow skill guidelines. Preserve:

- Existing element names and API references (other flows/components may reference them)
- Existing fault paths and error handling
- Description and label conventions already in use

### Step 4. Validate before deploying — REQUIRED, MANUAL

The same four-question self-check from the **Create** workflow applies here. The hook is not guaranteed to be wired up; the manual validator run is the contract. Write the updated metadata to a temp file and validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-flow/scripts/validate_flow_cli.py" "/tmp/<FlowApiName>.flow-meta.xml"
```

Fix any CRITICAL or HIGH issues before deploying. Score below 80% (88/110) is a hard stop unless you can explain why the deployment is going ahead anyway.

### Step 5. Deploy

```
metadata_update(
  type="Flow",
  metadata=[{"fullName": "<FlowApiName>", "label": "<Flow Label>", "apiVersion": 65, "processType": "<ProcessType>", "status": "Draft", ...}]
)
```

### Step 6. Report

Summarise the changes made and show the final validation score.

---

## Action Workflow: Validate Flow

Validate one or more Flows using the 110-point static analysis pipeline and return a scored report.

### Parsing the request

| Input after `validate`                                                               | Interpretation                                   |
| ------------------------------------------------------------------------------------ | ------------------------------------------------ |
| `Auto_Lead_Assignment`                                                               | Flow API name — fetch XML from org, validate     |
| `force-app/.../Auto_Lead_Assignment.flow-meta.xml` (ends `.flow-meta.xml` or `.xml`) | Local file — validate directly                   |
| `Auto_Lead_Assignment,Screen_Case_Intake`                                            | Comma-separated list — bulk fetch, validate each |
| `All`                                                                                | All Flow records in the org                      |
| _(no argument)_                                                                      | Ask the user what to validate                    |

### Validation script

The validation script is at `${CLAUDE_PLUGIN_ROOT}/skills/sf-flow/scripts/validate_flow_cli.py`. Locate it with:

```bash
# $CLAUDE_PLUGIN_ROOT is set by Claude Code. Other hosts: see references/execution-modes.md.
# If not set, find the script:
find ~/.claude/plugins -name "validate_flow_cli.py" 2>/dev/null | grep sf-flow | head -1
```

### Local file

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-flow/scripts/validate_flow_cli.py" "<file_path>"
```

### Flow API name (fetch from org)

1. Fetch the Flow XML:

```
metadata_read(
  type="Flow",
  fullNames=["<FlowApiName>"],
  sf_user="<sf_user>"
)
```

2. Write the XML content to a temp file:

```
Write /tmp/validate_<FlowApiName>.flow-meta.xml  ← the flow XML
```

3. Validate:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sf-flow/scripts/validate_flow_cli.py" "/tmp/validate_<FlowApiName>.flow-meta.xml"
```

4. Delete the temp file after validation.

### Comma-separated list

Fetch all flow XML bodies in a single call:

```
metadata_read(
  type="Flow",
  fullNames=["Flow1", "Flow2", "Flow3"],
  sf_user="<sf_user>"
)
```

**Fallback**: If the bulk read fails (timeout or size error), fall back to individual `metadata_read` calls per flow.

Validate each flow body (write → validate → delete). After all flows are validated, show a summary table sorted by score ascending (worst first):

| Flow                        | Score  | %   | Status          |
| --------------------------- | ------ | --- | --------------- |
| Before_Opportunity_Validate | 72/110 | 65% | Below threshold |
| Auto_Lead_Assignment        | 98/110 | 89% | Pass            |

### All

1. Fetch all flow names:

```
metadata_list(type="Flow", sf_user="<sf_user>")
```

2. Fetch flow XML in batches of 20 (large flows can make bigger batches fail):

```
metadata_read(
  type="Flow",
  fullNames=["Flow1", ..., "Flow20"],
  sf_user="<sf_user>"
)
```

**Backoff strategy**: If a batch of 20 fails (timeout or response size error), retry with 10, then 5, then fall back to individual reads for that batch.

3. Validate each flow (write → validate → delete).
4. Show the summary table sorted by score ascending.
5. Highlight any below 88/110 (80%) as requiring attention.

---

## 📋 Quick Reference: Validation and Deployment

**Flow Creation & Deployment Workflow:**

```text
1. Call cirra_ai_init (REQUIRED - one per session)
2. Generate Flow metadata (JSON object — NOT XML)
3. Deploy via metadata_create tool (Cirra AI MCP Server)
4. Retrieve existing flows via metadata_read or metadata_list (Cirra AI MCP Server)
5. Query Flow metadata via tooling_api_query for Flow/FlowDefinition;
   flow catalog via soql_query for FlowDefinitionView (see Query Tool Routing)
6. Describe objects/fields via sobject_describe before flow creation
```

**Scoring**: 110 points across 6 categories. Minimum 88 (80%) for deployment. Trivial flows (single-step automations, test/throwaway flows) are exempt from the minimum threshold — score them for informational purposes but do not block deployment. Guardrail anti-pattern checks (DML in loops, missing fault paths) still apply regardless of complexity.

---

## Execution modes

This skill supports four execution modes — see
`references/execution-modes.md` for detection logic and full details,
and `references/mcp-pagination.md` for handling large MCP responses.

All Flow operations go through MCP tools regardless of mode. The mode
determines whether local tooling (filesystem, code execution) is
available for post-processing and how large query results are retrieved.

---

## Core Responsibilities

1. **Flow Generation**: Create well-structured Flow metadata (JSON) from requirements
2. **Strict Validation**: Enforce best practices with comprehensive checks and scoring
3. **Cirra AI Integration**: Deploy via metadata_create, retrieve via metadata_read/metadata_list
4. **Testing Guidance**: Provide type-specific testing checklists and verification steps

---

## ⚠️ CRITICAL: Cirra AI MCP Server Setup

**BEFORE using any Cirra AI tools:**

```python
cirra_ai_init()
```

Call with no parameters — uses the default org. If a default is configured, confirm with the user before proceeding. If no default is configured, ask for the Salesforce user/alias.

This initializes your Salesforce org connection. It must be called once per session before using any of these Cirra AI tools:

- `metadata_create` (deploy flows)
- `metadata_read` (retrieve flows)
- `metadata_list` (list existing flows)
- `tooling_api_query` (query Flow / FlowDefinition — Tooling API objects only)
- `sobject_describe` (verify objects/fields)
- `soql_query` (query org data, plus FlowDefinitionView / FlowInterview — standard objects)

---

## ⚠️ CRITICAL: Orchestration Order

**sf-metadata → sf-flow → sf-data** (you are here: sf-flow with Cirra AI)

⚠️ Flow references custom object/fields? Create with sf-metadata FIRST. Deploy objects BEFORE flows.

```text
1. sf-metadata  → Create objects/fields (local)
2. sf-flow               ◀── YOU ARE HERE (create flow, deploy via Cirra AI)
3. sf-data               → Create test data (remote - objects must exist!)
```

See `references/orchestration.md` for extended orchestration patterns including Agentforce.

---

## 🔑 Key Insights

| Insight                  | Details                                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Before vs After Save** | Before-Save: same-record updates (no DML), validation. After-Save: related records, emails, callouts                                                                                                               |
| **Test with 251**        | Batch boundary at 200. Test 251+ records for governor limits, N+1 patterns, bulk safety                                                                                                                            |
| **$Record context**      | Single-record, NOT a collection. Platform handles batching. Never loop over $Record                                                                                                                                |
| **$Record traversal**    | `$Record` supports relationship traversal: `{!$Record.Contact__r.FirstName}`, `{!$Record.Account__r.Name}`. Do NOT use Get Records for data already available through `$Record` lookups — this wastes a SOQL query |
| **Transform vs Loop**    | Transform: data mapping/shaping (30-50% faster). Loop: per-record decisions, counters, varying logic. See `references/transform-vs-loop-guide.md`                                                                  |

---

## Fast Path (Simple Requests)

For simple, self-contained flows (single record update, basic field mapping, straightforward screen flow), bypass the detailed requirements/design elaboration and full scoring while still performing initialization and mandatory guardrails, then generate + deploy:

1. Call `cirra_ai_init()` (always required)
2. Use `sobject_describe` to verify the target object/fields exist
3. Generate the flow metadata as JSON
4. Run guardrail checks (anti-patterns only — skip full 110-point scoring)
5. Deploy via `metadata_create`
6. Verify deployment

**Use the fast path when**: the request is explicit, the flow is a single straightforward automation, and there are no ambiguous requirements.

**Use the full 5-phase workflow when**: the flow involves multiple decision branches, screen flows with complex logic, subflow orchestration, or underspecified requirements.

---

## Workflow Design (5-Phase Pattern)

See [Workflow Design](references/workflow-design.md) for the full 5-phase pattern, template selection, and generation checklist.

## Best Practices (Built-In Enforcement)

See [Best Practices Enforcement](references/best-practices-enforcement.md) for bulkification, fault handling, and scoring rules enforced by this skill.

## Common Error Patterns

See [Common Error Patterns](references/common-error-patterns.md).

## Critical Lessons Learned (Metadata API Flows)

See [Metadata API Lessons](references/metadata-api-lessons.md) before deploying Flow metadata via the API.

## Edge Cases

| Scenario     | Solution                                      |
| ------------ | --------------------------------------------- |
| >200 records | Warn limits, suggest scheduled flow           |
| >5 branches  | Use subflows                                  |
| Cross-object | Check circular deps, test recursion           |
| Production   | Deploy Draft, activate explicitly             |
| Unknown org  | Use standard objects (Account, Contact, etc.) |

**Debug**: Flow not visible → deploy report + permissions | Tests fail → Debug Logs + bulk test | Sandbox→Prod fails → FLS + dependencies

---

## Flow MCP Patterns

See [Flow MCP Patterns](references/flow-mcp-patterns.md) for create/update/read call shapes.

## Cirra AI Integration Examples

See [Integration Examples](references/integration-examples.md).

## Cross-Skill Integration

| From Skill     | To sf-flow | When                                 |
| -------------- | ---------- | ------------------------------------ |
| sf-apex        | → sf-flow  | "Create Flow wrapper for Apex logic" |
| sf-integration | → sf-flow  | "Create HTTP Callout Flow"           |

| From sf-flow | To Skill      | When                                                |
| ------------ | ------------- | --------------------------------------------------- |
| sf-flow      | → sf-metadata | "Describe Invoice\_\_c" (verify fields before flow) |
| sf-flow      | → sf-data     | "Create 200 test Accounts" (after deploy)           |

**Deployment**: See Phase 4 above.

---

## LWC Integration (Screen Flows)

See [LWC Screen Flow Integration](references/lwc-screen-flow-integration.md) and `references/lwc-integration-guide.md`.

## Apex Integration

See [Apex Integration](references/apex-integration.md).

## Notes

**Dependencies** (optional): sf-metadata, sf-data | **API**: 65.0 | **Mode**: Strict (warnings block) | **MCP Server**: Cirra AI (required)

**Required Setup**:

- Cirra AI account connected to Salesforce org
- `cirra_ai_init()` called once per session
- Valid Salesforce username for `sf_user` parameter
- **Audit Output**: All audit intermediate files go to `--output-dir` by default

**Validation hook**: A plugin-level `PreToolUse` hook (`pre-mcp-validate.py`) is shipped with this skill and, when registered, runs automatically against `metadata_create`, `metadata_update`, and `tooling_api_dml` on Flow/FlowDefinition. **The hook is not guaranteed to be registered in every host environment.** Until you have confirmed it is wired up for your runtime, you MUST run `python scripts/validate_flow_cli.py <path>` manually before every Flow deployment — see the four-question self-check in the Create workflow.
