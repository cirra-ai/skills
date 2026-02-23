# Phase 1b: Setup — Metadata Artifacts

**Time estimate:** ~60 minutes
**Prerequisite:** Phase 0 smoke test TC-003 must PASS.

> **Gate:** If TC-003 failed with a hook/subprocess error, skip this entire file.
> Mark all metadata tests in Phase 2, Phase 3, and Phase 4 as BLOCKED.
> Proceed to Phase 1a data setup only.

Run these steps sequentially. Record actual results in the **Result** column.

---

## Apex Classes

### 1b.1 Create Apex — Trigger + TAF Action (Account)

**Command**: `/create-apex`

**Prompt**: Create a before-insert trigger action for Account that auto-populates
the Description field with a summary of Industry and BillingCity, and defaults
Rating to "Warm" when not set.

Expected artifacts:

- `CirraTest_AccountTrigger` (thin trigger using MetadataTriggerHandler)
- `TA_CirraTest_Account_SetDefaults` (trigger action class)
- `TA_CirraTest_Account_SetDefaultsTest` (test class)

| Check                       | Expected                                      | Result |
| --------------------------- | --------------------------------------------- | ------ |
| Trigger created             | MetadataTriggerHandler.run() pattern          |        |
| Action class created        | Implements TriggerAction.BeforeInsert         |        |
| Test class created          | PNB pattern, 201+ bulk test                   |        |
| No SOQL/DML in trigger body | Body delegates to MetadataTriggerHandler only |        |
| Validation score            | >= 90/150                                     |        |
| Deployment successful       | tooling_api_dml returns success               |        |

---

### 1b.2 Create Apex — Service Class (Account)

**Command**: `/create-apex`

**Prompt**: Create an AccountService class with methods to: (1) get accounts by
IDs with related contacts, (2) create accounts with validation, (3) update
account annual revenue in bulk, and (4) transfer account ownership. Include a
corresponding test class.

Expected artifacts: `CirraTest_AccountService`, `CirraTest_AccountServiceTest`

| Check                            | Expected                        | Result |
| -------------------------------- | ------------------------------- | ------ |
| Service class has `with sharing` | Yes                             |        |
| Uses USER_MODE in SOQL           | Yes                             |        |
| Bulkified (Map-based lookups)    | Yes                             |        |
| Test class has @TestSetup        | Yes                             |        |
| Positive, negative, bulk tests   | 3+ test methods                 |        |
| Validation score                 | >= 90/150                       |        |
| Deployment successful            | tooling_api_dml returns success |        |

---

### 1b.3 Create Apex — Selector Class (Account)

**Command**: `/create-apex`

**Prompt**: Create an AccountSelector class with methods: selectById, selectByIdWithContacts,
selectByIndustry, selectActive, selectByRevenueRange, and countByIndustry.
Include test class.

Expected artifacts: `CirraTest_AccountSelector`, `CirraTest_AccountSelectorTest`

| Check                                          | Expected  | Result |
| ---------------------------------------------- | --------- | ------ |
| Uses `with sharing`                            | Yes       |        |
| All queries use USER_MODE or SECURITY_ENFORCED | Yes       |        |
| selectByIdWithContacts uses subquery           | Yes       |        |
| countByIndustry uses GROUP BY                  | Yes       |        |
| Validation score                               | >= 90/150 |        |

---

### 1b.4 Create Apex — Batch Class

**Command**: `/create-apex`

**Prompt**: Create a batch Apex class that finds all Accounts where
AnnualRevenue is null and sets it to 0. Process in batches of 200.
Include Stateful tracking of processed/failed counts and email notification
on finish. Include test class.

Expected artifacts: `CirraTest_AccountRevenueBatch`, `CirraTest_AccountRevenueBatchTest`

| Check                                                     | Expected                        | Result |
| --------------------------------------------------------- | ------------------------------- | ------ |
| Implements Database.Batchable<SObject>, Database.Stateful | Yes                             |        |
| start() returns QueryLocator                              | Yes                             |        |
| execute() uses Database.update with allOrNone=false       | Yes                             |        |
| finish() sends email summary                              | Yes                             |        |
| Test covers batch execution                               | Test.startTest/stopTest pattern |        |
| Validation score                                          | >= 90/150                       |        |

