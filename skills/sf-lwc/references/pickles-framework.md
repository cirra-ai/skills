## PICKLES Framework (Architecture Methodology)

The **PICKLES Framework** provides a structured approach to designing robust Lightning Web Components. Apply each principle during component design and implementation.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     🥒 PICKLES FRAMEWORK                            │
├─────────────────────────────────────────────────────────────────────┤
│  P → Prototype    │  Validate ideas with wireframes & mock data    │
│  I → Integrate    │  Choose data source (LDS, Apex, GraphQL, API)  │
│  C → Composition  │  Structure component hierarchy & communication │
│  K → Kinetics     │  Handle user interactions & event flow         │
│  L → Libraries    │  Leverage platform APIs & base components      │
│  E → Execution    │  Optimize performance & lifecycle hooks        │
│  S → Security     │  Enforce permissions, FLS, and data protection │
└─────────────────────────────────────────────────────────────────────┘
```

### Quick Reference

| Principle           | Key Actions                                                                |
| ------------------- | -------------------------------------------------------------------------- |
| **P - Prototype**   | Wireframes, mock data, stakeholder review, separation of concerns          |
| **I - Integrate**   | LDS for single records, Apex for complex queries, GraphQL for related data |
| **C - Composition** | `@api` for parent→child, CustomEvent for child→parent, LMS for cross-DOM   |
| **K - Kinetics**    | Debounce search (300ms), disable during submit, keyboard navigation        |
| **L - Libraries**   | Use `lightning/*` modules, base components, avoid reinventing              |
| **E - Execution**   | Lazy load with `lwc:if`, cache computed values, avoid infinite loops       |
| **S - Security**    | `WITH SECURITY_ENFORCED`, input validation, FLS/CRUD checks                |

**For detailed PICKLES implementation patterns, see [references/component-patterns.md](references/component-patterns.md)**

---
