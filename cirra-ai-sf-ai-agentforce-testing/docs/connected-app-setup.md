# Connected App Setup for Live Preview

Guide for configuring OAuth to enable live preview mode with real Flow and Apex execution.

---

## Overview

Agent preview has two modes:

| Mode          | Flag                 | Actions                      | Use Case                         |
| ------------- | -------------------- | ---------------------------- | -------------------------------- |
| **Simulated** | (default)            | LLM simulates action results | Logic testing, early development |
| **Live**      | `--use-live-actions` | Real Flows/Apex execute      | Integration testing, validation  |

Live mode requires a **Connected App** for OAuth authentication.

---

## When You Need a Connected App

✅ **Required for:**

- `sf agent preview --use-live-actions` (not available via MCP — UI-only feature)
- Testing real data queries
- Validating Flow execution
- Debugging Apex integration

❌ **Not required for:**

- `sf agent preview` (simulated mode, not available via MCP — UI-only feature)
- Automated agent test runs via MCP
- Agent validation and publishing

---

## Quick Setup

### Option 1: Use sf-connected-apps Skill (Recommended)

```
Skill(skill="sf-connected-apps", args="Create Connected App for Agentforce live preview with callback http://localhost:1717/OauthRedirect")
```

### Option 2: Manual Setup via UI

1. **Setup → App Manager → New Connected App**
2. Configure OAuth settings (see below)
3. Get Consumer Key and Secret

---

## Connected App Configuration

### Required Settings

| Field                     | Value                                   |
| ------------------------- | --------------------------------------- |
| **Connected App Name**    | Agentforce Preview App (or your choice) |
| **API Name**              | Agentforce_Preview_App                  |
| **Contact Email**         | Your email                              |
| **Enable OAuth Settings** | ✅ Checked                              |
| **Callback URL**          | `http://localhost:1717/OauthRedirect`   |
| **Selected OAuth Scopes** | See below                               |

### Required OAuth Scopes

| Scope                                                             | Purpose                      |
| ----------------------------------------------------------------- | ---------------------------- |
| `Full access (full)`                                              | OR use specific scopes below |
| `Access and manage your data (api)`                               | Data operations              |
| `Perform requests on your behalf (refresh_token, offline_access)` | Token refresh                |
| `Access unique user identifiers (openid)`                         | User identification          |

**Minimal Scopes (if not using `full`):**

- `api`
- `refresh_token`
- `offline_access`
- `openid`

### Security Settings (Optional)

| Setting                                        | Recommendation                  |
| ---------------------------------------------- | ------------------------------- |
| **Require Secret for Refresh Token Flow**      | ✅ Enable for production        |
| **Require Proof Key for Code Exchange (PKCE)** | ✅ Enable for enhanced security |
| **IP Restrictions**                            | Configure if needed             |

---

## Retrieve Credentials

After creating the Connected App:

1. **Click "Manage Consumer Details"**
2. **Verify identity** (email/SMS code)
3. **Copy:**
   - Consumer Key (Client ID)
   - Consumer Secret (Client Secret)

---

## Authentication

### Connect to the Salesforce Org

```
# Connect to the org via Cirra AI MCP Server
cirra_ai_init()
```

### Or verify existing org connection

If already connected to the org:

```
# Verify org connection
cirra_ai_init()
```

---

## Using Live Preview

### Basic Live Preview

> **Note:** `sf agent preview` is not available via MCP (UI-only feature). Use the Salesforce Setup UI or CLI directly for live preview.

```
sf agent preview \
  --api-name Customer_Support_Agent \
  --use-live-actions \
  --client-app Agentforce_Preview_App \
  --target-org dev
```

### With Debug Logs

```
sf agent preview \
  --api-name Customer_Support_Agent \
  --use-live-actions \
  --client-app Agentforce_Preview_App \
  --apex-debug \
  --output-dir ./logs \
  --target-org dev
```

### Save Transcripts

```
sf agent preview \
  --api-name Customer_Support_Agent \
  --use-live-actions \
  --client-app Agentforce_Preview_App \
  --output-dir ./preview-logs \
  --target-org dev
```

---

## Output Files

When using `--output-dir`, you get:

### transcript.json

Conversation record:

```json
{
  "conversationId": "0Af7X000000001",
  "messages": [
    { "role": "user", "content": "Where is my order?", "timestamp": "..." },
    { "role": "assistant", "content": "Let me check...", "timestamp": "..." }
  ],
  "status": "completed"
}
```

### responses.json

Full API details including action invocations:

```json
{
  "messages": [
    {
      "role": "function",
      "name": "get_order_status",
      "content": {
        "orderId": "a1J7X00000001",
        "status": "Shipped",
        "trackingNumber": "1Z999..."
      },
      "executionTimeMs": 450
    }
  ],
  "metrics": {
    "flowInvocations": 1,
    "apexInvocations": 0,
    "totalDuration": 3050
  }
}
```

### apex-debug.log

When using `--apex-debug`:

