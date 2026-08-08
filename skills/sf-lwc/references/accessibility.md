## Accessibility

WCAG compliance is mandatory for all components.

### Quick Checklist

| Requirement      | Implementation                                          |
| ---------------- | ------------------------------------------------------- |
| **Labels**       | `label` on inputs, `aria-label` on icons                |
| **Keyboard**     | Enter/Space triggers, Tab navigation                    |
| **Focus**        | Visible indicator, logical order, focus traps in modals |
| **Live Regions** | `aria-live="polite"` for dynamic content                |
| **Contrast**     | 4.5:1 minimum for text                                  |

```html
<!-- Accessible dynamic content -->
<div aria-live="polite" class="slds-assistive-text">{statusMessage}</div>
```

**For comprehensive accessibility guide (focus management, ARIA patterns, screen reader testing), see [references/accessibility-guide.md](references/accessibility-guide.md)**

---
