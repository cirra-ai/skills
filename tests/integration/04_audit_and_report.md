# Phase 4: Audit — Generate Full Org Reports

Run after Phase 3 completes. This phase exercises the `/audit-org` command
and validates the completeness and accuracy of the generated reports.

---

## 4.1 Run Full Org Audit

**Command**: `/audit-org`

This single command orchestrates a full audit across Apex, Flows, and LWC.

### Expected Execution Sequence

```
1. cirra_ai_init() — confirm connection
2. tooling_api_query → count ApexClass, FlowDefinition, LightningComponentBundle
3. Fetch + score all Apex classes (batches of 200)
4. Fetch + score all Flows (batches of 25, with fallback)
5. Fetch + score all LWC components (batches of 200)
6. Generate Salesforce_Org_Audit_Report.docx
7. Generate Salesforce_Org_Audit_Scores.xlsx
8. Generate Salesforce_Org_Audit_Report.html
9. Display org health summary
```

| Check                        | Expected                          | Result |
| ---------------------------- | --------------------------------- | ------ |
| Audit starts without error   | cirra_ai_init successful          |        |
| Component counts displayed   | Apex: N, Flows: N, LWC: N         |        |
| Apex scoring completes       | All CirraTest\_\* classes scored  |        |
| Flow scoring completes       | All CirraTest\_\* flows scored    |        |
| LWC scoring completes        | All cirraTest\* components scored |        |
| Three output files generated | .docx, .xlsx, .html               |        |
| Summary displayed            | Overall health score, top issues  |        |

---

## 4.2 Validate Word Report (Salesforce_Org_Audit_Report.docx)

| Check                          | Expected                                   | Result |
| ------------------------------ | ------------------------------------------ | ------ |
| File exists at ./audit_output/ | Yes                                        |        |
| File is non-empty              | > 10 KB                                    |        |
| Executive summary section      | Overall health score, component counts     |        |
| Apex section present           | Class list with scores, top issues         |        |
| Flow section present           | Flow list with scores, top issues          |        |
| LWC section present            | Component list with scores, top issues     |        |
| Top 5 recommendations          | Prioritized improvement list               |        |
| CirraTest\_\* artifacts appear | All test artifacts from Phase 1-3 included |        |

### Apex Report Checks

| Check                                   | Expected              | Result |
| --------------------------------------- | --------------------- | ------ |
| CirraTest_AccountService listed         | Score >= 90/150       |        |
| CirraTest_AccountSelector listed        | Score >= 90/150       |        |
| CirraTest_AccountRevenueBatch listed    | Score >= 90/150       |        |
| CirraTest_ContactTaskCreator listed     | Score >= 90/150       |        |
| CirraTest_AccountWinChecker listed      | Score >= 90/150       |        |
| TA_CirraTest_Account_SetDefaults listed | Score >= 90/150       |        |
| All test classes listed                 | \*Test suffix classes |        |
| Score breakdown by category             | 8 categories shown    |        |

### Flow Report Checks

| Check                                | Expected                                         | Result |
| ------------------------------------ | ------------------------------------------------ | ------ |
| CirraTest_Account_Before_Save listed | Score >= 88/110                                  |        |
| CirraTest_Opp_After_Save_Task listed | Score >= 88/110                                  |        |
| CirraTest_Case_Intake_Screen listed  | Score >= 88/110                                  |        |
| CirraTest_VIP_Contact_Tasks listed   | Score >= 88/110                                  |        |
| CirraTest_Stale_Opp_Cleanup listed   | Score >= 88/110                                  |        |
| CirraTest_Order_Event_Handler listed | Score >= 88/110                                  |        |
| Score breakdown by category          | 6 categories shown                               |        |
| Flow type identified                 | RT Before, RT After, Screen, Auto, Scheduled, PE |        |

### LWC Report Checks

| Check                            | Expected         | Result |
| -------------------------------- | ---------------- | ------ |
| cirraTestAccountDashboard listed | Score >= 100/165 |        |
| cirraTestAccountForm listed      | Score >= 100/165 |        |
| cirraTestRecordSelector listed   | Score >= 100/165 |        |
| cirraTestConfirmModal listed     | Score >= 100/165 |        |
| cirraTestContactList listed      | Score >= 100/165 |        |
| Per-file scores shown            | .html, .js, .css |        |
| SLDS 2 compliance noted          | Dark mode status |        |

