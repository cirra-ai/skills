---
name: sf-lwc-cirra-ai
description: >
  Lightning Web Components development skill with PICKLES architecture methodology,
  component scaffolding, wire service patterns, event handling, Apex integration,
  GraphQL support, and Jest test generation. Build modern Salesforce UIs with
  proper reactivity, accessibility, dark mode compatibility, and performance patterns.
  Now powered by Cirra AI MCP Server for seamless metadata deployment.
license: MIT
metadata:
  version: "2.2.0"
  author: "Jag Valaiyapathy"
  scoring: "165 points across 8 categories (SLDS 2 + Dark Mode compliant)"
  mcp_enabled: true
  cirra_ai_required: true
---

# sf-lwc-cirra-ai: Lightning Web Components Development

Expert frontend engineer specializing in Lightning Web Components for Salesforce. Generate production-ready LWC components using the **PICKLES Framework** for architecture, with proper data binding, Apex/GraphQL integration, event handling, SLDS 2 styling, and comprehensive Jest tests. Deploy components directly via **Cirra AI MCP Server** for seamless org integration.

## Core Responsibilities

1. **Component Scaffolding**: Generate complete LWC bundles (JS, HTML, CSS, meta.xml)
2. **PICKLES Architecture**: Apply structured design methodology for robust components
3. **Wire Service Patterns**: Implement @wire decorators for data fetching (Apex & GraphQL)
4. **Apex/GraphQL Integration**: Connect LWC to backend with @AuraEnabled and GraphQL
5. **Event Handling**: Component communication (CustomEvent, LMS, pubsub)
6. **Lifecycle Management**: Proper use of connectedCallback, renderedCallback, etc.
7. **Jest Testing**: Generate comprehensive unit tests with advanced patterns
8. **Accessibility**: WCAG compliance with ARIA attributes, focus management
9. **Dark Mode**: SLDS 2 compliant styling with global styling hooks
10. **Performance**: Lazy loading, virtual scrolling, debouncing, efficient rendering
11. **Cirra AI Deployment**: Deploy via metadata_create with validation

---

## Cirra AI MCP Integration

The refactored sf-lwc skill uses **Cirra AI MCP Server** for deployment and metadata operations, replacing local CLI commands.

### Workflow Changes

| Task | Original (CLI) | New (Cirra AI) |
|------|---|---|
| **Generate Component** | `sf lightning generate component` | Claude generates files directly |
| **Deploy Component** | `sf project deploy start -m LightningComponentBundle` | `metadata_create` with type "LightningComponentBundle" |
| **Query Component Metadata** | `sf data query --use-tooling-api` | `tooling_api_query` for LightningComponentBundle |
| **Describe sObjects** | `sf sobject describe Account` | `sobject_describe` tool |
| **SOQL Queries** | `sf data query` | `soql_query` tool |
| **Run Jest Tests** | `sf lightning lwc test run` | Jest runs locally; tests are code-generated |

### Deployment Process

```
1. Claude generates LWC bundle files (JS, HTML, CSS, meta.xml)
   ↓
2. User reviews generated code (PICKLES + SLDS 2 validation)
   ↓
3. Claude calls cirra_ai_init() to authenticate with target org
   ↓
4. Claude calls metadata_create with:
   - type: "LightningComponentBundle"
   - metadata: [{ fullName: "c/componentName", ...bundle files }]
   ↓
5. Component deployed to org
   ↓
6. Validation: tooling_api_query to verify LightningComponentBundle metadata
```

### Quick Reference: MCP Tool Mapping

| Cirra AI Tool | Purpose | Parameters |
|---|---|---|
| `cirra_ai_init` | Authenticate with Salesforce org | `sf_user`, `cirra_ai_team`, `scope` |
| `metadata_create` | Deploy LWC bundle | `type`, `metadata`, `sf_user` |
| `metadata_list` | List existing components | `type`, `sf_user` |
| `sobject_describe` | Get object metadata | `sObject`, `sf_user` |
| `soql_query` | Execute SOQL queries | `sObject`, `fields`, `whereClause`, `sf_user` |
| `tooling_api_query` | Query metadata objects | `sObject`, `fields`, `whereClause`, `sf_user` |

### Authentication Example

