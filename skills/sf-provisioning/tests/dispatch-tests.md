# sf-provisioning dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## provision new contractor user

- **Input**: `/sf-provisioning create-user Jane Doe contractor jane@acme.com`
- **Dispatch**: Provision User
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `user_create`, `permission_set_assignments`
- **Should NOT call**: `metadata_create`, `metadata_delete`, `sobject_dml` (on objects other than `User`)
- **Should ask user**: yes (must confirm archetype/license if ambiguous, must get explicit plan approval before creating)
- **Follow-up skills**: `sf-permissions`

**Notes**: Full Provision User workflow. Discovery phase issues multiple `soql_query` calls (comparable users, `UserLicense`, `ObjectPermissions`/`PermissionSetAssignment` for capability, username availability). Plan is presented for approval — turn ends. After approval, `user_create` uses `template=<comparable user>` and overrides only firstName/lastName/username/email. Permission set assignments follow. Final verification reads the new user and assignments back.

---

## grant scratch org access to existing user

- **Input**: `/sf-provisioning grant scratch-org access to jane@acme.com`
- **Dispatch**: Grant Capability
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `permission_set_assignments`
- **Should NOT call**: `user_create`, `metadata_create` (existing `SFDX` PS should be reused)
- **Should ask user**: yes (scope: create-only vs create+manage, plus plan approval)
- **Follow-up skills**: `sf-permissions`

**Notes**: Capability must be scoped precisely (create vs create+manage). Search `ObjectPermissions` for `ScratchOrgInfo`/`ActiveScratchOrg` to find the existing PS (typically standard `SFDX`). Do NOT create a new PS. Assign with `permission_set_assignments` operation `add`. Verify with a follow-up `soql_query` on `PermissionSetAssignment`.

---

## mirror a user's access

- **Input**: `/sf-provisioning mirror alice@acme.com to bob@acme.com`
- **Dispatch**: Mirror a User
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `user_create`, `permission_set_assignments`
- **Should NOT call**: `metadata_create`
- **Should ask user**: yes (confirm Bob's name/email/username pattern, plan approval)
- **Follow-up skills**: `sf-permissions`

**Notes**: Read the model user fully (profile, license, role, all `PermissionSetAssignment` records where `IsOwnedByProfile = false`). Create the new user via `user_create` with `template=<model user>`. Cloning does NOT copy permission set assignments — explicitly re-assign each one with `permission_set_assignments`. Verify.

---

## deactivate a user (offboard)

- **Input**: `/sf-provisioning deactivate john@acme.com`
- **Dispatch**: Revoke / Deactivate
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `soql_query`, `user_update`
- **Should NOT call**: `user_create`, `metadata_create`
- **Should ask user**: yes (surface record ownership / automation dependencies, then plan approval)
- **Follow-up skills**: `sf-audit`

**Notes**: Dependency check first — record ownership, running automation owned by the user, integration usage. Surface findings. After approval, set `IsActive = false` via `user_update` (or `sobject_dml` on `User`). Users cannot be deleted. Freeze (`UserLogin.IsFrozen = true`) is an alternative for a faster lockout.

---

## ambiguous request — ask user

- **Input**: `/sf-provisioning`
- **Dispatch**: Ask the user
- **Init required**: no
- **Init timing**: n/a
- **Path**: ask
- **First tool**: `AskUserQuestion`
- **Tool params**: question listing the 4 workflows (create-user / grant / revoke / mirror)
- **Should call**: `AskUserQuestion`
- **Should NOT call**: `cirra_ai_init`, `user_create`, `permission_set_assignments`, `sobject_dml`
- **Should ask user**: yes
- **Follow-up skills**: none

**Notes**: No subcommand or archetype given. Must ask before acting — do not guess archetype, license, or profile.
