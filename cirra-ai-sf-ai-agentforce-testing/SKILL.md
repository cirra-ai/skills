---
name: sf-ai-agentforce-testing
description: >
  Comprehensive Agentforce testing skill with dual-track workflow: multi-turn API testing
  (primary) and CLI Testing Center (secondary). Execute multi-turn conversations via Agent
  Runtime API, run single-utterance tests via Cirra AI MCP, analyze topic/action/context coverage,
  and automatically fix failing agents with 100-point scoring across 7 categories. Uses Cirra AI
  MCP Server instead of Salesforce CLI for org access.
license: MIT
compatibility: "Requires API v65.0+ (Winter '26), Agentforce enabled org, and Cirra AI MCP Server connection"
metadata:
  version: '2.0.0-cirra'
  author: 'Jag Valaiyapathy'
  scoring: '100 points across 7 categories'
  mcp_server: 'cirra_ai'
---

<!-- TIER: 1 | ENTRY POINT -->
<!-- This is the starting document - read this FIRST -->
<!-- Pattern: Follows sf-testing for agentic test-fix loops -->
<!-- v2.0.0-cirra: Dual-track workflow with Cirra AI MCP Server integration -->

# sf-ai-agentforce-testing: Agentforce Test Execution & Coverage Analysis (Cirra AI MCP)

Expert testing engineer specializing in Agentforce agent testing via **dual-track workflow**: multi-turn Agent Runtime API testing (primary) and CLI Testing Center (secondary). Uses **Cirra AI MCP Server** for org access, metadata queries, and test management. Execute multi-turn conversations, analyze topic/action/context coverage, and automatically fix issues via sf-ai-agentscript (or sf-ai-agentforce-legacy for existing agents).

## Core Responsibilities

1. **Multi-Turn API Testing** (PRIMARY): Execute multi-turn conversations via Agent Runtime API
2. **CLI Test Execution** (SECONDARY): Run single-utterance tests via Cirra AI `tooling_api_dml` on AiEvaluationDefinition
3. **Test Spec / Scenario Generation**: Create YAML test specifications and multi-turn scenarios
4. **Coverage Analysis**: Track topic, action, context preservation, and re-matching coverage
5. **Preview Testing**: Interactive simulated and live agent testing
6. **Agentic Fix Loop**: Automatically fix failing agents and re-test
7. **Cross-Skill Orchestration**: Delegate fixes to sf-ai-agentscript, data to sf-data
8. **Observability Integration**: Guide to sf-ai-agentforce-observability for STDM analysis

## 📚 Document Map

| Need                      | Document                                                             | Description                                       |
| ------------------------- | -------------------------------------------------------------------- | ------------------------------------------------- |
| **Agent Runtime API**     | [agent-api-reference.md](docs/agent-api-reference.md)                | REST endpoints for multi-turn testing             |
| **ECA Setup**             | [eca-setup-guide.md](docs/eca-setup-guide.md)                        | External Client App for API authentication        |
| **Multi-Turn Testing**    | [multi-turn-testing-guide.md](docs/multi-turn-testing-guide.md)      | Multi-turn test design and execution              |
| **Test Patterns**         | [multi-turn-test-patterns.md](resources/multi-turn-test-patterns.md) | 6 multi-turn test patterns with examples          |
| **Cirra AI Tool Mapping** | [cirra-ai-integration.md](docs/cirra-ai-integration.md)              | Complete MCP Server tool reference                |
| **Test spec format**      | [test-spec-reference.md](resources/test-spec-reference.md)           | YAML specification format and examples            |
| **Auto-fix workflow**     | [agentic-fix-loops.md](resources/agentic-fix-loops.md)               | Automated test-fix cycles (10 failure categories) |
| **Live preview setup**    | [connected-app-setup.md](docs/connected-app-setup.md)                | OAuth for live preview mode                       |
| **Coverage metrics**      | [coverage-analysis.md](docs/coverage-analysis.md)                    | Topic/action/multi-turn coverage analysis         |
| **Fix decision tree**     | [agentic-fix-loop.md](docs/agentic-fix-loop.md)                      | Detailed fix strategies                           |

**⚡ Quick Links:**

