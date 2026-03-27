# sf-apex dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## create a trigger

- **Input**: `/sf-apex create trigger AccountTrigger on Account for before insert, after update`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no (type, object, and events are all specified)
- **Follow-up skills**: none

**Notes**: `create` + `trigger` routes to Create Apex. The request includes type (Trigger), target object (Account), and events (before insert, after update). Should check if AccountTrigger already exists via `tooling_api_query` on ApexTrigger, then generate code and deploy via `tooling_api_dml`. Should also ask about Trigger Actions Framework (TAF).

---

## create a test class

- **Input**: `/sf-apex create test-class for AccountService`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **Should call**: `tooling_api_query`, `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `create` + `test-class` routes to Create Apex. Should first fetch AccountService source via `tooling_api_query` on ApexClass to understand what to test, then generate a test class following best practices (factory patterns, bulk testing with 201+ records to cross batch boundary).

---

## update existing class

- **Input**: `/sf-apex update AccountService add a method to calculate total revenue`
- **Dispatch**: Update Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: ApexClass, whereClause: Name = 'AccountService'`
- **Should call**: `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `update` keyword routes to Update Apex. Should first fetch the current implementation via `tooling_api_query` on ApexClass (try class first, then trigger if not found). Apply changes, validate with 150-point scoring, and redeploy via `tooling_api_dml`.

---

## validate a class by name

- **Input**: `/sf-apex validate MyController`
- **Dispatch**: Validate Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: ApexClass, whereClause: Name = 'MyController'`
- **Should NOT call**: `tooling_api_dml` (validation only, no deployment)
- **Should ask user**: no
- **Follow-up skills**: `/sf-apex update` (if issues are found worth fixing)

**Notes**: `validate` keyword routes to Validate Apex. Fetches the class body from the org, runs 150-point static analysis, returns scored report. Does NOT redeploy — validation is read-only.

---

## validate a local file

- **Input**: `/sf-apex validate /path/to/MyClass.cls`
- **Dispatch**: Validate Apex
- **Init required**: no (local file — no org needed for validation)
- **Init timing**: `n/a`
- **Path**: `fast`
- **Should NOT call**: `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: Local file path (ends in `.cls`) means validate directly without fetching from org. The validation script runs locally. No MCP tools needed for pure local validation.

---

## validate All in org

- **Input**: `/sf-apex validate All`
- **Dispatch**: Validate Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: ApexClass` (then also ApexTrigger)
- **Should NOT call**: `tooling_api_dml` (validation only, no deployment)
- **Should ask user**: no
- **Batch behavior**: fetches and validates all classes and triggers
- **Follow-up skills**: `/sf-apex update` (for classes with low scores)

**Notes**: The special keyword `All` means org-wide audit. Should query all ApexClass and all ApexTrigger records, validate each, and produce a summary report. This can be a large operation.

---

## no arguments — show menu

- **Input**: `/sf-apex`
- **Dispatch**: (none — present menu)
- **Init required**: no
- **Init timing**: `after-menu`
- **Path**: `n/a`
- **Should NOT call**: `cirra_ai_init`, `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: yes
- **Menu options**: Create, Update, Validate
- **Follow-up skills**: none

**Notes**: No arguments. Present the three-option dispatch menu.

---

## fast path — simple utility class

- **Input**: `/sf-apex create class StringUtils with a method to capitalize first letter`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `fast`
- **Should call**: `cirra_ai_init`, `tooling_api_dml`
- **Should NOT call**: `tooling_api_query` (fast path skips existence check for new simple classes)
- **Should ask user**: no
- **Follow-up skills**: `/sf-apex validate` (to score the generated class)

**Notes**: `create` + `class` routes to Create Apex. This is a simple, self-contained request — should use the fast path (bypass full 5-phase workflow). Generate code, run mandatory guardrail checks (anti-patterns only, skip full 150-point scoring), deploy via `tooling_api_dml`.

---

## ambiguous — just a class name

- **Input**: `/sf-apex AccountService`
- **Dispatch**: (ambiguous — could be validate or update)
- **Init required**: no
- **Init timing**: `after-menu`
- **Path**: `n/a`
- **Should NOT call**: `cirra_ai_init`, `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: yes
- **Follow-up skills**: none

**Notes**: A bare class name with no verb doesn't match any dispatch keyword. Should ask whether the user wants to validate or update the class.

---

## create a batch class

- **Input**: `/sf-apex create batch class ProcessAccountsBatch to update Account ratings based on revenue`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `create` + `batch` routes to Create Apex. Should generate a Batch Apex class implementing `Database.Batchable<SObject>` with `start`, `execute`, and `finish` methods. Must check for existing class via `tooling_api_query`, generate the batch class plus a test class with bulk testing (251+ records), and deploy via `tooling_api_dml`. Should use `with sharing` and bulkified patterns.

---

## create a queueable class

