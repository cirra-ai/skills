# Phase 1: Setup — Populate Salesforce Org

Run these steps sequentially. Each step lists the command or MCP tool call to
execute and the expected result. Record actual results in the **Result** column.

---

## 1.1 Initialize MCP Connection

```
cirra_ai_init()
```

| Check | Expected | Result |
|-------|----------|--------|
| Connection established | Success message with org alias | |
| Default org confirmed | User prompted to confirm or select | |

---

## 1.2 Describe Target Objects

Verify standard objects exist and discover field metadata before creating data.

```
sobject_describe(sObject="Account")
sobject_describe(sObject="Contact")
sobject_describe(sObject="Opportunity")
sobject_describe(sObject="Case")
sobject_describe(sObject="Lead")
sobject_describe(sObject="Task")
sobject_describe(sObject="Event")
```

| Check | Expected | Result |
|-------|----------|--------|
| All 7 objects described | Metadata returned for each | |
| Required fields identified | Name (Account), LastName (Contact), StageName+CloseDate (Opp), etc. | |
| Field types confirmed | Industry=Picklist, AnnualRevenue=Currency, etc. | |

---

## 1.3 Create Apex — Trigger + TAF Action (Account)

**Command**: `/create-apex`

**Prompt**: Create a before-insert trigger action for Account that auto-populates
the Description field with a summary of Industry and BillingCity, and defaults
Rating to "Warm" when not set.

Expected artifacts:
- `CirraTest_AccountTrigger` (thin trigger using MetadataTriggerHandler)
- `TA_CirraTest_Account_SetDefaults` (trigger action class)
- `TA_CirraTest_Account_SetDefaultsTest` (test class)

| Check | Expected | Result |
|-------|----------|--------|
| Trigger created | MetadataTriggerHandler.run() pattern | |
| Action class created | Implements TriggerAction.BeforeInsert | |
| Test class created | PNB pattern, 201+ bulk test | |
| No SOQL/DML in trigger body | Body delegates to MetadataTriggerHandler only | |
| Validation score | >= 90/150 | |
| Deployment successful | tooling_api_dml returns success | |

---

## 1.4 Create Apex — Service Class (Account)

**Command**: `/create-apex`

**Prompt**: Create an AccountService class with methods to: (1) get accounts by
IDs with related contacts, (2) create accounts with validation, (3) update
account annual revenue in bulk, and (4) transfer account ownership. Include a
corresponding test class.

Expected artifacts:
- `CirraTest_AccountService`
- `CirraTest_AccountServiceTest`

| Check | Expected | Result |
|-------|----------|--------|
| Service class has `with sharing` | Yes | |
| Uses USER_MODE in SOQL | Yes | |
| Bulkified (Map-based lookups) | Yes | |
| Test class has @TestSetup | Yes | |
| Positive, negative, bulk tests | 3+ test methods | |
| Validation score | >= 90/150 | |
| Deployment successful | tooling_api_dml returns success | |

---

## 1.5 Create Apex — Selector Class (Account)

**Command**: `/create-apex`

**Prompt**: Create an AccountSelector class with methods: selectById, selectByIdWithContacts,
selectByIndustry, selectActive, selectByRevenueRange, and countByIndustry.
Include test class.

Expected artifacts:
- `CirraTest_AccountSelector`
- `CirraTest_AccountSelectorTest`

| Check | Expected | Result |
|-------|----------|--------|
| Uses `with sharing` | Yes | |
| All queries use USER_MODE or SECURITY_ENFORCED | Yes | |
| selectByIdWithContacts uses subquery | Yes | |
| countByIndustry uses GROUP BY | Yes | |
| Validation score | >= 90/150 | |

---

## 1.6 Create Apex — Batch Class

**Command**: `/create-apex`

**Prompt**: Create a batch Apex class that finds all Accounts where
AnnualRevenue is null and sets it to 0. Process in batches of 200.
Include Stateful tracking of processed/failed counts and email notification
on finish. Include test class.

Expected artifacts:
- `CirraTest_AccountRevenueBatch`
- `CirraTest_AccountRevenueBatchTest`

| Check | Expected | Result |
|-------|----------|--------|
| Implements Database.Batchable<SObject>, Database.Stateful | Yes | |
| start() returns QueryLocator | Yes | |
| execute() uses Database.update with allOrNone=false | Yes | |
| finish() sends email summary | Yes | |
| Test covers batch execution | Test.startTest/stopTest pattern | |
| Validation score | >= 90/150 | |

