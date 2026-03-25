# cirra-ai-sf-kugamon

Kugamon CPQ quote management for Salesforce. Create, verify, and manage opportunities, quotes, and orders using the Kugamon package (kugo2p) via the Cirra AI MCP Server.

## Features

- **Quote Creation**: Create Kugamon quotes from opportunities with proper record type mapping
- **Package Detection**: Automatically detects kuga_sub (Kugamon Subscriptions) and adapts workflows
- **Line Item Management**: Handle product and service line separation with correct Renew field settings
- **Consistency Checking**: Keep quotes and opportunity line items in sync
- **Amount Interpretation**: Correctly interpret MRR, ARR, ACV, and TCV fields

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Quick Start

### 1. Invoke the skill

#### In Claude Cowork or Claude Code

```
Skill: cirra-ai-sf-kugamon
Request: "Create a renewal quote for opportunity Acme Corp - Annual Subscription"
```

#### In other tools

```
Skill: cirra-ai-sf-kugamon
Request: "Create a new business quote for this opportunity"
```

### 2. Answer discovery questions

The skill will:

- Connect to your org via `cirra_ai_init()`
- Detect whether kuga_sub (Subscriptions) is installed
- Validate billing address and contact on the account
- Query the opportunity and existing line items

### 3. Review created quote

The skill produces:

- A Kugamon quote with correct record type
- Auto-populated service lines and product lines
- Amount comparison between quote and opportunity
- Direct links to records

## Supported Workflows

| Workflow           | Description                                     |
| ------------------ | ----------------------------------------------- |
| New Business Quote | Create a quote for a new customer opportunity   |
| Renewal Quote      | Create a renewal quote for an existing contract |
| Expansion Quote    | Create an upsell/expansion quote                |
| Quote Sync         | Synchronize quote and opportunity line items    |
| Amount Analysis    | Interpret MRR, ARR, ACV, TCV fields correctly   |

## Key Objects

| Object       | API Name                           | Purpose            |
| ------------ | ---------------------------------- | ------------------ |
| Quote        | `kugo2p__SalesQuote__c`            | Main quote record  |
| Service Line | `kugo2p__SalesQuoteServiceLine__c` | Recurring services |
| Product Line | `kugo2p__SalesQuoteProductLine__c` | One-time products  |

## Cross-Skill Integration

| Related Skill        | When to Use                                   |
| -------------------- | --------------------------------------------- |
| sf-data              | Query opportunities, accounts, contacts       |
| cirra-ai-sf-metadata | Describe Kugamon custom objects and fields    |
| cirra-ai-sf-ordermgt | Order returns, cases, and post-sale lifecycle |
| cirra-ai-sf-diagram  | Visualize quote-to-order data model           |

## Documentation

- [Field Reference](references/field-reference.md)
- [Amount Fields Guide](references/amount-fields-guide.md)
- [Record Types](references/record-types.md)
- [Renew Field Guide](references/renew-field-guide.md)

## Resources

- [Kugamon YouTube Channel](https://www.youtube.com/playlist?list=PL63Lb4qcQBZcTLAkBTdyn08bKpHVpy7fx) — Video tutorials and walkthroughs

## Execution Modes

| Mode                      | When                                              | Speed   |
| ------------------------- | ------------------------------------------------- | ------- |
| `sfdx-repo`               | Working directory is an SFDX project              | Fastest |
| `cli`                     | Salesforce CLI installed and authed               | Fast    |
| `mcp-plus-code-execution` | MCP + filesystem + code execution (Cowork, Codex) | Medium  |
| `mcp-core`                | MCP only, no filesystem (chat interfaces)         | Slowest |

All Kugamon operations go through MCP tools regardless of mode.

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org with the Kugamon (kugo2p) package installed

## License

Cirra AI License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