---

## 4.3 Validate Excel Report (Salesforce_Org_Audit_Scores.xlsx)

| Check                          | Expected                  | Result |
| ------------------------------ | ------------------------- | ------ |
| File exists at ./audit_output/ | Yes                       |        |
| File is non-empty              | > 5 KB                    |        |
| 4 worksheets present           | Apex, Flows, LWC, Summary |        |

### Apex Sheet

| Check                              | Expected                      | Result |
| ---------------------------------- | ----------------------------- | ------ |
| Columns: Name, Type, Score, %      | Yes                           |        |
| All CirraTest\_\* classes listed   | >= 10 rows                    |        |
| Scores match Phase 2/3 validations | Consistent with validate-apex |        |
| Sorted by score ascending          | Worst first                   |        |

### Flows Sheet

| Check                              | Expected                                             | Result |
| ---------------------------------- | ---------------------------------------------------- | ------ |
| Columns: Name, Type, Score, %      | Yes                                                  |        |
| All CirraTest\_\* flows listed     | >= 6 rows                                            |        |
| Scores match Phase 2/3 validations | Consistent with validate-flow                        |        |
| Flow types identified              | Before Save, After Save, Screen, Auto, Scheduled, PE |        |

### LWC Sheet

| Check                              | Expected                     | Result |
| ---------------------------------- | ---------------------------- | ------ |
| Columns: Name, Score, %            | Yes                          |        |
| All cirraTest\* components listed  | >= 5 rows                    |        |
| Scores match Phase 2/3 validations | Consistent with validate-lwc |        |

### Summary Sheet

| Check                      | Expected                                      | Result |
| -------------------------- | --------------------------------------------- | ------ |
| Total component counts     | Apex + Flow + LWC                             |        |
| Average scores per domain  | Apex avg, Flow avg, LWC avg                   |        |
| Score distribution         | Count per score range                         |        |
| Components below threshold | Count below 67% (Apex), 80% (Flow), 61% (LWC) |        |

---

## 4.4 Validate HTML Report (Salesforce_Org_Audit_Report.html)

| Check                              | Expected                                  | Result |
| ---------------------------------- | ----------------------------------------- | ------ |
| File exists at ./audit_output/     | Yes                                       |        |
| File is non-empty                  | > 20 KB                                   |        |
| Viewable in browser                | Valid HTML                                |        |
| Charts/visualizations present      | Score distribution charts                 |        |
| Links to intermediate source files | Clickable paths to source                 |        |
| Executive summary                  | Overall health score                      |        |
| Apex section                       | Table with scores and details             |        |
| Flow section                       | Table with scores and details             |        |
| LWC section                        | Table with scores and details             |        |
| Color-coded scoring                | Green (pass), Yellow (review), Red (fail) |        |

---

## 4.5 Validate Intermediate Files

The audit generates intermediate files for each scored component.

### Apex Intermediates

```
./audit_output/intermediate/apex/CirraTest_AccountService.cls
./audit_output/intermediate/apex/CirraTest_AccountSelector.cls
./audit_output/intermediate/apex/CirraTest_AccountRevenueBatch.cls
./audit_output/intermediate/apex/CirraTest_ContactTaskCreator.cls
./audit_output/intermediate/apex/CirraTest_AccountWinChecker.cls
./audit_output/intermediate/apex/TA_CirraTest_Account_SetDefaults.cls
(plus test classes)
```

| Check                                | Expected                 | Result |
| ------------------------------------ | ------------------------ | ------ |
| All CirraTest\_\* .cls files present | >= 10 files              |        |
| Files contain actual Apex code       | Not empty                |        |
| Code matches org version             | Includes Phase 3 updates |        |

### Flow Intermediates

```
./audit_output/intermediate/flows/CirraTest_Account_Before_Save.flow-meta.xml
./audit_output/intermediate/flows/CirraTest_Opp_After_Save_Task.flow-meta.xml
./audit_output/intermediate/flows/CirraTest_Case_Intake_Screen.flow-meta.xml
./audit_output/intermediate/flows/CirraTest_VIP_Contact_Tasks.flow-meta.xml
./audit_output/intermediate/flows/CirraTest_Stale_Opp_Cleanup.flow-meta.xml
./audit_output/intermediate/flows/CirraTest_Order_Event_Handler.flow-meta.xml
```

