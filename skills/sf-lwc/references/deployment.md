## Deployment via Cirra AI

### Step 1: Initialize & Generate

**FIRST**: Call `cirra_ai_init`:

```
Use: cirra_ai_init()
```

If you need to override the default connection, pass `cirra_ai_team` and/or `sf_user` explicitly.

Then generate the LWC bundle:

```
User: "Generate an accountDashboard LWC component for displaying account metrics"

Agent:
1. Generates accountDashboard.js (with @wire, event handling)
2. Generates accountDashboard.html (SLDS 2 structure)
3. Generates accountDashboard.css (dark mode variables)
4. Generates accountDashboard.meta.xml (targets and config)
5. Generates accountDashboard.test.js (Jest tests)
6. Validates against PICKLES framework (165-point score: ~155 pts)
7. Shows code preview to user
```

### Step 2: Deploy via metadata_create

The `metadata_create` call requires a flat metadata structure with **Base64-encoded** sources in `lwcResources`:

```
metadata_create(
  type="LightningComponentBundle",
  metadata=[{
    "fullName": "accountDashboard",
    "apiVersion": "66.0",
    "isExposed": true,
    "masterLabel": "Account Dashboard",
    "description": "SLDS 2 compliant account metrics dashboard",
    "lwcResources": {
      "lwcResource": [
        {
          "filePath": "lwc/accountDashboard/accountDashboard.js",
          "source": "<Base64-encoded JS source>"
        },
        {
          "filePath": "lwc/accountDashboard/accountDashboard.html",
          "source": "<Base64-encoded HTML source>"
        },
        {
          "filePath": "lwc/accountDashboard/accountDashboard.css",
          "source": "<Base64-encoded CSS source>"
        }
      ]
    }
  }]
)
```

> **Encoding note**: `metadata_create` and `metadata_update` require **Base64-encoded** source files in `lwcResources.lwcResource[].source`. When updating an existing component via `tooling_api_dml` on `LightningComponentResource.Source`, use **plain text** (NOT Base64). This is an intentional Salesforce API difference between the Metadata API and Tooling API. See [Source encoding rules](#source-encoding-rules-read-this-before-any-deployupdate) at the top of this skill for the full reference.

### Step 3: Verify Deployment

```
tooling_api_query(
  sObject="LightningComponentBundle",
  whereClause="DeveloperName = 'accountDashboard'"
)
```

---
