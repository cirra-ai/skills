## Flow Screen Integration

LWC components can be embedded in Flow Screens for custom UI experiences within guided processes.

### Key Concepts

| Mechanism                      | Direction  | Purpose                       |
| ------------------------------ | ---------- | ----------------------------- |
| `@api` with `role="inputOnly"` | Flow → LWC | Pass context data             |
| `FlowAttributeChangeEvent`     | LWC → Flow | Return user selections        |
| `FlowNavigationFinishEvent`    | LWC → Flow | Programmatic Next/Back/Finish |
| `availableActions`             | Flow → LWC | Check available navigation    |

### Quick Example

```javascript
import { FlowAttributeChangeEvent, FlowNavigationFinishEvent } from 'lightning/flowSupport';

@api recordId;           // Input from Flow
@api selectedRecordId;   // Output to Flow
@api availableActions = [];

handleSelect(event) {
    this.selectedRecordId = event.detail.id;
    // CRITICAL: Notify Flow of the change
    this.dispatchEvent(new FlowAttributeChangeEvent(
        'selectedRecordId',
        this.selectedRecordId
    ));
}

handleNext() {
    if (this.availableActions.includes('NEXT')) {
        this.dispatchEvent(new FlowNavigationFinishEvent('NEXT'));
    }
}
```

**For complete Flow integration patterns, see:**

- [assets/flow-integration-guide.md](assets/flow-integration-guide.md)
- [assets/triangle-pattern.md](assets/triangle-pattern.md)

---
