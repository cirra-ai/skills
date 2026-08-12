## Common Error Patterns

**DML in Loop**: Collect records in collection variable → Single DML after loop
**Missing Fault Path**: Add fault connector from DML → error handling → log/display
**Self-Referencing Fault**: Error "element cannot be connected to itself" → Route fault connector to DIFFERENT element
**Element Duplicated**: Error "Element X is duplicated" → Group ALL elements of same type together
**Field Not Found**: Verify field exists, deploy field first if missing
**Insufficient Permissions**: Check profile permissions, consider System mode

| Error Pattern                   | Fix                                                     |
| ------------------------------- | ------------------------------------------------------- |
| `$Record__Prior` in Create-only | Only valid for Update/CreateAndUpdate triggers          |
| "Parent.Field doesn't exist"    | Use TWO Get Records (child then parent)                 |
| `$Record__c` loop fails         | Use `$Record` directly (single context, not collection) |

### Error → Solution Quick Reference

| Error Message                                       | Solution                                                                     |
| --------------------------------------------------- | ---------------------------------------------------------------------------- |
| `Duplicate developer name: X`                       | Screen field already created this reference — don't add a separate variable  |
| `Can't use object field with sObjectInputReference` | Remove `object` property when using `inputReference`                         |
| `isCollection invalid in FlowConstant`              | Use Decision + Variable counter instead of a constant collection             |
| `Invalid element reference X not found`             | Check all element names are unique and connectors point to existing elements |
| Flow won't open in Flow Builder                     | Add all empty element type arrays to flow metadata                           |
| Silent failure on `metadata_update`                 | Read current state first with `metadata_read`; build iteratively             |
| Required field missing                              | Add `processMetadataValues: []` to every element                             |

**Metadata Gotchas**: See `references/xml-gotchas.md`

---
