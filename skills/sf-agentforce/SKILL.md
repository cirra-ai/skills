---
name: sf-agentforce
plugin: cirra-ai-sf
argument-hint: '[create|configure|validate|deploy] [agent|topic|action|prompt-template] <Name> ...'
metadata:
  version: 2.0.0
description: >
  Agentforce platform agent building via Setup UI and Cirra AI MCP Server.
  TRIGGER when: user maintains or configures agents via the Setup UI / Agent Builder path,
  creates topics/actions, writes PromptTemplates, touches .genAiFunction/.genAiPlugin/.promptTemplate
  metadata XML files, or works with Einstein Models API in Apex.
  DO NOT TRIGGER when: agent testing, persona design, or general Flow/Apex creation
  (use sf-flow / sf-apex).
---

# Salesforce Agentforce Platform Development

Expert Agentforce developer specializing in the **Setup UI / Agentforce Builder** approach to agent development. Covers topic and action configuration, GenAiFunction/GenAiPlugin metadata, PromptTemplate authoring, Einstein Models API, and custom Lightning types. Uses Cirra AI MCP Server for deployment.

> **Legacy Path**: This skill covers the Setup UI / Agent Builder approach (GenAiPlannerBundle metadata). For new agent development using the Agent Script DSL (AiAuthoringBundle), use a dedicated Agent Script skill.

## Dispatch

Parse `$ARGUMENTS` to determine which action workflow to run:

| First argument or intent                 | Workflow                     |
| ---------------------------------------- | ---------------------------- |
| `create`, new agent/topic/action request | Create Agent Components      |
| `configure`, modify existing agent       | Configure Agent              |
| `validate`, review, score                | Validate Agent Configuration |
| `deploy`, publish, activate              | Deploy & Publish Agent       |
| _(no argument or unclear)_               | Ask the user (see below)     |

When intent is unclear, present:

> What would you like to do?
>
> 1. **Create** — set up a new agent, topic, action, or prompt template
> 2. **Configure** — modify an existing agent's topics, actions, or settings
> 3. **Validate** — score an agent configuration (100-point system)
> 4. **Deploy** — deploy metadata and publish/activate the agent

---

## Prerequisites

Call `cirra_ai_init()` first if not already done this session.

---

## Environment Detection

Determine execution mode once, at the start of every session. Three modes are supported:

### Mode 1 — `sfdx-repo` (metadata on disk)

The working directory (or a user-specified path) is a Salesforce DX project with Agentforce metadata already retrieved.

**Detection:**

```bash
test -f sfdx-project.json && echo "SFDX project found"
```

If found, read `sfdx-project.json` to locate the source directory (usually `force-app/main/default`). Verify key subdirectories exist:

```bash
ls force-app/main/default/genAiFunctions/ \
   force-app/main/default/genAiPlugins/ \
   force-app/main/default/promptTemplates/ \
   force-app/main/default/bots/ 2>/dev/null
```

Ask the user to confirm: "I found an SFDX project at {path}. Should I use the local metadata? If the repo is out of date with the org, results may differ from a live query."

**In this mode:**

- Read `.genAiFunction-meta.xml`, `.genAiPlugin-meta.xml`, `.promptTemplate-meta.xml`, and `.bot-meta.xml` directly from disk
- No API calls for metadata retrieval — fastest mode
- Still use MCP for live-only data: agent status, active versions, org configuration
- For validation: parse XML on disk and score locally

### Mode 2 — `cli` (Salesforce CLI available)

The Salesforce CLI is installed and authenticated to the target org.

**Detection:**

```bash
command -v sf >/dev/null 2>&1 && sf --version
```

If the CLI is present, verify the target org is usable:

```bash
sf org display --target-org <alias-or-username> --json 2>/dev/null
```

Compare the target org from `sf org display` against the org selected during `cirra_ai_init()`. If the tool response exposes an OrgId, compare OrgIds; if it only exposes username/alias, compare that instead. If they differ, warn the user and fall back to `cloud`.

**In this mode:**

- Bulk retrieve via `sf project retrieve start -m GenAiFunction,GenAiPlugin,PromptTemplate`
- Agent lifecycle via `sf agent activate`, `sf agent deactivate`, `sf agent publish authoring-bundle`
- Queries via `sf data query` with `--json` output
- Deploy via `sf project deploy start --source-dir force-app`
- Use consistent `sf data query -q "..." --target-org <org> --json` patterns so the user only needs to grant CLI permission once

