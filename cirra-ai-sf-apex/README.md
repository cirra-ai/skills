# cirra-ai-sf-apex

Generates and reviews Salesforce Apex code with 2025 best practices and 150-point scoring. Build production-ready, secure, and maintainable Apex.

## Features

- **Code Generation**: Create Apex classes, triggers (TAF), tests, batch jobs, queueables from requirements
- **Code Review**: Analyze existing Apex for best practices violations with actionable fixes
- **150-Point Scoring**: Automated validation across 8 categories
- **Template Library**: Pre-built patterns for common class types
- **LSP Integration**: Real-time syntax validation via Apex Language Server

## Installation

```bash
# Install standalone
claude /plugin install github:cirra-ai/skills/cirra-ai-sf-apex

# Or install the complete Cirra AI skills suite
claude /plugin install github:cirra-ai/skills
```

## Quick Start

### 1. Invoke the skill

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

## Validation Hooks

This plugin ships Python validation scripts in `hooks/scripts/` that run automatically after every `Write` or `Edit` tool call on Apex files (`.cls`, `.trigger`). All hooks are **advisory** — they provide feedback but never block operations.

### Active hook: `post-tool-validate.py`

Triggered by `hooks/hooks.json` on `PostToolUse` for `Write|Edit`. Runs a two-phase validation pipeline and outputs a scored report to the transcript.

**Phase 1 — `validate_apex.py`: 150-point static analysis**

| Category | Points | What it checks |
|---|---|---|
| Bulkification | 25 | SOQL/DML inside loops |
| Security | 25 | Sharing keywords, SOQL injection risk |
| Testing | 25 | Test methods, assertions, coverage patterns |
| Architecture | 20 | SOLID principles, separation of concerns |
| Clean Code | 20 | PascalCase classes, camelCase methods |
| Error Handling | 15 | Empty catch blocks, exception patterns |
| Performance | 10 | Async patterns, governor limit awareness |
| Documentation | 10 | ApexDoc on public methods |

**Phase 1.5 — `llm_pattern_validator.py`: LLM anti-pattern detection**

Catches mistakes that AI models commonly make when generating Apex:

- **Java types**: `ArrayList`, `HashMap`, `StringBuilder`, etc. (don't exist in Apex)
- **Hallucinated methods**: `stream()`, `collect()`, `addMilliseconds()`, `getOrDefault()`, `entrySet()`, `String.matches()`, etc.
- **Unsafe Map access**: `map.get(key).method()` without null check or `containsKey()`
- **SOQL field gaps**: queries with very few fields where subsequent code accesses many more

**Phase 2 — Scoring and output**

Score is mapped to a 1–5 star rating (Excellent / Very Good / Good / Needs Work / Critical Issues) with a per-category breakdown and prioritised issue list (up to 12 issues, sorted by severity).

### Other scripts

| Script | Purpose |
|---|---|
| `post-write-validate.py` | Legacy version of the hook (Write only, no LLM check). Not wired in hooks.json |
| `apex-lsp-validate.py` | Apex Language Server syntax validation. Requires VS Code + Salesforce Extension Pack + Java 11+. Not wired by default |
| `mcp_validator_cli.py` | Manual pre-flight check for MCP metadata deployment calls |

**Manual MCP pre-flight** — validate an Apex deployment payload before calling the MCP tool:

```bash
echo '{"tool":"metadata_create","params":{"type":"ApexClass","metadata":[{"fullName":"MyClass","body":"public class MyClass {}"}]}}' \
  | python hooks/scripts/mcp_validator_cli.py --format report
```

## Cross-Skill Integration

| Related Skill | When to Use                                 |
| ------------- | ------------------------------------------- |
| cirra-ai-sf-flow       | Create Flow to call @InvocableMethod        |
| cirra-ai-sf-lwc        | Create LWC to call @AuraEnabled controllers |
| cirra-ai-sf-testing    | Run tests and analyze coverage              |
| cirra-ai-sf-deploy     | Deploy Apex to org                          |

## Documentation

- [Naming Conventions](docs/naming-conventions.md)
- [Best Practices](docs/best-practices.md)
- [Testing Guide](docs/testing-guide.md)
- [Flow Integration](docs/flow-integration.md)
- [Design Patterns](docs/design-patterns.md)

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
