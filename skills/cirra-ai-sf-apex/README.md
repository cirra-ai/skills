# cirra-ai-sf-apex

Generates and reviews Salesforce Apex code with 2025 best practices and 150-point scoring. Build production-ready, secure, and maintainable Apex.

## Features

- **Code Generation**: Create Apex classes, triggers (TAF), tests, batch jobs, queueables from requirements
- **Code Review**: Analyze existing Apex for best practices violations with actionable fixes
- **150-Point Scoring**: Automated validation across 8 categories
- **Template Library**: Pre-built patterns for common class types
- **LSP Integration**: Real-time syntax validation via Apex Language Server

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Quick Start

### 1. Invoke the skill

#### In Claude Cowork or Claude Code

Use one of the pre-built commands

```
/create-apex
/update-apex
/validate-apex
```

#### In other tools

```
Skill: cirra-ai-sf-apex
Request: "Create an AccountService class with CRUD methods"
```

### 2. Answer requirements questions

The skill will ask about:

- Class type (Service, Selector, Trigger, Batch, etc.)
- Primary purpose
- Target object(s)
- Test requirements

### 3. Review generated code

The skill generates:

- Main class with ApexDoc comments
- Corresponding test class with 90%+ coverage patterns
- Proper naming following conventions

## Scoring System (150 Points)

| Category       | Points | Focus                                                    |
| -------------- | ------ | -------------------------------------------------------- |
| Bulkification  | 25     | No SOQL/DML in loops, collection patterns                |
| Security       | 25     | CRUD/FLS checks, no injection, SOQL injection prevention |
| Testing        | 25     | Test coverage, assertions, negative tests                |
| Architecture   | 20     | SOLID principles, separation of concerns                 |
| Error Handling | 15     | Try-catch, custom exceptions, logging                    |
| Naming         | 15     | Consistent naming, ApexDoc comments                      |
| Performance    | 15     | Async patterns, efficient queries                        |
| Code Quality   | 10     | Clean code, no hardcoding                                |

**Thresholds**: 90+ | 80-89 | 70-79 | Block: <60

## Templates

| Template             | Use Case                          |
| -------------------- | --------------------------------- |
| `trigger.trigger`    | Trigger with TAF pattern          |
| `trigger-action.cls` | Trigger Actions Framework handler |
| `service.cls`        | Business logic service class      |
| `selector.cls`       | SOQL selector pattern             |
| `batch.cls`          | Batch Apex job                    |
| `queueable.cls`      | Queueable async job               |
| `test-class.cls`     | Test class with data factory      |

## Automatic Validation

Apex code is automatically validated before deployment:

- **Before deployment**: Critical issues (SOQL/DML in loops, injection risks) block deployment until fixed. Lower-severity issues are flagged as warnings.
- **AI anti-pattern detection**: Catches common AI-generated mistakes like invalid Java types, hallucinated methods, and unsafe Map access.

Use `/validate-apex` at any time for on-demand checks:

| Invocation                           | What happens                                           |
| ------------------------------------ | ------------------------------------------------------ |
| `/validate-apex MyClass`             | Fetches the class from your org and validates it       |
| `/validate-apex path/to/MyClass.cls` | Validates a local file                                 |
| `/validate-apex MyClass,OtherClass`  | Validates multiple classes with a summary table        |
| `/validate-apex All`                 | Validates all Apex classes in the org, sorted by score |

## Cross-Skill Integration

| Related Skill       | When to Use                                 |
| ------------------- | ------------------------------------------- |
| cirra-ai-sf-flow    | Create Flow to call @InvocableMethod        |
| cirra-ai-sf-lwc     | Create LWC to call @AuraEnabled controllers |
| cirra-ai-sf-testing | Run tests and analyze coverage              |
| cirra-ai-sf-deploy  | Deploy Apex to org                          |

## Documentation

- [Naming Conventions](references/naming-conventions.md)
- [Best Practices](references/best-practices.md)
- [Testing Guide](references/testing-guide.md)
- [Flow Integration](references/flow-integration.md)
- [Design Patterns](references/design-patterns.md)

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)

