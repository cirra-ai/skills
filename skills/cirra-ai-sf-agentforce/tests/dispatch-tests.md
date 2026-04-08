# cirra-ai-sf-agentforce dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## create a GenAiFunction for case lookup

- **Input**: `/cirra-ai-sf-agentforce create a GenAiFunction for case lookup`
- **Dispatch**: Create Agentforce Component
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (needs target object discovery)
- **First tool**: `sobject_describe`
- **Tool params**: `sObject: Case`
- **Should call**: `metadata_create`
- **Should NOT call**: `metadata_delete`, `metadata_update`
- **Should ask user**: no (requirements are clear)
- **Follow-up skills**: `sf-apex`, `sf-flow`, `sf-permissions`

**Notes**: The `create` keyword routes to Create Agentforce Component. The workflow should detect that a GenAiFunction needs an invocation target (Flow or Apex), create the metadata XML, and optionally hand off to `sf-apex` or `sf-flow` for the backing action.

---

## configure agent topics and instructions

- **Input**: `/cirra-ai-sf-agentforce configure topics for the Service Agent`
- **Dispatch**: Configure Agent
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (needs agent discovery)
- **First tool**: `soql_query` or `tooling_api_query`
- **Should NOT call**: `metadata_delete`
- **Should ask user**: no (intent is clear — configure topics)
- **Follow-up skills**: `sf-data`

**Notes**: The `configure` keyword routes to Configure Agent. The workflow should query existing agent configuration, then guide the user through topic and action setup in Agent Builder.

---

## deploy agent metadata

- **Input**: `/cirra-ai-sf-agentforce deploy`
- **Dispatch**: Deploy Agent
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (needs validation before deploy)
- **Should ask user**: yes (confirm deployment target)
- **Should NOT call**: `metadata_delete`

**Notes**: The `deploy` keyword routes correctly. The workflow MUST validate agent metadata (100-point scoring) before pushing. Must confirm the target org with the user. Uses the two-command deployment pattern: retrieve → modify → push.

---

## describe current agent configuration

- **Input**: `/cirra-ai-sf-agentforce describe the Service Agent`
- **Dispatch**: Describe Agent
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `soql_query` or `tooling_api_query`
- **Should NOT call**: `metadata_create`, `metadata_update`, `metadata_delete`
- **Should ask user**: no
- **Follow-up skills**: `sf-data`, `sf-diagram`

**Notes**: The `describe` keyword triggers Describe Agent. Query GenAiPlanner, GenAiPlugin, and GenAiFunction metadata to show the full agent configuration tree. Single, unambiguous operation qualifies for fast path.

---

## validate agent metadata quality

- **Input**: `/cirra-ai-sf-agentforce validate`
- **Dispatch**: Validate Agent
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (needs metadata retrieval then scoring)
- **First tool**: `soql_query` or `tooling_api_query`
- **Should NOT call**: `metadata_create`, `metadata_update`, `metadata_delete`
- **Should ask user**: yes (which agent to validate if multiple exist)

**Notes**: The `validate` keyword routes to Validate Agent. Retrieves all agent metadata and runs the 100-point scoring rubric across 6 categories. Reports category-level and overall scores with actionable remediation steps.

---

## no arguments — show menu

- **Input**: `/cirra-ai-sf-agentforce`
- **Dispatch**: (none — present menu)
- **Init required**: no
- **Init timing**: after-menu (defer init until workflow selected)
- **Path**: n/a
- **Should ask user**: yes (AskUserQuestion with 5 options)
- **Should NOT call**: any MCP tool before user answers

**Notes**: No arguments means no workflow can be selected. Present the AskUserQuestion menu with Create, Configure, Deploy, Describe, Validate options. Do not call `cirra_ai_init()` until the user picks a workflow.

---

## ambiguous input — ask for clarification

- **Input**: `/cirra-ai-sf-agentforce agent stuff`
- **Dispatch**: (none — unclear intent)
- **Init required**: no
- **Init timing**: after-menu
- **Path**: n/a
- **Should ask user**: yes (AskUserQuestion with 5 options)
- **Should NOT call**: any MCP tool before user answers

**Notes**: The input does not match any known keyword. Present the AskUserQuestion menu. Do NOT guess the intent or default to any workflow.

---

## create a PromptTemplate

- **Input**: `/cirra-ai-sf-agentforce create a flex prompt template for case summarization`
- **Dispatch**: Create Agentforce Component
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full (needs template type confirmation)
- **First tool**: `metadata_create`
- **Should NOT call**: `metadata_delete`
- **Should ask user**: no (intent and type are clear)
- **Follow-up skills**: `sf-apex`, `sf-data`

**Notes**: The `create` keyword with `prompt template` qualifier routes to Create Agentforce Component. Should generate PromptTemplate metadata XML with templateType `flexPrompt`, variable bindings, and resolution configuration.