---

### 1b.5 Create Apex — Queueable Class

**Command**: `/create-apex`

**Prompt**: Create a Queueable class that processes a list of Account IDs,
queries their related Contacts, and creates a Task for each Contact
that has no open Tasks. Include test class.

Expected artifacts: `CirraTest_ContactTaskCreator`, `CirraTest_ContactTaskCreatorTest`

| Check                             | Expected                 | Result |
| --------------------------------- | ------------------------ | ------ |
| Implements Queueable              | Yes                      |        |
| Constructor accepts List<Id>      | Yes                      |        |
| Bulkified Task creation           | Single DML for all Tasks |        |
| Test uses Test.startTest/stopTest | Yes                      |        |
| Validation score                  | >= 90/150                |        |

---

### 1b.6 Create Apex — Invocable Method

**Command**: `/create-apex`

**Prompt**: Create an invocable Apex method callable from Flow that accepts a
list of Account IDs and returns a list of results indicating whether each
Account has at least one Closed Won Opportunity. Use Request/Response wrapper
pattern.

Expected artifacts: `CirraTest_AccountWinChecker`, `CirraTest_AccountWinCheckerTest`

| Check                                      | Expected                          | Result |
| ------------------------------------------ | --------------------------------- | ------ |
| @InvocableMethod annotation present        | With label, description, category |        |
| Request class has @InvocableVariable       | Yes                               |        |
| Bulkified (single SOQL for all IDs)        | Yes                               |        |
| Response has success/error factory methods | Yes                               |        |
| Validation score                           | >= 90/150                         |        |

---

## Flows

### 1b.7 Create Flow — Before-Save Record-Triggered

**Command**: `/create-flow`

**Prompt**: Create a before-save record-triggered flow on Account that runs on
insert and update. When Industry is "Technology" and AnnualRevenue > 1000000,
set Rating to "Hot". When Industry is "Healthcare", set Description to
"Healthcare partner". Include entry conditions to skip when Rating is already
set by user.

Expected artifact: `CirraTest_Account_Before_Save`

| Check                             | Expected             | Result |
| --------------------------------- | -------------------- | ------ |
| processType = AutoLaunchedFlow    | Yes                  |        |
| triggerType = RecordBeforeSave    | Yes                  |        |
| Uses $Record for field assignment | Yes (no DML element) |        |
| Entry conditions present          | Yes                  |        |
| Decision element with 2+ outcomes | Yes                  |        |
| API version >= 65.0               | Yes                  |        |
| Validation score                  | >= 88/110            |        |

---

### 1b.8 Create Flow — After-Save Record-Triggered

**Command**: `/create-flow`

**Prompt**: Create an after-save record-triggered flow on Opportunity that runs
when Stage changes to "Closed Won". Create a Task assigned to the Account owner
with subject "Follow up on closed deal: {OpportunityName}". Query the related
Account to get the OwnerId. Include fault handling.

Expected artifact: `CirraTest_Opp_After_Save_Task`

| Check                                 | Expected                         | Result |
| ------------------------------------- | -------------------------------- | ------ |
| triggerType = RecordAfterSave         | Yes                              |        |
| Entry criteria check StageName change | $Record.StageName = 'Closed Won' |        |
| Get Records for Account               | With fault path                  |        |
| Create Records for Task               | With fault path                  |        |
| Fault connectors on all DML elements  | Yes                              |        |
| Validation score                      | >= 88/110                        |        |

---

### 1b.9 Create Flow — Screen Flow

**Command**: `/create-flow`

**Prompt**: Create a screen flow for case intake. Screen 1: welcome message.
Screen 2: collect Subject, Description, Priority (picklist), and Account lookup.
Screen 3: confirmation with created Case number. Include input validation and
error handling for the Create Records element.

Expected artifact: `CirraTest_Case_Intake_Screen`

| Check                               | Expected                     | Result |
| ----------------------------------- | ---------------------------- | ------ |
| processType = Flow (Screen Flow)    | Yes                          |        |
| 3 screen elements                   | Welcome, Input, Confirmation |        |
| Create Records with fault path      | Yes                          |        |
| Input validation on required fields | Yes                          |        |
| Navigation between screens          | Yes                          |        |
| Validation score                    | >= 88/110                    |        |

