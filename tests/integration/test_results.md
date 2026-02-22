# Integration Test Results

**Sandbox**: `admin@demo2.cirra.ai.dev`
**MCP URL**: `https://mcp.cirra.ai/mcp`
**Mode**: `local-only`
**Run Date**: 2026-02-22 06:16:49 UTC

---

## Summary

| Metric | Count |
| --- | --- |
| Total Steps | 78 |
| Passed | 19 |
| Failed | 0 |
| Skipped | 59 |
| Errors | 0 |

## Phase 1: Setup

| Step | Description | Status | Score | Details |
| --- | --- | --- | --- | --- |
| 1.1 | Initialize MCP connection | SKIP | - | Local-only mode — MCP not available |
| 1.2 | Describe target objects | SKIP | - | Local-only mode — MCP not available |
| 1.3 | Create Apex — Trigger + TAF Action | SKIP | - | Local-only mode — MCP not available for Apex deployment |
| 1.4 | Create Apex — Service Class | SKIP | - | Local-only mode — MCP not available for Apex deployment |
| 1.5 | Create Apex — Selector Class | SKIP | - | Local-only mode — MCP not available for Apex deployment |
| 1.6 | Create Apex — Batch Class | SKIP | - | Local-only mode — MCP not available for Apex deployment |
| 1.7 | Create Apex — Queueable Class | SKIP | - | Local-only mode — MCP not available for Apex deployment |
| 1.8 | Create Apex — Invocable Method | SKIP | - | Local-only mode — MCP not available for Apex deployment |
| 1.9 | Create Flow — Before-Save RT | SKIP | - | Local-only mode — MCP not available for Flow deployment |
| 1.10 | Create Flow — After-Save RT | SKIP | - | Local-only mode — MCP not available for Flow deployment |
| 1.11 | Create Flow — Screen Flow | SKIP | - | Local-only mode — MCP not available for Flow deployment |
| 1.12 | Create Flow — Autolaunched | SKIP | - | Local-only mode — MCP not available for Flow deployment |
| 1.13 | Create Flow — Scheduled | SKIP | - | Local-only mode — MCP not available for Flow deployment |
| 1.14 | Create Flow — Platform Event | SKIP | - | Local-only mode — MCP not available for Flow deployment |
| 1.15 | Create LWC — Wire Datatable | SKIP | - | Local-only mode — MCP not available for LWC deployment |
| 1.16 | Create LWC — Form Component | SKIP | - | Local-only mode — MCP not available for LWC deployment |
| 1.17 | Create LWC — Flow Screen | SKIP | - | Local-only mode — MCP not available for LWC deployment |
| 1.18 | Create LWC — Modal Component | SKIP | - | Local-only mode — MCP not available for LWC deployment |
| 1.19 | Create LWC — GraphQL Component | SKIP | - | Local-only mode — MCP not available for LWC deployment |
| 1.20 | Insert test data — 10 Accounts | PASS | - | Pre-flight validation passed for 10 Account inserts |
| 1.21 | Insert test data — 20 Contacts | SKIP | - | Local-only mode — requires Account IDs from step 1.20 |
| 1.22 | Insert test data — 15 Opportunities | SKIP | - | Local-only mode — requires Account IDs |
| 1.23 | Insert test data — 10 Cases | SKIP | - | Local-only mode — requires Account IDs |
| 1.24 | Insert test data — 10 Leads | PASS | - | Pre-flight validation passed for 10 Lead inserts |
| 1.25 | Insert test data — Tasks + Events | SKIP | - | Local-only mode — requires Contact/Account IDs |
| 1.26 | Insert test data — 251 Bulk Accounts | PASS | - | Pre-flight validation passed for 251 bulk Account inserts |
| 1.27 | Insert test data — Hierarchy | SKIP | - | Local-only mode — requires sequential inserts with IDs |

## Phase 2: Validate