```
User Request: "Deploy my accountDashboard component to my sandbox"

1. Claude: Calls cirra_ai_init(sf_user="user@example.com", scope="salesforce-metadata")
2. Org authentication established
3. Claude: Calls metadata_create(
     type="LightningComponentBundle",
     metadata=[{
       fullName: "c/accountDashboard",
       apiVersion: "66.0",
       description: "SLDS 2 compliant account dashboard",
       isExposed: true,
       ...
     }],
     sf_user="user@example.com"
   )
4. Component deployed successfully
```

---

## PICKLES Framework (Architecture Methodology)

The **PICKLES Framework** provides a structured approach to designing robust Lightning Web Components. Apply each principle during component design and implementation.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     🥒 PICKLES FRAMEWORK                            │
├─────────────────────────────────────────────────────────────────────┤
│  P → Prototype    │  Validate ideas with wireframes & mock data    │
│  I → Integrate    │  Choose data source (LDS, Apex, GraphQL, API)  │
│  C → Composition  │  Structure component hierarchy & communication │
│  K → Kinetics     │  Handle user interactions & event flow         │
│  L → Libraries    │  Leverage platform APIs & base components      │
│  E → Execution    │  Optimize performance & lifecycle hooks        │
│  S → Security     │  Enforce permissions, FLS, and data protection │
└─────────────────────────────────────────────────────────────────────┘
```

### Quick Reference

| Principle | Key Actions |
|-----------|-------------|
| **P - Prototype** | Wireframes, mock data, stakeholder review, separation of concerns |
| **I - Integrate** | LDS for single records, Apex for complex queries, GraphQL for related data |
| **C - Composition** | `@api` for parent→child, CustomEvent for child→parent, LMS for cross-DOM |
| **K - Kinetics** | Debounce search (300ms), disable during submit, keyboard navigation |
| **L - Libraries** | Use `lightning/*` modules, base components, avoid reinventing |
| **E - Execution** | Lazy load with `lwc:if`, cache computed values, avoid infinite loops |
| **S - Security** | `WITH SECURITY_ENFORCED`, input validation, FLS/CRUD checks |

**For detailed PICKLES implementation patterns, see [resources/component-patterns.md](resources/component-patterns.md)**

---

## Key Component Patterns

### Wire vs Imperative Apex Calls

| Aspect | Wire (@wire) | Imperative Calls |
|--------|--------------|------------------|
| **Execution** | Automatic / Reactive | Manual / Programmatic |
| **DML** | ❌ Read-Only | ✅ Insert/Update/Delete |
| **Data Updates** | ✅ Auto on param change | ❌ Manual refresh |
| **Control** | Low (framework decides) | Full (you decide) |
| **Caching** | ✅ Built-in | ❌ None |

**Quick Decision**: Use `@wire` for read-only display with auto-refresh. Use imperative for user actions, DML, or when you need control over timing.

**For complete comparison with code examples and decision tree, see [resources/component-patterns.md](resources/component-patterns.md#wire-vs-imperative-apex-calls)**

### Data Source Decision Tree

| Scenario | Recommended Approach |
|----------|---------------------|
| Single record by ID | Lightning Data Service (`getRecord`) |
| Simple record CRUD | `lightning-record-form` / `lightning-record-edit-form` |
| Complex queries | Apex with `@AuraEnabled(cacheable=true)` |
| Related records | GraphQL wire adapter |
| Real-time updates | Platform Events / Streaming API |
| External data | Named Credentials + Apex callout |

### Communication Patterns

| Pattern | Direction | Use Case |
|---------|-----------|----------|
| `@api` properties | Parent → Child | Pass data down |
| Custom Events | Child → Parent | Bubble actions up |
| Lightning Message Service | Any → Any | Cross-DOM communication |
| Pub/Sub | Sibling → Sibling | Same page, no hierarchy |

### Communication Pattern Quick Reference

```
┌─────────────────────────────────────────────────────────────────────┐
│              LWC COMMUNICATION - MADE SIMPLE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Parent → Child     │  [Parent] ─────→ [Child]   │  @api properties │
│                                                                     │
│  Child → Parent     │  [Child] ─────→ [Parent]   │  Custom Events   │
│                                                                     │
│  Sibling Components │  [A] → [Parent] → [B]      │  Events + @api   │
│                                                                     │
│  Unrelated          │  [Comp 1] ←─LMS─→ [Comp 2] │  Message Service │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Decision Tree**:
- Same parent? → Use parent as middleware (events up, `@api` down)
- Different DOM trees? → Use Lightning Message Service
- LWC ↔ Aura/VF? → Use Lightning Message Service

**For complete sibling communication code example, see [resources/component-patterns.md](resources/component-patterns.md#sibling-communication-via-parent)**

### Lifecycle Hook Guidance

| Hook | When to Use | Avoid |
|------|-------------|-------|
| `constructor()` | Initialize properties | DOM access (not ready) |
| `connectedCallback()` | Subscribe to events, fetch data | Heavy processing |
| `renderedCallback()` | DOM-dependent logic | Infinite loops, property changes |
| `disconnectedCallback()` | Cleanup subscriptions/listeners | Async operations |

**For complete code examples (Wire Service, GraphQL, Modal, Navigation, TypeScript), see:**
- [resources/component-patterns.md](resources/component-patterns.md) - Comprehensive patterns with full source code
- [resources/lms-guide.md](resources/lms-guide.md) - Lightning Message Service deep dive

---

## SLDS 2 Validation (165-Point Scoring)

The sf-lwc-cirra-ai skill includes automated SLDS 2 validation that ensures dark mode compatibility, accessibility, and modern styling.

| Category | Points | Key Checks |
|----------|--------|------------|
| **SLDS Class Usage** | 25 | Valid class names, proper `slds-*` utilities |
| **Accessibility** | 25 | ARIA labels, roles, alt-text, keyboard navigation |
| **Dark Mode Readiness** | 25 | No hardcoded colors, CSS variables only |
| **SLDS Migration** | 20 | No deprecated SLDS 1 patterns/tokens |
| **Styling Hooks** | 20 | Proper `--slds-g-*` variable usage |
| **Component Structure** | 15 | Uses `lightning-*` base components |
| **Performance** | 10 | Efficient selectors, no `!important` |
| **PICKLES Compliance** | 25 | Architecture methodology adherence (optional) |

**Scoring Thresholds**:
```
⭐⭐⭐⭐⭐ 150-165 pts → Production-ready, full SLDS 2 + Dark Mode
⭐⭐⭐⭐   125-149 pts → Good component, minor styling issues
⭐⭐⭐     100-124 pts → Functional, needs SLDS cleanup
⭐⭐       75-99 pts  → Basic functionality, SLDS issues
⭐         <75 pts   → Needs significant work
```

---

## Dark Mode Readiness

Dark mode is exclusive to SLDS 2 themes. Components must use global styling hooks to support light/dark theme switching.

### Dark Mode Checklist

- [ ] **No hardcoded hex colors** (`#FFFFFF`, `#333333`)
- [ ] **No hardcoded RGB/RGBA values**
- [ ] **All colors use CSS variables** (`var(--slds-g-color-*)`)
- [ ] **Fallback values provided** for SLDS 1 compatibility
- [ ] **No inline color styles** in HTML templates
- [ ] **Icons use SLDS utility icons** (auto-adjust for dark mode)

### Global Styling Hooks (Common)

| Category | SLDS 2 Variable | Purpose |
|----------|-----------------|---------|
| **Surface** | `--slds-g-color-surface-1` to `-4` | Background colors |
| **Container** | `--slds-g-color-surface-container-1` to `-3` | Card/section backgrounds |
| **Text** | `--slds-g-color-on-surface` | Primary text |
| **Border** | `--slds-g-color-border-1`, `-2` | Borders |
| **Brand** | `--slds-g-color-brand-1`, `-2` | Brand accent |
| **Spacing** | `--slds-g-spacing-0` to `-12` | Margins/padding |

**Example Migration**:
```css
/* SLDS 1 (Deprecated) */
.my-card { background-color: #ffffff; color: #333333; }

/* SLDS 2 (Dark Mode Ready) */
.my-card {
    background-color: var(--slds-g-color-surface-container-1, #ffffff);
    color: var(--slds-g-color-on-surface, #181818);
}
```

**For complete styling hooks reference and migration guide, see [resources/performance-guide.md](resources/performance-guide.md)**

---

## Jest Testing

Advanced testing patterns ensure robust, maintainable components. Tests are generated alongside component code.

### Essential Patterns

```javascript
// Render cycle helper
const runRenderingLifecycle = async (reasons = ['render']) => {
    while (reasons.length > 0) {
        await Promise.resolve(reasons.pop());
    }
};

// DOM cleanup
afterEach(() => {
    while (document.body.firstChild) {
        document.body.removeChild(document.body.firstChild);
    }
    jest.clearAllMocks();
});

// Proxy unboxing (LWS compatibility)
const unboxedData = JSON.parse(JSON.stringify(component.data));
expect(unboxedData).toEqual(expectedData);
```

### Test Template Structure

```javascript
import { createElement } from 'lwc';
import MyComponent from 'c/myComponent';
import getData from '@salesforce/apex/MyController.getData';

jest.mock('@salesforce/apex/MyController.getData', () => ({
    default: jest.fn()
}), { virtual: true });

describe('c-my-component', () => {
    afterEach(() => { /* DOM cleanup */ });

    it('displays data when loaded successfully', async () => {
        getData.mockResolvedValue(MOCK_DATA);
        const element = createElement('c-my-component', { is: MyComponent });
        document.body.appendChild(element);
        await runRenderingLifecycle();
        // Assertions...
    });
});
```

**For complete testing patterns (ResizeObserver polyfill, advanced mocks, event testing), see [resources/jest-testing.md](resources/jest-testing.md)**

### Local Test Execution

```bash
# All tests
npm run test

# Specific component
npm run test -- accountList

# With coverage
npm run test:coverage
```

---

## Accessibility

WCAG compliance is mandatory for all components.

### Quick Checklist

| Requirement | Implementation |
|-------------|----------------|
| **Labels** | `label` on inputs, `aria-label` on icons |
| **Keyboard** | Enter/Space triggers, Tab navigation |
| **Focus** | Visible indicator, logical order, focus traps in modals |
| **Live Regions** | `aria-live="polite"` for dynamic content |
| **Contrast** | 4.5:1 minimum for text |

```html
<!-- Accessible dynamic content -->
<div aria-live="polite" class="slds-assistive-text">
    {statusMessage}
</div>
```

**For comprehensive accessibility guide (focus management, ARIA patterns, screen reader testing), see [resources/accessibility-guide.md](resources/accessibility-guide.md)**

---

## Metadata Configuration

### meta.xml Targets

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Account Dashboard</masterLabel>
    <description>SLDS 2 compliant account dashboard with dark mode support</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
        <target>lightning__FlowScreen</target>
        <target>lightningCommunity__Page</target>
        <target>lightning__Dashboard</target> <!-- Spring '26 Beta -->
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
            </objects>
            <property name="title" type="String" default="Dashboard"/>
            <property name="maxRecords" type="Integer" default="10"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

---

## Deployment via Cirra AI

### Step 1: Generate Component

Request component generation with PICKLES framework adherence:

```
User: "Generate an accountDashboard LWC component for displaying account metrics"

Claude:
1. Generates accountDashboard.js (with @wire, event handling)
2. Generates accountDashboard.html (SLDS 2 structure)
3. Generates accountDashboard.css (dark mode variables)
4. Generates accountDashboard.meta.xml (targets and config)
5. Generates accountDashboard.test.js (Jest tests)
6. Validates against PICKLES framework (165-point score: ~155 pts)
7. Shows code preview to user
```

### Step 2: Deploy via metadata_create

```javascript
// Claude executes:
const metadata = [{
    fullName: 'c/accountDashboard',
    apiVersion: '66.0',
    isExposed: true,
    masterLabel: 'Account Dashboard',
    description: 'SLDS 2 compliant account metrics dashboard',
    source: 'export default class AccountDashboard extends LightningElement { ... }',
    html: '<template><div class="slds-box">...</div></template>',
    css: ':host { --slds-g-color-surface-1: var(--slds-c-card-color-background); }',
    meta: '<?xml version="1.0"?><LightningComponentBundle>...</LightningComponentBundle>'
}];

await metadata_create({
    type: 'LightningComponentBundle',
    metadata: metadata,
    sf_user: 'user@example.com'
});
```

### Step 3: Validate Deployment

```javascript
// Query deployed component via Tooling API:
const result = await tooling_api_query({
    sObject: 'LightningComponentBundle',
    fields: ['Id', 'DeveloperName', 'ApiVersion'],
    whereClause: "DeveloperName = 'accountDashboard'",
    sf_user: 'user@example.com'
});
```

---

## Code Generation Examples

### Example 1: Wire Service Component

**Request**: "Create an account list component that loads accounts using Apex wire service"

**Generated Files**:

```javascript
// accountList.js
import { LightningElement, wire, api } from 'lwc';
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

export default class AccountList extends LightningElement {
    @api maxRecords = 10;
    accounts;
    error;
    isLoading = true;

    @wire(getAccounts, { maxRecords: '$maxRecords' })
    wiredAccounts(result) {
        if (result.data) {
            this.accounts = result.data;
            this.error = undefined;
        } else if (result.error) {
            this.error = result.error;
            this.accounts = undefined;
        }
        this.isLoading = false;
    }
}
```

```html
<!-- accountList.html -->
<template>
    <lightning-card title="Accounts" icon-name="standard:account">
        <template lwc:if={isLoading}>
            <lightning-spinner variant="brand"></lightning-spinner>
        </template>

        <template lwc:else-if={accounts}>
            <div class="slds-m-around_medium">
                <div class="slds-table slds-table_striped slds-table_bordered">
                    <template for:each={accounts} for:item="account">
                        <div key={account.Id} class="slds-truncate">
                            {account.Name}
                        </div>
                    </template>
                </div>
            </div>
        </template>

        <template lwc:else-if={error}>
            <div class="slds-notify slds-notify_alert slds-theme_alert-danger">
                {error.body.message}
            </div>
        </template>
    </lightning-card>
</template>
```

```css
/* accountList.css */
:host {
    --slds-g-color-surface-1: var(--slds-c-card-color-background, #ffffff);
}

.slds-table {
    background-color: var(--slds-g-color-surface-1);
    color: var(--slds-g-color-on-surface);
}
```

### Example 2: Custom Event Communication

**Request**: "Create a parent-child component pair with custom event communication"

**Generated: parentComponent.js**
```javascript
import { LightningElement, track } from 'lwc';

export default class ParentComponent extends LightningElement {
    @track selectedAccountId;

    handleAccountSelection(event) {
        this.selectedAccountId = event.detail.id;
        console.log('Selected Account:', this.selectedAccountId);
    }
}
```

**Generated: parentComponent.html**
```html
<template>
    <div class="slds-box">
        <c-child-account-selector
            onaccountselected={handleAccountSelection}
        ></c-child-account-selector>

        <template lwc:if={selectedAccountId}>
            <p>Selected Account ID: {selectedAccountId}</p>
        </template>
    </div>
</template>
```

**Generated: childAccountSelector.js**
```javascript
import { LightningElement, track } from 'lwc';

export default class ChildAccountSelector extends LightningElement {
    @track selectedAccount;

    handleSelect(event) {
        this.selectedAccount = event.currentTarget.dataset.id;
        this.dispatchEvent(new CustomEvent('accountselected', {
            detail: { id: this.selectedAccount }
        }));
    }
}
```

---

## Flow Screen Integration

LWC components can be embedded in Flow Screens for custom UI experiences within guided processes.

### Key Concepts

| Mechanism | Direction | Purpose |
|-----------|-----------|---------|
| `@api` with `role="inputOnly"` | Flow → LWC | Pass context data |
| `FlowAttributeChangeEvent` | LWC → Flow | Return user selections |
| `FlowNavigationFinishEvent` | LWC → Flow | Programmatic Next/Back/Finish |
| `availableActions` | Flow → LWC | Check available navigation |

### Quick Example

```javascript
import { FlowAttributeChangeEvent, FlowNavigationFinishEvent } from 'lightning/flowSupport';

@api recordId;           // Input from Flow
@api selectedRecordId;   // Output to Flow
@api availableActions = [];

handleSelect(event) {
    this.selectedRecordId = event.detail.id;
    // CRITICAL: Notify Flow of the change
    this.dispatchEvent(new FlowAttributeChangeEvent(
        'selectedRecordId',
        this.selectedRecordId
    ));
}

handleNext() {
    if (this.availableActions.includes('NEXT')) {
        this.dispatchEvent(new FlowNavigationFinishEvent('NEXT'));
    }
}
```

**For complete Flow integration patterns, see:**
- [docs/flow-integration-guide.md](docs/flow-integration-guide.md)
- [docs/triangle-pattern.md](docs/triangle-pattern.md)

---

## Advanced Features

### TypeScript Support (Spring '26 - GA in API 66.0)

Lightning Web Components now support TypeScript with the `@salesforce/lightning-types` package.

```typescript
interface AccountRecord {
    Id: string;
    Name: string;
    Industry?: string;
}

export default class AccountList extends LightningElement {
    @api recordId: string | undefined;
    @track private _accounts: AccountRecord[] = [];

    @wire(getAccounts, { maxRecords: '$maxRecords' })
    wiredAccounts(result: WireResult<AccountRecord[]>): void {
        // Typed wire handling...
    }
}
```

**Requirements**: TypeScript 5.4.5+, `@salesforce/lightning-types` package

### LWC in Dashboards (Beta - Spring '26)

Components can be embedded as custom dashboard widgets.

```xml
<targets>
    <target>lightning__Dashboard</target>
</targets>
<targetConfigs>
    <targetConfig targets="lightning__Dashboard">
        <property name="metricType" type="String" label="Metric Type"/>
        <property name="refreshInterval" type="Integer" default="30"/>
    </targetConfig>
</targetConfigs>
```

**Note**: Requires enablement via Salesforce Customer Support

### Agentforce Discoverability (Spring '26 - GA in API 66.0)

Make components discoverable by Agentforce agents:

```xml
<capabilities>
    <capability>lightning__agentforce</capability>
</capabilities>
```

**Best Practices**:
- Clear `masterLabel` and `description`
- Detailed property descriptions
- Semantic naming conventions

**For TypeScript patterns and advanced configurations, see [resources/component-patterns.md](resources/component-patterns.md)**

---

## Cross-Skill Integration

| Skill | Use Case |
|-------|----------|
| sf-apex | Generate Apex controllers (`@AuraEnabled`, `@InvocableMethod`) |
| sf-flow | Embed components in Flow Screens, pass data to/from Flow |
| sf-testing | Generate Jest tests |
| sf-deploy | Deploy components (via Cirra AI metadata_create) |
| sf-metadata | Create message channels |

---

## Dependencies

**Required**:
- Cirra AI MCP Server connection (via `cirra_ai_init`)
- Target org with LWC support (API 45.0+)

**For Testing**:
- Node.js 18+
- Jest (`@salesforce/sfdx-lwc-jest`)

**For SLDS Validation**:
- `@salesforce-ux/slds-linter` (optional)

---

## Additional Resources

### Documentation Files

| Resource | Purpose |
|----------|---------|
| [resources/component-patterns.md](resources/component-patterns.md) | Complete code examples (Wire, GraphQL, Modal, Navigation, TypeScript) |
| [resources/lms-guide.md](resources/lms-guide.md) | Lightning Message Service deep dive |
| [resources/jest-testing.md](resources/jest-testing.md) | Advanced testing patterns (James Simone) |
| [resources/accessibility-guide.md](resources/accessibility-guide.md) | WCAG compliance, ARIA patterns, focus management |
| [resources/performance-guide.md](resources/performance-guide.md) | Dark mode migration, lazy loading, optimization |
| [docs/state-management.md](docs/state-management.md) | @track, Singleton Store, @lwc/state, Platform State Managers |
| [docs/template-anti-patterns.md](docs/template-anti-patterns.md) | LLM template mistakes (inline expressions, ternary operators) |
| [docs/async-notification-patterns.md](docs/async-notification-patterns.md) | Platform Events + empApi subscription patterns |
| [docs/flow-integration-guide.md](docs/flow-integration-guide.md) | Flow-LWC communication, apex:// type bindings |
| [docs/cirra-ai-deployment.md](docs/cirra-ai-deployment.md) | Cirra AI MCP Server integration guide |

### External References

- [PICKLES Framework (Salesforce Ben)](https://www.salesforceben.com/the-ideal-framework-for-architecting-salesforce-lightning-web-components/)
- [LWC Recipes (GitHub)](https://github.com/trailheadapps/lwc-recipes)
- [SLDS 2 Transition Guide](https://www.lightningdesignsystem.com/2e1ef8501/p/8184ad-transition-to-slds-2)
- [SLDS Styling Hooks](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-custom-properties.html)
- [James Simone - Composable Modal](https://www.jamessimone.net/blog/joys-of-apex/lwc-composable-modal/)
- [James Simone - Advanced Jest Testing](https://www.jamessimone.net/blog/joys-of-apex/advanced-lwc-jest-testing/)
- [Cirra AI MCP Server Docs](https://github.com/trailheadapps/cirra-ai-mcp-server)

---

## License

MIT License. See [LICENSE](LICENSE) file.
Copyright (c) 2024-2025 Jag Valaiyapathy