### Mode 3 — `cloud` (MCP only)

Fallback when neither an SFDX project nor an authenticated CLI is available.

**In this mode:**

- All metadata via `tooling_api_query`, `metadata_read`, `metadata_create`, `metadata_list`
- Use `metadata_list(type="GenAiFunction")` to inventory existing actions
- Use `metadata_read` for individual GenAiFunction/GenAiPlugin/PromptTemplate bodies
- Deploy via `metadata_create` / `metadata_update` (JSON objects, NOT XML)

### Mode summary

| Mode        | Metadata retrieval     | Agent lifecycle      | Deploy                | Speed   |
| ----------- | ---------------------- | -------------------- | --------------------- | ------- |
| `sfdx-repo` | Local filesystem       | MCP (live-only)      | `sf project deploy`   | Fastest |
| `cli`       | `sf` CLI bulk retrieve | `sf agent` commands  | `sf project deploy`   | Fast    |
| `cloud`     | MCP (one at a time)    | MCP (metadata tools) | MCP `metadata_create` | Slowest |

In all modes, use MCP tools (`soql_query`, `tooling_api_query`, `sobject_describe`) for targeted lookups when CLI is not available or not needed. The CLI is preferred only for bulk operations because it avoids per-record API calls.

### Handling large MCP responses

When a response exceeds ~75 KB, the MCP server returns a truncated preview plus retrieval metadata (`instructions.artifactId` + `instructions.artifactUrl`).

**Retrieval strategy per environment:**

- **IDE-based** (filesystem + Python available): Fetch URL, write JSON to disk
- **Conversational** (no filesystem): Fetch URL directly
- **Conversational** (no URL): Call `fetch_more(artifactId=...)`
- **Pagination**: `fetch_more(artifactId=..., cursor=_pagination.nextCursor)`

---

## Overview

Salesforce **Agentforce** enables organizations to build autonomous AI agents that handle customer interactions, automate tasks, and surface insights. This skill focuses on the **standard platform approach**:

- **Agentforce Builder** (Setup UI) for visual agent configuration
- **GenAiFunction** and **GenAiPlugin** metadata for registering actions
- **PromptTemplate** metadata for reusable AI prompts
- **Einstein Models API** (`aiplatform.ModelsAPI`) for native LLM access in Apex
- **Custom Lightning Types** (`LightningTypeBundle`) for rich agent action UIs

---

## Core Concepts

### Topics

Topics are the primary organizational unit for an agent's capabilities. Each topic groups related **actions** and **instructions** around a specific domain.

- **Description**: Tells the LLM planner when to route to this topic (must be specific and unambiguous)
- **Scope**: Defines what the topic can and cannot do (helps the planner make routing decisions)
- **Instructions**: Step-by-step guidance the agent follows when a topic is active
- **Actions**: The operations (Flow, Apex, Prompt Template) the agent can invoke within this topic

In the Agentforce Builder, topics are configured via **Setup > Agentforce > Agents > [Agent] > Topics**.

### Actions

Actions are the executable operations an agent can perform. Each action wraps an underlying invocation target:

| Target Type         | Description                                  | Registered Via                                    |
| ------------------- | -------------------------------------------- | ------------------------------------------------- |
| **Flow**            | Invokes an Autolaunched Flow                 | GenAiFunction with `invocationTargetType: flow`   |
| **Apex**            | Invokes an `@InvocableMethod`                | GenAiFunction with `invocationTargetType: apex`   |
| **Prompt Template** | Invokes a PromptTemplate                     | GenAiFunction with `invocationTargetType: prompt` |
| **Standard Action** | Built-in platform actions (send email, etc.) | Pre-registered by Salesforce                      |

### Instructions

Instructions guide the agent's behavior within a topic. They are natural language directives that tell the LLM:

- What steps to follow
- When to invoke specific actions
- How to handle edge cases and errors
- When to escalate to a human agent

---

## Agent Builder Workflow

### Step-by-Step: Creating an Agent via Setup UI

**1. Navigate to Agentforce Builder**

```
Setup > Agentforce > Agents > New Agent
```

**2. Choose Agent Type**

- **Service Agent** — Customer-facing support and service
- **Employee Agent** — Internal productivity and automation

**3. Add Topics**

For each capability area:

