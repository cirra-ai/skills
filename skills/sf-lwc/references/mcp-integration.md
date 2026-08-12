## Cirra AI MCP Integration

### Workflow

| Task                         | Original (CLI)                                        | New (Cirra AI)                                         |
| ---------------------------- | ----------------------------------------------------- | ------------------------------------------------------ |
| **Generate Component**       | `sf lightning generate component`                     | Generate files directly                                |
| **Deploy Component**         | `sf project deploy start -m LightningComponentBundle` | `metadata_create` with type "LightningComponentBundle" |
| **Query Component Metadata** | `sf data query --use-tooling-api`                     | `tooling_api_query` for LightningComponentBundle       |
| **Describe sObjects**        | `sf sobject describe Account`                         | `sobject_describe` tool                                |
| **SOQL Queries**             | `sf data query`                                       | `soql_query` tool                                      |
| **Run Jest Tests**           | `sf lightning lwc test run`                           | Jest runs locally; tests are code-generated            |

### Deployment Process

```
1. Generate LWC bundle files (JS, HTML, CSS, meta.xml)
   ↓
2. User reviews generated code (PICKLES + SLDS 2 validation)
   ↓
3. Call cirra_ai_init() to authenticate with target org
   ↓
4. Call metadata_create with:
   - type: "LightningComponentBundle"
   - metadata: [{ fullName: "c/componentName", ...bundle files }]
   ↓
5. Component deployed to org
   ↓
6. Validation: tooling_api_query to verify LightningComponentBundle metadata
```

### MCP Tools Mapping

| Operation              | CLI Command                                           | MCP Tool             | Example                                                                              |
| ---------------------- | ----------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------ |
| Generate component     | `sf lightning generate component`                     | (generated directly) | Write JS/HTML/CSS/meta.xml directly                                                  |
| Deploy component       | `sf project deploy start -m LightningComponentBundle` | `metadata_create`    | `metadata_create(type="LightningComponentBundle", metadata=[...])`                   |
| Update component       | `sf project deploy` (existing)                        | `metadata_update`    | `metadata_update(type="LightningComponentBundle", metadata=[...])`                   |
| Retrieve component     | `sf project retrieve`                                 | `metadata_read`      | `metadata_read(type="LightningComponentBundle", fullNames=["c/accountDashboard"])`   |
| List components        | `sf metadata list`                                    | `metadata_list`      | `metadata_list(type="LightningComponentBundle")`                                     |
| Query metadata objects | `sf data query --use-tooling-api`                     | `tooling_api_query`  | `tooling_api_query(sObject="LightningComponentBundle", whereClause="...")`           |
| Describe sObject       | `sf sobject describe`                                 | `sobject_describe`   | `sobject_describe(sObject="Account")`                                                |
| Query data             | `sf data query`                                       | `soql_query`         | `soql_query(sObject="Account", fields=["Id","Name"], whereClause="Industry='Tech'")` |
| Delete component       | `sf project delete`                                   | `metadata_delete`    | `metadata_delete(type="LightningComponentBundle", fullNames=["c/accountDashboard"])` |

### Required Initialization

**ALWAYS start with**:

```
cirra_ai_init()
```

Call with no parameters — uses the default org. If a default is configured, confirm with the user before proceeding. If no default is configured, ask for the Salesforce user/alias.

---
