# Managed Package Guide

How to package `Environment_Pool__c` and related components as a Salesforce package for distribution.

## Overview

The `Environment_Pool__c` custom object and its supporting metadata (Permission Set, List Views, optional Flows) can be packaged for distribution to multiple orgs. This eliminates the need for per-org Pool Setup and ensures consistency.

Two packaging approaches are available:

| Approach        | Namespace | Upgradeable | Best For                      |
| --------------- | --------- | ----------- | ----------------------------- |
| Managed Package | Required  | Yes         | AppExchange, ISV distribution |
| 2GP Unlocked    | Optional  | Yes         | Internal distribution, teams  |

## 2GP Unlocked Package (Recommended)

Recommended for internal distribution. No namespace required, easier to develop and test.

### Prerequisites

- Salesforce CLI installed
- Dev Hub enabled
- `sfdx-project.json` in the project root

### Project Configuration

Add to `sfdx-project.json`:

```json
{
  "packageDirectories": [
    {
      "path": "force-app/main/default",
      "default": true,
      "package": "EnvironmentPool",
      "versionName": "ver 1.0",
      "versionNumber": "1.0.0.NEXT"
    }
  ],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "62.0"
}
```

### Package Contents

```
force-app/main/default/
├── objects/
│   └── Environment_Pool__c/
│       ├── Environment_Pool__c.object-meta.xml
│       └── fields/
│           ├── Environment_Name__c.field-meta.xml
│           ├── Environment_Type__c.field-meta.xml
│           ├── Status__c.field-meta.xml
│           ├── Checked_Out_By__c.field-meta.xml
│           ├── Checkout_Timestamp__c.field-meta.xml
│           ├── Expected_Return__c.field-meta.xml
│           ├── Expiry_Date__c.field-meta.xml
│           ├── Purpose__c.field-meta.xml
│           ├── Org_Id__c.field-meta.xml
│           ├── Login_Url__c.field-meta.xml
│           ├── Last_Reset__c.field-meta.xml
│           └── Sandbox_Process_Id__c.field-meta.xml
├── permissionsets/
│   └── Environment_Pool_Access.permissionset-meta.xml
└── listviews/
    └── (optional list views)
```

### Create and Version

```bash
# Create the package (one-time)
sf package create \
  --name EnvironmentPool \
  --description "Sandbox pool tracking for sf-sandbox-manager" \
  --package-type Unlocked \
  --path force-app/main/default \
  --target-dev-hub <dev-hub-alias>

# Create a version
sf package version create \
  --package EnvironmentPool \
  --definition-file config/project-scratch-def.json \
  --installation-key-bypass \
  --wait 10 \
  --target-dev-hub <dev-hub-alias>

# List versions
sf package version list --packages EnvironmentPool

# Get install URL
sf package version report \
  --package EnvironmentPool@1.0.0-1 \
  --target-dev-hub <dev-hub-alias>
```

### Install in Target Org

```bash
sf package install \
  --package EnvironmentPool@1.0.0-1 \
  --target-org <target-org-alias> \
  --wait 10 \
  --no-prompt
```

### Upgrade

```bash
sf package install \
  --package EnvironmentPool@1.1.0-1 \
  --target-org <target-org-alias> \
  --upgrade-type Mixed \
  --wait 10 \
  --no-prompt
```

## Managed Package

For AppExchange distribution or when namespace protection is needed.

### Namespace Setup

1. Register a namespace prefix (e.g., `cirra_ep`) in a Developer Edition org
2. Link the namespace to the Dev Hub
3. All API names become namespaced: `cirra_ep__Environment_Pool__c`

### Package Development

Same structure as 2GP, but with `--package-type Managed`:

```bash
sf package create \
  --name EnvironmentPool \
  --description "Sandbox pool tracking for sf-sandbox-manager" \
  --package-type Managed \
  --path force-app/main/default \
  --target-dev-hub <dev-hub-alias>
```

### Considerations

- **Security Review**: Required for AppExchange listing
- **Namespace**: All API names are prefixed — SOQL queries must use `cirra_ep__Environment_Pool__c`
- **Upgrades**: Managed packages support push upgrades
- **Deprecation**: Fields can be deprecated but not deleted in managed packages

## Skill Adaptations for Packaged Deployments

The sf-sandbox-manager SKILL.md Pool Setup workflow should detect whether `Environment_Pool__c` already exists (from a package install) before attempting to create it.

### Detection Logic

```
sobject_describe(sObject="Environment_Pool__c")
```

If it succeeds → pool object exists (either from package or previous setup). Skip creation.

If it fails → object doesn't exist. Proceed with auto-creation.

### Namespace Handling

If the object exists with a namespace prefix (e.g., `cirra_ep__Environment_Pool__c`), all SOQL queries and DML operations must use the namespaced API name.

Detection:

```
sobjects_list()
```

Search the result for `Environment_Pool__c` or `*__Environment_Pool__c`. If the match includes a namespace prefix, store it and prepend to all field references:

```
soql_query(
  sObject="cirra_ep__Environment_Pool__c",
  fields=["Id", "cirra_ep__Environment_Name__c", "cirra_ep__Status__c"],
  ...
)
```

### Skip Setup When Package Installed

If `sobject_describe` succeeds and returns all expected fields, the Pool Setup workflow should skip object and field creation and only verify the Permission Set exists:

```
tooling_api_query(
  sObject="PermissionSet",
  fields=["Id", "Name"],
  whereClause="Name = 'Environment_Pool_Access' OR Name = 'cirra_ep__Environment_Pool_Access'",
  limit=1
)
```

If the Permission Set doesn't exist (unlikely if package is installed), create it.

## Future: Dedicated MCP Tools

If the Cirra AI MCP server adds dedicated `environment_pool_*` tools (e.g., `environment_checkout`, `environment_checkin`, `environment_status`), the sandbox pool workflows can switch to single-call operations. The dispatch table and user experience stay identical — only the underlying tool calls change.

The packaged `Environment_Pool__c` object would still be used as the backing store, but the MCP server would handle the SOQL/DML internally.
