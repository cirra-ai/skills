# Pool Object Setup

How to create and configure the `Environment_Pool__c` custom object for sandbox pool management.

## Automated Setup (Recommended)

The sf-sandbox-manager skill's **Pool Setup** workflow automatically creates the object, fields, and Permission Set. Run:

```
/sf-sandbox-manager setup
```

This calls `sobject_create`, `sobject_field_create`, and `metadata_create` to provision everything. See the Pool Setup section in SKILL.md for the exact tool calls.

## Manual Setup (Salesforce Setup UI)

For admins who prefer to create the object manually.

### Step 1: Create the Custom Object

1. Go to **Setup → Object Manager → Create → Custom Object**
2. Configure:
   - Label: `Environment Pool`
   - Plural Label: `Environment Pool`
   - Object Name: `Environment_Pool`
   - Record Name: `Pool Entry Name`
   - Data Type: `Auto Number`
   - Display Format: `ENV-{0000}`
   - Starting Number: `0`
   - Description: `Tracks sandbox environments for pool checkout/checkin lifecycle management`
3. Save

### Step 2: Create Custom Fields

Create each field on the `Environment_Pool__c` object:

| #   | Label              | API Name                | Type      | Length | Required | Notes                                                          |
| --- | ------------------ | ----------------------- | --------- | ------ | -------- | -------------------------------------------------------------- |
| 1   | Environment Name   | `Environment_Name__c`   | Text      | 80     | Yes      | Set as External ID and Unique                                  |
| 2   | Environment Type   | `Environment_Type__c`   | Picklist  | —      | Yes      | Values: Developer, Developer_Pro, Partial, Full                |
| 3   | Status             | `Status__c`             | Picklist  | —      | Yes      | Values: Available, Checked_Out, Pending_Reset, Creating, Error |
| 4   | Checked Out By     | `Checked_Out_By__c`     | Text      | 255    | No       |                                                                |
| 5   | Checkout Timestamp | `Checkout_Timestamp__c` | Date/Time | —      | No       |                                                                |
| 6   | Expected Return    | `Expected_Return__c`    | Date/Time | —      | No       |                                                                |
| 7   | Expiry Date        | `Expiry_Date__c`        | Date      | —      | No       |                                                                |
| 8   | Purpose            | `Purpose__c`            | Text      | 255    | No       |                                                                |
| 9   | Org ID             | `Org_Id__c`             | Text      | 18     | No       |                                                                |
| 10  | Login URL          | `Login_Url__c`          | URL       | —      | No       |                                                                |
| 11  | Last Reset         | `Last_Reset__c`         | Date/Time | —      | No       |                                                                |
| 12  | Sandbox Process ID | `Sandbox_Process_Id__c` | Text      | 18     | No       |                                                                |

### Step 3: Create Permission Set

1. Go to **Setup → Permission Sets → New**
2. Configure:
   - Label: `Environment Pool Access`
   - API Name: `Environment_Pool_Access`
   - Description: `Grants full access to Environment_Pool__c for sandbox pool management`
3. Object Settings → Environment Pool:
   - Read, Create, Edit, Delete: ✓
   - View All: ✓
4. Field Permissions → all custom fields:
   - Read Access: ✓
   - Edit Access: ✓
5. Save

### Step 4: Assign Permission Set

Assign `Environment_Pool_Access` to all users who need to manage the sandbox pool:

1. Go to **Setup → Permission Sets → Environment Pool Access → Manage Assignments**
2. Add the relevant users

### Step 5: Create List Views (Optional)

Create useful list views for the pool dashboard:

**All Environments:**

- Filter: none (show all records)
- Columns: Environment Name, Environment Type, Status, Checked Out By, Purpose, Expiry Date

**Available Environments:**

- Filter: `Status__c = 'Available'`
- Columns: Environment Name, Environment Type, Last Reset, Expiry Date

**Checked Out:**

- Filter: `Status__c = 'Checked_Out'`
- Columns: Environment Name, Checked Out By, Checkout Timestamp, Expected Return, Purpose

**Needs Attention:**

- Filter: `Status__c IN ('Pending_Reset', 'Creating', 'Error')`
- Columns: Environment Name, Status, Environment Type, Sandbox Process ID

## Validation Rules (Optional)

### Expected Return Must Be Future

Prevents users from setting an expected return date in the past.

- Rule Name: `Expected_Return_Must_Be_Future`
- Error Condition Formula:
  ```
  AND(
    NOT(ISBLANK(Expected_Return__c)),
    Expected_Return__c < NOW()
  )
  ```
- Error Message: `Expected return date must be in the future.`
- Error Location: `Expected_Return__c`

### Checkout Fields Required When Checked Out

Ensures checkout metadata is populated when status is Checked Out.

- Rule Name: `Checkout_Fields_Required`
- Error Condition Formula:
  ```
  AND(
    ISPICKVAL(Status__c, "Checked_Out"),
    OR(
      ISBLANK(Checked_Out_By__c),
      ISBLANK(Checkout_Timestamp__c)
    )
  )
  ```
- Error Message: `Checked Out By and Checkout Timestamp are required when status is Checked Out.`
- Error Location: Top of page

## Flow Automation (Optional)

### Stale Checkout Alert

A scheduled flow that runs daily and sends alerts for overdue checkouts.

- Type: Schedule-Triggered Flow
- Schedule: Daily at 8:00 AM
- Object: `Environment_Pool__c`
- Entry Criteria: `Status__c = 'Checked_Out' AND Expected_Return__c < NOW()`
- Action: Send email alert to the `Checked_Out_By__c` address and the pool administrator

### Auto-Expiry Warning

A scheduled flow that warns about sandboxes nearing their refresh expiry date.

- Type: Schedule-Triggered Flow
- Schedule: Weekly on Monday
- Object: `Environment_Pool__c`
- Entry Criteria: `Expiry_Date__c != null AND Expiry_Date__c <= TODAY() + 7`
- Action: Send email alert to the pool administrator
