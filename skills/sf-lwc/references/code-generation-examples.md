## Code Generation Examples

### Example 1: Wire Service Component

**Request**: "Create an account list component that loads accounts using Apex wire service"

**Generated: accountList.js**

```javascript
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

**Generated: accountList.html**

```html
<template>
  <lightning-card title="Accounts" icon-name="standard:account">
    <template lwc:if="{isLoading}">
      <lightning-spinner variant="brand"></lightning-spinner>
    </template>

    <template lwc:else-if="{accounts}">
      <div class="slds-m-around_medium">
        <div class="slds-table slds-table_striped slds-table_bordered">
          <template for:each="{accounts}" for:item="account">
            <div key="{account.Id}" class="slds-truncate">{account.Name}</div>
          </template>
        </div>
      </div>
    </template>

    <template lwc:else-if="{error}">
      <div class="slds-notify slds-notify_alert slds-theme_alert-danger">{error.body.message}</div>
    </template>
  </lightning-card>
</template>
```

**Generated: accountList.css**

```css
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
  }
}
```

**Generated: childAccountSelector.js**

```javascript
import { LightningElement } from 'lwc';

export default class ChildAccountSelector extends LightningElement {
  handleSelect(event) {
    const selectedId = event.currentTarget.dataset.id;
    this.dispatchEvent(
      new CustomEvent('accountselected', {
        detail: { id: selectedId },
      })
    );
  }
}
```

---
