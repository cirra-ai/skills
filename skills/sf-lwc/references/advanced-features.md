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

**For TypeScript patterns and advanced configurations, see [references/component-patterns.md](references/component-patterns.md)**

---
