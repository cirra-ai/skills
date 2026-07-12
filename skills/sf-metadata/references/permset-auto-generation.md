<!-- Parent: sf-metadata/SKILL.md -->

# Permission Set Generation (Access Strategy — Layer 1)

This is **Layer 1 (Object CRUD + FLS)** of the Phase 3.5 Access Strategy — see
`access-strategy.md` for the full, no-guesswork plan (page layouts, Lightning
record pages, and list-view/Kanban visibility are Layers 2–4).

After creating Custom Objects or Fields, ALWAYS propose object/field access via a
Permission Set, and confirm the **specific** permission set(s) / profile(s) with
the user — never assume the audience.

## Prompt Template

Do **not** ask a yes/no "generate a Permission Set?" question — that reintroduces
silent defaults. Use the **mandatory access-strategy prompt** in
`access-strategy.md` ("The mandatory prompt"), which makes the user name the
**concrete** permission set(s) / profile(s) for object + FLS access (Layer 1)
alongside the other layers. Collect the specific names before creating anything:

```
AskUserQuestion:
  question: "Who should have object + field access to [ObjectName__c]? Name the exact PERMISSION SET(S) and/or PROFILE(S) — no guesswork. (Permission sets recommended; profile edits cost credits.)"
  header: "Access — Layer 1"
  options:
    - label: "New permission set [ObjectName]_Access"
      description: "Create a new permission set with object CRUD + FLS; you confirm its name and who it's assigned to."
    - label: "Add to existing permission set(s)"
      description: "You name the existing permission set(s) to extend with this object/field access."
    - label: "Grant via named profile(s)"
      description: "You name the exact profile(s); I warn about per-profile credit cost before proceeding."
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
