# cirra-ai-sf-lwc

Lightning Web Components development skill with PICKLES architecture methodology, 165-point SLDS 2 scoring, and dark mode support. Build modern, accessible Salesforce UIs.

## Features

- **Component Scaffolding**: Generate complete LWC bundles (JS, HTML, CSS, meta.xml)
- **PICKLES Architecture**: Structured methodology for robust, maintainable components
- **165-Point Scoring**: SLDS 2 validation across 8 categories including dark mode readiness
- **Wire Service Patterns**: @wire decorators for Apex & GraphQL data fetching
- **Jest Testing**: Comprehensive unit test generation with async patterns
- **Spring '26 Features**: TypeScript, lwc:on directive, GraphQL mutations, Agentforce discoverability
- **SLDS Linting**: Automated validation via `post-tool-validate.py` on every Write/Edit

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Quick Start

### 1. Invoke the skill

#### In Claude Cowork or Claude Code

Use one of the pre-built commands

```
/create-lwc
/update-lwc
/validate-lwc
```

#### In other tools

```
Skill: cirra-ai-sf-lwc
Request: "Create a data table component for Account records"
```

### 2. Answer requirements questions

The skill will ask about:

- Component purpose and target (App Page, Record Page, Flow Screen)
- Data source (LDS, Apex, GraphQL)
- Accessibility requirements
- Dark mode / SLDS 2 compliance needs

### 3. Review generated component

The skill generates:

- JavaScript controller with decorators and wire adapters
- HTML template with SLDS 2 styling
- CSS with styling hooks (dark mode ready)
- meta.xml with targets and property configuration
- Jest test file with async patterns

## PICKLES Framework

```
P → Prototype    │ Validate ideas with wireframes & mock data
I → Integrate    │ Choose data source (LDS, Apex, GraphQL, API)
C → Composition  │ Structure component hierarchy & communication
K → Kinetics     │ Handle user interactions & event flow
L → Libraries    │ Leverage platform APIs & base components
E → Execution    │ Optimize performance & lifecycle hooks
S → Security     │ Enforce permissions, FLS, and data protection
```

## Scoring System (165 Points)

| Category            | Points | Focus                             |
| ------------------- | ------ | --------------------------------- |
| Component Structure | 25     | File organization, naming         |
| Data Layer          | 25     | Wire service, error handling      |
| UI/UX               | 25     | SLDS 2, responsiveness, dark mode |
| Accessibility       | 20     | WCAG, ARIA, keyboard navigation   |
| Testing             | 20     | Jest coverage, async patterns     |
| Performance         | 20     | Lazy loading, debouncing          |
| Events              | 15     | Component communication           |
| Security            | 15     | FLS, permissions                  |

**Thresholds**: 150+ (Production-ready) | 100-149 (Minor issues) | <100 (Needs work)

## Templates

| Template                 | Use Case                        |
| ------------------------ | ------------------------------- |
| `basic-component/`       | Simple component starter        |
| `form-component/`        | Form with validation            |
| `datatable-component/`   | Data table with sorting         |
| `modal-component/`       | Modal dialog pattern            |
| `flow-screen-component/` | Flow screen integration         |
| `graphql-component/`     | GraphQL data binding            |
| `typescript-component/`  | TypeScript support (Spring '26) |
| `message-channel/`       | Lightning Message Service       |

## Validation Hooks

This plugin ships Python validation scripts in `scripts/` that run automatically after every `Write` or `Edit` tool call on LWC files (`.html`, `.css`, `.js`). All hooks are **advisory** — they provide feedback but never block operations.

### Active hook: `post-tool-validate.py`

Triggered by `hooks/hooks.json` on `PostToolUse` for `Write|Edit`. Runs a two-phase SLDS 2 validation pipeline and outputs a scored report to the transcript.

**Phase 1 — `validate_slds.py`: SLDS 2 static analysis**

| Category            | Points | What it checks                                    |
| ------------------- | ------ | ------------------------------------------------- |
| SLDS Class Usage    | 25     | Valid `slds-*` class names, proper utility usage  |
| Accessibility       | 25     | ARIA labels/roles, alt-text, keyboard navigation  |
| Dark Mode Readiness | 25     | No hardcoded hex/RGB colors, CSS variables only   |
| SLDS Migration      | 20     | No deprecated SLDS 1 patterns or tokens           |
| Styling Hooks       | 20     | Proper `--slds-g-*` variable usage with fallbacks |
| Component Structure | 15     | Use of `lightning-*` base components              |
| Performance         | 10     | Efficient selectors, no `!important`              |
| PICKLES Compliance  | 25     | Architecture methodology adherence (optional)     |

**Phase 2 — `template_validator.py`: LWC template anti-pattern detection**

Catches mistakes AI models commonly make when generating LWC templates:

- **Inline expressions**: `{item.field + ' suffix'}` (not valid in LWC templates)
- **Ternary operators**: `{condition ? 'a' : 'b'}` (use getter or `lwc:if` instead)
- **Missing `key` on loops**: `for:each` without `key` attribute
- **Direct DOM access**: `document.querySelector` instead of `this.template.querySelector`
- **`@track` on primitives**: unnecessary in modern LWC

**Scoring** maps to 1–5 star rating with per-category breakdown and prioritised issue list.

### Other scripts

| Script                   | Purpose                                                     |
| ------------------------ | ----------------------------------------------------------- |
| `slds_linter_wrapper.py` | Wraps `@salesforce-ux/slds-linter` npm package if installed |
| `lwc-lsp-validate.py`    | LWC Language Server protocol validation                     |

## Cross-Skill Integration

| Related Skill        | When to Use                       |
| -------------------- | --------------------------------- |
| cirra-ai-sf-apex     | Create @AuraEnabled controllers   |
| cirra-ai-sf-flow     | Embed components in Flow screens  |
| cirra-ai-sf-metadata | Create Lightning Message Channels |
| cirra-ai-sf-deploy   | Deploy component to org           |

## Spring '26 Features (API 66.0)

- **lwc:on directive**: Dynamic event binding from JavaScript
- **GraphQL Mutations**: `executeMutation` for create/update/delete
- **Complex Expressions**: JS expressions in templates (Beta)
- **TypeScript Support**: `@salesforce/lightning-types` package
- **Agentforce Discoverability**: `lightning__agentforce` capability

## Documentation

- [Component Patterns](references/component-patterns.md) — Wire, GraphQL, Modal, Navigation, TypeScript
- [LMS Guide](references/lms-guide.md) — Lightning Message Service deep dive
- [Jest Testing](references/jest-testing.md) — Advanced testing patterns
- [Accessibility Guide](references/accessibility-guide.md) — WCAG, ARIA, focus management
- [Performance Guide](references/performance-guide.md) — Dark mode, lazy loading, optimization
- [LWC Best Practices](assets/lwc-best-practices.md)
- [Flow Integration](assets/flow-integration-guide.md)
- [State Management](assets/state-management.md)
- [Template Anti-Patterns](assets/template-anti-patterns.md)

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org
- API Version 65.0+ (Winter '26), 66.0+ recommended (Spring '26)
- Node.js 18+ (for Jest tests)

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
