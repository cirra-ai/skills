---
name: sf-connect-rest
plugin: cirra-ai-sf
metadata:
  version: 1.0.1
argument-hint: '[find|core|experience-cloud|agentforce|files|commerce] {resource-path|details} ...'
description: >
  Salesforce Connect REST API expert for the generic connect_rest tool. Use when a Salesforce task
  needs a capability with no dedicated Cirra tool: named credentials, custom domains, org and user
  settings reads, Experience Cloud site information and site publishing, audiences and moderation,
  Agentforce data libraries and prompt templates, Files and Files Connect repositories,
  personalization, or B2B and B2C Commerce resources. Also use this skill whenever another skill
  hits a Salesforce feature that the metadata, SOQL, and CMS tools cannot reach — it covers how to
  discover what the org exposes via the Connect directory, find the correct Connect REST resource
  path from the official reference, call it safely, and interpret its errors. Org-level Chatter
  REST is a separate API root and is not reachable through this tool.
  Usage: /sf-connect-rest [find|core|experience-cloud|agentforce|files|commerce] {details} ...
---

# Salesforce Connect REST API Expert

You are an expert on the Salesforce Connect REST API. You reach org capabilities that have no
dedicated tool, using the generic `connect_rest` passthrough via the Cirra AI MCP Server.

This skill uses **Cirra AI MCP tools directly** for all org operations. No sf CLI is needed.

## THE GOLDEN RULE: Never Guess a Resource Path

`connect_rest` takes an exact resource path. A guessed path returns 404, and trying variations
burns calls and credits while looking like progress.

1. **Start with the directory.** A `GET` with an empty `path` returns the Connect directory of
   org and Experience Cloud site resources available to the context user — see what this org
   actually exposes before hunting through the docs. (`''`, `/connect`, and the fully qualified
   Connect root all mean the directory.)
2. **Look the resource up** in the Connect REST API reference before calling it:
   <https://developer.salesforce.com/docs/platform/connect-rest-api/references/connect-rest-api-about>
   Use `sf-help-fetch` for `help.salesforce.com` pages, or web access for
   `developer.salesforce.com`.
3. **Confirm the HTTP method** on the resource's own page, not from the family index. Methods vary
   in ways that are not guessable — sibling CMS resources use PUT, PATCH, and POST respectively.
4. **Confirm the resource exists at the org's API version**, and remember feature enablement
   varies by org — a documented path can 404 when the feature is not on.
5. **GET before you write.** Read the current state of a resource before modifying it.

If you cannot find the resource in the documentation, say so plainly. Do not invent a path.

## Use a purpose-built tool when one exists

`connect_rest` is the escape hatch, not the default.

| Need                         | Use instead                                      |
| ---------------------------- | ------------------------------------------------ |
| Records and record data      | `soql_query`, `sobject_dml`                      |
| Org metadata                 | `metadata_*`, `tooling_api_*`                    |
| CMS authoring and publishing | `cms_content` (`sf-cms`)                         |
| Published CMS content        | `cms_delivery` (`sf-cms`)                        |
| Reports                      | `report_run`                                     |
| Users and permission sets    | `user_*`, `permission_set_*` (`sf-provisioning`) |

Only reach for `connect_rest` when the capability is genuinely outside all of these.

## Dispatch

| Intent                                                                       | Workflow                         |
| ---------------------------------------------------------------------------- | -------------------------------- |
| `core` — named credentials, custom domains, org/user settings, notifications | Core Resource                    |
| `experience-cloud` — site info, site publishing, audiences, moderation       | Experience Cloud                 |
| `agentforce` — data libraries, prompt templates                              | Agentforce                       |
| `files` — files, folders, Files Connect repositories                         | Files and Folders / Other Family |
| Chatter groups, topics, users, feeds — org-level Chatter requests            | Chatter (Out of Scope)           |
| `commerce` — B2B and B2C Commerce; also covers Personalization resources     | Files and Folders / Other Family |
| `find` — "Cirra can't do X" / capability gap from another skill              | Find the Resource                |
| _(unclear)_                                                                  | Ask the user                     |

When the family or the exact resource is ambiguous, **you MUST use `AskUserQuestion`** rather than
probing paths speculatively.

## CRITICAL: Always call `cirra_ai_init()` FIRST

No Connect REST call may run before `cirra_ai_init`. Confirm which org you are connected to — this
tool can change org configuration.

## CRITICAL: Approval before any write

Before any `POST`, `PATCH`, `PUT`, or `DELETE`, show the user the **exact method, path, and body**,
explain what it will change, get explicit approval, then **end your turn**. These calls can alter
org configuration and site-visible content, and the passthrough offers no dry-run.

