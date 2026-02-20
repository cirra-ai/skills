# cirra-ai-sf-flow

Creates and validates Salesforce Flows with 110-point scoring and Winter '26 best practices. Build production-ready, performant, and secure flows.

## Features

- **Flow Generation**: Create record-triggered, screen, autolaunched, and scheduled flows
- **110-Point Scoring**: Automated validation across 6 categories
- **Template Library**: Pre-built patterns for common flow types
- **Bulk Safety**: Automatic checks for 251+ record handling
- **Element Library**: Complete Wait, Loop, Get Records, Transform patterns
- **Transform vs Loop Guide**: Decision pattern for choosing Transform (data mapping) vs Loop (per-record decisions)
- **Flow Quick Reference**: Comprehensive cheat sheet with flow type selection trees and element reference

## Installation

```bash
# Install standalone
claude /plugin install github:cirra-ai/skills/cirra-ai-sf-flow

# Or install the complete Cirra AI skills suite
claude /plugin install github:cirra-ai/skills
```

## Quick Start

### 1. Invoke the skill

```
Skill: cirra-ai-sf-flow
Request: "Create a before-save flow to auto-populate Account fields"
```

### 2. Answer requirements questions

The skill will ask about:

- Flow type (Record-Triggered, Screen, Autolaunched, etc.)
- Trigger object and timing (Before/After Save)
- Entry conditions
- Actions needed

### 3. Review generated flow

The skill generates:

- Complete Flow XML metadata
- Proper element naming with alphabetical ordering
- Entry conditions and fault connectors

## Scoring System (110 Points)

| Category       | Points | Focus                                         |
| -------------- | ------ | --------------------------------------------- |
| Bulkification  | 25     | No DML/queries in loops, collection variables |
| Entry Criteria | 20     | Selective, indexed fields                     |
| Naming         | 20     | Consistent element names, descriptions        |
| Fault Handling | 20     | Fault paths on all DML/queries                |
| Performance    | 15     | Minimal elements, efficient paths             |
| Documentation  | 10     | Element descriptions, flow description        |

**Minimum Score**: 88 (80%) for deployment

## Key Insights

| Rule                  | Details                                                                |
| --------------------- | ---------------------------------------------------------------------- |
| Before vs After Save  | Before: same-record updates (no DML). After: related records, callouts |
| Test with 251 records | Batch boundary at 200. Test bulk behavior                              |
| $Record context       | Single record, not a collection. Platform handles batching             |
| Transform vs Loop     | Transform: data mapping (30-50% faster). Loop: per-record decisions    |
| Deploy as Draft       | Always deploy flows as Draft first, then activate                      |

## Templates

| Template                    | Use Case               |
| --------------------------- | ---------------------- |
| `before-save-template.xml`  | Field auto-population  |
| `after-save-template.xml`   | Related record updates |
| `screen-flow-template.xml`  | User interaction flows |
| `autolaunched-template.xml` | Background automation  |
| `scheduled-template.xml`    | Time-based automation  |
| `wait-template.xml`         | Wait element patterns  |

## Cross-Skill Integration

| Related Skill        | When to Use                               |
| -------------------- | ----------------------------------------- |
| cirra-ai-sf-apex     | Create @InvocableMethod for complex logic |
| cirra-ai-sf-lwc      | Create screen components for custom UI    |
| cirra-ai-sf-metadata | Deploy custom objects BEFORE flows        |
| cirra-ai-sf-deploy   | Deploy flows to org                       |

## Orchestration Order

```
cirra-ai-sf-metadata → cirra-ai-sf-flow → cirra-ai-sf-deploy → cirra-ai-sf-data
```

Always deploy custom objects/fields BEFORE flows that reference them.

## Documentation

- [Transform vs Loop Guide](docs/transform-vs-loop-guide.md) - When to use each element
- [Flow Quick Reference](docs/flow-quick-reference.md) - Comprehensive cheat sheet
- [Flow Best Practices](docs/flow-best-practices.md) - Performance and design patterns
- [LWC Integration](docs/lwc-integration-guide.md) - Screen components
- [Wait Patterns](docs/wait-patterns.md) - Delay and scheduling
- [Testing Guide](docs/testing-guide.md) - Validation strategies

