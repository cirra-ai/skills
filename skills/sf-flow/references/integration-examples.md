## Cirra AI Integration Examples

### Example 1: Verify Object Exists Before Creating Flow

```python
# Before generating a flow for a custom object
sobject_describe(
    sObject="Invoice__c",
    sf_user="prod-username"
)
# Returns: Field list, object metadata, standard fields
```

### Example 2: List Existing Flows

```python
# Check what flows already exist
metadata_list(
    type="Flow",
    sf_user="prod-username"
)
# Returns: All Flow metadata objects in org
```

### Example 3: Deploy a Complete Record-Triggered Flow

> **Pattern note:** the `faultConnector` on `Send_Email_Action` routes to the
> `Log_Error` step. This is the "error-log object" pattern from the
> fault-destination rubric: if the email fails (e.g. domain not verified,
> recipient suppressed), the originating Case save is **not** blocked, and
> the failure is captured in `Flow_Error__c` for investigation. See the
> rubric for alternative fault destinations.

```python
# Complete example: notify managers when case category changes
metadata_create(
    type="Flow",
    metadata=[{
        "fullName": "Case_Category_Change_Alert",
        "apiVersion": 65,
        "description": "Sends email when Case Category changes from Billing to Channel. Side-effect flow: email failures are caught via faultConnector so the originating Case save is never blocked.",
        "environments": ["Default"],
        "interviewLabel": "Case Category Change Alert {!$Flow.CurrentDateTime}",
        "label": "Case Category Change Alert",
        "processMetadataValues": [
            {"name": "BuilderType", "value": {"stringValue": "LightningFlowBuilder"}},
            {"name": "CanvasMode", "value": {"stringValue": "AUTO_LAYOUT_CANVAS"}}
        ],
        "processType": "AutoLaunchedFlow",
        "start": {
            "locationX": 0, "locationY": 0,
            "connector": {"targetReference": "Check_Previous_Category"},
            "filterLogic": "and",
            "filters": [
                {"field": "Case_Category__c", "operator": "EqualTo", "value": {"stringValue": "Channel"}},
                {"field": "Case_Category__c", "operator": "IsChanged", "value": {"booleanValue": True}}
            ],
            "object": "Case",
            "recordTriggerType": "Update",
            "triggerType": "RecordAfterSave"
        },
        "decisions": [{
            "name": "Check_Previous_Category",
            "label": "Check Previous Category",
            "locationX": 0, "locationY": 0,
            "defaultConnectorLabel": "Default Outcome",
            "rules": [{
                "name": "Was_Billing",
                "conditionLogic": "and",
                "conditions": [{
                    "leftValueReference": "$Record__Prior.Case_Category__c",
                    "operator": "EqualTo",
                    "rightValue": {"stringValue": "Billing"}
                }],
                "connector": {"targetReference": "Send_Email_Action"},
                "label": "Was Billing"
            }]
        }],
        "actionCalls": [{
            "name": "Send_Email_Action",
            "label": "Send Email",
            "locationX": 0, "locationY": 0,
            "actionName": "emailSimple",
            "actionType": "emailSimple",
            "flowTransactionModel": "CurrentTransaction",
            "inputParameters": [
                {"name": "emailAddresses", "value": {"stringValue": "support-managers@example.com"}},
                {"name": "emailSubject", "value": {"stringValue": "Case Category Changed to Channel"}},
                {"name": "emailBody", "value": {"stringValue": "Case {!$Record.CaseNumber} category changed from Billing to Channel."}}
            ],
            "faultConnector": {"targetReference": "Log_Error"}
        }],
        "recordCreates": [{
            "name": "Log_Error",
            "label": "Log Error",
            "locationX": 0, "locationY": 0,
            "object": "Flow_Error__c",
            "inputAssignments": [
                {"field": "Flow_Name__c", "value": {"stringValue": "Case_Category_Change_Alert"}},
                {"field": "Context_Record_Id__c", "value": {"elementReference": "$Record.Id"}},
                {"field": "Error_Source__c", "value": {"stringValue": "Send_Email_Action"}}
            ]
        }],
        "status": "Draft"
    }],
    sf_user="prod-username"
)
```

### Example 4: Retrieve Existing Flow for Review

```python
# Get the metadata of an existing flow
metadata_read(
    type="Flow",
    fullNames=["Auto_Lead_Assignment"],
    sf_user="prod-username"
)
# Returns: Complete Flow metadata from org (JSON)
```

### Example 5: Find All Active Flows

Two correct options — see "Query Tool Routing" under Flow MCP Patterns:

```python
# Option A: flow catalog via the standard object (soql_query, NOT tooling_api_query)
soql_query(
    query="SELECT DurableId, ApiName, Label, ProcessType, TriggerType, IsActive FROM FlowDefinitionView WHERE IsActive = true",
    sf_user="prod-username"
)

# Option B: Tooling API (FlowDefinition has no ApiName/Status fields —
# use DeveloperName, and ActiveVersionId != null for "active")
tooling_api_query(
    sObject="FlowDefinition",
    fields=["Id", "DeveloperName", "Description", "ActiveVersionId"],
    whereClause="ActiveVersionId != null",
    sf_user="prod-username"
)
```

---