---

### 1b.10 Create Flow — Autolaunched

**Command**: `/create-flow`

**Prompt**: Create an autolaunched flow that accepts a collection of Account IDs
as input, queries Contacts for those Accounts, and creates a follow-up Task for
each Contact where Title contains "VP" or "Director". Use a Loop element with
bulk DML after the loop. Include isInput/isOutput on variables.

Expected artifact: `CirraTest_VIP_Contact_Tasks`

| Check                                       | Expected        | Result |
| ------------------------------------------- | --------------- | ------ |
| processType = AutoLaunchedFlow              | Yes             |        |
| Input variable with isInput=true            | Yes             |        |
| Output variable with isOutput=true          | Yes             |        |
| Get Records for Contacts                    | With fault path |        |
| Loop + collection variable + DML after loop | Yes             |        |
| No DML inside the loop                      | Yes             |        |
| Validation score                            | >= 88/110       |        |

---

### 1b.11 Create Flow — Scheduled

**Command**: `/create-flow`

**Prompt**: Create a scheduled flow that runs daily, queries all Opportunities
with CloseDate in the past and StageName not in (Closed Won, Closed Lost),
and updates their StageName to "Closed Lost". Include error handling and
a limit of 2000 records.

Expected artifact: `CirraTest_Stale_Opp_Cleanup`

| Check                          | Expected          | Result |
| ------------------------------ | ----------------- | ------ |
| processType = AutoLaunchedFlow | Yes               |        |
| start element has schedule     | Yes               |        |
| Get Records with date filter   | CloseDate < TODAY |        |
| Update Records element         | With fault path   |        |
| LIMIT applied to query         | Yes               |        |
| Validation score               | >= 88/110         |        |

---

### 1b.12 Create Flow — Platform Event-Triggered

**Command**: `/create-flow`

**Prompt**: Create a platform event-triggered flow that listens for
Order_Event__e. When received, create an Account note Task with the event
payload data. Include decision logic to handle different event types. Include
error logging via a subflow.

Expected artifact: `CirraTest_Order_Event_Handler`

| Check                                   | Expected  | Result |
| --------------------------------------- | --------- | ------ |
| processType = AutoLaunchedFlow          | Yes       |        |
| triggerType = PlatformEvent             | Yes       |        |
| Decision element for event type routing | Yes       |        |
| Create Records with fault path          | Yes       |        |
| Validation score                        | >= 88/110 |        |

---

## LWC Components

### 1b.13 Create LWC — Wire-based Datatable

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestAccountDashboard that
displays a lightning-datatable of Accounts with columns: Name, Industry,
AnnualRevenue, Rating, BillingCity. Support sorting, row selection, and
inline editing on Rating. Use @wire with an Apex controller. Include dark
mode support and WCAG accessibility. Target: Lightning App Page.

Expected artifacts: `cirraTestAccountDashboard.html/js/css/js-meta.xml`

| Check                                           | Expected   | Result |
| ----------------------------------------------- | ---------- | ------ |
| Uses @wire decorator                            | Yes        |        |
| lightning-datatable with columns                | 5 columns  |        |
| Sorting handler                                 | Yes        |        |
| Row selection handler                           | Yes        |        |
| Inline edit with save handler                   | Yes        |        |
| SLDS 2 CSS (styling hooks, no hardcoded colors) | Yes        |        |
| ARIA labels on datatable                        | Yes        |        |
| meta.xml target: lightning__AppPage             | Yes        |        |
| Validation score                                | >= 100/165 |        |

---

### 1b.14 Create LWC — Form Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestAccountForm that provides
a create/edit form for Account records. Use lightning-record-edit-form with
fields: Name, Industry, AnnualRevenue, Phone, BillingCity, BillingState.
Include custom validation (AnnualRevenue > 0), toast notifications on
success/error, and navigation to the created record. Target: Lightning Record Page.

Expected artifacts: `cirraTestAccountForm.html/js/css/js-meta.xml`