---

## 1.7 Create Apex — Queueable Class

**Command**: `/create-apex`

**Prompt**: Create a Queueable class that processes a list of Account IDs,
queries their related Contacts, and creates a Task for each Contact
that has no open Tasks. Include test class.

Expected artifacts:
- `CirraTest_ContactTaskCreator`
- `CirraTest_ContactTaskCreatorTest`

| Check | Expected | Result |
|-------|----------|--------|
| Implements Queueable | Yes | |
| Constructor accepts List<Id> | Yes | |
| Bulkified Task creation | Single DML for all Tasks | |
| Test uses Test.startTest/stopTest | Yes | |
| Validation score | >= 90/150 | |

---

## 1.8 Create Apex — Invocable Method

**Command**: `/create-apex`

**Prompt**: Create an invocable Apex method callable from Flow that accepts a
list of Account IDs and returns a list of results indicating whether each
Account has at least one Closed Won Opportunity. Use Request/Response wrapper
pattern.

Expected artifacts:
- `CirraTest_AccountWinChecker`
- `CirraTest_AccountWinCheckerTest`

| Check | Expected | Result |
|-------|----------|--------|
| @InvocableMethod annotation present | With label, description, category | |
| Request class has @InvocableVariable | Yes | |
| Bulkified (single SOQL for all IDs) | Yes | |
| Response has success/error factory methods | Yes | |
| Validation score | >= 90/150 | |

---

## 1.9 Create Flow — Before-Save Record-Triggered

**Command**: `/create-flow`

**Prompt**: Create a before-save record-triggered flow on Account that runs on
insert and update. When Industry is "Technology" and AnnualRevenue > 1000000,
set Rating to "Hot". When Industry is "Healthcare", set Description to
"Healthcare partner". Include entry conditions to skip when Rating is already
set by user.

Expected artifact: `CirraTest_Account_Before_Save`

| Check | Expected | Result |
|-------|----------|--------|
| processType = AutoLaunchedFlow | Yes | |
| triggerType = RecordBeforeSave | Yes | |
| Uses $Record for field assignment | Yes (no DML element) | |
| Entry conditions present | Yes | |
| Decision element with 2+ outcomes | Yes | |
| API version >= 65.0 | Yes | |
| Validation score | >= 88/110 | |

---

## 1.10 Create Flow — After-Save Record-Triggered

**Command**: `/create-flow`

**Prompt**: Create an after-save record-triggered flow on Opportunity that runs
when Stage changes to "Closed Won". Create a Task assigned to the Account owner
with subject "Follow up on closed deal: {OpportunityName}". Query the related
Account to get the OwnerId. Include fault handling.

Expected artifact: `CirraTest_Opp_After_Save_Task`

| Check | Expected | Result |
|-------|----------|--------|
| triggerType = RecordAfterSave | Yes | |
| Entry criteria check StageName change | $Record.StageName = 'Closed Won' | |
| Get Records for Account | With fault path | |
| Create Records for Task | With fault path | |
| Fault connectors on all DML elements | Yes | |
| Validation score | >= 88/110 | |

---

## 1.11 Create Flow — Screen Flow

**Command**: `/create-flow`

**Prompt**: Create a screen flow for case intake. Screen 1: welcome message.
Screen 2: collect Subject, Description, Priority (picklist), and Account lookup.
Screen 3: confirmation with created Case number. Include input validation and
error handling for the Create Records element.

Expected artifact: `CirraTest_Case_Intake_Screen`

| Check | Expected | Result |
|-------|----------|--------|
| processType = Flow (Screen Flow) | Yes | |
| 3 screen elements | Welcome, Input, Confirmation | |
| Create Records with fault path | Yes | |
| Input validation on required fields | Yes | |
| Navigation between screens | Yes | |
| Validation score | >= 88/110 | |

---

## 1.12 Create Flow — Autolaunched

**Command**: `/create-flow`

**Prompt**: Create an autolaunched flow that accepts a collection of Account IDs
as input, queries Contacts for those Accounts, and creates a follow-up Task for
each Contact where Title contains "VP" or "Director". Use a Loop element with
bulk DML after the loop. Include isInput/isOutput on variables.

