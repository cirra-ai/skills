import { LightningElement,api,track } from 'lwc';
import searchRecords from '@salesforce/apex/{!ID:@@@sfdc=01pKh00000BpSQk=sfdc@@@}.getRecords';
import saveResultApex from '@salesforce/apex/{!ID:@@@sfdc=01pKh00000BpSQk=sfdc@@@}.saveResult';
import { ShowT