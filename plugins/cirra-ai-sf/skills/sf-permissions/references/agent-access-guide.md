<!-- Parent: sf-permissions/SKILL.md -->

# Agent Access Permissions & Visibility Troubleshooting

## Agent Access Permissions

Employee Agents (Agentforce) require explicit access via the `agentAccesses` element of a Permission Set (or Profile). Without it, users do not see the agent in the Lightning Experience Agentforce panel.

**Permission Set metadata shape** (what `metadata_read` returns and what `metadata_create` accepts):

```json
{
  "fullName": "Case_Assist_Access",
  "label": "Case Assist Agent Access",
  "hasActivationRequired": false,
  "agentAccesses": [{ "agentName": "Case_Assist", "enabled": true }]
}
```

**Key points:**

- `agentName` must exactly match the agent's developer name (the `developer_name` in the agent's config)
- Add one `agentAccesses` entry per agent
- `enabled: true` grants access; `false` or omission denies access

**Create, grant and assign via MCP:**

```
# New dedicated PS carrying the access
metadata_create(type="PermissionSet", metadata=[{"fullName": "Case_Assist_Access", "label": "Case Assist Agent Access", "hasActivationRequired": false, "agentAccesses": [{"agentName": "Case_Assist", "enabled": true}]}])

# Or add access to an existing PS (JSON Patch)
metadata_update(type="PermissionSet", fullName="Sales_Agent_Users", patch=[{"op": "add", "path": "/agentAccesses/-", "value": {"agentName": "Case_Assist", "enabled": true}}])
# equivalent: permission_set_update(permissionSet="Sales_Agent_Users", patch=[...same patch...])

# Assign to users
permission_set_assignments(operation="add", permissionSets=["Case_Assist_Access"], users=["jane@company.com"])
```

To revoke, `replace` the entry's `enabled` with `false` or `remove` it (`{"op": "remove", "path": "/agentAccesses/0"}` — index from `metadata_read`).

---

## Visibility Troubleshooting

When an Agentforce Employee Agent is deployed but not visible to users:

### Step 1: Verify Agent Status

Setup > Agentforce Agents — the agent must show Status: Active. (`link_build` can produce the Setup link.)

### Step 2: Find which permission sets grant agent access

Inspect candidates directly — `agentAccesses` is part of the PS metadata:

```
tooling_api_query(sObject="PermissionSet", fields=["Name", "Label"], whereClause="Name LIKE '%Agent%' OR Name LIKE '%Copilot%'")
metadata_read(type="PermissionSet", fullNames=["Case_Assist_Access", "Sales_Agent_Users"])
```

For an org-wide audit, agent access is stored as `SetupEntityAccess` rows. List the entity types in use first, then filter to the agent type:

```
soql_query(sObject="SetupEntityAccess", fields=["SetupEntityType", "COUNT(Id) cnt"], whereClause="Id != null", groupBy="SetupEntityType")
soql_query(sObject="SetupEntityAccess", fields=["Parent.Name", "Parent.Label", "SetupEntityId"], whereClause="SetupEntityType = '<agent entity type>'")
```

Cross-check the `SetupEntityId` values against the agent definitions (`BotDefinition` — `soql_query(sObject="BotDefinition", fields=["Id", "DeveloperName", "MasterLabel"], whereClause="Id != null")`) and resolve `Parent.Name` IDs to PS names.

### Step 3: Check the user's assignments

```
soql_query(sObject="PermissionSetAssignment", fields=["PermissionSet.Name"], whereClause="Assignee.Username = 'jane@company.com'")
```

The user needs both the platform PS (`CopilotSalesforceUser` or the org's Agentforce user PS) and a PS whose `agentAccesses` includes the agent.

### Step 4: Grant what is missing

Use the patch and assignment calls from the first section.

### Common Issues

| Symptom                         | Cause                                 | Solution                                                       |
| ------------------------------- | ------------------------------------- | -------------------------------------------------------------- |
| No Agentforce icon              | CopilotSalesforceUser PS not assigned | `permission_set_assignments` add `CopilotSalesforceUser`       |
| Icon visible, agent not in list | Missing `agentAccesses`               | Patch `/agentAccesses/-` on an assigned PS                     |
| Agent visible, errors on open   | Agent not fully published             | Check agent status and logs in Setup                           |
| "Agent not found" error         | Name mismatch                         | Ensure `agentName` matches the agent's developer name exactly  |
| Patch rejected                  | Agent name unknown to the org         | Confirm the developer name via `BotDefinition` before patching |
