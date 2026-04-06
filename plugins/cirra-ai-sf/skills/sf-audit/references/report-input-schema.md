# Input Schema for generate_reports.py

The report generator reads JSON files from the `--input-dir` directory.
All files are optional — missing files produce empty sections.

## counts.json

Component inventory counts. Also carries org metadata used in report headers.

```json
{
  "org_name": "Acme Corp",
  "org_id": "00D000000000001AAA",
  "instance": "CS42",
  "apex_classes": 45,
  "apex_triggers": 8,
  "active_flows": 12,
  "process_builders": 3,
  "lwc_bundles": 15,
  "custom_objects": 22,
  "validation_rules": 30,
  "workflow_rules": 5,
  "formula_fields": 42,
  "approval_processes": 3,
  "permission_sets": 18,
  "permission_set_groups": 4,
  "profiles": 6,
  "active_users": 150
}
```

## apex_scores.json

Array of scored Apex classes.

```json
[
  {
    "name": "AccountService",
    "score": 120,
    "max_score": 150,
    "issues": ["Missing null checks", "No test class found"]
  }
]
```

## trigger_findings.json

Array of Apex triggers with qualitative findings (not scored).

```json
[
  {
    "name": "ContactTrigger",
    "object": "Contact",
    "events": "before insert, before update",
    "findings": [{ "severity": "HIGH", "message": "Logic inside trigger body" }]
  }
]
```

## flow_scores.json

Array of scored Flows.

```json
[
  {
    "name": "Account_Update_Flow",
    "process_type": "RecordTriggeredFlow",
    "score": 85,
    "max_score": 110,
    "issues": ["No fault path on DML element"]
  }
]
```

## process_builders.json

Array of Process Builder inventory items (not scored).

```json
[
  {
    "name": "Update_Account_Status",
    "object": "Account",
    "criteria_count": 5,
    "actions_summary": "2 field updates, 1 email alert",
    "migration_priority": "HIGH"
  }
]
```

## lwc_scores.json

Array of scored Lightning Web Components.

```json
[
  {
    "name": "accountDashboard",
    "score": 130,
    "max_score": 165,
    "issues": ["Missing error handling in wire adapter"]
  }
]
```

## permission_findings.json

Array of permission-related findings. Each item must have a `type` field
(`"profile"` or `"permission_set"`) for proper Excel sheet routing.

```json
[
  {
    "type": "permission_set",
    "name": "Full_Access_PS",
    "label": "Full Access",
    "assignments": 3,
    "severity": "CRITICAL",
    "message": "Non-admin Permission Set with ModifyAllData enabled"
  },
  {
    "type": "profile",
    "name": "Custom Sales Profile",
    "user_type": "Standard",
    "key_permissions": "ViewAllData",
    "severity": "HIGH",
    "message": "Custom Profile with ViewAllData"
  }
]
```

## metadata_scores.json

Array of scored custom objects.

```json
[
  {
    "name": "Project__c",
    "score": 90,
    "max_score": 120,
    "field_count": 25,
    "relationship_count": 3,
    "issues": ["Missing description on 5 custom fields"]
  }
]
```

## validation_rules.json

Array of validation rules with findings. Includes formula-body anti-pattern
findings when `ErrorConditionFormula` was retrieved.

```json
[
  {
    "name": "Require_Amount",
    "object": "Opportunity",
    "active": true,
    "findings": [
      { "severity": "MEDIUM", "message": "No bypass mechanism" },
      { "severity": "HIGH", "message": "Formula contains hardcoded Record ID: 0015000000XyZaB" }
    ]
  }
]
```

## formula_fields.json

Array of formula fields with anti-pattern findings.

```json
[
  {
    "name": "Region_Label__c",
    "object": "Account",
    "data_type": "Text",
    "formula_length": 1240,
    "findings": [
      { "severity": "HIGH", "message": "Formula contains hardcoded Record ID: 0125000000AbCdE" },
      {
        "severity": "MEDIUM",
        "message": "Formula contains hardcoded Profile name: \"System Administrator\""
      }
    ]
  },
  {
    "name": "Tier__c",
    "object": "Account",
    "data_type": "Text",
    "formula_length": 320,
    "findings": []
  }
]
```

## workflow_rules.json

Array of workflow rule inventory items. Includes formula-body anti-pattern
findings when criteria/field-update formulas were retrieved via `metadata_read`.

```json
[
  {
    "name": "Set_Default_Status",
    "object": "Case",
    "action_types": "Field Update",
    "migration_priority": "HIGH",
    "findings": [
      {
        "severity": "HIGH",
        "message": "Criteria formula contains hardcoded Record ID: 00Q5000000AbCdE"
      }
    ]
  }
]
```

## other_rules_findings.json

Array of findings from approval processes, escalation rules, assignment rules,
and auto-response rules.

```json
[
  {
    "type": "ApprovalProcess",
    "name": "Discount_Approval",
    "object": "Opportunity",
    "findings": [
      {
        "severity": "HIGH",
        "message": "Entry criteria contains hardcoded Record ID: 0055000000XyZaB"
      }
    ]
  },
  {
    "type": "EscalationRule",
    "name": "Case_Escalation",
    "object": "Case",
    "findings": [
      {
        "severity": "MEDIUM",
        "message": "Rule entry criteria contains hardcoded Profile name: \"Support Agent\""
      }
    ]
  }
]
```
