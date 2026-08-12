## Dark Mode Readiness

Dark mode is exclusive to SLDS 2 themes. Components must use global styling hooks to support light/dark theme switching.

### Dark Mode Checklist

- [ ] **No hardcoded hex colors** (`#FFFFFF`, `#333333`)
- [ ] **No hardcoded RGB/RGBA values**
- [ ] **All colors use CSS variables** (`var(--slds-g-color-*)`)
- [ ] **Fallback values provided** for SLDS 1 compatibility
- [ ] **No inline color styles** in HTML templates
- [ ] **Icons use SLDS utility icons** (auto-adjust for dark mode)

### Global Styling Hooks (Common)

| Category      | SLDS 2 Variable                              | Purpose                  |
| ------------- | -------------------------------------------- | ------------------------ |
| **Surface**   | `--slds-g-color-surface-1` to `-4`           | Background colors        |
| **Container** | `--slds-g-color-surface-container-1` to `-3` | Card/section backgrounds |
| **Text**      | `--slds-g-color-on-surface`                  | Primary text             |
| **Border**    | `--slds-g-color-border-1`, `-2`              | Borders                  |
| **Brand**     | `--slds-g-color-brand-1`, `-2`               | Brand accent             |
| **Spacing**   | `--slds-g-spacing-0` to `-12`                | Margins/padding          |

**Example Migration**:

```css
/* SLDS 1 (Deprecated) */
.my-card {
  background-color: #ffffff;
  color: #333333;
}

/* SLDS 2 (Dark Mode Ready) */
.my-card {
  background-color: var(--slds-g-color-surface-container-1, #ffffff);
  color: var(--slds-g-color-on-surface, #181818);
}
```

**For complete styling hooks reference and migration guide, see [references/performance-guide.md](references/performance-guide.md)**

---