```
13:45:22.123 (123456789)|USER_DEBUG|[15]|DEBUG|Processing order lookup
13:45:22.234 (234567890)|SOQL_EXECUTE_BEGIN|[20]|Aggregations:0|SELECT Id, Status...
13:45:22.345 (345678901)|SOQL_EXECUTE_END|[20]|Rows:1
```

---

## Troubleshooting

### 401 Unauthorized

**Cause:** Connected App not properly configured or not authorized.

**Solution:**

1. Verify Connected App callback URL matches `http://localhost:1717/OauthRedirect`
2. Re-connect to the org: `cirra_ai_init()`
3. Check Connected App is enabled for the user's profile

### "Connected App not found"

**Cause:** Wrong API name in `--client-app` flag.

**Solution:**

1. Check the API Name (not Display Name) in Setup → App Manager
2. Use exact API name: `--client-app Agentforce_Preview_App`

### Actions not executing

**Cause:** Actions require deployed Flows/Apex.

**Solution:**

1. Verify Flow is active: `soql_query(query="SELECT Id, Status FROM Flow WHERE DefinitionId IN (SELECT Id FROM FlowDefinition WHERE DeveloperName='[FlowName]')")`
2. Verify Apex is deployed: `metadata_read(type="ApexClass", fullName="[ClassName]")`
3. Check agent is activated: `metadata_update(type="GenAiPlannerBundle", fullName="[Agent]", metadata={...})`

### Timeout errors

**Cause:** Flow or Apex taking too long.

**Solution:**

1. Add debug logs: `--apex-debug`
2. Check Flow for long-running operations
3. Verify external callouts are responsive

---

## Security Best Practices

| Practice              | Description                                             |
| --------------------- | ------------------------------------------------------- |
| **Use dedicated app** | Create separate Connected App for preview vs production |
| **Limit scopes**      | Use minimum necessary OAuth scopes                      |
| **Enable PKCE**       | Require Proof Key for Code Exchange                     |
| **IP restrictions**   | Limit access by IP range if possible                    |
| **Rotate secrets**    | Periodically rotate Consumer Secret                     |
| **Audit logs**        | Monitor Connected App usage                             |

---

## Connected App Metadata

If using metadata-based deployment:

```xml
<!-- connectedApps/Agentforce_Preview.connectedApp-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Agentforce Preview</label>
    <contactEmail>admin@example.com</contactEmail>
    <oauthConfig>
        <callbackUrl>http://localhost:1717/OauthRedirect</callbackUrl>
        <certificate>YOUR_CERT_IF_NEEDED</certificate>
        <consumerKey>AUTO_GENERATED</consumerKey>
        <isAdminApproved>true</isAdminApproved>
        <isConsumerSecretOptional>false</isConsumerSecretOptional>
        <isIntrospectAllTokens>false</isIntrospectAllTokens>
        <scopes>Full</scopes>
        <scopes>Api</scopes>
        <scopes>RefreshToken</scopes>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE</ipRelaxation>
        <refreshTokenPolicy>infinite</refreshTokenPolicy>
    </oauthPolicy>
</ConnectedApp>
```

Deploy with:

```
metadata_create(type="ConnectedApp", fullName="Agentforce_Preview", metadata={...})
```

---

## Web OAuth vs Client Credentials: Which Do You Need?

There are **two different OAuth approaches** used in agent testing, each requiring a different app type:

### Comparison

| Aspect               | Web OAuth (this guide)                | Client Credentials (ECA)                |
| -------------------- | ------------------------------------- | --------------------------------------- |
| **Used by**          | `sf agent preview --use-live-actions` | Agent Runtime API (multi-turn testing)  |
| **App type**         | Connected App                         | External Client App (ECA)               |
| **Auth flow**        | Authorization Code (browser login)    | Client Credentials (machine-to-machine) |
| **User interaction** | Browser redirect required             | None — fully automated                  |
| **Best for**         | Manual interactive testing            | Automated multi-turn API testing        |
| **Setup guide**      | This document                         | [ECA Setup Guide](eca-setup-guide.md)   |

### Decision Flow

```
What are you testing?
    │
    ├─ Interactive preview (sf agent preview — not available via MCP, UI-only)?
    │   → Use Connected App (Web OAuth) — this guide
    │
    └─ Multi-turn API conversations?
        → Use External Client App (Client Credentials) — see eca-setup-guide.md
```

### When You Need Both

If you're doing **comprehensive testing** (both CLI preview and multi-turn API), you'll need:

1. A **Connected App** for `sf agent preview --use-live-actions` (not available via MCP — UI-only feature) (this guide)
2. An **External Client App** for Agent Runtime API testing ([ECA Setup Guide](eca-setup-guide.md))

These are separate app types and can coexist in the same org.

---

## Related Skills

| Skill             | Use For                                   |
| ----------------- | ----------------------------------------- |
| sf-connected-apps | Create and manage Connected Apps and ECAs |
| sf-flow           | Debug failing Flow actions                |
| sf-apex           | Debug failing Apex actions                |
| sf-debug          | Analyze debug logs                        |