| Check                                          | Expected                          | Result |
| ---------------------------------------------- | --------------------------------- | ------ |
| All CirraTest\_\* .flow-meta.xml files present | >= 6 files                        |        |
| Files contain valid Flow XML                   | Well-formed XML with <?xml header |        |
| XML matches org version                        | Includes Phase 3 updates          |        |

### LWC Intermediates

```
./audit_output/intermediate/lwc/cirraTestAccountDashboard/
./audit_output/intermediate/lwc/cirraTestAccountForm/
./audit_output/intermediate/lwc/cirraTestRecordSelector/
./audit_output/intermediate/lwc/cirraTestConfirmModal/
./audit_output/intermediate/lwc/cirraTestContactList/
```

| Check                               | Expected                 | Result |
| ----------------------------------- | ------------------------ | ------ |
| All cirraTest\* directories present | >= 5 directories         |        |
| Each contains .html, .js, .css      | Bundle files present     |        |
| Code matches org version            | Includes Phase 3 updates |        |

---

## 4.6 Cross-Reference Audit Scores with Validation Scores

Compare audit report scores against individual validation scores from Phase 2
and Phase 3 to ensure consistency.

| Artifact                         | Phase 2 Score | Phase 3 Score | Audit Score | Match? |
| -------------------------------- | ------------- | ------------- | ----------- | ------ |
| CirraTest_AccountService         | \_\_\_/150    | \_\_\_/150    | \_\_\_/150  |        |
| CirraTest_AccountSelector        | \_\_\_/150    | N/A           | \_\_\_/150  |        |
| CirraTest_AccountRevenueBatch    | \_\_\_/150    | \_\_\_/150    | \_\_\_/150  |        |
| TA_CirraTest_Account_SetDefaults | \_\_\_/150    | \_\_\_/150    | \_\_\_/150  |        |
| CirraTest_Account_Before_Save    | \_\_\_/110    | \_\_\_/110    | \_\_\_/110  |        |
| CirraTest_Opp_After_Save_Task    | \_\_\_/110    | \_\_\_/110    | \_\_\_/110  |        |
| CirraTest_Case_Intake_Screen     | \_\_\_/110    | \_\_\_/110    | \_\_\_/110  |        |
| cirraTestAccountDashboard        | \_\_\_/165    | \_\_\_/165    | \_\_\_/165  |        |
| cirraTestAccountForm             | \_\_\_/165    | \_\_\_/165    | \_\_\_/165  |        |
| cirraTestConfirmModal            | \_\_\_/165    | \_\_\_/165    | \_\_\_/165  |        |

| Check                            | Expected                        | Result |
| -------------------------------- | ------------------------------- | ------ |
| Phase 3 scores >= Phase 2 scores | Updates improved or maintained  |        |
| Audit scores = Phase 3 scores    | Same code version, same results |        |
| No missing artifacts in audit    | All Phase 1 artifacts appear    |        |

---

## 4.7 Verify Org Health Summary

The audit should produce a final summary similar to:

```
Org Health Summary
==================
Overall Score: XX%
Components Audited: NN total (NN Apex + NN Flows + NN LWC)

Domain Breakdown:
  Apex:  avg XX/150 (XX%)  — N below threshold
  Flows: avg XX/110 (XX%)  — N below threshold
  LWC:   avg XX/165 (XX%)  — N below threshold

Top 3 Issues:
  1. [Domain] Issue description
  2. [Domain] Issue description
  3. [Domain] Issue description
```

| Check                           | Expected                                | Result |
| ------------------------------- | --------------------------------------- | ------ |
| Overall score calculated        | Weighted average                        |        |
| All CirraTest\_\* counted       | Matches Phase 1 artifact count          |        |
| Domain averages accurate        | Math correct                            |        |
| Below-threshold counts accurate | Only genuinely low scores               |        |
| Top issues are actionable       | Specific, not generic                   |        |
| No false positives              | Issues correspond to real code patterns |        |

---

## Phase 4 Summary

| Report Format         | Generated | Validated                |
| --------------------- | --------- | ------------------------ |
| Word (.docx)          | Yes       | Content verified         |
| Excel (.xlsx)         | Yes       | 4 sheets verified        |
| HTML (.html)          | Yes       | Viewable, charts present |
| Intermediate files    | Yes       | All artifacts present    |
| Score cross-reference | Yes       | Consistent across phases |
| Org health summary    | Yes       | Accurate and actionable  |
