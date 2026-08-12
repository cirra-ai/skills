## LWC Integration (Screen Flows)

Embed custom Lightning Web Components in Flow Screens for rich, interactive UIs.

### Templates

| Template                          | Purpose                            |
| --------------------------------- | ---------------------------------- |
| `assets/screen-flow-with-lwc.xml` | Flow embedding LWC component       |
| `assets/apex-action-template.xml` | Flow calling Apex @InvocableMethod |

### Flow Pattern (XML reference — deploy as JSON)

> The XML below shows the structural pattern. When deploying via `metadata_create`, translate to the equivalent JSON object.

```xml
<screens>
    <fields>
        <extensionName>c:recordSelector</extensionName>
        <fieldType>ComponentInstance</fieldType>
        <inputParameters>
            <name>recordId</name>
            <value><elementReference>var_RecordId</elementReference></value>
        </inputParameters>
        <outputParameters>
            <assignToReference>var_SelectedId</assignToReference>
            <name>selectedRecordId</name>
        </outputParameters>
    </fields>
</screens>
```

### Documentation

| Resource              | Location                                                                              |
| --------------------- | ------------------------------------------------------------------------------------- |
| LWC Integration Guide | [references/lwc-integration-guide.md](references/lwc-integration-guide.md)            |
| LWC Component Setup   | [sf-lwc/assets/flow-integration-guide.md](../sf-lwc/assets/flow-integration-guide.md) |
| Triangle Architecture | [references/triangle-pattern.md](references/triangle-pattern.md)                      |

---
