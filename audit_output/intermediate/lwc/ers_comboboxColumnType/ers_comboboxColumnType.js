import {LightningElement, api} from 'lwc';

export default class ers_comboboxColumnType extends LightningElement {
    @api editable;
    @api fieldName;
    @api keyField;
    @api keyFieldValue;
    @api picklistValues;
    @api value;
    @api