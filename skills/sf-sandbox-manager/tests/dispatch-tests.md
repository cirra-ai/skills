# sf-sandbox-manager dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## checkout a sandbox

- **Input**: `/sf-sandbox-manager checkout`
- **Dispatch**: Checkout Environment
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `soql_query`
- **Tool params**: `sObject: Environment_Pool__c, whereClause: Status__c = 'Available'`
- **Should NOT call**: `tooling_api_dml`, `metadata_create`, `sobject_create`
- **Should ask user**: yes (which environment, purpose, expected duration)
- **Follow-up skills**: `sf-metadata`, `sf-data`

**Notes**: The `checkout` keyword routes to Checkout Environment. The workflow queries available environments from the pool, presents options to the user, then updates the selected record with checkout metadata. Pool Setup is auto-triggered if `Environment_Pool__c` doesn't exist.

---

## checkin an environment

- **Input**: `/sf-sandbox-manager checkin dev-sandbox-1`
- **Dispatch**: Check In Environment
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `soql_query`
- **Tool params**: `sObject: Environment_Pool__c, whereClause: Environment_Name__c = 'dev-sandbox-1'`
- **Should call**: `sobject_dml`
- **Should NOT call**: `tooling_api_dml`, `sobject_create`
- **Should ask user**: yes (clean, dirty, or decommission)

**Notes**: The `checkin` keyword with a sandbox name routes to Check In Environment. The workflow identifies the environment, asks about its condition, and updates the pool record accordingly. If dirty, offers to initiate a refresh.

---

## return an environment (natural language)

- **Input**: `/sf-sandbox-manager I'm done with the QA sandbox`
- **Dispatch**: Check In Environment
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `soql_query`
- **Should ask user**: yes (confirm which environment, condition)

**Notes**: Natural language "done with" maps to Check In Environment. The skill should identify the environment from context ("QA sandbox") and confirm before proceeding.

---

## pool status

- **Input**: `/sf-sandbox-manager status`
- **Dispatch**: Pool Status
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `soql_query`
- **Tool params**: `sObject: Environment_Pool__c`
- **Should NOT call**: `sobject_dml`, `tooling_api_dml`, `sobject_create`
- **Should ask user**: no

**Notes**: The `status` keyword routes to Pool Status. The workflow queries all pool records, polls `SandboxProcess` for any in `Creating` state, and presents a combined status table. If CLI is available, also runs `sf org list` for scratch orgs.

---

## list environments (natural language)

- **Input**: `/sf-sandbox-manager show environments`
- **Dispatch**: Pool Status
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `soql_query`
- **Should ask user**: no

**Notes**: Natural language "show environments" maps to Pool Status. Same workflow as `status`.

---

## create a sandbox

- **Input**: `/sf-sandbox-manager create Developer sandbox called qa-test`
- **Dispatch**: Create Environment
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `tooling_api_dml`
- **Tool params**: `sObject: SandboxInfo, operation: create`
- **Should call**: `sobject_dml` (to create pool tracking record)
- **Should NOT call**: `sobject_create`, `sobject_field_create`
- **Should ask user**: no (type and name are specified)

**Notes**: The `create` keyword with sandbox type and name routes to Create Environment. The workflow creates the sandbox via Tooling API, then creates an `Environment_Pool__c` record with `Status__c = 'Creating'`. Reports estimated creation time.

---

## create a scratch org

- **Input**: `/sf-sandbox-manager create scratch org for 7 days`
- **Dispatch**: Create Environment (scratch org path)
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: CLI command `sf org create scratch`
- **Should NOT call**: `tooling_api_dml`, `sobject_dml`
- **Should ask user**: yes (template choice, alias)
- **Requires**: CLI execution mode (`cli` or `sfdx-repo`)

**Notes**: "create scratch org" routes to Create Environment's scratch org path. If CLI is not available, the skill should explain the limitation and offer a sandbox as fallback. No `Environment_Pool__c` record is created for scratch orgs.

---

## delete a sandbox

- **Input**: `/sf-sandbox-manager delete old-staging`
- **Dispatch**: Delete Environment
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: SandboxInfo, whereClause: SandboxName = 'old-staging'`
- **Should call**: `tooling_api_dml` (delete SandboxInfo), `sobject_dml` (delete pool record)
- **Should ask user**: yes (confirm destructive operation)

**Notes**: The `delete` keyword routes to Delete Environment. This is a destructive operation — the skill MUST confirm with the user before proceeding. Deletes both the actual sandbox and the pool tracking record.

---

## recommendation engine

- **Input**: `/sf-sandbox-manager recommend`
- **Dispatch**: Recommendation Engine
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **Should NOT call**: `sobject_dml`, `tooling_api_dml`, `sobject_create`
- **Should ask user**: yes (data needs, duration, constraints)

**Notes**: The `recommend` keyword routes to Recommendation Engine. The workflow asks questions about the user's requirements and presents a recommendation with rationale. Non-technical users get simplified questions; technical users get the full decision matrix.

---

## sandbox or scratch org question (natural language)

- **Input**: `/sf-sandbox-manager should I use a sandbox or scratch org for unit testing?`
- **Dispatch**: Recommendation Engine
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **Should ask user**: yes (gather additional requirements)

**Notes**: Natural language "should I use... sandbox or scratch" maps to Recommendation Engine. The skill should ask clarifying questions about data needs, duration, and constraints before making a recommendation.

---

## setup pool

- **Input**: `/sf-sandbox-manager setup`
- **Dispatch**: Pool Setup
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `sobject_describe`
- **Tool params**: `sObject: Environment_Pool__c`
- **Should call**: `sobject_create`, `sobject_field_create`, `metadata_create`
- **Should ask user**: yes (confirm before creating metadata)

**Notes**: The `setup` keyword routes to Pool Setup. The workflow checks if `Environment_Pool__c` exists, and if not, creates it with all fields and a Permission Set. Always confirms with the user before creating metadata.

---

## no arguments — show menu

- **Input**: `/sf-sandbox-manager`
- **Dispatch**: (none — present menu)
- **Init required**: no
- **Init timing**: after-menu (defer init until workflow selected)
- **Path**: n/a
- **Should ask user**: yes
- **Menu options**: Checkout, Check in, Status, Create, Delete, Recommend, Setup

**Notes**: No arguments means unclear intent. The skill should present the numbered menu with all seven options. No MCP tools should be called before the user picks an option. Init is deferred until a workflow is selected.

---

## ambiguous intent

- **Input**: `/sf-sandbox-manager dev-sandbox-1`
- **Dispatch**: (ambiguous — could be checkout, checkin, status, or delete)
- **Init required**: no
- **Init timing**: after-menu (defer until intent clarified)
- **Path**: n/a
- **Should ask user**: yes

**Notes**: Just an environment name with no verb. The dispatch table doesn't have a direct match for bare names. The skill should ask whether the user wants to check out, check in, view status of, or delete this environment.

---

## get me an org (natural language)

- **Input**: `/sf-sandbox-manager I need a clean environment for testing`
- **Dispatch**: Checkout Environment
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `soql_query`
- **Should ask user**: yes (which environment, purpose)

**Notes**: Natural language "I need an environment" maps to Checkout Environment. The skill should query available environments and present options to the user.

---

## provision new environment (natural language)

- **Input**: `/sf-sandbox-manager add a new sandbox to the pool`
- **Dispatch**: Create Environment
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **Should ask user**: yes (sandbox type, name)

**Notes**: Natural language "add to pool" maps to Create Environment. Since type and name aren't specified, the skill should ask for them (or run the recommendation engine to help choose the type).