| Step | Description | Status | Score | Details |
| --- | --- | --- | --- | --- |
| 2.1 | Validate data — Pre-flight insert | PASS | - | Pre-flight insert validation passed, no errors |
| 2.2 | Validate data — SOQL syntax check | PASS | - | SOQL syntax validation passed |
| 2.3 | Validate data — PII detection | PASS | - | PII detected: SSN + personal email (2 warnings) |
| 2.4 | Query data — Basic Account query | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.5 | Query data — Parent-to-child subquery | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.6 | Query data — Child-to-parent dot notation | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.7 | Query data — Aggregate GROUP BY | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.8 | Query data — Semi-join | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.9 | Query data — Anti-join | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.10 | Query data — Polymorphic Task query | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.11 | Query data — Bulk records verification | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.12 | Query data — Hierarchy verification | PASS | - | SOQL syntax valid (local pre-flight only) |
| 2.13 | Validate Apex — Single class (local) | PASS | 150/150 | 🔍 Apex Validation: CirraTest_AccountService.cls ════════════════════════════════ |
| 2.14 | Validate Apex — Comma-separated list (local) | PASS | - | All 3 classes >= 90/150: CirraTest_AccountService.cls: 150/150; CirraTest_Accoun |
| 2.15 | Validate Apex — All classes | SKIP | - | --all requires live org fetch via tooling_api_query |
| 2.16 | Validate Flow — Single flow (local) | SKIP | - | Flow validator missing shared modules (naming_validator, security_validator) |
| 2.17 | Validate Flow — Comma-separated list | SKIP | - | Flow validator missing shared modules |
| 2.18 | Validate Flow — All flows | SKIP | - | Requires live MCP + shared modules |
| 2.19 | Validate LWC — Single component (local) | PASS | 163/165 | Score: 163/165 — Production-ready SLDS 2 |
| 2.20 | Validate LWC — Comma-separated list | PASS | - | All 3 files >= 100/165: cirraTestAccountDashboard.css: 165/165; cirraTestAccount |
| 2.21 | Validate LWC — All components | SKIP | - | --all requires live org fetch via metadata_read |

## Phase 3: Update

| Step | Description | Status | Score | Details |
| --- | --- | --- | --- | --- |
| 3.1 | Update Apex — Add method to service class | SKIP | - | Requires live MCP + interactive session |
| 3.2 | Update Apex — Modify trigger action logic | SKIP | - | Requires live MCP + interactive session |
| 3.3 | Update Apex — Add error handling to batch | SKIP | - | Requires live MCP + interactive session |
| 3.4 | Update Flow — Add decision branch | SKIP | - | Requires live MCP + interactive session |
| 3.5 | Update Flow — Add fault handling | SKIP | - | Requires live MCP + interactive session |
| 3.6 | Update Flow — Add screen to screen flow | SKIP | - | Requires live MCP + interactive session |
| 3.7 | Update LWC — Add dark mode CSS | SKIP | - | Requires live MCP + interactive session |
| 3.8 | Update LWC — Add column to datatable | SKIP | - | Requires live MCP + interactive session |
| 3.9 | Update LWC — Fix accessibility on modal | SKIP | - | Requires live MCP + interactive session |
| 3.10 | Update LWC — Add Apex integration to form | SKIP | - | Requires live MCP + interactive session |
| 3.11 | Update data — Bulk update records | SKIP | - | Requires live MCP + interactive session |
| 3.12 | Update data — Upsert with external ID | SKIP | - | Requires live MCP + interactive session |
| 3.13 | Verify updates via query | SKIP | - | Requires live MCP + interactive session |
| 3.14 | Re-validate all Apex after updates | SKIP | - | Requires live MCP + interactive session |
| 3.15 | Re-validate all Flows after updates | SKIP | - | Requires live MCP + interactive session |
| 3.16 | Re-validate all LWC after updates | SKIP | - | Requires live MCP + interactive session |

## Phase 4: Audit

| Step | Description | Status | Score | Details |
| --- | --- | --- | --- | --- |
| 4.1 | Run full org audit | SKIP | - | Requires live MCP + /audit-org command |
| 4.2 | Validate Word report | SKIP | - | Requires live MCP + /audit-org command |
| 4.3 | Validate Excel report | SKIP | - | Requires live MCP + /audit-org command |
| 4.4 | Validate HTML report | SKIP | - | Requires live MCP + /audit-org command |
| 4.5 | Validate intermediate files | SKIP | - | Requires live MCP + /audit-org command |
| 4.6 | Cross-reference audit scores | SKIP | - | Requires live MCP + /audit-org command |
| 4.7 | Verify org health summary | SKIP | - | Requires live MCP + /audit-org command |

## Phase 5: Cleanup

| Step | Description | Status | Score | Details |
| --- | --- | --- | --- | --- |
| 5.1 | Delete test data (dependency order) | SKIP | - | Requires live MCP |
| 5.2 | Delete bulk test data | SKIP | - | Requires live MCP |
| 5.3 | Delete flows | SKIP | - | Requires live MCP |
| 5.4 | Delete LWC components | SKIP | - | Requires live MCP |
| 5.5 | Delete Apex classes and triggers | SKIP | - | Requires live MCP |
| 5.6 | Clean up audit output | SKIP | - | Requires live MCP |
| 5.7 | Final verification — zero CirraTest_ artifacts | SKIP | - | Requires live MCP |

## Validation Scores

| Step | Description | Score | Max | % | Threshold | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 2.13 | Validate Apex — Single class (local) | 150 | 150 | 100.0% | >= 90 (60%) | PASS |
| 2.19 | Validate LWC — Single component (local) | 163 | 165 | 98.8% | >= 100 (61%) | PASS |