- Provide a clear **Name** and **Description**
- Write **Instructions** that guide the agent's reasoning
- Add a **Scope** statement (what's in/out of bounds)

**4. Configure Actions per Topic**

Assign actions to each topic. Actions can target:

- Autolaunched Flows (most common)
- Apex InvocableMethods (via GenAiFunction)
- Prompt Templates (for LLM-generated content)
- Standard platform actions

**5. Set Action Inputs & Outputs**

For each action:

- Define **inputs** the agent collects from the user (slot filling)
- Define **outputs** the agent uses in its response
- Mark which outputs are **displayable** to the user

**6. Configure Agent-Level Settings**

- **System Instructions**: Global persona and behavior guidelines
- **Default Agent User**: The running user context for the agent
- **Welcome Message**: Initial greeting
- **Error Message**: Fallback when something goes wrong

**7. Preview & Test**

```bash
# sfdx-repo / cli mode
sf agent preview --api-name MyAgent --target-org MyOrg

# cloud mode — use MCP tools to query agent status
tooling_api_query(query="SELECT Id, DeveloperName, Status FROM BotDefinition")
```

**8. Publish & Activate**

```bash
# cli mode
sf agent publish authoring-bundle --api-name MyAgent --target-org MyOrg --json
sf agent activate --api-name MyAgent --target-org MyOrg

# cloud mode — use metadata_update
metadata_update(type="BotDefinition", metadata=[...])
```

> **Publishing does NOT activate.** After `sf agent publish`, the new BotVersion is Inactive. You MUST run `sf agent activate` separately.

Full lifecycle: Validate > Deploy > Publish > Activate > (Deactivate > Re-publish > Re-activate)

---

## GenAiFunction & GenAiPlugin Metadata

### GenAiFunction

A `GenAiFunction` registers a single action that an Agentforce agent can invoke. It wraps an underlying Flow, Apex method, or Prompt Template.

**Metadata XML Structure:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Look Up Order Status</masterLabel>
    <developerName>Lookup_Order_Status</developerName>
    <description>Retrieves the current status of a customer order</description>

    <!-- Target: the Flow, Apex, or Prompt to invoke -->
    <invocationTarget>Get_Order_Status_Flow</invocationTarget>
    <invocationTargetType>flow</invocationTargetType>

    <!-- Capability: tells the LLM planner WHEN to use this action -->
    <capability>
        Look up the current status of a customer's order when they
        ask about shipping, delivery, or order tracking.
    </capability>

    <!-- Inputs: what the agent collects from the user -->
    <genAiFunctionInputs>
        <developerName>orderNumber</developerName>
        <description>The customer's order number</description>
        <dataType>Text</dataType>
        <isRequired>true</isRequired>
    </genAiFunctionInputs>

    <!-- Outputs: what the action returns -->
    <genAiFunctionOutputs>
        <developerName>orderStatus</developerName>
        <description>Current status of the order</description>
        <dataType>Text</dataType>
        <isRequired>true</isRequired>
    </genAiFunctionOutputs>
</GenAiFunction>
```

**File Location:**

```
force-app/main/default/genAiFunctions/Lookup_Order_Status.genAiFunction-meta.xml
```

### Invocation Target Types

| `invocationTargetType` | Target Value        | Notes                              |
| ---------------------- | ------------------- | ---------------------------------- |
| `flow`                 | Flow API name       | Flow must be Active                |
| `apex`                 | Apex class name     | Class must have `@InvocableMethod` |
| `prompt`               | PromptTemplate name | Template must be Active            |

### GenAiPlugin

A `GenAiPlugin` groups multiple `GenAiFunction` entries into a logical unit. This is useful for organizing related actions.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPlugin xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Order Management Plugin</masterLabel>
    <developerName>Order_Management_Plugin</developerName>
    <description>Actions for managing customer orders</description>

    <genAiFunctions>
        <functionName>Lookup_Order_Status</functionName>
    </genAiFunctions>
    <genAiFunctions>
        <functionName>Cancel_Order</functionName>
    </genAiFunctions>
    <genAiFunctions>
        <functionName>Return_Order</functionName>
    </genAiFunctions>
</GenAiPlugin>
```

**File Location:**

```
force-app/main/default/genAiPlugins/Order_Management_Plugin.genAiPlugin-meta.xml
```

### Deployment: Two-Command Pattern

The production deployment pattern uses two commands — one for supporting metadata, one for the agent itself:

```bash
# Step 1: Deploy ALL supporting metadata at once
sf project deploy start --source-dir force-app -o ORG --json

# Step 2: Publish the agent (validates + publishes + retrieves + deploys agent metadata)
sf agent publish authoring-bundle --api-name Agent_Name -o ORG --json
```

| Command                                          | Deploys                                                    | Does NOT Deploy                     |
| ------------------------------------------------ | ---------------------------------------------------------- | ----------------------------------- |
| `sf project deploy start --source-dir force-app` | Flows, Apex, Objects, GenAiFunction, GenAiPlugin           | Agent action references, BotVersion |
| `sf agent publish authoring-bundle --api-name X` | Validates + Publishes + Retrieves + Deploys agent metadata | Supporting metadata (Flows, Apex)   |

> **WARNING**: `sf project deploy start` deploys supporting metadata but does **NOT** update agent action references or BotVersion. You must use `sf agent publish` to update the agent itself.

> **Bundle Metadata Warning**: The `bundle-meta.xml` file must contain ONLY `<bundleType>AGENT</bundleType>`. Adding extra fields (description, label, etc.) causes "Required fields missing" deployment errors.

---

## PromptTemplate Configuration

`PromptTemplate` is the metadata type for creating reusable AI prompts. Templates can be invoked by Agentforce agents (via GenAiFunction), Einstein Prompt Builder, Apex code, and Flows.

**Template Types:** `flexPrompt` | `salesGeneration` | `fieldCompletion` | `recordSummary`

**Variable Types:** `freeText` (runtime input) | `recordField` (SObject field binding) | `relatedList` (child records) | `resource` (Static Resource)

**Key Integration Points:**

- **Agent Action**: Register a GenAiFunction with `invocationTargetType: prompt`
- **Apex**: `ConnectApi.EinsteinLlm.generateMessagesForPromptTemplate()`
- **Flow**: Use the "Prompt Template" action element

> **Full reference**: See [references/prompt-templates.md](references/prompt-templates.md) for complete metadata structure, variable types, examples, Data Cloud grounding, and best practices.

---

## Models API

The **Einstein Models API** (`aiplatform.ModelsAPI`) enables native LLM access from Apex without external HTTP callouts. Use it for custom AI logic beyond what Agentforce topics/actions provide.

**Available Models:**

- `sfdc_ai__DefaultOpenAIGPT4OmniMini` — Cost-effective general tasks
- `sfdc_ai__DefaultOpenAIGPT4Omni` — Complex reasoning
- `sfdc_ai__DefaultAnthropic` — Nuanced understanding
- `sfdc_ai__DefaultGoogleGemini` — Multimodal tasks

**Key Patterns:**

- **Queueable** for single-record async AI processing
- **Batch** for bulk processing (scope size 10-20)
- **Platform Events** for notifying completion to LWC/Flow

**Prerequisites:** Einstein Generative AI enabled, API v61.0+, Einstein Generative AI User permission set assigned.

> **Full reference**: See [references/models-api.md](references/models-api.md) for complete Apex examples, Queueable/Batch patterns, Chatter integration, and governor limit guidance.

---

## Custom Lightning Types

**Custom Lightning Types** (`LightningTypeBundle`) define structured data types with custom UI components for agent action inputs and outputs. When an agent action needs a rich input form or a formatted output display, create a custom type with:

- **schema.json** — JSON Schema data structure definition
- **editor.json** — Custom input collection UI (lightning components)
- **renderer.json** — Custom output display UI (lightning components)

**Requirements:** API v64.0+ (Fall '25), Enhanced Chat V2 enabled in Service Cloud.

**File Structure:**

```
force-app/main/default/lightningTypeBundles/OrderDetails/
├── schema.json
├── editor.json
├── renderer.json
└── OrderDetails.lightningTypeBundle-meta.xml
```

> **Full reference**: See [references/custom-lightning-types.md](references/custom-lightning-types.md) for complete schema examples, editor/renderer configuration, and integration with GenAiFunction.

---

## Orchestration Order

**Prerequisite skills must run in this order:**

```
sf-metadata → sf-apex → sf-flow → sf-agentforce → deploy
```

**Why this order:**

1. **sf-metadata** — Custom objects/fields must exist before Apex/Flows reference them
2. **sf-apex** — InvocableMethod classes must be deployed before Flows or GenAiFunctions reference them
3. **sf-flow** — Flows must be active before GenAiFunctions can target them
4. **sf-agentforce** (this skill) — GenAiFunction/GenAiPlugin metadata and agent configuration
5. **Deploy** — Final deployment and agent publishing

**MANDATORY Delegations:**

| Requirement   | Delegate To               | Why                                           |
| ------------- | ------------------------- | --------------------------------------------- |
| Flow creation | Use the **sf-flow** skill | 110-point validation, proper XML              |
| Apex creation | Use the **sf-apex** skill | InvocableMethod generation, 150-point scoring |

---

## Cross-Skill Integration

| Skill              | Purpose                    | When to Use                                         |
| ------------------ | -------------------------- | --------------------------------------------------- |
| **sf-flow**        | Flow actions               | Creating Autolaunched Flows for agent actions       |
| **sf-apex**        | Apex actions               | Writing InvocableMethod classes for agent actions   |
| **sf-metadata**    | Object/field setup         | Creating SObjects and fields that actions reference |
| **sf-lwc**         | Custom UI                  | Creating screen components for agent UIs            |
| **sf-permissions** | Permission management      | Permission sets for agent users                     |
| **sf-data**        | Data operations            | Query or update data for agent testing              |
| **sf-diagram**     | Architecture visualization | Visualize agent topology and permission hierarchies |

### Integration Patterns

| Direction            | Pattern                                  | Notes                      |
| -------------------- | ---------------------------------------- | -------------------------- |
| Agent → Flow         | GenAiFunction targets Flow               | Most common action pattern |
| Agent → Apex         | GenAiFunction targets InvocableMethod    | For complex business logic |
| Agent → Prompt       | GenAiFunction targets PromptTemplate     | For AI-generated content   |
| Agent → Custom Type  | GenAiFunction uses LightningTypeBundle   | Rich input/output UIs      |
| Agent → External API | Flow/Apex wraps Named Credential callout | Via integration patterns   |

---

## Key Insights

| Insight                                   | Issue                                                           | Fix                                                    |
| ----------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------ |
| **GenAiFunction requires active target**  | Deploying GenAiFunction before its Flow/Apex target             | Deploy targets first, then GenAiFunction               |
| **PromptTemplate field bindings**         | `{!variableName}` must match variable `developerName` exactly   | Check spelling and case sensitivity                    |
| **Custom Lightning Types require v64.0+** | Bundle won't deploy on older API versions                       | Set `<version>64.0</version>` or higher in package.xml |
| **GenAiPlugin groups functions**          | Individual GenAiFunctions must exist before the plugin          | Deploy GenAiFunctions before GenAiPlugin               |
| **Capability text is critical**           | Vague capability descriptions cause poor routing                | Write specific, scenario-based capability text         |
| **Enhanced Chat V2 for custom types**     | Custom type UI won't render without it                          | Enable Enhanced Chat V2 in Setup > Chat Settings       |
| **Models API needs async context**        | Synchronous calls in triggers will timeout                      | Use Queueable with `Database.AllowsCallouts`           |
| **Input/output names must match**         | GenAiFunction input names must match Flow variable API names    | Verify exact name match (case-sensitive)               |
| **Validation before publish**             | Skipping validation causes late-stage failures                  | Always run `sf agent validate authoring-bundle` first  |
| **Data type mapping**                     | GenAiFunction `dataType` must align with target parameter types | Use `Text`, `Number`, `Boolean`, `Date` as appropriate |

> **GenAiPluginDefinition Name Collision**: If a topic and its parent agent share the same API name, the generated GenAiPluginDefinition metadata collides, causing publish failures. Ensure unique API names across all agent components.

---

## Scoring System (100 Points)

### Categories

| Category                  | Points | Key Criteria                                                                   |
| ------------------------- | ------ | ------------------------------------------------------------------------------ |
| **Agent Configuration**   | 20     | System instructions, welcome/error messages, agent user set                    |
| **Topic & Action Design** | 25     | Clear descriptions, proper scope, logical routing, capability text             |
| **Metadata Quality**      | 20     | Valid GenAiFunction/GenAiPlugin XML, correct target types, I/O defs            |
| **Integration Patterns**  | 15     | Proper orchestration order, dependency management, cross-skill delegation      |
| **PromptTemplate Usage**  | 10     | Variable bindings correct, template types appropriate, prompts well-structured |
| **Deployment Readiness**  | 10     | Validation passes, dependencies deployed first, package.xml correct            |

### Thresholds

| Score  | Rating     | Action                       |
| ------ | ---------- | ---------------------------- |
| 90-100 | Excellent  | Deploy with confidence       |
| 80-89  | Very Good  | Minor improvements suggested |
| 70-79  | Good       | Review before deploy         |
| 60-69  | Needs Work | Address issues before deploy |
| < 60   | Critical   | **Block deployment**         |

### Validation Report Format

```
Score: 87/100 Very Good
├─ Agent Configuration:     18/20 (90%)
├─ Topic & Action Design:   22/25 (88%)
├─ Metadata Quality:        17/20 (85%)
├─ Integration Patterns:    13/15 (87%)
├─ PromptTemplate Usage:     9/10 (90%)
└─ Deployment Readiness:     8/10 (80%)

Issues:
[Metadata] GenAiFunction "Cancel_Order" missing output definition
[Integration] Flow "Get_Order_Status" not yet deployed to org
All PromptTemplate variable bindings valid
GenAiPlugin references resolve correctly
```

---

## CLI Agent Lifecycle

Manage agent state via CLI (`cli` mode only — requires agent to be published first):

| Command                                                | Purpose                     |
| ------------------------------------------------------ | --------------------------- |
| `sf agent activate --api-name X --target-org Y`        | Activate a published agent  |
| `sf agent deactivate --api-name X --target-org Y`      | Deactivate an active agent  |
| `sf agent publish authoring-bundle --api-name X -o Y`  | Publish agent bundle        |
| `sf agent validate authoring-bundle --api-name X -o Y` | Validate before publish     |
| `sf agent preview --api-name X -o Y`                   | Preview agent interactively |

> **Note**: `activate` and `deactivate` do NOT support `--json` flag.

> Full CLI reference: See [references/cli-commands.md](references/cli-commands.md)

---

## Document Map

**Tier 2: Detailed References**

| Document                                                 | Description                                                       | Read When                 |
| -------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------- |
| [references/cli-commands.md](references/cli-commands.md) | CLI command reference for agent lifecycle, generation, publishing | Using `sf agent` commands |

**Tier 3: Deep-Dive References**

| Document                                                                     | Description                                                            | Read When                             |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------- |
| [references/prompt-templates.md](references/prompt-templates.md)             | Complete PromptTemplate metadata, variable types, Data Cloud grounding | Authoring reusable AI prompts         |
| [references/models-api.md](references/models-api.md)                         | `aiplatform.ModelsAPI` Apex patterns, Queueable/Batch integration      | Building custom AI logic in Apex      |
| [references/custom-lightning-types.md](references/custom-lightning-types.md) | LightningTypeBundle schema/editor/renderer configuration               | Creating rich action input/output UIs |

**Cross-Skill References**

| Need                            | Skill          |
| ------------------------------- | -------------- |
| Flow creation for actions       | sf-flow        |
| Apex InvocableMethod classes    | sf-apex        |
| Custom objects/fields           | sf-metadata    |
| LWC for custom UIs              | sf-lwc         |
| Permission sets for agent users | sf-permissions |

---

## Version History

| Version   | Date       | Changes                                                                                                                                                                     |
| --------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1.0.0** | 2026-03-12 | Initial migration from sf-ai-agentforce. Added 3 execution modes (sfdx-repo, cli, cloud), Cirra AI MCP Server integration, cross-skill references to cirra-ai-sf-\* skills. |
| **2.0.0** | 2026-03-26 | Renamed from cirra-ai-sf-agentforce to sf-agentforce. Added dispatch menu, argument-hint, plugin frontmatter key. Updated all cross-references to sf-\* naming convention.  |

---

## Sources & Acknowledgments

| Source                                                                                               | Contribution                                                   |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [Salesforce Agentforce Documentation](https://developer.salesforce.com/docs/einstein/genai/overview) | Official platform reference                                    |
| [Salesforce Diaries](https://salesforcediaries.com)                                                  | Models API patterns, Custom Lightning Types guide              |
| [trailheadapps/agent-script-recipes](https://github.com/trailheadapps/agent-script-recipes)          | Official Salesforce examples                                   |
| Jag Valaiyapathy                                                                                     | Original skill authoring, scoring system, orchestration design |

---

## License

MIT License. See [LICENSE](LICENSE) file.
Copyright (c) 2024-2025 Jag Valaiyapathy
Copyright (c) 2026 Cirra AI (modifications)
