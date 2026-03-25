# Metadata Setup Guide

Optional custom fields and flows for full Order Management functionality. These are **not** required for basic order status checks, return creation, or case management — only for the return label email tracking feature.

## Custom Fields on ReturnOrder

### LabelEmailSent\_\_c (Checkbox)

Track whether a return label email has been sent. Use `sobject_field_create`:

```
sobject_field_create(
  sObject="ReturnOrder",
  fieldName="LabelEmailSent__c",
  fieldType="Checkbox",
  label="Label Email Sent",
  description="Indicates whether the return shipping label has been emailed to the customer",
  defaultValue=false
)
```

### LabelEmailSentDate\_\_c (DateTime)

Track when the return label email was sent:

```
sobject_field_create(
  sObject="ReturnOrder",
  fieldName="LabelEmailSentDate__c",
  fieldType="DateTime",
  label="Label Email Sent Date",
  description="Date and time when the return shipping label email was sent to the customer"
)
```

## Flow: Send Return Label Email

Auto-launched flow that sends an HTML email with return details to the customer.

### Input Variables

| Variable          | Type   | Description                |
| ----------------- | ------ | -------------------------- |
| returnOrderId     | String | Return Order Salesforce ID |
| customerEmail     | String | Customer email address     |
| returnOrderNumber | String | Return Order Number        |
| returnStatus      | String | Current return status      |
| returnDescription | String | Return description text    |

### Flow Specifications

- **API Name**: `Send_Return_Label_Email`
- **Process Type**: AutoLaunchedFlow
- **API Version**: 60.0+
- **Status**: Active
- **Email Subject**: "Return Label for Return Order #{returnOrderNumber}"
- **Sender**: Current User
- **Body**: HTML formatted with return details and shipping instructions

Use the `sf-flow` skill to create this flow. The flow skill handles JSON-based deployment via `metadata_create` — do not use raw XML.

### Alternative: Manual Email Approach

If deploying a flow is not feasible, the skill falls back to creating a Task record as a reminder to send the label manually. The Task contains all information needed to send the email.

## Optional Flows

### ReturnOrder Status Change Logging

Record-triggered flow that creates Task records when a ReturnOrder status changes, providing an audit trail.

- **Trigger**: ReturnOrder record update where Status field changes
- **Action**: Create a Task with old and new status values

### ReturnOrder Label Email Management

Record-triggered flow that manages the tracking fields automatically.

- **Trigger**: ReturnOrder record update where `LabelEmailSent__c` changes to true
- **Action**: Set `LabelEmailSentDate__c` to the current date/time