## Validation Hooks

This plugin ships Python validation scripts in `hooks/scripts/` that run automatically at two points. Validation is **skill-scoped** — the pre-deployment hook only registers while the cirra-ai-sf-flow skill is active, so there is no overhead when doing unrelated work.

Use [`/validate-flow`](#validate-flow-command) for on-demand checks at any time.

### Hook 1: `pre-mcp-validate.py` — pre-deployment (blocking)

Defined in `skills/cirra-ai-sf-flow/SKILL.md` frontmatter as a **skill-scoped PreToolUse hook**. Fires before every `metadata_create`, `metadata_update`, and `tooling_api_dml` call while the Flow skill is active.

| Result                                                   | Action                                       |
| -------------------------------------------------------- | -------------------------------------------- |
| Critical/High issues (DML in loops, missing fault paths) | Blocks deployment, surfaces issues to Claude |
| Score < 80% (< 88/110)                                   | Allows deployment with advisory warning      |
| Pass                                                     | Allows deployment with score summary         |
| Non-Flow type (ApexClass, CustomObject, etc.)            | Passes through silently                      |

### Hook 2: `post-tool-validate.py` — post-write (advisory)

Triggered by `hooks/hooks.json` on `PostToolUse` for `Write|Edit`. Runs `EnhancedFlowValidator` on any `.flow-meta.xml` file written to the local working folder and outputs a scored report to the transcript.

**`validate_flow.py`: 110-point static analysis**

| Category                       | Points | What it checks                                                      |
| ------------------------------ | ------ | ------------------------------------------------------------------- |
| Design & Naming                | 25     | Element naming conventions, alphabetical ordering, flow description |
| Logic & Structure              | 20     | Entry criteria, flow variables, decision logic                      |
| Architecture & Orchestration   | 20     | Flow type appropriateness, subflow usage, API versioning            |
| Performance & Bulk Safety      | 20     | DML/queries in loops, 251-record bulk handling, collection patterns |
| Error Handling & Observability | 15     | Fault connectors on all DML/queries, unhandled paths                |
| Security & Governance          | 10     | Sharing mode, hardcoded IDs, API version ≥ 59.0                     |

**Scoring thresholds**: 88+ (80%) required for deployment. Score maps to star rating (Excellent / Very Good / Good / Needs Work / Critical Issues) with per-category breakdown and prioritised issue list.

## /validate-flow Command

On-demand validation command. Accepts a flow API name, local file path, comma-separated list, or `--all`:

| Invocation                                                        | What happens                                                               |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `/validate-flow Auto_Lead_Assignment`                             | Fetches `Auto_Lead_Assignment` XML from org via `metadata_read`, validates |
| `/validate-flow force-app/.../Auto_Lead_Assignment.flow-meta.xml` | Reads local file, validates                                                |
| `/validate-flow Auto_Lead_Assignment,Screen_Case_Intake`          | Validates each in sequence, shows summary table                            |
| `/validate-flow --all`                                            | Validates all Flow records in the org, summary sorted by score             |

The command uses `validate_flow_cli.py` under the hood — the same 110-point pipeline as the hooks.

### Other scripts

| Script                   | Purpose                                                                    |
| ------------------------ | -------------------------------------------------------------------------- |
| `validate_flow_cli.py`   | Standalone CLI used by `/validate-flow` — takes a file path argument       |
| `pre-mcp-validate.py`    | PreToolUse hook adapter — translates hook stdin to FlowMCPValidator format |
| `post-write-validate.py` | Legacy hook (Write only). Not wired in hooks.json                          |
| `mcp_validator_cli.py`   | Manual pre-flight check for MCP Flow deployment calls                      |

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org
  - API Version 65.0+ (Winter '26)

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