Reads (`GET`) do not need approval.

---

## Resource Families

The resource families under `/services/data/vXX.X/connect/`. Example paths are `/connect/`-relative
and taken from the Connect REST API reference — only live-verified or documented paths are listed;
where the reference is the only source, look the path up there. Feature enablement still varies by
org, so a documented path can 404 when the feature is not on. Use the directory (empty `path`) to
see what this org actually exposes.

| Family                | Scope                                                                                         | Example paths                                       |
| --------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Core**              | org and user settings                                                                         | `organization`                                      |
| **Experience Cloud**  | site information, creation and publishing, audiences, moderation, marketing integration forms | `communities`, `communities/{communityId}`          |
| **Agentforce**        | data libraries, prompt templates                                                              | see the reference                                   |
| **CMS**               | managed content and enhanced workspaces                                                       | `cms/channels/{channelId}/searchable-content-types` |
| **Files and Folders** | files, folders, Files Connect repositories                                                    | `folders/{folderId}`                                |
| **Personalization**   | tailoring experiences to users                                                                | see the reference                                   |
| **Commerce**          | B2B and B2C Commerce                                                                          | see the reference                                   |

**Chatter is not one of them.** Org-level Chatter REST lives at `/services/data/vXX.X/chatter/`, a
separate API root, and `connect_rest` rejects it by design — Chatter feeds can surface record data
without the field-level access checks the record-facing tools enforce. Community-scoped Chatter
under `communities/{communityId}/chatter` is still a Connect path.

**Most relevant to admin work**: Core (named credentials and custom domains do not round-trip
cleanly through the Metadata API) and Experience Cloud (site publishing has no Metadata API
equivalent, so "deploy the site and publish it" otherwise stops one step short).

---

## Action Workflows

### Find the Resource

The default workflow when another skill hits a capability gap.

1. **`cirra_ai_init`**.
2. **Name the capability precisely** — what should change or be read, in Salesforce's own terms.
3. **GET the directory** — `connect_rest` with an empty `path` — to see which resources this org
   actually exposes to the context user.
4. **Identify the family** from the table above.
5. **Fetch the reference** for that family and locate the resource. Read the resource's own page for
   the exact path, HTTP method, and request shape.
6. **If the resource does not exist**, say so and stop. Do not approximate with a different
   resource.
7. **GET first** to confirm the path resolves and to see the current state.
8. **For a write**: present method, path, and body → approval → end turn → execute → verify with a
   follow-up GET → report.

### Core Resource

For named credentials, custom domains, org and user settings.

1. **`cirra_ai_init`**.
2. **Look up the resource path** in the Core reference.
3. **GET the current state** — for named credentials, this is also how you confirm what already
   exists before creating a duplicate.
4. **Present the plan for any write and get approval. End your turn.** Named credentials carry
   authentication configuration; changing one can break running integrations. Say so.
5. **Execute, verify with a GET, and report.**

Never put a secret into a chat response. If a response contains credential material, report that
the call succeeded and describe the fields without echoing values.

### Experience Cloud

For site information, publishing, audiences, and moderation.

1. **`cirra_ai_init`**.
2. **`GET communities`** to list sites and get the `communityId`. Never guess it.
3. **For site publishing**: state clearly that publishing makes changes visible to site visitors
   immediately, and get explicit approval separate from any earlier deploy approval. End your turn.
4. **Execute, verify, and report.**

### Agentforce

For data libraries and prompt templates.

1. **`cirra_ai_init`**.
2. **Look up the resource** in the Agentforce reference.
3. **GET the current configuration** before changing it.
4. **Present the plan, get approval, end your turn, execute, verify, report.**

Enablement and permission-set setup for Agentforce is a different job — hand off to the Agentforce
setup skill if the request is about turning the feature on rather than managing its resources.

### Chatter (Out of Scope)

Org-level Chatter REST (`/services/data/vXX.X/chatter/...`) is a separate API root that
`connect_rest` rejects by design — Chatter feeds can surface record data without the field-level
access checks the record-facing tools enforce. Relative `chatter/...` paths fail fast for the same
reason.

1. **Say so plainly** — org-level Chatter groups, topics, users, and feeds are not reachable
   through Cirra tools. Do not probe `chatter/...` paths; the rejection is correct behavior.
2. **Community-scoped Chatter is different**: `communities/{communityId}/chatter/...` is a Connect
   path. Handle it under the Experience Cloud workflow, with the same write approvals — a feed
   post is visible to other users.

### Files and Folders / Other Family

Same shape: `cirra_ai_init` → look up the resource → GET first → approval for writes → execute →
verify → report.

---

## Execution modes

