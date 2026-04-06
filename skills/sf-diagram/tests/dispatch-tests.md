# sf-diagram dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## oauth — JWT Bearer flow

- **Input**: `/sf-diagram oauth JWT Bearer`
- **Dispatch**: OAuth flow diagram
- **Init required**: no
- **Init timing**: n/a
- **Path**: fast
- **First tool**: n/a (no MCP tools needed; template-driven)
- **Tool params**: n/a
- **Should call**: (none — no org connection required)
- **Should NOT call**: `sobject_describe`, `soql_query`, `tooling_api_query`, `cirra_ai_init`
- **Should ask user**: no (diagram type and flow variant are fully specified)
- **Menu options**: n/a
- **Follow-up skills**: `sf-metadata`

**Notes**: `oauth` keyword maps directly to the OAuth flow diagram type. `JWT Bearer` in `$ARGUMENTS` selects the `oauth/jwt-bearer.md` template. No org metadata is needed, so MCP tools must not be called. Output must include both Mermaid `sequenceDiagram` with `autonumber` and an ASCII fallback.

---

## erd — Account-Contact-Opportunity with org metadata

- **Input**: `/sf-diagram erd Account Contact Opportunity`
- **Dispatch**: ERD / data model diagram
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: n/a (no required params beyond defaults)
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should NOT call**: `tooling_api_query`
- **Should ask user**: no (objects are specified; output preference may be clarified but is not blocking)
- **Menu options**: n/a
- **Follow-up skills**: `sf-metadata`

**Notes**: Object names in `$ARGUMENTS` trigger ERD dispatch. `cirra_ai_init` must be called first because live org metadata is required. `sobject_describe` is called once per object (Account, Contact, Opportunity) to resolve relationships. `soql_query` is called to obtain record counts for LDV indicators. Output uses `flowchart LR` with Tailwind pastel color coding (blue for standard objects).

---

## integration — Heroku to Salesforce REST callout

- **Input**: `/sf-diagram integration Heroku Salesforce REST`
- **Dispatch**: Integration sequence diagram
- **Init required**: no
- **Init timing**: n/a
- **Path**: fast
- **First tool**: n/a
- **Tool params**: n/a
- **Should call**: (none — user-provided system names are sufficient)
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`
- **Should ask user**: no (systems are named; async vs sync may be clarified but is optional)
- **Menu options**: n/a
- **Follow-up skills**: `sf-metadata`

**Notes**: `integration` keyword plus system names dispatch to the integration sequence diagram type using the `integration/api-sequence.md` template. No org connection is required. Mermaid output uses `sequenceDiagram` with `alt`/`else` for error paths and `-)` notation for async calls.

---

## landscape — system architecture overview

- **Input**: `/sf-diagram landscape`
- **Dispatch**: System landscape / architecture
- **Init required**: no
- **Init timing**: n/a
- **Path**: full
- **First tool**: n/a
- **Tool params**: n/a
- **Should call**: (none — user description drives the diagram)
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`
- **Should ask user**: yes (scope is vague — must ask which systems/components to include)
- **Menu options**: n/a
- **Follow-up skills**: `sf-metadata`

**Notes**: `landscape` maps to the system landscape type using `architecture/system-landscape.md`. The keyword alone gives no component detail, so the skill must prompt the user for the systems and components before generating the diagram. Output uses `flowchart` Mermaid syntax.

---

## hierarchy — role and permission structure

- **Input**: `/sf-diagram hierarchy`
- **Dispatch**: Role / permission hierarchy diagram
- **Init required**: no
- **Init timing**: n/a
- **Path**: full
- **First tool**: n/a
- **Tool params**: n/a
- **Should call**: (none by default; org query optional if connected)
- **Should NOT call**: `sobject_describe`, `soql_query`, `tooling_api_query`
- **Should ask user**: yes (must clarify whether this is a user role hierarchy, profile/permission set structure, or both)
- **Menu options**: n/a
- **Follow-up skills**: `sf-permissions`

**Notes**: Both `hierarchy` and `role` keywords dispatch to this type. The single keyword provides no structural detail, so the skill must ask the user to describe the hierarchy scope. Uses `role-hierarchy/user-hierarchy.md` template and `flowchart` Mermaid syntax. `sf-permissions` is the natural follow-up to supply real permission data.

---

## agentforce — agent topic action flow

- **Input**: `/sf-diagram agentforce`
- **Dispatch**: Agentforce agent flow diagram
- **Init required**: no
- **Init timing**: n/a
- **Path**: full
- **First tool**: n/a
- **Tool params**: n/a
- **Should call**: (none — architecture is described by the user)
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`
- **Should ask user**: yes (agent name, topics, and actions must be gathered before generating)
- **Menu options**: n/a
- **Follow-up skills**: (none specified in SKILL.md)

**Notes**: `agentforce` keyword dispatches to the Agentforce agent flow diagram using `agentforce/agent-flow.md`. The keyword alone carries no agent details, so the skill must ask for agent name, topics, and actions. Output uses `flowchart` Mermaid syntax representing Agent -> Topic -> Action relationships.

---

## no arguments — ask user for diagram type

- **Input**: `/sf-diagram`
- **Dispatch**: Ask the user (see below)
- **Init required**: no
- **Init timing**: n/a
- **Path**: n/a
- **First tool**: n/a
- **Tool params**: n/a
- **Should call**: (none until user selects a type)
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`
- **Should ask user**: yes (no diagram type was provided)
- **Menu options**: OAuth Flow, ERD / Data Model, Integration Sequence, System Landscape, Role / Permission Hierarchy, Agentforce Agent Flow
- **Follow-up skills**: `sf-metadata`, `sf-permissions`, `sf-flow`

