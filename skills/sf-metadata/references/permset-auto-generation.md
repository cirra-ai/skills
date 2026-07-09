<!-- Parent: sf-metadata/SKILL.md -->

# Permission Set Generation (Access Strategy — Layer 1)

This is **Layer 1 (Object CRUD + FLS)** of the Phase 3.5 Access Strategy — see
`access-strategy.md` for the full, no-guesswork plan (page layouts, Lightning
record pages, and list-view/Kanban visibility are Layers 2–4).

After creating Custom Objects or Fields, ALWAYS propose object/field access via a
Permission Set, and confirm the **specific** permission set(s) / profile(s) with
the user — never assume the audience.

## Prompt Template

```
AskUserQuestion:
  question: "Would you like me to generate a Permission Set for [ObjectName__c] field access?"
  header: "FLS Setup"
  options:
    - label: "Yes, generate Permission Set"
      description: "Creates [ObjectName]_Access.permissionset-meta.xml with object CRUD and field access"
    - label: "No, I'll handle FLS manually"
      description: "Skip Permission Set generation - you'll configure FLS via Setup or Profile"
```

## Generation Rules

| Field Type      | Include in Permission Set? | Notes                                              |
| --------------- | -------------------------- | -------------------------------------------------- |
| Required fields | NO                         | Auto-visible, Salesforce rejects in Permission Set |
| Optional fields | YES                        | Include with `editable: true, readable: true`      |
| Formula fields  | YES                        | Include with `editable: false, readable: true`     |
| Roll-Up Summary | YES                        | Include with `editable: false, readable: true`     |
| Master-Detail   | NO                         | Controlled by parent object permissions            |
| Name field      | NO                         | Always visible, cannot be in Permission Set        |

## Workflow

1. **Collect field information** from created metadata
2. **Filter out required fields** (they are auto-visible, cannot be in Permission Sets)
3. **Filter out formula fields** (can only be readable, not editable)
4. **Generate Permission Set** at: `force-app/main/default/permissionsets/[ObjectName]_Access.permissionset-meta.xml`

## Example Auto-Generated Permission Set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Auto-generated: Grants access to Customer_Feedback__c and its fields</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Customer Feedback Access</label>

    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Customer_Feedback__c</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>

    <!-- NOTE: Required fields are EXCLUDED (auto-visible) -->
    <!-- NOTE: Formula fields have editable=false -->

    <fieldPermissions>
        <editable>true</editable>
        <field>Customer_Feedback__c.Optional_Field__c</field>
        <readable>true</readable>
    </fieldPermissions>
</PermissionSet>
```
