# sf-connect-rest dispatch tests

Each test case describes a user input and expected behavior.
Phase 1 (static) validates dispatch routing and tool references against SKILL.md.
Phase 2 (prompt) constructs the full prompt and validates its structure.

---

## list named credentials

- **Input**: `/sf-connect-rest core list the named credentials in this org`
- **Dispatch**: Core Resource
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `connect_rest`
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Should ask user**: no (read-only GET)
- **Follow-up skills**: `sf-metadata`

**Notes**: Read-only Core family call. The resource path must be confirmed against the Connect REST reference before calling — no guessing. Reads need no approval. If the response carries credential material, the skill must describe the fields without echoing secret values.

---

## create a named credential

- **Input**: `/sf-connect-rest core create a named credential for the billing API`
- **Dispatch**: Core Resource
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `connect_rest`
- **Should NOT call**: `metadata_create`, `sobject_dml`
- **Should ask user**: yes (must show the exact method, path, and body, note the risk to running integrations, and get explicit approval)
- **Follow-up skills**: `sf-metadata`

**Notes**: Write path. The skill must GET the existing named credentials first to avoid creating a duplicate, look up the exact resource path and HTTP method on the resource's own reference page, then present method + path + body for approval and END ITS TURN before executing. Verification is a follow-up GET.

---

## publish an Experience Cloud site

- **Input**: `/sf-connect-rest experience-cloud publish the partner community site`
- **Dispatch**: Experience Cloud
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `connect_rest`
- **Should NOT call**: `metadata_delete`, `sobject_dml`
- **Should ask user**: yes (must state that publishing is immediately visible to site visitors and get approval separate from any earlier deploy approval)
- **Follow-up skills**: `sf-metadata`, `sf-cms`

**Notes**: Must `GET communities` first to resolve the `communityId` — never guess it. Site publishing has no Metadata API equivalent, which is why this lands here. The approval must be separate from any earlier deploy approval because the blast radius (visible to all site visitors) is different.

---

## capability gap handed off from another skill

- **Input**: `/sf-connect-rest find Cirra can't reach custom domains — how do I list them`
- **Dispatch**: Find the Resource
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `connect_rest`
- **Should NOT call**: `metadata_create`, `sobject_dml`
- **Should ask user**: no (read-only lookup and GET)
- **Follow-up skills**: `sf-metadata`, `sf-help-fetch`

**Notes**: The Find the Resource workflow — name the capability, identify the family (Core), fetch the reference, locate the exact path and method, then GET. If the resource cannot be found in the documentation the skill MUST say so and stop rather than approximating with a different resource.

---

## chatter feed request — rate limit awareness

- **Input**: `/sf-connect-rest chatter post an announcement to the company Chatter group`
- **Dispatch**: Chatter
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`, `connect_rest`
- **Should NOT call**: `sobject_dml`, `metadata_create`
- **Should ask user**: yes (posting is visible to other users — must show the exact request and get approval)
- **Follow-up skills**: `sf-connect-rest`

**Notes**: Chatter resources are subject to a per-user, per-application, per-hour rate limit; a 503 means throttling, not an outage, and the skill must NOT retry immediately. Calls should be spaced out. Writes to a feed are visible to other users, so approval is required.

---

## request that belongs to another tool

- **Input**: `/sf-connect-rest find all Account records created this month`
- **Dispatch**: Ask the user
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: fast
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`
- **Should NOT call**: `connect_rest`
- **Should ask user**: yes (must redirect to `soql_query` rather than attempting a Connect REST path)
- **Follow-up skills**: `sf-data`

**Notes**: Record data is not Connect REST territory. `connect_rest` is confined to the `/connect/` namespace by design, because the record-facing tools enforce field-level access checks a general passthrough would bypass. The skill must redirect to `soql_query` (`sf-data`) instead of attempting a path.

---

## unknown resource — must not guess

- **Input**: `/sf-connect-rest core change the org's widget throttling setting`
- **Dispatch**: Find the Resource
- **Init required**: yes
- **Init timing**: before-workflow
- **Path**: full
- **First tool**: `cirra_ai_init`
- **Tool params**: `(no parameters)`
- **Should call**: `cirra_ai_init`
- **Should NOT call**: `connect_rest`
- **Should ask user**: yes (must report that no such resource was found rather than probing paths)
- **Follow-up skills**: `sf-help-fetch`, `sf-metadata`

**Notes**: THE GOLDEN RULE case. No matching Connect REST resource exists for an invented capability. The skill must look it up, fail to find it, and say so plainly. It must NOT brute-force candidate paths — a guessed path returns 404 and burns calls while appearing to make progress.