| Check                                    | Expected          | Result |
| ---------------------------------------- | ----------------- | ------ |
| lightning-record-edit-form               | Yes               |        |
| Custom validation logic                  | AnnualRevenue > 0 |        |
| Toast notification on success            | ShowToastEvent    |        |
| NavigationMixin for redirect             | Yes               |        |
| Error state handling                     | Yes               |        |
| SLDS 2 CSS                               | Yes               |        |
| meta.xml target: lightning__RecordPage   | Yes               |        |
| Validation score                         | >= 100/165        |        |

---

### 1b.15 Create LWC — Flow Screen Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestRecordSelector for use in
Flow screens. Accept an input property `objectApiName` and display a searchable
list of records. When user selects a record, dispatch FlowAttributeChangeEvent
with the selected record ID. Support FlowNavigationNextEvent for advancing.
Target: Flow Screen.

Expected artifacts: `cirraTestRecordSelector.html/js/css/js-meta.xml`

| Check                                    | Expected   | Result |
| ---------------------------------------- | ---------- | ------ |
| @api property for objectApiName          | Yes        |        |
| @api property for selectedRecordId       | Yes        |        |
| FlowAttributeChangeEvent dispatched      | Yes        |        |
| FlowNavigationNextEvent or finish        | Yes        |        |
| meta.xml target: lightning__FlowScreen   | Yes        |        |
| Validation score                         | >= 100/165 |        |

---

### 1b.16 Create LWC — Modal Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestConfirmModal that renders a
modal dialog with a configurable title, message body, and confirm/cancel
buttons. Dispatch custom events on confirm and cancel. Include focus trap,
keyboard escape handling, and ARIA attributes for accessibility.
Target: Lightning App Page.

Expected artifacts: `cirraTestConfirmModal.html/js/css/js-meta.xml`

| Check                                          | Expected   | Result |
| ---------------------------------------------- | ---------- | ------ |
| @api open property to show/hide                | Yes        |        |
| Focus trap (first/last focusable)              | Yes        |        |
| Escape key closes modal                        | Yes        |        |
| Custom events: confirm, cancel                 | Yes        |        |
| ARIA: role=dialog, aria-modal, aria-labelledby | Yes        |        |
| Backdrop overlay                               | Yes        |        |
| SLDS modal classes                             | Yes        |        |
| Validation score                               | >= 100/165 |        |

---

### 1b.17 Create LWC — GraphQL Component

**Command**: `/create-lwc`

**Prompt**: Create an LWC component called cirraTestContactList that uses the
GraphQL wire adapter to query Contacts with fields FirstName, LastName, Email,
Account.Name. Display in a formatted list with loading and error states.
Target: Lightning Record Page (Account).

Expected artifacts: `cirraTestContactList.html/js/css/js-meta.xml`

| Check                                                 | Expected   | Result |
| ----------------------------------------------------- | ---------- | ------ |
| import { graphql, gql } from 'lightning/uiGraphQLApi' | Yes        |        |
| @wire with graphql adapter                            | Yes        |        |
| Loading state                                         | Yes        |        |
| Error state                                           | Yes        |        |
| Empty state                                           | Yes        |        |
| Displays Account.Name (relationship)                  | Yes        |        |
| meta.xml target: lightning__RecordPage                | Yes        |        |
| Validation score                                      | >= 100/165 |        |

---

## Phase 1b Summary

| Category       | Artifacts                                                                                                             | Count | Status |
| -------------- | --------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| Apex Classes   | AccountService, AccountSelector, AccountRevenueBatch, ContactTaskCreator, AccountWinChecker (+ test classes)          | 10    |        |
| Apex Triggers  | CirraTest_AccountTrigger + TA_CirraTest_Account_SetDefaults                                                           | 2     |        |
| Flows          | Account_Before_Save, Opp_After_Save_Task, Case_Intake_Screen, VIP_Contact_Tasks, Stale_Opp_Cleanup, Order_Event_Handler | 6   |        |
| LWC Components | cirraTestAccountDashboard, cirraTestAccountForm, cirraTestRecordSelector, cirraTestConfirmModal, cirraTestContactList  | 5     |        |

**Proceed to Phase 2** (validate all artifacts).
