# sf-flow

Creates and validates Salesforce Flows with 110-point scoring and Summer '26 best practices. Build production-ready, performant, and secure flows.

## Features

- **Flow Generation**: Create record-triggered, screen, autolaunched, and scheduled flows
- **110-Point Scoring**: Automated validation across 6 categories
- **Template Library**: Pre-built patterns for common flow types
- **Bulk Safety**: Automatic checks for 251+ record handling
- **Element Library**: Complete Wait, Loop, Get Records, Transform patterns
- **Transform vs Loop Guide**: Decision pattern for choosing Transform (data mapping) vs Loop (per-record decisions)
- **Flow Quick Reference**: Comprehensive cheat sheet with flow type selection trees and element reference

## Installation

For full installation instructions (various AI tools), see the [root README](../../../../README.md).

## Quick Start

### 1. Invoke the skill

#### Installation

Invoke the unified skill:

```
/sf-flow
/sf-flow create before-save flow for Account
/sf-flow validate Auto_Lead_Assignment
```

#### In other tools

```
Skill: sf-flow
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

| Category                       | Points | Focus                                                                    |
| ------------------------------ | ------ | ------------------------------------------------------------------------ |
| Design & Naming                | 20     | Flow/element/variable naming conventions, flow description               |
| Logic & Structure              | 20     | DML/SOQL/Apex in loops, decision complexity, Transform vs Loop           |
| Architecture & Orchestration   | 15     | Subflow usage, unused variables, orphaned elements, Auto-Layout          |
| Performance & Bulk Safety      | 20     | Get Records filters, same-object queries, hardcoded IDs, SOQL/DML counts |
| Error Handling & Observability | 20     | Infinite-loop risk, fault connectors, null checks, error logging         |
| Security & Governance          | 15     | System mode, sensitive fields, active scheduled flows, API version       |

(Same categories and weights as `scripts/validate_flow.py`.)

**Deploy gate**: CRITICAL/HIGH issues block deployment; a score below 88 (80%) is a hard stop unless the user explicitly accepts it

## Key Insights

| Rule                  | Details                                                                |
| --------------------- | ---------------------------------------------------------------------- |
| Before vs After Save  | Before: same-record updates (no DML). After: related records, callouts |
| Test with 251 records | Batch boundary at 200. Test bulk behavior                              |
| $Record context       | Single record, not a collection. Platform handles batching             |
| Transform vs Loop     | Transform: data mapping (30-50% faster). Loop: per-record decisions    |
| Deploy as Draft       | Always deploy flows as Draft first, then activate                      |

## Templates

All templates live in `assets/` (element snippets in `assets/elements/`, reusable subflows in `assets/subflows/`):

| Template                             | Use Case                              |
| ------------------------------------ | ------------------------------------- |
| `record-triggered-before-save.xml`   | Field auto-population (same record)   |
| `record-triggered-after-save.xml`    | Related record updates, notifications |
| `record-triggered-before-delete.xml` | Pre-delete validation / cleanup       |
| `screen-flow-template.xml`           | User interaction flows                |
| `screen-flow-with-lwc.xml`           | Screen flow embedding an LWC          |
| `autolaunched-flow-template.xml`     | Background automation / subflows      |
| `scheduled-flow-template.xml`        | Time-based automation                 |
| `platform-event-flow-template.xml`   | Platform event subscribers            |
| `apex-action-template.xml`           | Calling an Apex `@InvocableMethod`    |
| `wait-template.xml`                  | Wait element patterns                 |

For `metadata_create` deployments start from `assets/json-deployment-reference.md` — the XML templates are structural references.

## Cross-Skill Integration

| Related Skill   | When to Use                                                             |
| --------------- | ----------------------------------------------------------------------- |
| sf-apex         | Create @InvocableMethod for complex logic or external callouts          |
| sf-lwc          | Create screen components for custom UI                                  |
| sf-metadata     | Deploy custom objects BEFORE flows                                      |
| sf-connect-rest | Named Credentials / External Services an HTTP Callout action depends on |
| sf-data         | Create test data AFTER the flow is deployed                             |

sf-flow deploys its own flows through the Cirra AI MCP Server (`metadata_create` / `metadata_update`, then `metadata_update` on `FlowDefinition` to activate) — there is no separate deploy skill.

## Orchestration Order

```
sf-metadata → sf-flow → sf-data
```

Always deploy custom objects/fields BEFORE flows that reference them.

## Documentation

- [Transform vs Loop Guide](references/transform-vs-loop-guide.md) - When to use each element
- [Flow Quick Reference](references/flow-quick-reference.md) - Comprehensive cheat sheet
- [Flow Best Practices](references/flow-best-practices.md) - Performance and design patterns
- [LWC Integration](references/lwc-integration-guide.md) - Screen components
- [Testing Guide](references/testing-guide.md) - Validation strategies

## Validation

Validation is **manual and required** before every Flow deployment. The skill
ships a `PreToolUse` hook script (`scripts/pre-mcp-validate.py`), but **it is
not wired up in every runtime environment** — there is no `hooks/hooks.json`
shipped with this skill and the script does not run unless your host registers
it. Until you have confirmed the hook is registered for your host, run the
validator manually before every `metadata_create`, `metadata_update`, or
`tooling_api_dml` call on a Flow:

```bash
python3 scripts/validate_flow_cli.py <path-to-flow.flow-meta.xml>
```

The validator blocks deployment for CRITICAL/HIGH issues (DML in loops, missing
fault paths on any fallible element, invalid resource properties). See the
four-question self-check in `SKILL.md` for the contract.

Use `/sf-flow validate` at any time for on-demand checks:

| Invocation                                                           | What happens                                    |
| -------------------------------------------------------------------- | ----------------------------------------------- |
| `/sf-flow validate Auto_Lead_Assignment`                             | Fetches the flow from your org and validates it |
| `/sf-flow validate force-app/.../Auto_Lead_Assignment.flow-meta.xml` | Validates a local file                          |
| `/sf-flow validate Auto_Lead_Assignment,Screen_Case_Intake`          | Validates multiple flows with a summary table   |
| `/sf-flow validate All`                                              | Validates all flows in the org, sorted by score |

## Execution Modes

| Mode                      | When                                              | Speed   |
| ------------------------- | ------------------------------------------------- | ------- |
| `sfdx-repo`               | Working directory is an SFDX project              | Fastest |
| `cli`                     | Salesforce CLI installed and authed               | Fast    |
| `mcp-plus-code-execution` | MCP + filesystem + code execution (Cowork, Codex) | Medium  |
| `mcp-core`                | MCP only, no filesystem (chat interfaces)         | Slowest |

All Flow operations go through MCP tools regardless of mode. The mode
determines how large responses are handled and whether local tooling is
available.

## Requirements

- An AI coding tool with skill/plugin support
- Cirra AI MCP Server
- Target Salesforce org
  - API Version 67.0+ (Summer '26)

## For Contributors

### Validation Hooks

This skill ships Python validation scripts in `scripts/`. A `PreToolUse` hook
adapter (`scripts/pre-mcp-validate.py`) is shipped for hosts that want to wire
it up, but **no `hooks/hooks.json` is shipped with the skill** and registration
is the host's responsibility. Treat the validator as manual until you have
confirmed your host runs the hook.

#### Hook 1: `pre-mcp-validate.py` — pre-deployment (script only, not auto-registered)

Designed for use as a plugin-level PreToolUse hook against `metadata_create`,
`metadata_update`, and `tooling_api_dml`. The script inspects the metadata type
and only validates Flow payloads; non-Flow types pass through silently. It is
**not registered** by the skill itself — register it in your host's
`hooks.json` if you want validator output surfaced before each Flow deployment.

The hook is **advisory**: every outcome returns `permissionDecision: allow`
and emits an `additionalContext` message. Nothing is blocked at the protocol
level — the agent is expected to read the message and choose to stop before
calling the deployment tool. If you need hard blocking, fork the hook to
return `deny`/`ask` when CRITICAL/HIGH issues are present.

| Result                                                   | Action                                                     |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| Critical/High issues (DML in loops, missing fault paths) | Allows the call; emits a 🚨 critical-issue context message |
| Score < 80% (< 88/110)                                   | Allows the call; emits a ⚠️ advisory context message       |
| Pass                                                     | Allows the call; emits a ✅ score-summary context message  |
| Non-Flow type (ApexClass, CustomObject, etc.)            | Passes through silently (no context emitted)               |

#### Hook 2: `post-tool-validate.py` — post-write (advisory, not wired by default)

Available for PostToolUse `Write|Edit` integration. The skill does not ship a `hooks.json`, so this is host-side opt-in. When registered, runs `EnhancedFlowValidator` on any `.flow-meta.xml` file and outputs a scored report to the transcript.

**`validate_flow.py`: 110-point static analysis**

| Category                       | Points | What it checks                                                                           |
| ------------------------------ | ------ | ---------------------------------------------------------------------------------------- |
| Design & Naming                | 20     | Flow name prefix, element/variable naming conventions, `Copy_of` names, flow description |
| Logic & Structure              | 20     | DML / SOQL / Apex actions inside loops, formula-in-loop CPU, decision count, Transform   |
| Architecture & Orchestration   | 15     | Subflow usage, unused variables, orphaned elements, Auto-Layout, flow size               |
| Performance & Bulk Safety      | 20     | Get Records filters, same-object queries, hardcoded IDs/URLs, SOQL/DML counts            |
| Error Handling & Observability | 20     | Infinite-loop risk, fault connectors on fallible elements, null checks, error logging    |
| Security & Governance          | 15     | System mode, sensitive fields, `storeOutputAutomatically` in system mode, API version    |

### Scripts

| Script                   | Purpose                                                                    |
| ------------------------ | -------------------------------------------------------------------------- |
| `validate_flow_cli.py`   | Standalone CLI used by `/sf-flow validate` — takes a file path argument    |
| `pre-mcp-validate.py`    | PreToolUse hook adapter — translates hook stdin to FlowMCPValidator format |
| `post-write-validate.py` | Legacy hook (Write only). Not wired in hooks.json                          |
| `mcp_validator_cli.py`   | Manual pre-flight check for MCP Flow deployment calls                      |

## License

MIT License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.

For credits see [CREDITS](CREDITS.md)
