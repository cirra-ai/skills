import { LightningElement, wire, api } from 'lwc';
import getAccounts from '@salesforce/apex/CirraTest_AccountService.getAccounts';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { refreshApex } from '@salesforce/apex';

const COLUMNS = [
    { label: 'Name', fieldName: 'Name', type: 'text', sortable: true },
    { label: 'Industry', fieldName: 'Industry', type: 'text', sortable: true },
    {
        label: 'Annual Revenue',
        fieldName: 'AnnualRevenue',
        type: 'currency',
        sortable: true,
        typeAttributes: { currencyCode: 'USD' },
    },
    {
        label: 'Rating',
        fieldName: 'Rating',
        type: 'text',
        sortable: true,
        editable: true,
    },
    { label: 'Billing City', fieldName: 'BillingCity', type: 'text', sortable: true },
    {
        type: 'action',
        typeAttributes: {
            rowActions: [
                { label: 'Edit', name: 'edit' },
                { label: 'Delete', name: 'delete' },
            ],
            menuAlignment: 'auto',
            menuAlternativeText: 'Show actions',
        },
    },
];

export default class CirraTestAccountDashboard extends LightningElement {
    columns = COLUMNS;
    sortedBy;
    sortedDirection = 'asc';
    selectedRows = [];
    wiredResult;

    @wire(getAccounts)
    wiredAccounts(result) {
        this.wiredResult = result;
        if (result.data) {
            this.accounts = result.data;
            this.error = undefined;
        } else if (result.error) {
            this.error = result.error.body?.message ?? 'Unknown error';
            this.accounts = undefined;
        }
    }

    accounts;
    error;

    get isLoading() {
        return !this.accounts && !this.error;
    }

    get hasData() {
        return this.accounts && this.accounts.length > 0;
    }

    get isEmpty() {
        return this.accounts && this.accounts.length === 0;
    }

    handleSort(event) {
        const { fieldName, sortDirection } = event.detail;
        this.sortedBy = fieldName;
        this.sortedDirection = sortDirection;
        this.accounts = this.sortData(fieldName, sortDirection);
    }

    sortData(fieldName, direction) {
        const data = [...this.accounts];
        const multiplier = direction === 'asc' ? 1 : -1;
        return data.sort((a, b) => {
            const valA = a[fieldName] ?? '';
            const valB = b[fieldName] ?? '';
            if (valA > valB) return multiplier;
            if (valA < valB) return -multiplier;
            return 0;
        });
    }

    handleRowSelection(event) {
        this.selectedRows = event.detail.selectedRows;
    }

    handleRowAction(event) {
        const action = event.detail.action;
        const row = event.detail.row;
        switch (action.name) {
            case 'edit':
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Edit',
                        message: `Editing ${row.Name}`,
                        variant: 'info',
                    })
                );
                break;
            case 'delete':
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Delete',
                        message: `Deleting ${row.Name}`,
                        variant: 'warning',
                    })
                );
                break;
            default:
                break;
        }
    }

    async handleRefresh() {
        await refreshApex(this.wiredResult);
    }
}
