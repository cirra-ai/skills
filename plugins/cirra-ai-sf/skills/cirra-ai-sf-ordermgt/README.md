# cirra-ai-sf-ordermgt

Salesforce Order Management for managing orders, returns, and support cases. Covers the full order-to-return-to-case lifecycle using the Cirra AI MCP Server.

## Features

- **Order Status**: Query order details, line items, and related Kugamon quotes
- **Return Creation**: Create ReturnOrder with line items from an existing Order
- **Return Label Email**: Send return shipping labels (requires flow deployment)
- **Case Management**: Create and update support cases linked to returns
- **Kugamon Integration**: Automatically enriches order data with quote context when kugo2p is installed

## Installation

For full installation instructions (Claude Cowork, OpenAI, browser), see the [root README](../../../../README.md).

## Quick Start

### 1. Invoke the skill

#### In Claude Cowork or Claude Code

```
Skill: cirra-ai-sf-ordermgt
Request: "Check the status of order 00000100"
```

#### In other tools

```
Skill: cirra-ai-sf-ordermgt
Request: "Create a return for order 00000100 — the product was defective"
```

### 2. Answer discovery questions

The skill will:

- Connect to your org via `cirra_ai_init()`
- Detect available objects (Order, ReturnOrder, Case)
- Detect Kugamon package (kugo2p) for quote enrichment
- Check for return label email infrastructure

### 3. Review results

The skill produces:

- Order status with line items and Kugamon quote context
- Return orders with proper status transitions
- Support cases linked to return orders
- Direct links to all records

## Supported Operations

| Operation               | Description                                        |
| ----------------------- | -------------------------------------------------- |
| Check Order Status      | Query order details, line items, related quotes    |
| Create Return           | Create ReturnOrder with line items and reason      |
| Email Return Label      | Send return label via flow or create Task fallback |
| Update Case Status      | Update case with transition validation             |
| Create Case from Return | Generate support case linked to a return order     |

## Key Objects

| Object           | API Name              | Purpose            |
| ---------------- | --------------------- | ------------------ |
| Order            | `Order`               | Sales order record |
| Order Item       | `OrderItem`           | Order line item    |
| Return Order     | `ReturnOrder`         | Return request     |
| Return Line Item | `ReturnOrderLineItem` | Return line item   |
| Case             | `Case`                | Support case       |

## Cross-Skill Integration

| Related Skill        | When to Use                                          |
| -------------------- | ---------------------------------------------------- |
| cirra-ai-sf-kugamon  | Quote creation, amount interpretation (MRR/ARR/ACV)  |
| cirra-ai-sf-data     | Advanced SOQL queries for orders, accounts, contacts |
| cirra-ai-sf-metadata | Create custom fields or objects for order management |
| cirra-ai-sf-flow     | Build notification or return label email flows       |
| cirra-ai-sf-diagram  | Visualize order-to-return-to-case data model         |

## Documentation

- [Field Reference](references/field-reference.md)
- [Status Transitions](references/status-transitions.md)
- [Metadata Setup](references/metadata-setup.md)

## Requirements

- Claude Cowork or Claude Code with skill plugins enabled
- Cirra AI MCP Server
- Target Salesforce org with Order Management or Service Cloud (for returns)

## License

Cirra AI License — see [LICENSE](LICENSE) for details.

This plugin is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc. The plugin and its contents are provided independently and are not part of the Cirra AI product itself. Use of Cirra AI is subject to its own separate terms and conditions.
