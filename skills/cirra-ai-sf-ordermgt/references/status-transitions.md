# Status Transition Reference

## Case Status Transitions

### Valid Transitions Matrix

| From \ To     | New | Working | Escalated | Closed |
| ------------- | --- | ------- | --------- | ------ |
| **New**       | -   | Yes     | Yes       | Yes    |
| **Working**   | No  | -       | Yes       | Yes    |
| **Escalated** | No  | Yes     | -         | Yes    |
| **Closed**    | No  | No      | No        | -      |

### Business Rules

1. **Closed cases cannot be reopened.** Reject with: "Cannot reopen a closed case. Please create a new case instead."

2. **Same-status updates are no-ops.** Inform: "Case is already in {status} status. No update needed."

3. **Priority escalation triggers.** When status changes to "Escalated":
   - Consider automatically setting Priority to "High" if currently "Low" or "Medium"
   - Create a CaseComment noting the escalation

4. **Closing a case.** When status changes to "Closed":
   - A reason should be provided (create CaseComment with the reason)
   - Verify any related ReturnOrders are in a terminal state (Fulfilled, Rejected, or Canceled)

## ReturnOrder Status Transitions

### Standard Lifecycle

```
Draft → Submitted → Approved → Partially Fulfilled → Fulfilled
                  ↘ Rejected
                  ↘ Canceled
```

### Valid Transitions

| From \ To               | Draft | Submitted | Approved | Partially Fulfilled | Fulfilled | Rejected | Canceled |
| ----------------------- | ----- | --------- | -------- | ------------------- | --------- | -------- | -------- |
| **Draft**               | -     | Yes       | No       | No                  | No        | No       | Yes      |
| **Submitted**           | No    | -         | Yes      | No                  | No        | Yes      | Yes      |
| **Approved**            | No    | No        | -        | Yes                 | Yes       | No       | Yes      |
| **Partially Fulfilled** | No    | No        | No       | -                   | Yes       | No       | No       |
| **Fulfilled**           | No    | No        | No       | No                  | -         | No       | No       |
| **Rejected**            | No    | No        | No       | No                  | No        | -        | No       |
| **Canceled**            | No    | No        | No       | No                  | No        | No       | -        |

### Operations by Status

| Status              | Can Create Case? | Can Send Label? | Can Add Line Items? |
| ------------------- | ---------------- | --------------- | ------------------- |
| Draft               | No               | No              | Yes                 |
| Submitted           | Yes              | No              | No                  |
| Approved            | Yes              | Yes             | No                  |
| Partially Fulfilled | Yes              | Yes             | No                  |
| Fulfilled           | No               | No              | No                  |
| Rejected            | No               | No              | No                  |
| Canceled            | No               | No              | No                  |

### Return Reasons

Standard return reasons supported:

- **Defective** — Product has manufacturing defect (triggers High priority case)
- **Damaged** — Product was damaged in shipping (triggers High priority case)
- **Wrong Item** — Incorrect product received
- **Not Needed** — Customer no longer needs the product
- **Quality Issue** — Product quality below expectations (triggers High priority case)
- **Size/Color** — Wrong size or color
- **Other** — Other reasons (requires description)

### Priority Determination

When creating a case from a return, priority is determined by the return reason:

| Reason        | Case Priority |
| ------------- | ------------- |
| Defective     | High          |
| Damaged       | High          |
| Quality Issue | High          |
| Wrong Item    | Medium        |
| Not Needed    | Medium        |
| Size/Color    | Medium        |
| Other         | Medium        |
