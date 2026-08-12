## Tooling API fallback — per-file edits

If `metadata_update` returns a partial failure or the bundle-level call is rejected (e.g. the `targetConfigs` validates differently against the org), you can update a single resource at a time via the Tooling API. **The `Source` field on this path is plain text — do NOT Base64-encode it.**

### 1. Resolve the bundle id and resource ids

```
tooling_api_query(
  sObject="LightningComponentBundle",
  fields=["Id", "DeveloperName"],
  whereClause="DeveloperName = '<ComponentName>'"
)

tooling_api_query(
  sObject="LightningComponentResource",
  fields=["Id", "FilePath", "Format", "Source"],
  whereClause="LightningComponentBundleId = '<bundleId>'"
)
```

`FilePath` is on `LightningComponentResource`, NOT on `LightningComponentBundle` — querying the latter for `FilePath` will fail with `No such column 'FilePath' on entity 'LightningComponentBundle'`.

### 2. Update one resource at a time

```
tooling_api_dml(
  operation="update",
  sObject="LightningComponentResource",
  record={
    "Id": "<resourceId>",
    "Source": "<plain-text source — NOT Base64>"
  }
)
```

Common mistakes that produce Salesforce errors on this path:

| Symptom                                                          | Cause                                               |
| ---------------------------------------------------------------- | --------------------------------------------------- |
| `XML parse error: Content is not allowed in prolog.: Source`     | You Base64-encoded the value before sending.        |
| `Compilation Failure` / `Unexpected token`                       | You Base64-encoded a JS or HTML resource.           |
| `No such column 'FilePath' on entity 'LightningComponentBundle'` | Queried `FilePath` on the bundle, not the resource. |

`*.js-meta.xml` is also a `LightningComponentResource` and is updated the same way (plain text). Use it to change bundle-level properties (apiVersion, isExposed, targets, targetConfigs) when `metadata_update` is unavailable.

### 3. Validate `*.js-meta.xml` content before writing

The `js-meta.xml` is XML that Salesforce validates strictly against the org's metadata. Common rejection causes:

| Salesforce error                        | Likely cause                                                                                                                     |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `No such relation 'X' on entity 'User'` | `userPermissions` referencing a permission name that doesn't exist in the org                                                    |
| `Invalid type: <name>` in `<targets>`   | Target not enabled / not available on this edition (e.g. `lightning__Dashboard` requires Salesforce Customer Support enablement) |
| `<targetConfigs>` parse / schema error  | `<targetConfig targets="...">` does not match an entry in the bundle's `<targets>`                                               |

Before sending the updated `js-meta.xml`:

- **Do not invent `userPermissions`**. If you need to gate visibility, use `tooling_api_query` on `PermissionSet` describes (or `soql_query` on `PermissionSetTabSetting` / known standard permissions) to confirm the name is real before referencing it. Standard SF user permissions (`ViewSetup`, `ManageUsers`, etc.) are safe; custom/named ones are not.
- **Each `<targetConfig targets="X">`** must reference a target that's also present in the bundle's `<targets>` block.
- **API version on `<apiVersion>`** must be one the org supports — query an existing component if unsure.

### 4. Listing many LWC components in large orgs

`metadata_list(type="LightningComponentBundle")` returns one record per component plus per-file properties and can exceed the per-call response cap in orgs with many LWCs (the response then gets paginated to a 3-record preview). For enumeration, prefer the lightweight Tooling API list:

```
tooling_api_query(
  sObject="LightningComponentBundle",
  fields=["Id", "DeveloperName", "NamespacePrefix", "ApiVersion", "MasterLabel", "Description"],
  whereClause="NamespacePrefix = null"
)
```

This returns just the bundle metadata (no embedded sources), is small, and uses the same plain-text path as the per-file edits above.

---
