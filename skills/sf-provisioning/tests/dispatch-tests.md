# sf-provisioning dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## provision contractor user

- **Input**: `/sf-provisioning create-user Jane Doe contractor`
- **Dispatch**: Provision User
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `user_create`, `permission_set_assignments`, `link_build`
- **Should NOT call**: `metadata_create`, `metadata_delete`
- **Should ask user**: yes (must present full provisioning plan and get explicit approval before any write)
- **Follow-up skills**: `sf-permissions`, `sf-metadata`

**Notes**: Full Provision User workflow. Discovery phase must query active contractor users to read off the org's username pattern, profile, license, and assigned permission sets BEFORE proposing any values. Username must be checked for global uniqueness with `soql_query` on `User`. `user_create` should prefer `template=<comparable contractor>` over inventing properties (see Cirra issue PLTFRM-752 — `properties` map fails with "No such column '0'"). Permission set assignments are added separately via `permission_set_assignments` because clones do not copy them. Verification `soql_query` follows. Final report includes a `link_build` to the user setup record.

---

## grant scratch org capability

- **Input**: `/sf-provisioning grant scratch-org access to jane@cirra.ai`
- **Dispatch**: Grant Capability
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `permission_set_assignments`
- **Should NOT call**: `user_create`, `metadata_create`
- **Should ask user**: yes (must confirm "create only" vs "create + manage" scope and get plan approval)
- **Follow-up skills**: `sf-permissions`, `sf-metadata`

**Notes**: Capability search uses `soql_query` on `ObjectPermissions` filtered to `ScratchOrgInfo` / `ActiveScratchOrg` to find the existing permission set that already grants this (typically the standard `SFDX` permission set). MUST NOT create a new permission set when one exists. Scope clarification ("create" vs "create + manage") is mandatory — different access sets. After approval, `permission_set_assignments` operation `add` assigns the existing PS.

---

## mirror access from one user to another

- **Input**: `/sf-provisioning mirror access from john@cirra.ai to jane@cirra.ai`
- **Dispatch**: Mirror a User
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `user_create`, `permission_set_assignments`, `link_build`
- **Should NOT call**: `metadata_create`, `metadata_delete`
- **Should ask user**: yes (must confirm new user identity fields — firstName/lastName/username/email — and approve plan)
- **Follow-up skills**: `sf-permissions`

**Notes**: Mirror workflow reads the model user via `soql_query` (profile, license, role, and all `PermissionSetAssignment` rows). `user_create` uses `template=<model user>` to clone profile/locale. CRITICAL: clones do NOT copy permission set assignments — each PS the model user has must be re-assigned via `permission_set_assignments` (`add`).

---

## deactivate user for offboarding

- **Input**: `/sf-provisioning deactivate john@cirra.ai`
- **Dispatch**: Revoke / Deactivate
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `user_update`
- **Should NOT call**: `user_create`, `metadata_delete`
- **Should ask user**: yes (must surface dependency check results and confirm deactivation)
- **Follow-up skills**: `sf-permissions`, `sf-audit`

**Notes**: Dependency-check phase queries record ownership and running automation owned by the user with `soql_query` and surfaces results BEFORE deactivation. Deactivation uses `user_update` with `IsActive=false`. Users cannot be deleted in Salesforce — only deactivated or frozen. For freeze instead, the skill uses `sobject_dml` on `UserLogin` with `IsFrozen=true`.

---

## revoke a single permission set

- **Input**: `/sf-provisioning revoke SFDX from jane@cirra.ai`
- **Dispatch**: Revoke / Deactivate
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `permission_set_assignments`
- **Should NOT call**: `user_update`, `metadata_delete`
- **Should ask user**: yes (must confirm narrow revoke vs full deactivation and approve plan)
- **Follow-up skills**: `sf-permissions`

**Notes**: Narrow revoke path — `permission_set_assignments` with operation `remove`. The skill must distinguish a narrow PS revoke from a full user deactivation. `soql_query` first to confirm the assignment exists, then remove, then verify.

---

## unclear request — must ask archetype

- **Input**: `/sf-provisioning create-user Alex Kim`
- **Dispatch**: Provision User
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`
- **Should NOT call**: `user_create`, `permission_set_assignments`, `metadata_create`
- **Should ask user**: yes (must ask the archetype — internal admin, contractor, or integration user — before discovery)
- **Follow-up skills**: `sf-permissions`

**Notes**: Archetype is ambiguous. Per SKILL.md, the skill MUST call `AskUserQuestion` to clarify "Is this an internal admin, a contractor, or an integration user?" before running discovery queries. License/profile must not be guessed.