**Notes**: When `$ARGUMENTS` is empty the dispatch table explicitly requires asking the user what type of diagram to create. The skill should present the six supported types as a menu. No MCP calls are made until a type is confirmed and (where applicable) scope details are provided. Init timing is `after-menu` if the user selects ERD and an org is connected.

---

## natural language — draw me a PKCE OAuth flow

- **Input**: `/sf-diagram draw me a PKCE OAuth flow for a mobile app`
- **Dispatch**: OAuth flow diagram
- **Init required**: no
- **Init timing**: n/a
- **Path**: fast
- **First tool**: n/a
- **Tool params**: n/a
- **Should call**: (none)
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`
- **Should ask user**: no (PKCE variant and mobile context are clear from the natural language)
- **Menu options**: n/a
- **Follow-up skills**: `sf-metadata`

**Notes**: Natural language input containing "OAuth" and "PKCE" must be parsed as an OAuth flow diagram, selecting the `oauth/authorization-code-pkce.md` template. The dispatch logic must handle free-form phrasing, not just bare keywords. "Mobile app" context should be reflected in the diagram actors (e.g., Mobile App instead of Browser). Output is Mermaid `sequenceDiagram` with `autonumber` plus ASCII fallback.

---

## edge case — conflicting keywords (erd + oauth)

- **Input**: `/sf-diagram erd oauth Account`
- **Dispatch**: ERD / data model diagram
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: n/a
- **Should call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should NOT call**: `tooling_api_query`
- **Should ask user**: yes (ambiguous input — skill should confirm which diagram type the user actually wants before proceeding)
- **Menu options**: n/a
- **Follow-up skills**: `sf-metadata`

**Notes**: When `$ARGUMENTS` contains keywords that match more than one row of the dispatch table (`erd` and `oauth` both appear), the skill must not silently pick one. It should surface the ambiguity to the user and confirm intent before selecting a template. If the user confirms ERD, `cirra_ai_init` is required because live org metadata is needed for the `Account` object. This tests that the dispatch parser does not short-circuit on the first matching keyword.

---

## oauth — authorization code flow

- **Input**: `/sf-diagram oauth authorization code flow for a web application`
- **Dispatch**: OAuth flow diagram
- **Init required**: no
- **Init timing**: `n/a`
- **Path**: `fast`
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`, `tooling_api_query`
- **Should ask user**: no (flow type is specified)
- **Follow-up skills**: `sf-permissions`

**Notes**: `oauth` keyword with explicit flow type (authorization code) routes to OAuth Flow Diagrams. No org data needed — OAuth diagrams are generated from reference templates. Should use the Authorization Code template, not PKCE. The request specifies "web application" which confirms standard auth code (not PKCE for SPAs).

---

## erd — static data model without org

- **Input**: `/sf-diagram erd Account Contact Opportunity without org metadata`
- **Dispatch**: ERD / data model diagram
- **Init required**: no
- **Init timing**: `n/a`
- **Path**: `fast`
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should ask user**: no (objects are specified)
- **Follow-up skills**: `sf-metadata`, `sf-data`

**Notes**: `erd` keyword with object names plus explicit "without org metadata" qualifier. Can generate a standard ERD from known standard object relationships without connecting to an org. Differentiates from the existing "erd with org metadata" test by explicitly opting out of live org data. If the user omits the qualifier, the default behavior is to fetch org metadata (as tested in the existing case).

---

## sequence diagram for API integration

- **Input**: `/sf-diagram sequence Salesforce to Stripe payment sync`
- **Dispatch**: Integration sequence diagram
- **Init required**: no
- **Init timing**: `n/a`
- **Path**: `full`
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should ask user**: yes (need details about the integration steps, endpoints, and data flow)
- **Follow-up skills**: `sf-apex`, `sf-flow`

**Notes**: `sequence` keyword routes to Integration Sequence Diagrams per the dispatch table. The request names two systems (Salesforce and Stripe) but doesn't specify the detailed steps. Should ask the user for the specific API calls, data transformations, and error handling to include in the diagram.

---

## data-model synonym for erd

- **Input**: `/sf-diagram data-model for CPQ objects`
- **Dispatch**: ERD / data model diagram
- **Init required**: no
- **Init timing**: `n/a`
- **Path**: `full`
- **Should NOT call**: `cirra_ai_init`, `sobject_describe`, `soql_query`
- **Should ask user**: yes (need to clarify which CPQ objects to include — standard vs custom)
- **Follow-up skills**: `sf-metadata`

**Notes**: `data-model` is listed as a synonym for `erd` in the dispatch table. "CPQ objects" is underspecified — the user could mean standard Salesforce CPQ objects (Quote, QuoteLineItem, Product2, PricebookEntry) or custom CPQ objects. Should ask for clarification before generating.

---

## role hierarchy with org data

- **Input**: `/sf-diagram hierarchy show role and permission set structure from the org`
- **Dispatch**: Role / permission hierarchy diagram
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `soql_query`
- **Should NOT call**: `metadata_create`, `metadata_update`
- **Should ask user**: no (request is clear — pull from org)
- **Follow-up skills**: `sf-permissions`

**Notes**: `hierarchy` keyword routes to Role & Permission Hierarchy. The request explicitly asks for org data ("from the org"), so init is required. Should query UserRole, PermissionSet, and PermissionSetGroup objects to build the hierarchy visualization.
