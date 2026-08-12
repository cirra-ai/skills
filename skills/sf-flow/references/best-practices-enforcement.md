## Best Practices (Built-In Enforcement)

### ⛔ CRITICAL: Save-blocking is opt-in, not opt-out

**No record-triggered flow should block the originating save unless blocking is an
explicit, stated requirement.** This is the single most important architectural
rule in this skill — it overrides every other consideration except security.

Why this matters: in a `RecordAfterSave` flow, any unhandled fault in any element
propagates back to the originating DML as `CANNOT_EXECUTE_FLOW_TRIGGER`, blocking
the save. From the user's perspective, the record appears to fail to save —
when in reality the save would have succeeded but a downstream side effect
(an email server, a callout, a custom notification) failed. The wrong incident
gets paged: the team spends the afternoon debugging an "opportunity creation
bug" that is actually an email outage.

**Classify every record-triggered flow before designing it:**

| Category                        | Trigger type       | Fault handling                                                | Examples                                                                                           |
| ------------------------------- | ------------------ | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Side-effect flow** (default)  | `RecordAfterSave`  | Every fallible element MUST have a `faultConnector`           | Notifications, logging, integrations, derived-field computation, async work                        |
| **Save-gating flow** (explicit) | `RecordBeforeSave` | Faults intentionally propagate; document why in `description` | Validation that the platform's validation rules can't express, regulatory gates, anti-fraud checks |

If you can't articulate which category your flow belongs to, it's a side-effect
flow — handle the faults.

**The fallible elements** (every one of these can fail at runtime and must have
a `faultConnector` in a side-effect flow):

- `recordCreates`, `recordUpdates`, `recordDeletes` — DML failures (validation rules,
  permission errors, locked rows, governor limits)
- `recordLookups` — query failures, permission errors, missing records
- `actionCalls` — this is the one that gets missed. `emailSimple`, `emailAlert`,
  custom notifications, platform events, Apex invocable methods, external
  callouts, and Send Custom Notification all sit under `actionCalls`. **Email
  in particular fails for reasons completely outside the flow's control**
  (unverified domain, suppressed recipient, bounce rules, deliverability
  configuration). Missing a fault connector here is the most common way a
  notification flow becomes a save-blocking incident.
- `subflows` — the called subflow can fault; that fault propagates up
- `waits` — alarm/event resume can fault

**Save-gating flows must be documented.** When you do legitimately want to block
a save (i.e. the save shouldn't happen if the flow can't complete), the
`description` field of the flow must say so explicitly. Future maintainers
must be able to tell whether the absence of a fault connector is intentional
or a bug. Suggested phrasing:

> "Save-gating: this flow validates X before allowing the record to save.
> Faults are intentionally propagated to block invalid saves."

### ⛔ CRITICAL: Record-Triggered Flow Architecture

**NEVER loop over triggered records.** `$Record` = single record; platform handles batching.

| Pattern                          | OK? | Notes                                                     |
| -------------------------------- | --- | --------------------------------------------------------- |
| `$Record.FieldName`              | ✅  | Direct field access                                       |
| `$Record.Lookup__r.FieldName`    | ✅  | Relationship traversal — NO Get Records needed            |
| `$Record.Account__r.Owner.Name`  | ✅  | Multi-level traversal (up to 5 levels)                    |
| Get Records for `$Record` lookup | ❌  | Wastes SOQL — use `$Record.Relationship__r.Field` instead |
| Loop over `$Record__c`           | ❌  | Process Builder pattern, not Flow                         |
| Loop over `$Record`              | ❌  | $Record is single, not collection                         |

**`$Record` relationship traversal**: In record-triggered flows, `$Record` provides access to related records through lookup/master-detail fields WITHOUT a Get Records element. Use `{!$Record.Contact__r.FirstName}` instead of querying Contact separately. Only use Get Records when you need related records that are NOT accessible through `$Record` lookups (e.g., child records, or records with no relationship to the trigger object).

**Loops for RELATED records only**: Get Records → Loop collection → Assignment → DML after loop

### ⛔ CRITICAL: No Parent Traversal in Get Records

`recordLookups` cannot query `Parent.Field` (e.g., `Manager.Name`). **Solution**: Two Get Records - child first, then parent by Id.

### ⛔ CRITICAL: No Compound Fields in Formulas

Compound fields — the person **`Name`** (on Contact and Lead), **Address** fields (`BillingAddress`, `MailingAddress`, …), and **Geolocation** fields — **cannot be used in formula expressions** except inside `ISBLANK`, `ISNULL`, or `ISCHANGED`. Concatenating, comparing, or wrapping them in `TEXT()` is a save/deploy error ("Contact formulas can't use the compound Name").

| Compound field (object)    | ❌ In a formula             | ✅ Use component fields                                 |
| -------------------------- | --------------------------- | ------------------------------------------------------- |
| `Name` (Contact, Lead)     | `{!$Record.Name}`           | `{!$Record.FirstName} & " " & {!$Record.LastName}`      |
| `MailingAddress` (Contact) | `{!$Record.MailingAddress}` | `{!$Record.MailingStreet}`, `{!$Record.MailingCity}`, … |
| `BillingAddress` (Account) | `{!$Record.BillingAddress}` | `{!$Record.BillingStreet}`, `{!$Record.BillingCity}`, … |