## For Contributors

### Validation Hooks

This skill ships Python validation scripts in `scripts/`. The pre-deployment hook is registered at the plugin level in `hooks/hooks.json` and is **type-scoped** — it inspects the metadata type in each MCP call and only validates Apex payloads.

#### Hook 1: `pre-mcp-validate.py` — pre-deployment (blocking)

Registered in `hooks/hooks.json` as a plugin-level PreToolUse hook. Fires before every `metadata_create`, `metadata_update`, and `tooling_api_dml` call. The script inspects the metadata type and only validates Apex payloads; non-Apex types pass through silently.

| Result                                              | Action                                       |
| --------------------------------------------------- | -------------------------------------------- |
| Critical/High issues (SOQL/DML in loops, injection) | Blocks deployment, surfaces issues to Claude |
| Score < 67%                                         | Allows deployment with advisory warning      |
| Pass                                                | Allows deployment with score summary         |
| Non-Apex type (Flow, CustomObject, etc.)            | Passes through silently                      |

#### Hook 2: `post-tool-validate.py` — post-write (advisory, not wired by default)

Available for PostToolUse `Write|Edit` integration but **not currently registered** in `hooks/hooks.json`. When enabled, runs a two-phase validation pipeline and outputs a scored report to the transcript.

**Phase 1 — `validate_apex.py`: 150-point static analysis**

| Category       | Points | What it checks                              |
| -------------- | ------ | ------------------------------------------- |
| Bulkification  | 25     | SOQL/DML inside loops                       |
| Security       | 25     | Sharing keywords, SOQL injection risk       |
| Testing        | 25     | Test methods, assertions, coverage patterns |
| Architecture   | 20     | SOLID principles, separation of concerns    |
| Clean Code     | 20     | PascalCase classes, camelCase methods       |
| Error Handling | 15     | Empty catch blocks, exception patterns      |
| Performance    | 10     | Async patterns, governor limit awareness    |
| Documentation  | 10     | ApexDoc on public methods                   |

**Phase 1.5 — `llm_pattern_validator.py`: LLM anti-pattern detection**

Catches mistakes that AI models commonly make when generating Apex:

- **Java types**: `ArrayList`, `HashMap`, `StringBuilder`, etc. (don't exist in Apex)
- **Hallucinated methods**: `stream()`, `collect()`, `addMilliseconds()`, `getOrDefault()`, `entrySet()`, `String.matches()`, etc.
- **Unsafe Map access**: `map.get(key).method()` without null check or `containsKey()`
- **SOQL field gaps**: queries with very few fields where subsequent code accesses many more

### Scripts

| Script                   | Purpose                                                                 |
| ------------------------ | ----------------------------------------------------------------------- |
| `validate_apex_cli.py`   | Standalone script used by `/validate-apex` — takes a file path argument |
| `pre-mcp-validate.py`    | PreToolUse hook adapter — translates hook stdin to mcp_validator format |
| `post-write-validate.py` | Legacy hook (Write only, no LLM check). Not wired in hooks.json         |
| `mcp_validator_cli.py`   | Manual pre-flight check for MCP metadata deployment calls               |

**Manual MCP pre-flight** — validate an Apex deployment payload before calling the MCP tool:

```bash
echo '{"tool":"metadata_create","params":{"type":"ApexClass","metadata":[{"fullName":"MyClass","body":"public class MyClass {}"}]}}' \
  | python scripts/mcp_validator_cli.py --format report
```

### Integration Testing (Actual Org)

This section is primarily for open-source contributors to this repository.
If you are using the skill as an end user, you do not need to run these tests.

To validate end-to-end behavior in a real Salesforce org (LLM prompt → MCP calls → deployed metadata → org verification), use:

- [`tests/test_apex_mcp_integration.md`](tests/test_apex_mcp_integration.md)

The protocol includes:

- a reusable prompt for running the test in an LLM session
- positive deployment scenarios
- negative scenarios (critical/advisory findings)
- verification queries and optional cleanup steps
