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
- **Dispatch**: (ambiguous — could be validate, update, or describe)
- **Init required**: no
- **Init timing**: `after-menu`
- **Path**: `n/a`
- **Should NOT call**: `cirra_ai_init`, `tooling_api_query`, `tooling_api_dml`
- **Should ask user**: yes
- **Follow-up skills**: none

**Notes**: A bare class name with no verb doesn't match any dispatch keyword. Should ask whether the user wants to validate, update, or view the class.
