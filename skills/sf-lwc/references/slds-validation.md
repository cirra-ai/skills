## SLDS 2 Validation (165-Point Scoring)

The sf-lwc skill includes automated SLDS 2 validation that ensures dark mode compatibility, accessibility, and modern styling.

| Category                | Points | Key Checks                                        |
| ----------------------- | ------ | ------------------------------------------------- |
| **SLDS Class Usage**    | 25     | Valid class names, proper `slds-*` utilities      |
| **Accessibility**       | 25     | ARIA labels, roles, alt-text, keyboard navigation |
| **Dark Mode Readiness** | 25     | No hardcoded colors, CSS variables only           |
| **SLDS Migration**      | 20     | No deprecated SLDS 1 patterns/tokens              |
| **Styling Hooks**       | 20     | Proper `--slds-g-*` variable usage                |
| **Component Structure** | 15     | Uses `lightning-*` base components                |
| **Performance**         | 10     | Efficient selectors, no `!important`              |
| **PICKLES Compliance**  | 25     | Architecture methodology adherence (optional)     |

**Scoring Thresholds**:

```
✅ 150-165 pts → Production-ready, full SLDS 2 + Dark Mode
⚠️ 100-149 pts → Good component, minor styling issues to address
❌  <100 pts   → Needs significant SLDS 2 cleanup before deploy
```

**Exemption for trivial components**: Simple display components, wrappers, and prototypes are exempt from the <100 block threshold. Score them for informational purposes but do not block deployment. Basic accessibility and dark mode checks still apply regardless of complexity.

**CLI usage**: `validate_slds.py` validates a **single file** (not a directory):

```bash
python scripts/validate_slds.py path/to/component.html    # Human-readable report
python scripts/validate_slds.py path/to/component.css      # CSS validation
python scripts/validate_slds.py path/to/component.js       # JS validation
python scripts/validate_slds.py path/to/component.html --json  # JSON output
```

> **Note**: The local SLDS validator catches styling and pattern issues but cannot detect server-side compile errors (e.g. invalid component references like `lightning-formatted-phone-number` or inaccessible schema imports). Always verify deployment succeeds after local validation passes.

---
