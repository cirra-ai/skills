# Phase 3: Update — Modify Artifacts and Re-Validate

Run after Phase 2 completes. Each step modifies an existing artifact, then
re-validates to confirm scores are maintained or improved.

---

## 3.1 Update Apex — Add Method to Service Class

**Command**: `/update-apex CirraTest_AccountService`

**Prompt**: Add a new method `mergeAccounts(Id masterId, List<Id> duplicateIds)`
that re-parents Contacts and Opportunities from duplicate Accounts to the
master Account, then deletes the duplicates. Use bulkified queries and single
DML statements. Update the test class with positive and negative tests.

| Check | Expected | Result |
|-------|----------|--------|
| Method added to service class | mergeAccounts with correct signature | |
| Bulkified queries (no SOQL in loops) | Yes | |
| Single DML per operation | Yes | |
| Error handling for invalid IDs | Yes | |
| Test class updated | New test methods for merge | |
| Validation score maintained | >= 90/150 (same or better than Phase 2) | |
| Redeployment successful | tooling_api_dml update | |

---

## 3.2 Update Apex — Modify Trigger Action Logic

**Command**: `/update-apex TA_CirraTest_Account_SetDefaults`

**Prompt**: Extend the trigger action to also handle BeforeUpdate context. When
the Industry field changes, update the Description to reflect the new Industry.
Add a guard to prevent recursive updates using a static variable. Update tests.

| Check | Expected | Result |
|-------|----------|--------|
| Implements both BeforeInsert and BeforeUpdate | Yes | |
| Recursion guard with static variable | Yes | |
| Industry change detection (Trigger.oldMap) | Yes | |
| Test class covers both insert and update paths | Yes | |
| Validation score maintained | >= 90/150 | |

---

## 3.3 Update Apex — Add Error Handling to Batch

**Command**: `/update-apex CirraTest_AccountRevenueBatch`

**Prompt**: Add retry logic using Database.update with allOrNone=false.
Collect failed record IDs and create a custom log entry for each failure.
Add a MAX_RETRIES constant. Update the test class to cover the error path.

| Check | Expected | Result |
|-------|----------|--------|
| Database.update with allOrNone=false | Yes | |
| Error collection and logging | Yes | |
| MAX_RETRIES constant | Yes | |
| Test covers error/retry path | Yes | |
| Validation score maintained | >= 90/150 | |

---

## 3.4 Update Flow — Add Decision Branch

**Command**: `/update-flow CirraTest_Account_Before_Save`

**Prompt**: Add a third decision outcome: when Industry is "Finance" and
AnnualRevenue > 5000000, set Rating to "Hot" and Description to
"High-value financial partner". Keep existing outcomes intact.

| Check | Expected | Result |
|-------|----------|--------|
| Existing outcomes preserved | Technology and Healthcare branches intact | |
| New Finance outcome added | With correct conditions | |
| Field assignments correct | Rating = Hot, Description set | |
| No DML elements (before-save) | Yes | |
| Validation score maintained | >= 88/110 | |

---

## 3.5 Update Flow — Add Fault Handling to After-Save

**Command**: `/update-flow CirraTest_Opp_After_Save_Task`

**Prompt**: Add a fault path on the Create Records element that creates an error
log record (using a subflow pattern or direct assignment) capturing the flow
name, error message, and record ID. Ensure the fault connector targets a
dedicated error handler element, not itself.

| Check | Expected | Result |
|-------|----------|--------|
| Fault connector on Create Records | Yes | |
| Fault does NOT self-reference | Points to different element | |
| Error details captured | Flow name, error message, record ID | |
| Existing logic preserved | Task creation unchanged | |
| Validation score maintained or improved | >= 88/110 | |

---

## 3.6 Update Flow — Add Screen to Screen Flow

**Command**: `/update-flow CirraTest_Case_Intake_Screen`

**Prompt**: Add a new screen between the input and confirmation screens that
asks the user to upload an attachment (file input) and add internal notes
(long text area). Include a "Back" navigation button to return to the input
screen.

| Check | Expected | Result |
|-------|----------|--------|
| New screen element added | Between input and confirmation | |
| File input component | Yes | |
| Long text area | Yes | |
| Back navigation | Previous button | |
| Screen flow navigation intact | All paths work | |
| Validation score maintained | >= 88/110 | |

---

## 3.7 Update LWC — Add Dark Mode CSS

**Command**: `/update-lwc cirraTestAccountDashboard`

**Prompt**: Update the CSS to fully support dark mode using SLDS 2 global
styling hooks. Replace any hardcoded colors with `--slds-g-color-*` tokens.
Add `--slds-g-spacing-*` tokens for padding/margins. Ensure no deprecated
SLDS 1 classes remain.

| Check | Expected | Result |
|-------|----------|--------|
| All colors use --slds-g-color-* tokens | Yes | |
| Spacing uses --slds-g-spacing-* tokens | Yes | |
| No hardcoded hex/rgb values | Yes | |
| No deprecated SLDS 1 classes | Yes | |
| Dark mode score improved | >= 23/25 | |
| Overall validation score improved | Yes | |

---

## 3.8 Update LWC — Add Column to Datatable

**Command**: `/update-lwc cirraTestAccountDashboard`

**Prompt**: Add a "Phone" column to the datatable and a row-level action menu
with "Edit" and "Delete" actions. Handle the action events with toast
notifications. Add ARIA labels for the action menu.

| Check | Expected | Result |
|-------|----------|--------|
| Phone column added to columns array | Yes | |
| Row actions column added | Edit, Delete actions | |
| Action handler dispatches correct events | Yes | |
| Toast notifications on action | Yes | |
| ARIA labels on action menu | Yes | |
| Validation score maintained | >= 100/165 | |

