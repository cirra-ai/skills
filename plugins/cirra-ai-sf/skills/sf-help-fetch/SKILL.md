---
name: sf-help-fetch
plugin: cirra-ai-sf
argument-hint: '[url|topic-id|release-info [instance]]'
metadata:
  version: 1.3.1
description: >
  Read the full text of a Salesforce documentation page — both Salesforce Help
  (help.salesforce.com) and the developer docs (developer.salesforce.com) — without a
  browser, and answer Salesforce release questions. Doc pages render their content with
  JavaScript, so a plain fetch only returns an empty "Loading…" shell; this skill pulls the
  real article body through Salesforce's own content APIs. Just pass the page URL (or a Help
  topic id) and it returns the readable text. Release-notes URLs fetch the release named in
  the URL (current, preview, or previous). The special target release-info reports the
  current and preview Salesforce release and upcoming release windows — org-wide, or for one
  instance (also reachable by passing a status.salesforce.com instance URL). Usage:
  /sf-help-fetch [url|topic-id|release-info [instance]]
---

# sf-help-fetch

## Problem

Salesforce doc pages are client-rendered single-page apps. A plain `curl`/`WebFetch` of
`https://help.salesforce.com/s/articleView?id=<topic>.htm&type=5` (an Aura/LWC SPA) or of a
`https://developer.salesforce.com/docs/...` page returns the app shell whose only visible text
is _"Loading…"_ — the article body never appears because it is injected by JavaScript after
load. A headless browser is often not an option either (e.g. a sandbox whose network stack
can't traverse the egress proxy), while `curl` can.

Both surfaces have anonymous content APIs behind them. For Help, the real body is
DITA-generated XHTML that originates from Zoomin (`zoominsoftware.io`) and is cached/re-served
by Salesforce (Strategies B/A). For the developer docs, Salesforce serves an "Atlas" JSON
content API (Strategy C). This skill picks the right one by host, automatically.

## Usage

One argument — the page URL (or a bare Help topic id, or the literal `release-info`). No
flags, no options; the host picks the retrieval path automatically.

```bash
python3 scripts/fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_authenticate.htm&type=5"
python3 scripts/fetch_sf_help.py xcloud.remoteaccess_authenticate   # bare Help topic id
python3 scripts/fetch_sf_help.py "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_features_list_views.htm"
python3 scripts/fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow.htm&release=264&type=5"
python3 scripts/fetch_sf_help.py release-info         # current + preview release, upcoming windows
python3 scripts/fetch_sf_help.py release-info AP52    # one instance's release + windows
```

The only exception to "one argument" is release info: the literal target `release-info` takes
an optional second argument (a Salesforce instance key like `NA209`). A
`status.salesforce.com/instances/KEY` URL routes to the same path with one argument.

The readable text is written to stdout; a one-line progress note goes to stderr. All network
I/O shells out to `curl` so an ambient `HTTPS_PROXY` + CA bundle are honored automatically.
`help.salesforce.com` URLs use the anonymous Aura path (below), silently falling back to the
credentialed Zoomin path only if `ZOOMIN_BASIC` is set; `developer.salesforce.com/docs` URLs
use Strategy C (a page's Markdown twin when it has one, else the Atlas content API). The caller
never chooses.

## Requirements & no-Python environments

The helper needs `python3` and `curl` — nothing else. If the running client has **no Python**
(or no code execution at all), the script can't run, but the skill is still usable: the
Strategy B section below documents the exact HTTP contract (endpoint, headers, `message` /
`aura.context` payloads, and the `release=""` self-discovery step), so an agent can drive it
with the same two `curl` calls plus any JSON tool (`jq`) or its own fetch capability. There is
no non-Python turnkey entrypoint; the Python script is a convenience wrapper around that
documented contract.

If handed a URL for a Salesforce surface it does **not** cover (Trailhead, Trailblazer
Community, or any other host), the script exits `2` with a specific message naming that surface
and the real way to fetch it — see below — rather than a generic "could not determine a topic
id".

## Egress preflight

Each strategy first checks that its host is reachable and fails fast with an allowlist hint if
not. A real HTTP status (even 4xx/5xx) counts as reachable; only a proxy/DNS block —
`http_code 000` / a curl CONNECT failure — is treated as unreachable:

- Aura → probes `help.salesforce.com`; on block: _"…is not reachable from this environment. You
  may want to add `*.salesforce.com` to your domain allowlist and retry."_
- Atlas dev-docs → probes `developer.salesforce.com`; on block: the same `*.salesforce.com`
  message.
- Zoomin → probes `zd-ht-prod.zoominsoftware.io`; on block: the same message with
  `*.zoominsoftware.io`.

## Strategy B — Salesforce Aura endpoint (primary, anonymous)

Verified end-to-end: no auth, no captured tokens, no hardcoded version.

```text
POST https://help.salesforce.com/s/sfsites/aura?r=1&aura.ApexAction.execute=1
  descriptor: aura://ApexActionController/ACTION$execute
  classname : Help_ArticleDataController      method: getData
  params.articleParameters: {
    urlName: "<topicId>.htm", language: "en_US", release: "<currentRelease>",
    requestedArticleType: "HelpDocs", requestedArticleTypeNumber: "5" }
```

(That shape is for `type=5` Help Docs topics; `type=1` Knowledge Articles use the same action
with `requestedArticleType: "KBKnowledgeArticle"`, `requestedArticleTypeNumber: "1"`, an empty
`release`, and a multi-field body — see "Scope" above.) For HelpDocs the body lands in
`returnValue.returnValue.record.Content__c` (DITA XHTML). The two volatile inputs are resolved
automatically each run:

1. **`aura.context`** (`fwuid`, `app`, `loaded`) — rotates every Salesforce release. Scraped
   live from the article page (URL-decode + JSON-parse, not brittle regex).
2. **`release`** (e.g. `262.0.0`, HelpDocs only) — MUST be a release the API serves or the
   call returns `SUCCESS` with empty content. Self-discovered: one throwaway call with
   `release=""` still returns `returnValue.latestRNVersion`, which is then reused for the real
   fetch. A `release=NNN` query param in the input URL (release-notes pages) takes precedence
   over discovery — see "Release info" below. Override with `HELP_RELEASE=262.0.0` if ever
   needed (precedence: URL param, then `HELP_RELEASE`, then discovery).

This is the default path and needs nothing beyond `help.salesforce.com` being reachable.

## Strategy A — Zoomin "H&T adaptor" (optional, credentialed)

The upstream source Salesforce caches (it appears as `record.URL__c` in the Aura response). The
live `https://zd-ht-prod.zoominsoftware.io/openapi.json` (a FastAPI/`uvicorn` service) documents
the route:

```text
GET /v1/topics/<topicId>/content?lang=en&locale=en-us&major=262&minor=0&patch=0
```

`<topicId>` is the `id` param with `.htm` stripped, and `major.minor.patch` is the doc's
`Version__c`. **This host is not a public content API.** Every content route requires BOTH an
`Authorization: Basic <base64(user:pass)>` header (a Bearer token yields
`401 "Basic prefix is missing from Authorization header"`) AND an additional unnamed header —
without it every route returns `406 {"error":{"code":406,"message":"required header is missing"}}`.
These are Salesforce H&T service credentials used server-side; they do not appear in browser
DevTools. Strategy A therefore only runs when they are supplied out-of-band:

```bash
ZOOMIN_BASIC="user:pass" ZOOMIN_HEADER="Name: value" ZOOMIN_VERSION="262.0.0" \
  python3 scripts/fetch_sf_help.py <topicId>
```

When those env vars are present the script tries Zoomin automatically as a fallback if the Aura
path fails; otherwise it never touches Zoomin. There is no user-facing strategy switch.

## Strategy C — developer.salesforce.com docs (anonymous)

`developer.salesforce.com/docs` is a JS SPA too. Two anonymous paths are tried in order, both
automatic (routed by host — any `developer.salesforce.com/docs/...` URL uses this strategy):

### C1 — Markdown twin (fast path)

Many docs pages expose a **plain-Markdown twin at the same path with a `.md` extension** — the
skill fetches it in one request and returns the Markdown as-is (no HTML-to-text pass). E.g.
`https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.html` →
`https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.md`.

**This is not universal, so availability is detected by the response `Content-Type`, not the
HTTP status.** A page with a twin returns `Content-Type: text/markdown`; a page without one
still returns `200` but with `Content-Type: text/html` (the SPA shell — the `.md` effectively
falls back to `.htm`), so checking the status alone is not enough. The newer
`docs/<cloud>/<product>/guide/<topic>` deliverables tend to have twins (and are **only**
reachable this way — they have no `atlas.*.meta` segment for C2); the older
`atlas.<lang>.<deliverable>.meta/...` guides (e.g. the Apex Developer Guide) generally do not,
and fall through to C2. The twin is only attempted when the URL has a leaf document segment
(`<name>.htm`/`.html`/`.md`); a deliverable-landing URL with no leaf skips straight to C2.

### C2 — Atlas JSON content API (fallback)

For `atlas.<lang>.<deliverable>.meta` URLs without a Markdown twin, Salesforce exposes an
anonymous JSON content API — no auth, no tokens:

```text
1. GET /docs/get_document/<meta>
     <meta> = the "atlas.<lang>.<deliverable>.meta" segment from the URL path.
     Returns the deliverable manifest: `deliverable`, `locale`, `version.doc_version`,
     and the landing page's own `content`.
2. GET /docs/get_document_content/<deliverable>/<topic>.htm/<locale>/<doc_version>
     Returns {id, title, content} — `content` is the body HTML.
```

The `deliverable`/`locale`/`doc_version` are read from the step-1 manifest (authoritative),
**not** parsed out of the URL, so a version-less URL still resolves the current release. The
`<topic>` leaf is taken from the last `.htm`/`.html` path segment (or the URL fragment); a URL
with no leaf returns the deliverable's landing document. A blank `200` from step 2 means a bad
topic id / version and is reported as such.

## Release info (release notes + Trust status API)

The skill answers Salesforce release questions from two anonymous sources, both verified live:

### Release-notes pages honor the URL's release

Release-notes URLs carry the release in the query string, e.g.
`help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow.htm&release=264&type=5`.
The `release` param is passed through to the Aura call (normalized `264` → `264.0.0`) instead
of the discovered current release — without this, an archived- or preview-release URL would
silently return the **current** release's notes. Coverage (verified): the Aura API serves
roughly the **previous, current, and preview** releases (e.g. `260.0.0`/`262.0.0`/`264.0.0`
when current is 262); anything older returns `type: "NotFound"` and the skill fails with a
message pointing at the archive index topic `release-notes.rn_previous_release_notes.htm`
(itself fetchable by this skill — it links every older release's notes).

### The `release-info` target

`release-info` is the one non-URL special target (optionally followed by an instance key);
a `status.salesforce.com/instances/KEY` URL routes to the same code path.

- **`release-info`** (no instance) — prints the current release ("Summer '26 (262.0.0)" —
  number from `latestRNVersion`, seasonal name read from the release-notes landing title, no
  hardcoded mapping), the preview release when its notes are already published (the current
  major version plus 2, e.g. 262 → 264), and upcoming release maintenance windows across all
  instances. Degrades gracefully: if one source is unreachable the other still prints.
- **`release-info NA209`** (or `ap52` — case-insensitive, resolved via search) — that
  instance's running release (`releaseVersion`/`releaseNumber`, e.g.
  "Summer '26 Patch 13.7" / `262.13.7`), its maintenance window, and its upcoming
  release-maintenance events with planned start dates.

### Release name ↔ API version mapping

`release-info` also reports the **platform API version** for each release (the `vNN.0` used in
REST/SOAP/Apex endpoints). The mapping is **derived live, not hardcoded**: the anonymous Atlas
manifest `GET https://developer.salesforce.com/docs/get_document/atlas.en-us.api_rest.meta`
ties all three identifiers together in its `version` block — `version_text`
"Summer '26 (API version 67.0)", `release_version` `67.0`, `doc_version` `262.0` — and each
seasonal release adds 2 to the release major and 1 to the API version, so any release's API
version follows arithmetically from that anchor. The cadence was cross-checked against the
[REST Versions resource](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_versions.htm)
(`GET https://INSTANCE.salesforce.com/services/data/`, anonymous), which lists every
`label`/`version` pair (… Winter '25 = 62.0, Spring '25 = 63.0, Summer '25 = 64.0,
Winter '26 = 65.0, Spring '26 = 66.0, Summer '26 = 67.0). Snapshot of the recent mapping as
of August 2026 — the tool output is always the live-derived version:

| Release              | Release number | API version |
| -------------------- | -------------- | ----------- |
| Winter '27 (preview) | 264            | v68.0       |
| Summer '26 (current) | 262            | v67.0       |
| Spring '26           | 260            | v66.0       |
| Winter '26           | 258            | v65.0       |
| Summer '25           | 256            | v64.0       |

If the anchor fetch fails (e.g. `developer.salesforce.com` blocked), release-info simply omits
the API-version annotations rather than failing.

### Trust status API contract (verified empirically)

`https://api.status.salesforce.com` — anonymous, no tokens. The hosted Swagger UI at
`/v1/docs/` ships the default petstore stub, so these routes were verified by probing:

```text
GET /v1/instances/KEY/status   -> releaseVersion, releaseNumber, maintenanceWindow,
                                  status, isActive, embedded Maintenances[] (upcoming,
                                  with name/releaseType/plannedStartTime/plannedEndTime)
                                  404 {"message":"Instance Not Found"} for a bad key
GET /v1/search/QUERY           -> case-insensitive instance lookup: [{key, location,
                                  environment, isActive}, ...]
GET /v1/maintenances?limit=N   -> upcoming events across all instances; release events
                                  have type "release" and carry instanceKeys
```

Release maintenance events sharing a name (one per instance group / product) are collapsed to
`name: earliest .. latest planned start (N scheduled events)`.

## Scope: which Help articles are covered

`help.salesforce.com/s/articleView` serves two article kinds, distinguished by the `type` query
param — **both are handled**, dispatched automatically by id shape:

- **`type=5` — Help Docs topics** (ids like `xcloud.remoteaccess_authenticate.htm`): via
  `Help_ArticleDataController.getData` with `requestedArticleType: "HelpDocs"`; the body is
  `record.Content__c` (a single DITA XHTML blob).
- **`type=1` — numeric Knowledge Articles** (ids like `005360285`): the same `getData` action
  with `requestedArticleType: "KBKnowledgeArticle"`, `requestedArticleTypeNumber: "1"`, and an
  empty `release`. Knowledge Articles have **no `Content__c`**; the body is spread across
  rich-text fields (`title`, `summary`, `description`, `prerequisites`, `steps`, `task`,
  `resolution`, `additionalResources`), which the skill joins in reading order. Any numeric id
  (bare or in a URL) is routed here automatically.

## Other Salesforce doc surfaces (out of scope)

Different sites need different handling — verified separately, not wired into this skill:

- **`trailhead.salesforce.com` modules**: the page HTML exposes only title/description
  (JSON-LD / og tags); the unit body loads via a `/graphql` API (not verified anonymously).
- **`trailhead.salesforce.com/trailblazer-community/feed/...`**: the feed body is not in the
  page HTML, but it _is_ retrievable anonymously via
  `POST https://trailhead.salesforce.com/services/community/graphql` with the `FeedItemDetail`
  operation (`variables.activityId` = the feed id) — no login required; the activity's
  `headline`/`body.segments` carry the text.
- **Server-rendered docs** (e.g. `docs.github.com`) need no skill — plain `curl`/`WebFetch`
  returns the prose directly.