Expected artifact: `CirraTest_VIP_Contact_Tasks`

| Check | Expected | Result |
|-------|----------|--------|
| processType = AutoLaunchedFlow | Yes | |
| Input variable with isInput=true | Yes | |
| Output variable with isOutput=true | Yes | |
| Get Records for Contacts | With fault path | |
| Loop + collection variable + DML after loop | Yes | |
| No DML inside the loop | Yes | |
| Validation score | >= 88/110 | |

---

## 1.13 Create Flow — Scheduled

**Command**: `/create-flow`

**Prompt**: Create a scheduled flow that runs daily, queries all Opportunities
with CloseDate in the past and StageName not in (Closed Won, Closed Lost),
and updates their StageName to "Closed Lost". Include error handling and
a limit of 2000 records.

Expected artifact: `CirraTest_Stale_Opp_Cleanup`

| Check | Expected | Result |
|-------|----------|--------|
| processType = AutoLaunchedFlow | Yes | |
| start element has schedule | Yes | |
| Get Records with date filter | CloseDate < TODAY | |
| Update Records element | With fault path | |
| LIMIT applied to query | Yes | |
| Validation score | >= 88/110 | |

---

## 1.14 Create Flow — Platform Event-Triggered

**Command**: `/create-flow`

**Prompt**: Create a platform event-triggered flow that listens for
Order_Event__e. When received, create an Account note Task with the event
payload data. Include decision logic to handle different event types. Include
error logging via a subflow.

Expected artifact: `CirraTest_Order_Event_Handler`

| Check | Expected | Result |
|-------|----------|--------|
| processType = AutoLaunchedFlow | Yes | |
| triggerType = PlatformEvent | Yes | |
| Decision element for event type routing | Yes | |
| Create Records with fault path | Yes | |
| Validation score | >= 88/110 | |

---

## 1.15 Create LWC — Wire-based Datatable

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestAccountDashboard that
displays a lightning-datatable of Accounts with columns: Name, Industry,
AnnualRevenue, Rating, BillingCity. Support sorting, row selection, and
inline editing on Rating. Use @wire with an Apex controller. Include dark
mode support and WCAG accessibility. Target: Lightning App Page.

Expected artifacts:
- `cirraTestAccountDashboard.html`
- `cirraTestAccountDashboard.js`
- `cirraTestAccountDashboard.css`
- `cirraTestAccountDashboard.js-meta.xml`

| Check | Expected | Result |
|-------|----------|--------|
| Uses @wire decorator | Yes | |
| lightning-datatable with columns | 5 columns | |
| Sorting handler | Yes | |
| Row selection handler | Yes | |
| Inline edit with save handler | Yes | |
| SLDS 2 CSS (styling hooks, no hardcoded colors) | Yes | |
| ARIA labels on datatable | Yes | |
| meta.xml target: lightning__AppPage | Yes | |
| Validation score | >= 100/165 | |

---

## 1.16 Create LWC — Form Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestAccountForm that provides
a create/edit form for Account records. Use lightning-record-edit-form with
fields: Name, Industry, AnnualRevenue, Phone, BillingCity, BillingState.
Include custom validation (AnnualRevenue > 0), toast notifications on
success/error, and navigation to the created record. Target: Lightning Record Page.

Expected artifacts:
- `cirraTestAccountForm.html`
- `cirraTestAccountForm.js`
- `cirraTestAccountForm.css`
- `cirraTestAccountForm.js-meta.xml`

| Check | Expected | Result |
|-------|----------|--------|
| lightning-record-edit-form | Yes | |
| Custom validation logic | AnnualRevenue > 0 | |
| Toast notification on success | ShowToastEvent | |
| NavigationMixin for redirect | Yes | |
| Error state handling | Yes | |
| SLDS 2 CSS | Yes | |
| meta.xml target: lightning__RecordPage | Yes | |
| Validation score | >= 100/165 | |

---

## 1.17 Create LWC — Flow Screen Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestRecordSelector for use in
Flow screens. Accept an input property `objectApiName` and display a searchable
list of records. When user selects a record, dispatch FlowAttributeChangeEvent
with the selected record ID. Support FlowNavigationNextEvent for advancing.
Target: Flow Screen.

Expected artifacts:
- `cirraTestRecordSelector.html`
- `cirraTestRecordSelector.js`
- `cirraTestRecordSelector.css`
- `cirraTestRecordSelector.js-meta.xml`