- [Scoring System](#scoring-system-100-points) - 7-category validation
- [Phase A: Multi-Turn API Testing](#phase-a-multi-turn-api-testing-primary) - Primary workflow
- [Phase B: CLI Testing Center](#phase-b-cli-testing-center-secondary) - Secondary workflow (Cirra AI)
- [Agentic Fix Loop](#phase-c-agentic-fix-loop) - Auto-fix workflow
- [Multi-Turn Templates](#multi-turn-test-templates) - Pre-built test scenarios
- [Cirra AI Integration](#cirra-ai-mcp-integration) - MCP Server setup and tool mapping

---

## ⚠️ CRITICAL: Orchestration Order

**sf-metadata → sf-apex → sf-flow → sf-deploy → sf-ai-agentscript → sf-deploy → sf-ai-agentforce-testing** (you are here)

**Why testing is LAST:**

1. Agent must be **published** before running automated tests
2. Agent must be **activated** for preview mode and API access
3. All dependencies (Flows, Apex) must be deployed first
4. Test data (via sf-data) should exist before testing actions

**⚠️ MANDATORY Delegation:**

- **Fixes**: ALWAYS use `Skill(skill="sf-ai-agentscript")` for agent script fixes (or `sf-ai-agentforce-legacy` for existing legacy agents)
- **Test Data**: Use `Skill(skill="sf-data")` for action test data
- **OAuth Setup**: Use `Skill(skill="sf-connected-apps")` for ECA or Connected App
- **Observability**: Use `Skill(skill="sf-ai-agentforce-observability")` for STDM analysis of test sessions

---

## Architecture: Dual-Track Testing Workflow

```
Phase 0: Prerequisites & Agent Discovery (Cirra AI tooling_api_query)
    │
    ├──► Phase A: Multi-Turn API Testing (PRIMARY)
    │    A1: ECA Credential Setup
    │    A2: Agent Discovery & Metadata Retrieval (Cirra AI)
    │    A3: Test Scenario Planning (interview user)
    │    A4: Multi-Turn Execution (Agent Runtime API)
    │    A5: Results & Scoring
    │
    └──► Phase B: CLI Testing Center (SECONDARY, Cirra AI)
         B1: Test Spec Creation (Python script or manual)
         B2: Test Execution (tooling_api_dml on AiEvaluationDefinition)
         B3: Results Analysis (tooling_api_query)
    │
Phase C: Agentic Fix Loop (shared)
Phase D: Coverage Improvement (shared)
Phase E: Observability Integration (STDM analysis)
```

**When to use which track:**

| Condition                                                  | Use                                            |
| ---------------------------------------------------------- | ---------------------------------------------- |
| Agent Testing Center NOT available                         | Phase A only                                   |
| Need multi-turn conversation testing                       | Phase A                                        |
| Need topic re-matching validation                          | Phase A                                        |
| Need context preservation testing                          | Phase A                                        |
| Agent Testing Center IS available + single-utterance tests | Phase B                                        |
| CI/CD pipeline integration                                 | Phase A (Python scripts) or Phase B (Cirra AI) |
| Quick smoke test                                           | Phase B                                        |

---

## Cirra AI MCP Integration

### CRITICAL: Initialize Cirra AI Connection

**BEFORE using ANY Cirra AI tools, call:**

```
cirra_ai_init(sf_user="username@company.com", cirra_ai_team="your-team-name")
```

This establishes connection to Salesforce org via Cirra AI MCP Server. All subsequent tool calls use the initialized connection.

### Tool Mapping Reference

| CLI Command                                               | Cirra AI Tool                                     | Use Case                           |
| --------------------------------------------------------- | ------------------------------------------------- | ---------------------------------- |
| `sf data query --use-tooling-api`                         | `tooling_api_query`                               | Find agents, tests, query metadata |
| `sf agent test list`                                      | `tooling_api_query(AiEvaluationDefinition)`       | List test definitions              |
| `sf agent test create`                                    | `tooling_api_dml(create, AiEvaluationDefinition)` | Create test in org                 |
| `sf agent test run`                                       | `tooling_api_dml(create, AiEvaluationRun)`        | Execute test run                   |
| `sf agent test results`                                   | `tooling_api_query(AiEvaluationRun)`              | Fetch test results                 |
| `sf project retrieve start --metadata GenAiPlannerBundle` | `metadata_read(GenAiPlannerBundle)`               | Get agent config                   |
| `sf agent list`                                           | `tooling_api_query(BotDefinition)`                | Find all agents                    |
| `sf agent preview`                                        | Not available via MCP                             | Manual UI operation                |

See [cirra-ai-integration.md](docs/cirra-ai-integration.md) for complete tool reference and examples.

---

## Phase 0: Prerequisites & Agent Discovery

### Step 1: Initialize Cirra AI

```
cirra_ai_init(sf_user="your.email@company.com")
```

Connection is now established. All Cirra AI tools will use this connection.

### Step 2: Gather User Information

Use **AskUserQuestion** to gather:

```
AskUserQuestion:
  questions:
    - question: "Which agent do you want to test?"
      header: "Agent"
      options:
        - label: "Let me discover agents in the org"
          description: "Query BotDefinition to find available agents"
        - label: "I know the agent name"
          description: "Provide agent name/API name directly"

    - question: "What is your target org alias?"
      header: "Org"
      options:
        - label: "vivint-DevInt"
          description: "Development integration org"
        - label: "Other"
          description: "Specify a different org alias"

    - question: "What type of testing do you need?"
      header: "Test Type"
      options:
        - label: "Multi-turn API testing (Recommended)"
          description: "Full conversation testing via Agent Runtime API — tests topic switching, context retention, escalation cascades"
        - label: "CLI single-utterance testing"
          description: "Traditional CLI tests via Testing Center — requires Agent Testing Center feature"
        - label: "Both"
          description: "Run both multi-turn and CLI tests for comprehensive coverage"
```

### Step 3: Agent Discovery

**Using Cirra AI MCP:**

```
tooling_api_query(
  sObject="BotDefinition",
  whereClause="IsActive=true",
  fields=["Id", "DeveloperName", "MasterLabel"],
  limit=50
)
```

Returns list of active agents with IDs and names.

### Step 4: Agent Metadata Retrieval

**Using Cirra AI MCP:**

```
metadata_read(
  type="GenAiPlannerBundle",
  fullNames=["AgentDeveloperName"]
)
```

Claude reads the GenAiPlannerBundle to understand:

- All topics and their `classificationDescription` values
- All actions and their configurations
- System instructions and guardrails
- Escalation paths

### Step 5: Check Agent Testing Center Availability

**Using Cirra AI MCP:**

```
tooling_api_query(
  sObject="AiEvaluationDefinition",
  limit=1
)
```

If success: → Both Phase A and Phase B available
If error: → Agent Testing Center NOT enabled → Phase A only

### Step 6: Prerequisites Checklist

| Check                              | Cirra AI Tool                                                       | Why                            |
| ---------------------------------- | ------------------------------------------------------------------- | ------------------------------ |
| **Agent exists**                   | `tooling_api_query(BotDefinition, whereClause="DeveloperName='X'")` | Can't test non-existent agent  |
| **Agent published**                | Check via `metadata_read(GenAiPlannerBundle)`                       | Must be published to test      |
| **Agent activated**                | Check activation status                                             | Required for API access        |
| **Dependencies deployed**          | Query metadata for Flows, Apex                                      | Actions will fail without them |
| **ECA configured** (Phase A)       | Token request test                                                  | Required for Agent Runtime API |
| **Agent Testing Center** (Phase B) | `tooling_api_query(AiEvaluationDefinition)`                         | Required for CLI testing       |

---

## Phase A: Multi-Turn API Testing (PRIMARY)

### A1: ECA Credential Setup

```
AskUserQuestion:
  question: "Do you have an External Client App (ECA) with Client Credentials flow configured?"
  header: "ECA Setup"
  options:
    - label: "Yes, I have credentials"
      description: "I have Consumer Key, Secret, and My Domain URL ready"
    - label: "No, I need to create one"
      description: "Delegate to sf-connected-apps skill to create ECA"
```

**If YES:** Collect credentials (kept in conversation context only, NEVER written to files):

- Consumer Key
- Consumer Secret
- My Domain URL (e.g., `your-domain.my.salesforce.com`)

**If NO:** Delegate to sf-connected-apps:

```
Skill(skill="sf-connected-apps", args="Create External Client App with Client Credentials flow for Agent Runtime API testing. Scopes: api, chatbot_api, sfap_api, refresh_token, offline_access. Name: Agent_API_Testing")
```

**Verify credentials work:**

```bash
# Test token request (credentials passed inline, never stored in files)
curl -s -X POST "https://${SF_MY_DOMAIN}/services/oauth2/token" \
  -d "grant_type=client_credentials&client_id=${CONSUMER_KEY}&client_secret=${CONSUMER_SECRET}" \
  | jq '.access_token | length'
```

See [ECA Setup Guide](docs/eca-setup-guide.md) for complete instructions.

### A2: Agent Discovery & Metadata Retrieval

**Get agent ID for API calls (Cirra AI):**

```
tooling_api_query(
  sObject="BotDefinition",
  whereClause="DeveloperName='[AgentName]' AND IsActive=true",
  fields=["Id", "DeveloperName", "MasterLabel"],
  limit=1
)
```

**Retrieve full agent configuration (Cirra AI):**

```
metadata_read(
  type="GenAiPlannerBundle",
  fullNames=["AgentName"]
)
```

Claude reads the GenAiPlannerBundle to understand:

- **Topics**: Names, classificationDescriptions, instructions
- **Actions**: Types (flow, apex), triggers, inputs/outputs
- **System Instructions**: Global rules and guardrails
- **Escalation Paths**: When and how the agent escalates

This metadata drives automatic test scenario generation in A3.

### A3: Test Scenario Planning

```
AskUserQuestion:
  question: "What testing do you need?"
  header: "Scenarios"
  options:
    - label: "Comprehensive coverage (Recommended)"
      description: "All 6 test patterns: topic routing, context preservation, escalation, guardrails, action chaining, variable injection"
    - label: "Topic routing accuracy"
      description: "Test that utterances route to correct topics, including mid-conversation topic switches"
    - label: "Context preservation"
      description: "Test that the agent retains information across turns"
    - label: "Specific bug reproduction"
      description: "Reproduce a known issue with targeted multi-turn scenario"
  multiSelect: true
```

Claude uses the agent metadata from A2 to **auto-generate multi-turn scenarios** tailored to the specific agent:

- Generates topic switching scenarios based on actual topic names
- Creates context preservation tests using actual action inputs/outputs
- Builds escalation tests based on actual escalation configuration
- Creates guardrail tests based on system instructions

**Available templates** (see [templates/](#multi-turn-test-templates)):

| Template                               | Pattern             | Scenarios |
| -------------------------------------- | ------------------- | --------- |
| `multi-turn-topic-routing.yaml`        | Topic switching     | 4         |
| `multi-turn-context-preservation.yaml` | Context retention   | 4         |
| `multi-turn-escalation-flows.yaml`     | Escalation cascades | 4         |
| `multi-turn-comprehensive.yaml`        | All 6 patterns      | 6         |

### A4: Multi-Turn Execution

Execute conversations via Agent Runtime API using the **reusable Python scripts** in `hooks/scripts/`.

> ⚠️ **Agent API is NOT supported for agents of type "Agentforce (Default)".** Only custom agents created via Agentforce Builder are supported.

**Option 1: Run Test Scenarios from YAML Templates (Recommended)**

Use the multi-turn test runner to execute entire scenario suites:

```bash
# Run comprehensive test suite against an agent
python3 hooks/scripts/multi_turn_test_runner.py \
  --my-domain "${SF_MY_DOMAIN}" \
  --consumer-key "${CONSUMER_KEY}" \
  --consumer-secret "${CONSUMER_SECRET}" \
  --agent-id "${AGENT_ID}" \
  --scenarios templates/multi-turn-comprehensive.yaml \
  --verbose

# Run specific scenario within a suite
python3 hooks/scripts/multi_turn_test_runner.py \
  --my-domain "${SF_MY_DOMAIN}" \
  --consumer-key "${CONSUMER_KEY}" \
  --consumer-secret "${CONSUMER_SECRET}" \
  --agent-id "${AGENT_ID}" \
  --scenarios templates/multi-turn-topic-routing.yaml \
  --scenario-filter topic_switch_natural \
  --verbose

# With context variables and JSON output for fix loop
python3 hooks/scripts/multi_turn_test_runner.py \
  --my-domain "${SF_MY_DOMAIN}" \
  --consumer-key "${CONSUMER_KEY}" \
  --consumer-secret "${CONSUMER_SECRET}" \
  --agent-id "${AGENT_ID}" \
  --scenarios templates/multi-turn-comprehensive.yaml \
  --var '$Context.AccountId=001XXXXXXXXXXXX' \
  --var '$Context.EndUserLanguage=en_US' \
  --output results.json \
  --verbose
```

**Exit codes:** `0` = all passed, `1` = some failed (fix loop should process), `2` = execution error

**Option 2: Use Environment Variables (cleaner for repeated runs)**

```bash
export SF_MY_DOMAIN="your-domain.my.salesforce.com"
export SF_CONSUMER_KEY="your_key"
export SF_CONSUMER_SECRET="your_secret"
export SF_AGENT_ID="0XxRM0000004ABC"

# Now run without credential flags
python3 hooks/scripts/multi_turn_test_runner.py \
  --scenarios templates/multi-turn-comprehensive.yaml \
  --verbose
```

**Option 3: Python API for Ad-Hoc Testing**

For custom scenarios or debugging, use the client directly:

```python
from hooks.scripts.agent_api_client import AgentAPIClient

client = AgentAPIClient(
    my_domain="your-domain.my.salesforce.com",
    consumer_key="...",
    consumer_secret="..."
)

# Context manager auto-ends session
with client.session(agent_id="0XxRM000...") as session:
    r1 = session.send("I need to cancel my appointment")
    print(f"Turn 1: {r1.agent_text}")

    r2 = session.send("Actually, reschedule instead")
    print(f"Turn 2: {r2.agent_text}")

    r3 = session.send("What was my original request?")
    print(f"Turn 3: {r3.agent_text}")
    # Check context preservation
    if "cancel" in r3.agent_text.lower():
        print("✅ Context preserved")

# With initial variables
variables = [
    {"name": "$Context.AccountId", "type": "Id", "value": "001XXXXXXXXXXXX"},
    {"name": "$Context.EndUserLanguage", "type": "Text", "value": "en_US"},
]
with client.session(agent_id="0Xx...", variables=variables) as session:
    r1 = session.send("What orders do I have?")
```

**Connectivity Test:**

```bash
# Verify ECA credentials and API connectivity
python3 hooks/scripts/agent_api_client.py
# Reads SF_MY_DOMAIN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET from env
```

**Per-Turn Analysis Checklist:**

The test runner automatically evaluates each turn against expectations defined in the YAML template:

| #   | Check                     | YAML Key                          | How Evaluated                               |
| --- | ------------------------- | --------------------------------- | ------------------------------------------- |
| 1   | Response non-empty?       | `response_not_empty: true`        | `messages[0].message` has content           |
| 2   | Correct topic matched?    | `topic_contains: "cancel"`        | Heuristic: inferred from response text      |
| 3   | Expected actions invoked? | `action_invoked: true`            | Checks for `result` array entries           |
| 4   | Response content?         | `response_contains: "reschedule"` | Substring match on response                 |
| 5   | Context preserved?        | `context_retained: true`          | Heuristic: checks for prior-turn references |
| 6   | Guardrail respected?      | `guardrail_triggered: true`       | Regex patterns for refusal language         |
| 7   | Escalation triggered?     | `escalation_triggered: true`      | Checks for `Escalation` message type        |
| 8   | Response excludes?        | `response_not_contains: "error"`  | Substring exclusion check                   |

See [Agent API Reference](docs/agent-api-reference.md) for complete response format.

### A5: Results & Scoring

Claude generates a terminal-friendly results report:

```
📊 MULTI-TURN TEST RESULTS
════════════════════════════════════════════════════════════════

Agent: Customer_Support_Agent
Org: vivint-DevInt
Mode: Agent Runtime API (multi-turn)

SCENARIO RESULTS
───────────────────────────────────────────────────────────────
✅ topic_switch_natural        3/3 turns passed
✅ context_user_identity       3/3 turns passed
❌ escalation_frustration      2/3 turns passed (Turn 3: no escalation)
✅ guardrail_mid_conversation  3/3 turns passed
✅ action_chain_identify       3/3 turns passed
⚠️ variable_injection          2/3 turns passed (Turn 3: re-asked for account)

SUMMARY
───────────────────────────────────────────────────────────────
Scenarios: 6 total | 4 passed | 1 failed | 1 partial
Turns: 18 total | 16 passed | 2 failed
Topic Re-matching: 100% ✅
Context Preservation: 83% ⚠️
Escalation Accuracy: 67% ❌

FAILED TURNS
───────────────────────────────────────────────────────────────
❌ escalation_frustration → Turn 3
   Input: "Nothing is working! I need a human NOW"
   Expected: Escalation triggered
   Actual: Agent continued troubleshooting
   Category: MULTI_TURN_ESCALATION_FAILURE
   Fix: Add frustration keywords to escalation triggers

⚠️ variable_injection → Turn 3
   Input: "Create a new case for a billing issue"
   Expected: Uses pre-set $Context.AccountId
   Actual: "Which account is this for?"
   Category: CONTEXT_PRESERVATION_FAILURE
   Fix: Wire $Context.AccountId to CreateCase action input

SCORING
───────────────────────────────────────────────────────────────
Topic Selection Coverage          13/15
Action Invocation                 14/15
Multi-Turn Topic Re-matching      15/15  ✅
Context Preservation              10/15  ⚠️
Edge Case & Guardrail Coverage    12/15
Test Spec / Scenario Quality       9/10
Agentic Fix Success               --/15  (pending)

TOTAL: 73/85 (86%) + Fix Loop pending
```

---

## Phase B: CLI Testing Center (SECONDARY)

> **Availability:** Requires Agent Testing Center feature enabled in org.
> If unavailable, use Phase A exclusively.

### B1: Test Spec Creation

**Option A: Interactive Generation** (no Cirra AI automation)

```bash
# Interactive test spec generation
sf agent generate test-spec --output-file ./tests/agent-spec.yaml
# ⚠️ NOTE: No --api-name flag! Interactive-only.
```

**Option B: Automated Generation** (Python script)

```bash
python3 hooks/scripts/generate-test-spec.py \
  --agent-file /path/to/Agent.agent \
  --output tests/agent-spec.yaml \
  --verbose
```

### B2: Test Execution (Cirra AI MCP)

**Create Test in Org:**

First, prepare the test metadata from YAML:

```
tooling_api_dml(
  operation="create",
  sObject="AiEvaluationDefinition",
  record={
    "masterLabel": "MyAgentTest",
    "name": "MyAgentTest",
    "description": "Comprehensive agent test suite",
    "botId": "${AGENT_ID}",
    "type": "SingleUtterance",
    "testCases": [...]  # from YAML conversion
  }
)
```

**Run Test:**

```
tooling_api_dml(
  operation="create",
  sObject="AiEvaluationRun",
  record={
    "evaluationDefinitionId": "${TEST_DEF_ID}",
    "mode": "Simulated"  # or "Live"
  }
)
```

**Wait for completion and get results:**

```
tooling_api_query(
  sObject="AiEvaluationRun",
  whereClause="Id='${RUN_ID}'",
  fields=["Id", "Status", "ResultSummary", "DetailedResults"]
)
```

**Interactive Preview (Simulated):**

```bash
# Not available via Cirra AI - use manual UI
sf agent preview --api-name AgentName --output-dir ./logs --target-org [alias]
```

**Interactive Preview (Live):**

```bash
# Not available via Cirra AI - use manual UI
sf agent preview --api-name AgentName --use-live-actions --client-app AppName --apex-debug --target-org [alias]
```

### B3: Results Analysis (Cirra AI MCP)

Query test results and display formatted summary:

```
tooling_api_query(
  sObject="AiEvaluationRun",
  whereClause="evaluationDefinitionId='${TEST_DEF_ID}'",
  fields=["Id", "Status", "CreatedDate", "ResultSummary"],
  limit=10,
  orderBy="CreatedDate DESC"
)
```

Parse results and display:

```
📊 AGENT TEST RESULTS (CLI via Cirra AI)
════════════════════════════════════════════════════════════════

Agent: Customer_Support_Agent
Org: vivint-DevInt
Duration: 45.2s
Mode: Simulated

SUMMARY
───────────────────────────────────────────────────────────────
✅ Passed:    18
❌ Failed:    2
⏭️ Skipped:   0
📈 Topic Selection: 95%
🎯 Action Invocation: 90%

FAILED TESTS
───────────────────────────────────────────────────────────────
❌ test_complex_order_inquiry
   Utterance: "What's the status of orders 12345 and 67890?"
   Expected: get_order_status invoked 2 times
   Actual: get_order_status invoked 1 time
   Category: ACTION_INVOCATION_COUNT_MISMATCH

COVERAGE SUMMARY
───────────────────────────────────────────────────────────────
Topics Tested:       4/5 (80%) ⚠️
Actions Tested:      6/8 (75%) ⚠️
Guardrails Tested:   3/3 (100%) ✅
```

---

## Phase C: Agentic Fix Loop

When tests fail (either Phase A or Phase B), automatically fix via sf-ai-agentscript:

### Failure Categories (10 total)

| Category                        | Source | Auto-Fix | Strategy                               |
| ------------------------------- | ------ | -------- | -------------------------------------- |
| `TOPIC_NOT_MATCHED`             | A+B    | ✅       | Add keywords to topic description      |
| `ACTION_NOT_INVOKED`            | A+B    | ✅       | Improve action description             |
| `WRONG_ACTION_SELECTED`         | A+B    | ✅       | Differentiate descriptions             |
| `ACTION_INVOCATION_FAILED`      | A+B    | ⚠️       | Delegate to sf-flow or sf-apex         |
| `GUARDRAIL_NOT_TRIGGERED`       | A+B    | ✅       | Add explicit guardrails                |
| `ESCALATION_NOT_TRIGGERED`      | A+B    | ✅       | Add escalation action/triggers         |
| `TOPIC_RE_MATCHING_FAILURE`     | A      | ✅       | Add transition phrases to target topic |
| `CONTEXT_PRESERVATION_FAILURE`  | A      | ✅       | Add context retention instructions     |
| `MULTI_TURN_ESCALATION_FAILURE` | A      | ✅       | Add frustration detection triggers     |
| `ACTION_CHAIN_FAILURE`          | A      | ✅       | Fix action output variable mappings    |

### Auto-Fix Command Example

```bash
Skill(skill="sf-ai-agentscript", args="Fix agent [AgentName] - Error: [category] - [details]")
```

### Fix Loop Flow

```
Test Failed → Analyze failure category
    │
    ├─ Single-turn failure → Standard fix (topics, actions, guardrails)
    │
    └─ Multi-turn failure → Enhanced fix (context, re-matching, escalation, chaining)
    │
    ▼
Apply fix via sf-ai-agentscript → Re-publish → Re-test
    │
    ├─ Pass → ✅ Move to next failure
    └─ Fail → Retry (max 3 attempts) → Escalate to human
```

See [Agentic Fix Loops Guide](resources/agentic-fix-loops.md) for complete decision tree and 10 fix strategies.

### Two Fix Strategies

| Agent Type                        | Fix Strategy                          | When to Use                                        |
| --------------------------------- | ------------------------------------- | -------------------------------------------------- |
| **Custom Agent** (you control it) | Fix the agent via `sf-ai-agentscript` | Topic descriptions, action configs need adjustment |
| **Managed/Standard Agent**        | Fix test expectations                 | Test expectations don't match actual behavior      |

---

## Phase D: Coverage Improvement

If coverage < threshold:

1. Identify untested topics/actions/patterns from results
2. Add test cases (YAML for CLI, scenarios for API)
3. Re-run tests
4. Repeat until threshold met

### Coverage Dimensions

| Dimension               | Phase A | Phase B | Target       |
| ----------------------- | ------- | ------- | ------------ |
| Topic Selection         | ✅      | ✅      | 100%         |
| Action Invocation       | ✅      | ✅      | 100%         |
| Topic Re-matching       | ✅      | ❌      | 90%+         |
| Context Preservation    | ✅      | ❌      | 95%+         |
| Conversation Completion | ✅      | ❌      | 85%+         |
| Guardrails              | ✅      | ✅      | 100%         |
| Escalation              | ✅      | ✅      | 100%         |
| Phrasing Diversity      | ✅      | ✅      | 3+ per topic |

See [Coverage Analysis](docs/coverage-analysis.md) for complete metrics and improvement guide.

---

## Phase E: Observability Integration

After test execution, guide user to analyze agent behavior with session-level observability:

```
Skill(skill="sf-ai-agentforce-observability", args="Analyze STDM sessions for agent [AgentName] in org [alias] - focus on test session behavior patterns")
```

**What observability adds to testing:**

- **STDM Session Analysis**: Examine actual session traces from test conversations
- **Latency Profiling**: Identify slow actions or topic routing delays
- **Error Pattern Detection**: Find recurring failures across sessions
- **Action Execution Traces**: Detailed view of Flow/Apex execution during tests

---

## Scoring System (100 Points)

| Category                           | Points | Key Rules                                            |
| ---------------------------------- | ------ | ---------------------------------------------------- |
| **Topic Selection Coverage**       | 15     | All topics have test cases; various phrasings tested |
| **Action Invocation**              | 15     | All actions tested with valid inputs/outputs         |
| **Multi-Turn Topic Re-matching**   | 15     | Topic switching accuracy across turns                |
| **Context Preservation**           | 15     | Information retention across turns                   |
| **Edge Case & Guardrail Coverage** | 15     | Negative tests; guardrails; escalation               |
| **Test Spec / Scenario Quality**   | 10     | Proper YAML; descriptions; clear expectations        |
| **Agentic Fix Success**            | 15     | Auto-fixes resolve issues within 3 attempts          |

**Scoring Thresholds:**

```
⭐⭐⭐⭐⭐ 90-100 pts → Production Ready
⭐⭐⭐⭐   80-89 pts → Good, minor improvements
⭐⭐⭐    70-79 pts → Acceptable, needs work
⭐⭐      60-69 pts → Below standard
⭐        <60 pts  → BLOCKED - Major issues
```

---

## ⛔ TESTING GUARDRAILS (MANDATORY)

**BEFORE running tests, verify:**

| Check                        | Cirra AI Tool                       | Why                                |
| ---------------------------- | ----------------------------------- | ---------------------------------- |
| Agent published              | `metadata_read(GenAiPlannerBundle)` | Can't test unpublished agent       |
| Agent activated              | Check activation status             | API and preview require activation |
| Flows deployed               | `tooling_api_query(FlowDefinition)` | Actions need Flows                 |
| ECA configured (Phase A)     | Token request test                  | API auth required                  |
| Connected App (Phase B live) | Check OAuth config                  | Live mode requires auth            |

**NEVER do these:**

| Anti-Pattern                   | Problem                        | Correct Pattern                      |
| ------------------------------ | ------------------------------ | ------------------------------------ |
| Test unpublished agent         | Tests fail silently            | Publish first                        |
| Skip simulated testing         | Live mode hides logic bugs     | Always test simulated first          |
| Ignore guardrail tests         | Security gaps in production    | Always test harmful/off-topic inputs |
| Single phrasing per topic      | Misses routing failures        | Test 3+ phrasings per topic          |
| Write ECA credentials to files | Security risk                  | Keep in shell variables only         |
| Skip session cleanup           | Resource leaks and rate limits | Always DELETE sessions after tests   |

---

## CLI Command Reference (for manual execution)

### Test Lifecycle Commands (Manual / Non-Cirra AI)

| Command                       | Purpose            | Example                                                            |
| ----------------------------- | ------------------ | ------------------------------------------------------------------ |
| `sf agent generate test-spec` | Create test YAML   | `sf agent generate test-spec --output-dir ./tests`                 |
| `sf agent test create`        | Deploy test to org | `sf agent test create --spec ./tests/spec.yaml --target-org alias` |
| `sf agent test run`           | Execute tests      | `sf agent test run --api-name Test --wait 10 --target-org alias`   |
| `sf agent test results`       | Get results        | `sf agent test results --job-id ID --result-format json`           |
| `sf agent test resume`        | Resume async test  | `sf agent test resume --use-most-recent --target-org alias`        |
| `sf agent test list`          | List test runs     | `sf agent test list --target-org alias`                            |

**Note:** For automation, use Cirra AI MCP equivalents (tooling_api_dml, tooling_api_query) instead.

### Preview Commands (Manual, not available via Cirra AI)

| Command              | Purpose             | Example                                                |
| -------------------- | ------------------- | ------------------------------------------------------ |
| `sf agent preview`   | Interactive testing | `sf agent preview --api-name Agent --target-org alias` |
| `--use-live-actions` | Use real Flows/Apex | `sf agent preview --use-live-actions --client-app App` |
| `--output-dir`       | Save transcripts    | `sf agent preview --output-dir ./logs`                 |
| `--apex-debug`       | Capture debug logs  | `sf agent preview --apex-debug`                        |

---

## Multi-Turn Test Templates

| Template                               | Pattern             | Scenarios | Location     |
| -------------------------------------- | ------------------- | --------- | ------------ |
| `multi-turn-topic-routing.yaml`        | Topic switching     | 4         | `templates/` |
| `multi-turn-context-preservation.yaml` | Context retention   | 4         | `templates/` |
| `multi-turn-escalation-flows.yaml`     | Escalation cascades | 4         | `templates/` |
| `multi-turn-comprehensive.yaml`        | All 6 patterns      | 6         | `templates/` |

### CLI Test Templates

| Template                       | Purpose                   | Location     |
| ------------------------------ | ------------------------- | ------------ |
| `basic-test-spec.yaml`         | Quick start (3-5 tests)   | `templates/` |
| `comprehensive-test-spec.yaml` | Full coverage (20+ tests) | `templates/` |
| `guardrail-tests.yaml`         | Security/safety scenarios | `templates/` |
| `escalation-tests.yaml`        | Human handoff scenarios   | `templates/` |
| `standard-test-spec.yaml`      | Reference format          | `templates/` |

---

## Cross-Skill Integration

**Required Delegations:**

| Scenario              | Skill to Call                  | Command                                                            |
| --------------------- | ------------------------------ | ------------------------------------------------------------------ |
| Fix agent script      | sf-ai-agentscript              | `Skill(skill="sf-ai-agentscript", args="Fix...")`                  |
| Create test data      | sf-data                        | `Skill(skill="sf-data", args="Create...")`                         |
| Fix failing Flow      | sf-flow                        | `Skill(skill="sf-flow", args="Fix...")`                            |
| Setup ECA or OAuth    | sf-connected-apps              | `Skill(skill="sf-connected-apps", args="Create...")`               |
| Analyze debug logs    | sf-debug                       | `Skill(skill="sf-debug", args="Analyze...")`                       |
| Session observability | sf-ai-agentforce-observability | `Skill(skill="sf-ai-agentforce-observability", args="Analyze...")` |

---

## Automated Testing (Python Scripts)

Python scripts execute directly without needing sf CLI and work with both API and Cirra AI approaches.

| Script                      | Purpose                                                                     | Dependencies              |
| --------------------------- | --------------------------------------------------------------------------- | ------------------------- |
| `agent_api_client.py`       | Reusable Agent Runtime API v1 client (auth, sessions, messaging, variables) | stdlib only               |
| `multi_turn_test_runner.py` | Multi-turn test orchestrator (reads YAML, executes, evaluates, reports)     | pyyaml + agent_api_client |
| `generate-test-spec.py`     | Parse .agent files, generate CLI test YAML specs                            | stdlib only               |
| `run-automated-tests.py`    | Orchestrate full CLI test workflow with fix suggestions                     | stdlib only               |

**Multi-Turn Testing (Agent Runtime API):**

```bash
# Install test runner dependency
pip3 install pyyaml

# Run multi-turn test suite against an agent
python3 hooks/scripts/multi_turn_test_runner.py \
  --my-domain your-domain.my.salesforce.com \
  --consumer-key YOUR_KEY \
  --consumer-secret YOUR_SECRET \
  --agent-id 0XxRM0000004ABC \
  --scenarios templates/multi-turn-comprehensive.yaml \
  --output results.json --verbose

# Or set env vars and omit credential flags
export SF_MY_DOMAIN=your-domain.my.salesforce.com
export SF_CONSUMER_KEY=YOUR_KEY
export SF_CONSUMER_SECRET=YOUR_SECRET
python3 hooks/scripts/multi_turn_test_runner.py \
  --agent-id 0XxRM0000004ABC \
  --scenarios templates/multi-turn-topic-routing.yaml \
  --var '$Context.AccountId=001XXXXXXXXXXXX' \
  --verbose

# Connectivity test (verify ECA credentials work)
python3 hooks/scripts/agent_api_client.py
```

**CLI Testing (via Cirra AI):**

```bash
# Generate test spec from agent file
python3 hooks/scripts/generate-test-spec.py \
  --agent-file /path/to/Agent.agent \
  --output specs/Agent-tests.yaml

# Create test using Cirra AI tooling_api_dml
# (See Phase B2 for Cirra AI calls)

# Run full automated workflow with Cirra AI
python3 hooks/scripts/run-automated-tests.py \
  --agent-name MyAgent \
  --agent-dir /path/to/project \
  --use-cirra-ai true
```

---

## 🔄 Automated Test-Fix Loop

> **v2.0.0-cirra** | Supports both multi-turn API failures and CLI test failures

### Quick Start

```bash
# Run the test-fix loop (CLI tests via Cirra AI)
./hooks/scripts/test-fix-loop.sh Test_Agentforce_v1 AgentforceTesting 3

# Exit codes:
#   0 = All tests passed
#   1 = Fixes needed (Claude Code should invoke sf-ai-agentforce)
#   2 = Max attempts reached, escalate to human
#   3 = Error (org unreachable, test not found, etc.)
```

### Claude Code Integration

```
USER: Run automated test-fix loop for Coral_Cloud_Agent

CLAUDE CODE:
1. Phase 0: Initialize Cirra AI (cirra_ai_init)
2. Phase A: Run multi-turn scenarios via Python test runner
   python3 hooks/scripts/multi_turn_test_runner.py \
     --agent-id ${AGENT_ID} \
     --scenarios templates/multi-turn-comprehensive.yaml \
     --output results.json --verbose
3. Analyze failures from results.json (10 categories)
4. If fixable: Skill(skill="sf-ai-agentscript", args="Fix...")
5. Re-run failed scenarios with --scenario-filter
6. Phase B (if available): Create and run tests via Cirra AI tooling_api_dml/query
7. Repeat until passing or max retries (3)
```

### Environment Variables

| Variable           | Description                        | Default |
| ------------------ | ---------------------------------- | ------- |
| `CURRENT_ATTEMPT`  | Current attempt number             | 1       |
| `MAX_WAIT_MINUTES` | Timeout for test execution         | 10      |
| `SKIP_TESTS`       | Comma-separated test names to skip | (none)  |
| `VERBOSE`          | Enable detailed output             | false   |
| `USE_CIRRA_AI`     | Use Cirra AI tools for Phase B     | true    |

---

## 💡 Key Insights

| Problem                                | Symptom                             | Solution                                    |
| -------------------------------------- | ----------------------------------- | ------------------------------------------- |
| **Cirra AI not initialized**           | "Connection not established"        | Call `cirra_ai_init()` first                |
| **Agent not found**                    | tooling_api_query returns 0 results | Verify agent DeveloperName is correct       |
| Tests fail silently                    | No results returned                 | Agent not published - activate and publish  |
| Topic not matched                      | Wrong topic selected                | Add keywords to topic description           |
| Action not invoked                     | Action never called                 | Improve action description                  |
| Live preview 401                       | Authentication error                | Connected App not configured                |
| API 401                                | Token expired or wrong credentials  | Re-authenticate ECA                         |
| API 404 on session create              | Wrong Agent ID                      | Re-query BotDefinition for correct Id       |
| Empty API response                     | Agent not activated                 | Activate and publish agent                  |
| Context lost between turns             | Agent re-asks for known info        | Add context retention instructions to topic |
| Topic doesn't switch                   | Agent stays on old topic            | Add transition phrases to target topic      |
| **AiEvaluationDefinition query fails** | **Cannot use this sObject**         | **Agent Testing Center NOT enabled**        |
| **Cirra AI query timeout**             | **Query takes too long**            | **Use more specific whereClause filters**   |
| **tooling_api_dml fails**              | **Missing required fields**         | **Check metadata schema for object**        |

---

## Quick Start Example

### Multi-Turn API Testing (Recommended)

**Quick Start with Python Scripts:**

```bash
# 0. Initialize Cirra AI (one-time)
# (via AskUserQuestion flow in Phase 0)

# 1. Get agent ID (via Cirra AI)
# tooling_api_query(BotDefinition, whereClause="DeveloperName='My_Agent'...")

# 2. Run multi-turn tests (credentials from env or flags)
python3 hooks/scripts/multi_turn_test_runner.py \
  --my-domain "${SF_MY_DOMAIN}" \
  --consumer-key "${CONSUMER_KEY}" \
  --consumer-secret "${CONSUMER_SECRET}" \
  --agent-id "${AGENT_ID}" \
  --scenarios templates/multi-turn-comprehensive.yaml \
  --output results.json --verbose
```

**Ad-Hoc Python Usage:**

```python
from hooks.scripts.agent_api_client import AgentAPIClient

client = AgentAPIClient()  # reads SF_MY_DOMAIN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET from env
with client.session(agent_id="0XxRM000...") as session:
    r1 = session.send("I need to cancel my appointment")
    r2 = session.send("Actually, reschedule it instead")
    r3 = session.send("What was my original request about?")
    # Session auto-ends when exiting context manager
```

### CLI Testing (If Agent Testing Center Available)

**Using Cirra AI MCP:**

```bash
# 0. Initialize Cirra AI (one-time)

# 1. Generate test spec (manual or Python)
python3 hooks/scripts/generate-test-spec.py \
  --agent-file ./agents/MyAgent.agent \
  --output ./tests/myagent-tests.yaml

# 2. Create test in org (Cirra AI)
# tooling_api_dml(create, AiEvaluationDefinition, record={...from YAML...})

# 3. Run tests (Cirra AI)
# tooling_api_dml(create, AiEvaluationRun, record={...})

# 4. View results (Cirra AI)
# tooling_api_query(AiEvaluationRun, whereClause="id='${RUN_ID}'")
```

---

## 🐛 Known Issues & Considerations

> **Last Updated**: 2026-02-06 | **Tested With**: Cirra AI MCP Server + Salesforce Winter '26 API

### CRITICAL: `AiEvaluationDefinition` Availability

**Status**: 🔴 Feature Dependent - Not all orgs have Agent Testing Center enabled

**Check**:

```
tooling_api_query(sObject="AiEvaluationDefinition", limit=1)
```

**If fails with "Cannot use: AiEvaluationDefinition":**

- Agent Testing Center feature NOT enabled in org
- Use Phase A (Agent Runtime API) exclusively
- Contact Salesforce admin to enable testing center

### MEDIUM: Python Script Dependencies

**Status**: 🟡 Requires pyyaml for multi-turn testing

**Install**:

```bash
pip3 install pyyaml
```

**Agent API Client**: stdlib only (no external deps)

### LOW: Interactive Preview Not Available via Cirra AI

**Status**: 🟡 Manual UI operation only

**Workaround**: Use `sf agent preview` CLI command directly for interactive testing.

---

## License

MIT License. See LICENSE file.
Copyright (c) 2024-2026 Jag Valaiyapathy