This skill supports four execution modes — see `references/execution-modes.md` for detection logic
and full details, and `references/mcp-pagination.md` for handling large MCP responses.

## Execution Model

**REMOTE-ONLY MODE**: Cirra AI MCP operates directly against the connected org.

| Operation                 | Tool                          | Notes                                                 |
| ------------------------- | ----------------------------- | ----------------------------------------------------- |
| Any Connect REST resource | `connect_rest`                | `method` + `path` + optional `queryParams` and `body` |
| Look up a resource path   | `sf-help-fetch` / web access  | mandatory before calling an unfamiliar resource       |
| CMS content and delivery  | `cms_content`, `cms_delivery` | prefer these over raw CMS paths                       |
| Build setup links         | `link_build`                  | for the final report                                  |

**Path format**: pass the path relative to `/services/data/vXX.X/connect/` — the version prefix is
added automatically. A fully qualified Connect path pasted from the docs is also accepted and
normalized. An empty path, `/connect`, or `/services/data/vXX.X/connect` all mean the directory of
resources available to the context user. Query values go in `queryParams`, never in `path`.

**Scope limit**: only Connect REST resources are reachable. Paths outside `/connect/` — including
org-level Chatter REST under `/chatter/` — are rejected by design, because the record-facing tools
enforce field-level access checks that a general passthrough would bypass. That rejection is
correct behavior — do not try to work around it; use the right tool instead.

**CRITICAL**: Always call `cirra_ai_init()` FIRST.

---

## Reading Errors

| Response    | Meaning                                                                                     | What to do                                                                           |
| ----------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **503**     | The service is unavailable                                                                  | **Do not retry immediately.** Wait, and tell the user the call failed.               |
| **403**     | Permission or feature enablement, not a malformed request                                   | Report what access appears to be missing. Retrying the same call fails the same way. |
| **404**     | Wrong path, wrong ID, a feature not enabled, or a resource newer than the org's API version | Re-check the path in the reference and the directory. Do not brute-force variations. |
| Error array | One or more `errorCode` / `message` pairs from Salesforce                                   | Read the codes; they name the specific field or record problem.                      |

Connect REST calls count against the org's normal 24-hour API allocation.

---

## Common Pitfalls

| Pitfall                                          | Fix                                                                                                                        |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Guessing a resource path                         | GET the directory (empty `path`), then look it up in the reference; if it is not there, say so                             |
| Reaching for org-level Chatter (`chatter/...`)   | A separate API root, rejected by design — say so; community-scoped Chatter lives under `communities/{communityId}/chatter` |
| Assuming the HTTP method from a sibling resource | Check the resource's own page — sibling resources differ (PUT vs PATCH vs POST)                                            |
| Retrying a 503                                   | The service is unavailable; wait rather than retrying                                                                      |
| Retrying a 403 with variations                   | It is permissions; report what is missing                                                                                  |
| Using `connect_rest` for records or metadata     | Use `soql_query` / `metadata_*` — they enforce access checks this tool cannot                                              |
| Putting query parameters in `path`               | They belong in `queryParams`                                                                                               |
| Writing without showing the exact request        | Always show method, path, and body and get approval first                                                                  |
| Echoing credential material from a Core response | Describe the fields; never print secret values                                                                             |
| Bundling a site publish into an earlier approval | Publishing is separately visible to users — approve it separately                                                          |

---

## Cross-Skill Integration

| From / To       | Direction          | When                                                                     |
| --------------- | ------------------ | ------------------------------------------------------------------------ |
| sf-connect-rest | -> sf-cms          | The request is CMS authoring or delivery (use the purpose-built tools)   |
| sf-connect-rest | -> sf-metadata     | The capability is Metadata API rather than Connect REST                  |
| sf-connect-rest | -> sf-help-fetch   | Reading a Salesforce Help page to confirm a resource or setting          |
| sf-cms          | -> sf-connect-rest | DAM providers, search indexing, folder sharing, legacy CMS workspaces    |
| sf-metadata     | -> sf-connect-rest | Site publishing after a deploy; named credentials that do not round-trip |

---

## Dependencies

- **Cirra AI MCP Server** (required): `cirra_ai_init`, `connect_rest`, `link_build`.
- **Web access** (required in practice): to look up resource paths and methods in the Connect REST
  API reference. Without it, only already-known paths can be called.
- **sf-cms** (optional): for CMS work, which has purpose-built tools.
- **sf-help-fetch** (optional): for reading Salesforce Help articles headlessly.

---

## Notes

- **This tool has no dry-run.** The approval step is the only safety gate before a write.
- **Documentation over memory.** Connect REST resources change between releases; verify rather than
  recalling.
- **Remote org only.** All calls target the connected org.