| Check | Expected | Result |
|-------|----------|--------|
| @api property for objectApiName | Yes | |
| @api property for selectedRecordId | Yes | |
| FlowAttributeChangeEvent dispatched | Yes | |
| FlowNavigationNextEvent or finish | Yes | |
| meta.xml target: lightning__FlowScreen | Yes | |
| Validation score | >= 100/165 | |

---

## 1.18 Create LWC — Modal Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestConfirmModal that renders a
modal dialog with a configurable title, message body, and confirm/cancel
buttons. Dispatch custom events on confirm and cancel. Include focus trap,
keyboard escape handling, and ARIA attributes for accessibility.
Target: Lightning App Page.

Expected artifacts:
- `cirraTestConfirmModal.html`
- `cirraTestConfirmModal.js`
- `cirraTestConfirmModal.css`
- `cirraTestConfirmModal.js-meta.xml`

| Check | Expected | Result |
|-------|----------|--------|
| @api open property to show/hide | Yes | |
| Focus trap (first/last focusable) | Yes | |
| Escape key closes modal | Yes | |
| Custom events: confirm, cancel | Yes | |
| ARIA: role=dialog, aria-modal, aria-labelledby | Yes | |
| Backdrop overlay | Yes | |
| SLDS modal classes | Yes | |
| Validation score | >= 100/165 | |

---

## 1.19 Create LWC — GraphQL Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestContactList that uses the
GraphQL wire adapter to query Contacts with fields FirstName, LastName, Email,
Account.Name. Display in a formatted list with loading and error states.
Target: Lightning Record Page (Account).

Expected artifacts:
- `cirraTestContactList.html`
- `cirraTestContactList.js`
- `cirraTestContactList.css`
- `cirraTestContactList.js-meta.xml`

| Check | Expected | Result |
|-------|----------|--------|
| import { graphql, gql } from 'lightning/uiGraphQLApi' | Yes | |
| @wire with graphql adapter | Yes | |
| Loading state | Yes | |
| Error state | Yes | |
| Empty state | Yes | |
| Displays Account.Name (relationship) | Yes | |
| meta.xml target: lightning__RecordPage | Yes | |
| Validation score | >= 100/165 | |

---

## 1.20 Insert Test Data — Single Records

**Command**: `/insert-data`

**Prompt**: Insert 10 Account records with varied Industries (Technology,
Healthcare, Finance, Manufacturing, Retail), AnnualRevenue ($500K–$10M),
and BillingCity. Use naming pattern CirraTest_Account_001 through _010.

```
sobject_dml(
  operation="insert",
  sObject="Account",
  records=[
    {"Name": "CirraTest_Account_001", "Industry": "Technology", "AnnualRevenue": 5000000, "BillingCity": "San Francisco"},
    {"Name": "CirraTest_Account_002", "Industry": "Healthcare", "AnnualRevenue": 3000000, "BillingCity": "Boston"},
    {"Name": "CirraTest_Account_003", "Industry": "Finance", "AnnualRevenue": 10000000, "BillingCity": "New York"},
    {"Name": "CirraTest_Account_004", "Industry": "Manufacturing", "AnnualRevenue": 2000000, "BillingCity": "Detroit"},
    {"Name": "CirraTest_Account_005", "Industry": "Retail", "AnnualRevenue": 1500000, "BillingCity": "Chicago"},
    {"Name": "CirraTest_Account_006", "Industry": "Technology", "AnnualRevenue": 8000000, "BillingCity": "Seattle"},
    {"Name": "CirraTest_Account_007", "Industry": "Healthcare", "AnnualRevenue": 500000, "BillingCity": "Houston"},
    {"Name": "CirraTest_Account_008", "Industry": "Finance", "AnnualRevenue": 7500000, "BillingCity": "Charlotte"},
    {"Name": "CirraTest_Account_009", "Industry": "Manufacturing", "AnnualRevenue": 4000000, "BillingCity": "Pittsburgh"},
    {"Name": "CirraTest_Account_010", "Industry": "Retail", "AnnualRevenue": 900000, "BillingCity": "Atlanta"}
  ]
)
```

| Check | Expected | Result |
|-------|----------|--------|
| 10 Account IDs returned | Yes | |
| No errors | Success for all 10 | |
| Record IDs saved for later steps | Yes | |