- **Input**: `/sf-apex create queueable class SendWelcomeEmails to send emails after account creation`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `create` + `queueable` routes to Create Apex. Should generate a Queueable class implementing `Queueable` interface with an `execute` method. Must include proper error handling, bulkification, and a test class. The async decision matrix in SKILL.md identifies Queueable for complex logic with chaining needs.

---

## create an invocable method

- **Input**: `/sf-apex create class RecordProcessor with an invocable method to process records from Flow`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `create` + `class` with invocable method routes to Create Apex. Should generate a class with `@InvocableMethod` annotation, inner `Request` and `Response` classes with `@InvocableVariable`, and a corresponding test class. Follows the Flow Integration pattern in SKILL.md.

---

## update a trigger

- **Input**: `/sf-apex update AccountTrigger add after delete handling`
- **Dispatch**: Update Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: ApexClass, whereClause: Name = 'AccountTrigger'`
- **Should call**: `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `update` keyword routes to Update Apex. Should first try fetching as ApexClass; when not found, try ApexTrigger. After fetching the trigger body, modify to include after delete event, update the handler/action class if needed, validate, and redeploy via `tooling_api_dml`. Related handler classes may also need updating.

---

## update with no name specified

- **Input**: `/sf-apex update`
- **Dispatch**: Update Apex
- **Init required**: no
- **Init timing**: `after-menu`
- **Path**: `n/a`
- **Should NOT call**: `cirra_ai_init`, `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: yes (which class or trigger to update and what changes are needed)
- **Follow-up skills**: none

**Notes**: `update` keyword routes to Update Apex but no class name or description is provided. SKILL.md says "If no name is given, ask the user which class or trigger to update and what changes are needed." Must not proceed without user input.

---

## validate comma-separated list

- **Input**: `/sf-apex validate AccountService,ContactTrigger,OpportunityHelper`
- **Dispatch**: Validate Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: ApexClass, whereClause: Name IN ('AccountService', 'ContactTrigger', 'OpportunityHelper')`
- **Should NOT call**: `tooling_api_dml` (validation only, no deployment)
- **Should ask user**: no
- **Follow-up skills**: `/sf-apex update` (for classes with low scores)

**Notes**: Comma-separated list triggers bulk validation. Should fetch all as classes in one query, then try remaining names as triggers. Validate each body and produce a summary table sorted by score ascending. Falls back to individual queries if bulk fetch fails.

---

## validate a local trigger file

- **Input**: `/sf-apex validate /path/to/AccountTrigger.trigger`
- **Dispatch**: Validate Apex
- **Init required**: no (local file — no org needed for validation)
- **Init timing**: `n/a`
- **Path**: `fast`
- **Should NOT call**: `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: Local file path ending in `.trigger` means validate directly without fetching from org. The validation script runs locally using the `.trigger` extension. Same as local `.cls` validation — no MCP tools needed.

---

## review existing code — synonym for validate

- **Input**: `/sf-apex review AccountService`
- **Dispatch**: Validate Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: ApexClass, whereClause: Name = 'AccountService'`
- **Should NOT call**: `tooling_api_dml` (review/validation only, no deployment)
- **Should ask user**: no
- **Follow-up skills**: `/sf-apex update` (if issues are found worth fixing)

**Notes**: The dispatch table lists `review` and `score` as synonyms for `validate`. The `review` keyword should route to Validate Apex workflow. Same behavior as "validate a class by name" — fetch, score, report.

---

## create a selector class

- **Input**: `/sf-apex create selector AccountSelector for Account with methods for active accounts and by industry`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `create` + `selector` routes to Create Apex. Should generate a Selector class following the Selector pattern (centralized query logic, `with sharing`, `WITH USER_MODE` in SOQL). Must check for existing class, generate both the selector and its test class, and deploy via `tooling_api_dml`.

---

## score existing code — synonym for validate

- **Input**: `/sf-apex score OpportunityService`
- **Dispatch**: Validate Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `tooling_api_query`
- **Tool params**: `sObject: ApexClass, whereClause: Name = 'OpportunityService'`
- **Should NOT call**: `tooling_api_dml` (scoring only, no deployment)
- **Should ask user**: no
- **Follow-up skills**: `/sf-apex update` (if issues are found worth fixing)

**Notes**: The dispatch table lists `score` as a synonym for `validate`. Should route to Validate Apex, fetch the class body, run 150-point analysis, and return the scored report.

---

## create a service class

- **Input**: `/sf-apex create service class OpportunityService with methods for calculating pipeline value and updating stages`
- **Dispatch**: Create Apex
- **Init required**: yes
- **Init timing**: `before-workflow`
- **Path**: `full`
- **First tool**: `cirra_ai_init`
- **Should call**: `tooling_api_query`, `tooling_api_dml`
- **Should NOT call**: `metadata_create` (Apex uses Tooling API, not Metadata API)
- **Should ask user**: no
- **Follow-up skills**: none

**Notes**: `create` + `service` routes to Create Apex. Should generate a Service class following the Service layer pattern (business logic encapsulation, `with sharing`, bulkified methods). Must include a corresponding test class with PNB pattern (positive, negative, bulk) and deploy both via `tooling_api_dml`.