---

## 3.9 Update LWC — Fix Accessibility on Modal

**Command**: `/update-lwc cirraTestConfirmModal`

**Prompt**: Enhance accessibility by adding: live region announcements when modal
opens/closes, proper tab order management, high-contrast border on focus, and
screen reader-only close button label. Run SLDS 2 validation.

| Check | Expected | Result |
|-------|----------|--------|
| aria-live region for announcements | Yes | |
| Tab order: first focusable on open | Yes | |
| Focus returns to trigger on close | Yes | |
| High-contrast focus border | :focus-visible styles | |
| Screen reader label on close button | aria-label or sr-only text | |
| Accessibility score improved | >= 23/25 | |

---

## 3.10 Update LWC — Add Apex Integration to Form

**Command**: `/update-lwc cirraTestAccountForm`

**Prompt**: Switch from lightning-record-edit-form to a custom form that calls
an imperative Apex method for submission. Add client-side validation for
Phone number format. Show a spinner during the Apex call. Handle errors with
an inline error message component.

| Check | Expected | Result |
|-------|----------|--------|
| Imperative Apex call for save | Yes | |
| Client-side phone validation | Regex pattern check | |
| Lightning-spinner during save | Yes | |
| Inline error messages | Not just toast, also in-form | |
| Wire adapter removed for save (imperative) | Yes | |
| Validation score maintained | >= 100/165 | |

---

## 3.11 Update Data — Bulk Update Records

**Command**: `/insert-data` (update operation)

**Prompt**: Update all 10 CirraTest_Account_* records: set AnnualRevenue to
double its current value and add " - Updated" to the Description.

```
sobject_dml(
  operation="update",
  sObject="Account",
  records=[
    {"Id": "<id1>", "AnnualRevenue": 10000000, "Description": "Technology partner - Updated"},
    ...10 records...
  ]
)
```

| Check | Expected | Result |
|-------|----------|--------|
| 10 records updated | Success for all | |
| AnnualRevenue doubled | Verify via query | |
| Description updated | Contains " - Updated" | |

---

## 3.12 Update Data — Upsert with External ID

**Command**: `/insert-data` (upsert operation)

**Prompt**: Upsert 5 Accounts: 3 existing (by Id) with updated Industry, and
2 new records. Demonstrate upsert behavior with mixed insert/update.

```
sobject_dml(
  operation="upsert",
  sObject="Account",
  records=[
    {"Id": "<existing_id_1>", "Name": "CirraTest_Account_001", "Industry": "Energy"},
    {"Id": "<existing_id_2>", "Name": "CirraTest_Account_002", "Industry": "Media"},
    {"Id": "<existing_id_3>", "Name": "CirraTest_Account_003", "Industry": "Government"},
    {"Name": "CirraTest_Upsert_New_001", "Industry": "Technology", "AnnualRevenue": 2000000},
    {"Name": "CirraTest_Upsert_New_002", "Industry": "Retail", "AnnualRevenue": 1000000}
  ]
)
```

| Check | Expected | Result |
|-------|----------|--------|
| 3 records updated | Existing IDs, Industry changed | |
| 2 records inserted | New IDs returned | |
| Upsert result distinguishes insert vs update | Yes | |

---

## 3.13 Verify Updates via Query

**Command**: `/query-data`

**Prompt**: Query updated Accounts to verify changes.

```
soql_query(query="SELECT Id, Name, Industry, AnnualRevenue, Description FROM Account WHERE Name LIKE 'CirraTest_Account_%' OR Name LIKE 'CirraTest_Upsert_%' ORDER BY Name")
```

| Check | Expected | Result |
|-------|----------|--------|
| CirraTest_Account_001 Industry = Energy | Updated via upsert | |
| CirraTest_Account_002 Industry = Media | Updated via upsert | |
| CirraTest_Account_003 Industry = Government | Updated via upsert | |
| AnnualRevenue doubled on remaining | From step 3.11 | |
| 2 new upsert records present | CirraTest_Upsert_New_001, _002 | |

---

## 3.14 Re-Validate All Apex After Updates

**Command**: `/validate-apex CirraTest_AccountService,TA_CirraTest_Account_SetDefaults,CirraTest_AccountRevenueBatch`

| Check | Expected | Result |
|-------|----------|--------|
| All 3 classes pass validation | Yes | |
| Scores same or improved vs Phase 2 | Yes | |
| No new CRITICAL issues introduced | Yes | |

---

## 3.15 Re-Validate All Flows After Updates

**Command**: `/validate-flow CirraTest_Account_Before_Save,CirraTest_Opp_After_Save_Task,CirraTest_Case_Intake_Screen`

| Check | Expected | Result |
|-------|----------|--------|
| All 3 flows pass validation | Yes | |
| Scores same or improved vs Phase 2 | Yes | |
| No new BLOCK issues introduced | Yes | |

---

## 3.16 Re-Validate All LWC After Updates

**Command**: `/validate-lwc cirraTestAccountDashboard,cirraTestAccountForm,cirraTestConfirmModal`

| Check | Expected | Result |
|-------|----------|--------|
| All 3 components pass validation | Yes | |
| Dark mode scores improved | Yes | |
| Accessibility scores improved | Yes | |
| No new issues introduced | Yes | |

---

## Phase 3 Summary

| Update Type | Count | All Re-Validated |
|-------------|-------|------------------|
| Apex class updates | 3 | Yes — scores maintained/improved |
| Flow updates | 3 | Yes — scores maintained/improved |
| LWC updates | 4 | Yes — scores maintained/improved |
| Data updates (bulk) | 1 (10 records) | Verified via query |
| Data upserts | 1 (5 records: 3 update + 2 insert) | Verified via query |