---

## 1.21 Insert Test Data — Related Records (Contacts)

**Command**: `/insert-data`

**Prompt**: Insert 20 Contact records — 2 per Account — with varied Titles
(CEO, CTO, CFO, VP Sales, VP Marketing, Director Engineering, etc.) and Departments.

| Check | Expected | Result |
|-------|----------|--------|
| 20 Contact IDs returned | Yes | |
| Each Contact linked to correct Account | Verify via AccountId | |
| Varied titles across contacts | Yes | |

---

## 1.22 Insert Test Data — Opportunities

**Command**: `/insert-data`

**Prompt**: Insert 15 Opportunity records across the 10 Accounts with varied
Stages (Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost),
Amounts ($30K–$500K), and CloseDates spanning next 6 months.

| Check | Expected | Result |
|-------|----------|--------|
| 15 Opportunity IDs returned | Yes | |
| Varied stages | At least 4 different stages | |
| Future close dates | Yes | |
| Amounts in expected range | $30K–$500K | |

---

## 1.23 Insert Test Data — Cases

**Command**: `/insert-data`

**Prompt**: Insert 10 Case records across 5 Accounts with varied Status (New,
Working, Escalated), Priority (Low, Medium, High), and Type (Question, Problem,
Feature Request).

| Check | Expected | Result |
|-------|----------|--------|
| 10 Case IDs returned | Yes | |
| Linked to Accounts and Contacts | Yes | |
| Varied priorities and statuses | Yes | |

---

## 1.24 Insert Test Data — Leads

**Command**: `/insert-data`

**Prompt**: Insert 10 Lead records with varied LeadSource (Web, Phone, Email,
Partner Referral, Trade Show), Status (Open, Working, Qualified), and Industries.

| Check | Expected | Result |
|-------|----------|--------|
| 10 Lead IDs returned | Yes | |
| Varied lead sources | At least 4 different | |
| Varied statuses | Yes | |

---

## 1.25 Insert Test Data — Activities (Tasks + Events)

**Command**: `/insert-data`

**Prompt**: Insert 10 Tasks linked to Contacts and Accounts with varied subjects
and statuses. Insert 5 Events linked to Contacts with varied subjects and
durations.

| Check | Expected | Result |
|-------|----------|--------|
| 10 Task IDs returned | Yes | |
| 5 Event IDs returned | Yes | |
| Tasks linked to WhoId (Contact) and WhatId (Account) | Yes | |
| Events linked to WhoId (Contact) | Yes | |

---

## 1.26 Insert Test Data — Bulk 201+ Records

**Command**: `/insert-data`

**Prompt**: Insert 251 Account records named CirraTest_Bulk_001 through _251
with varied Industries to test the 200-record batch boundary. Use a single
sobject_dml call.

| Check | Expected | Result |
|-------|----------|--------|
| 251 Account IDs returned | Yes | |
| Single DML call used | Yes (not 251 separate calls) | |
| Batch boundary crossed | Records span 2+ batches | |
| All records created successfully | 251 successes | |

---

## 1.27 Insert Test Data — Hierarchy (Account → Contact → Opp → Case)

**Command**: `/insert-data`

**Prompt**: Create a 3-level hierarchy: 5 parent Accounts, each with 3 Contacts,
2 Opportunities, and 1 Case. Use the hierarchy factory pattern.

| Check | Expected | Result |
|-------|----------|--------|
| 5 Accounts created | Yes | |
| 15 Contacts (3 per Account) | Yes | |
| 10 Opportunities (2 per Account) | Yes | |
| 5 Cases (1 per Account) | Yes | |
| All relationships valid | Contacts/Opps/Cases → correct parent | |

---

## Phase 1 Summary

| Category | Artifact Count | Expected |
|----------|---------------|----------|
| Apex Classes | 10 (5 classes + 5 tests) | All deployed |
| Apex Triggers | 1 | Deployed |
| Flows | 6 | All deployed |
| LWC Components | 5 | All deployed |
| Account Records | 261+ (10 + 251 bulk) | All inserted |
| Contact Records | 35+ | All inserted |
| Opportunity Records | 25+ | All inserted |
| Case Records | 15+ | All inserted |
| Lead Records | 10 | All inserted |
| Task Records | 10+ | All inserted |
| Event Records | 5+ | All inserted |
