# sf-permissions dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## hierarchy view

- **Input**: `/sf-permissions hierarchy`
- **Dispatch**: Hierarchy Viewer
- **Init required**: yes
- **First tool**: `soql_query`
- **Should call**: `soql_query` (multiple — PermissionSet, PermissionSetGroup, PermissionSetGroupComponent)
- **Should ask user**: no
- **Should NOT call**: `metadata_create`, `metadata_update`, `metadata_delete`

**Notes**: `hierarchy` keyword routes directly. Should query all PS (non-profile), all PSGs, and PSG components, then render as a structured tree showing PSG → PS relationships and standalone PS.

---

## who has delete on Account

- **Input**: `/sf-permissions analyze who can delete Account`
- **Dispatch**: Analyze Permissions
- **Init required**: yes
- **First tool**: `soql_query`
- **Tool params**: `sObject: ObjectPermissions, whereClause includes SobjectType = 'Account' AND PermissionsDelete = true`
- **Should ask user**: no

**Notes**: `analyze` keyword routes to Analyze Permissions, sub-case "Who has X?". Should query ObjectPermissions with Account + Delete filter, then resolve PS names (Parent.Name returns hex IDs — needs follow-up query), then count assigned users per PS.

---

## user permission trace

- **Input**: `/sf-permissions analyze what permissions does john@company.com have`
- **Dispatch**: Analyze Permissions
- **Init required**: yes
- **Should call**: `soql_query` (multiple — User lookup, PermissionSetAssignment, then per-PS queries)
- **Should ask user**: no

**Notes**: Routes to Analyze Permissions, sub-case "User permissions". Must first look up the User record by email to get the UserId, then query PermissionSetAssignment, then aggregate all permissions from each assigned PS/PSG.

---

## debug access issue

- **Input**: `/sf-permissions analyze why can't John edit Opportunities`
- **Dispatch**: Analyze Permissions
- **Init required**: yes
- **Should call**: `soql_query`
- **Should ask user**: yes (need to identify which John — may need email or UserId)

**Notes**: Routes to Analyze Permissions, sub-case "Debug access". The name "John" is ambiguous — should ask for email or UserId. Then check the user's PS assignments against ObjectPermissions for Opportunity with PermissionsEdit. If no PS grants edit, suggest which PS/PSG to assign.

---

## security audit

- **Input**: `/sf-permissions audit`
- **Dispatch**: Security Audit
- **Init required**: yes
- **First tool**: `soql_query`
- **Should ask user**: no

**Notes**: `audit` keyword routes to Security Audit. Should query for: PS with PermissionsModifyAllData = true (flag non-admin), PS with PermissionsViewAllData on sensitive objects, orphaned PS (no assigned users), PSGs with "Outdated" status.

---

## create permission set

- **Input**: `/sf-permissions create a permission set for contractors with read-only Account access`
- **Dispatch**: Create Permission Set
- **Init required**: yes
- **Should call**: `metadata_create`, `sobject_dml`
- **Should ask user**: no (requirements are clear)

**Notes**: `create` keyword routes to Create Permission Set. Should create the PS shell via `metadata_create`, get its record ID, then add ObjectPermissions (Account read-only) via `sobject_dml`. Follow naming convention: `Contractor_Account_ReadOnly_PS` or similar.

---

## clone permission set

- **Input**: `/sf-permissions clone Sales_Admin into Sales_Viewer`
- **Dispatch**: Clone Permission Set
- **Init required**: yes
- **Should call**: `metadata_read`, `metadata_create`
- **Should ask user**: no

**Notes**: `clone` keyword routes to Clone Permission Set. Should read the source PS metadata via `metadata_read`, modify fullName/label, then create the copy via `metadata_create`. The user can then modify permissions on the clone.

---

## update permission set

- **Input**: `/sf-permissions update Sales_Admin add delete access to Opportunity`
- **Dispatch**: Update Permission Set
- **Init required**: yes
- **Should call**: `soql_query`, `sobject_dml`
- **Should ask user**: no

**Notes**: `update` keyword routes to Update Permission Set. Should first query the PS record ID, then insert/update ObjectPermissions via `sobject_dml` to add PermissionsDelete = true for Opportunity.

---

## delete permission set

- **Input**: `/sf-permissions delete Unused_Legacy_PS`
- **Dispatch**: Delete Permission Set
- **Init required**: yes
- **Should call**: `metadata_delete`
- **Should ask user**: yes (confirm before destructive operation)

**Notes**: `delete` keyword routes to Delete Permission Set. MUST confirm with user before deleting. Use `metadata_delete` with type PermissionSet and the fullName.

---

## agent access

- **Input**: `/sf-permissions agent-access`
- **Dispatch**: Agent Access Permissions
- **Init required**: yes
- **First tool**: `tooling_api_query`
- **Should ask user**: yes (query or manage?)

**Notes**: `agent-access` keyword routes to Agent Access Permissions. Should ask whether the user wants to query existing agent access or modify it. Query uses `tooling_api_query` on PermissionSet with Name LIKE '%Agent%'.

---

## no arguments — show menu

- **Input**: `/sf-permissions`
- **Dispatch**: (none — present menu)
- **Should ask user**: yes
- **Menu options**: Hierarchy, Audit, Analyze, Create, Clone, Update, Delete, Agent access

**Notes**: No arguments. Present the eight-option dispatch menu. No tools called until user selects.

---

## natural language — field access

- **Input**: `/sf-permissions who can edit Account.AnnualRevenue`
- **Dispatch**: Analyze Permissions
- **Init required**: yes
- **First tool**: `soql_query`
- **Tool params**: `sObject: FieldPermissions, whereClause includes Field = 'Account.AnnualRevenue'`
- **Should ask user**: no

**Notes**: Natural language "who can" should route to Analyze Permissions even without the explicit `analyze` keyword. This tests intent inference from the dispatch table's pattern column. Should query FieldPermissions (not ObjectPermissions — this is field-level). Known caveat: verify the Field column prefix matches Account, as the API may return cross-object matches.