`Account.Name` / `Opportunity.Name` are **plain text** (not compound) and are fine in formulas. `ISBLANK({!$Record.MailingAddress})` is allowed. See [references/xml-gotchas.md](references/xml-gotchas.md#compound-fields-cannot-be-used-in-formulas) and the [Salesforce compound-field limitations doc](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/compound_fields_limitations.htm). The validator flags this as a CRITICAL issue.

### recordLookups Best Practices

| Element                            | Recommendation                          | Why                                                                                                                                                    |
| ---------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `getFirstRecordOnly`               | Set to `true` for single-record queries | Avoids collection overhead                                                                                                                             |
| `storeOutputAutomatically`         | Set to `true` (default)                 | Simpler, modern approach — auto-stores all fields. Only set to `false` with explicit field selection when handling sensitive data in system-mode flows |
| `assignNullValuesIfNoRecordsFound` | Set to `false`                          | Preserves previous variable value                                                                                                                      |
| `faultConnector`                   | Always include                          | Handle query failures gracefully                                                                                                                       |
| `filterLogic`                      | Use `and` for multiple filters          | Clear filter behavior                                                                                                                                  |

### Critical Requirements

- **API 65.0**: Latest features
- **No DML in Loops**: Collect in loop → DML after loop (causes bulk failures otherwise)
- **Bulkify**: For RELATED records only - platform handles triggered record batching
- **Fault Paths**: All DML must have fault connectors
  - ⚠️ **Fault connectors CANNOT self-reference** - Error: "element cannot be connected to itself"
  - Route fault connectors to a DIFFERENT element (dedicated error handler)

#### Fault-destination rubric

When you add a `faultConnector`, the question "where does it go?" has five
common answers, each with a different trade-off. Pick deliberately:

| Fault destination                                                                                                         | When to use                                                                                        | Trade-off                                                                       |
| ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Terminating end** (no further connector after the fault element)                                                        | Transient external failure; OK to retry on next edit; flow is genuinely fire-and-forget            | Can re-fire repeatedly until the external dependency recovers — noisy logs      |
| **Same dedup/idempotency step as success path** (e.g., set a `*_Notified__c` flag whether or not the email actually sent) | One-shot side effect; "best effort" semantics; want to avoid retry storms                          | Lost work stays lost — no auto-recovery when the external dependency comes back |
| **Error-log object** (`Flow_Error__c` or similar)                                                                         | Production org with observability requirements; want failures investigable                         | Requires the log object to exist and be writable in flow context                |
| **Platform event**                                                                                                        | Multiple downstream subscribers need to know about failures (monitoring, alerting, retry handlers) | Heavier; only worth it when something actually subscribes                       |
| **Continue down the same path after a best-effort attempt**                                                               | The failed action was optional enrichment, not core to the flow's purpose                          | Hides failures unless logged; use sparingly                                     |

**Default for most side-effect flows: terminating end OR same-as-success
dedup step.** Pick the dedup-step pattern when the cost of duplicate
notifications/work is high; pick the terminating-end pattern when transient
recovery is desirable.

- **Auto-Layout**: All locationX/Y = 0 (cleaner git diffs)
  - UI may show "Free-Form" dropdown, but locationX/Y = 0 IS Auto-Layout in metadata
- **No Parent Traversal**: Use separate Get Records for relationship field data

### Property Ordering (CRITICAL)

**All properties of the same type MUST be grouped together. Do NOT scatter them across the object.**

Complete alphabetical order:

```
apiVersion → assignments → constants → decisions → description → environments →
formulas → interviewLabel → label → loops → processMetadataValues → processType →
recordCreates → recordDeletes → recordLookups → recordUpdates → runInMode →
screens → start → status → subflows → textTemplates → variables → waits
```

**Common Mistake**: Adding an assignment near related logic (e.g., after a loop) when other assignments exist earlier.

- **Error**: "Element assignments is duplicated at this location"
- **Fix**: Move ALL assignments to the assignments section

### Performance

- **Batch DML**: Get Records → Assignment → Update Records pattern
- **Filters over loops**: Use Get Records with filters instead of loops + decisions
- **Transform element**: Powerful but complex structure - NOT recommended for hand-written flows

### Design & Security

- **Variable Names (v2.0.0)**: Use prefixes for clarity:
  - `var_` Regular variables (e.g., `var_AccountName`)
  - `col_` Collections (e.g., `col_ContactIds`)
  - `rec_` Record variables (e.g., `rec_Account`)
  - `inp_` Input variables (e.g., `inp_RecordId`)
  - `out_` Output variables (e.g., `out_IsSuccess`)
- **Element Names**: PascalCase_With_Underscores (e.g., `Check_Account_Type`)
- **Button Names (v2.0.0)**: `Action_[Verb]_[Object]` (e.g., `Action_Save_Contact`)
- **System vs User Mode**: Understand implications, validate FLS for sensitive fields
- **No hardcoded data**: Use variables/custom settings
- See `references/flow-best-practices.md` for comprehensive guidance
