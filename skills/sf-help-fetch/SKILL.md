---
name: sf-help-fetch
plugin: cirra-ai-sf
argument-hint: '<article-url|topic-id> [--strategy aura|zoomin|auto] [--raw]'
metadata:
  version: 1.0.0
description: >
  Fetch readable article content from Salesforce Help (help.salesforce.com/s/articleView)
  without a browser. Use when asked to read, quote, or extract the body of a Salesforce Help
  page — those pages are a client-rendered Aura SPA, so curl/WebFetch only get a "Loading…"
  shell. The primary path is the anonymous Aura endpoint (Help_ArticleDataController.getData);
  an optional credentialed Zoomin path exists if service creds are supplied.
  Usage: /sf-help-fetch <article-url|topic-id> [--strategy aura|zoomin|auto] [--raw]
---

# sf-help-fetch

## Problem

`https://help.salesforce.com/s/articleView?id=<topic>.htm&type=5` is a client-rendered
Aura/LWC single-page app. A plain `curl`/`WebFetch` returns the ~200 KB app shell whose only
visible text is _"Loading… / Sorry to interrupt / CSS Error"_ — the article body never appears
because it is injected by JavaScript after load. A headless browser is often not an option
either (e.g. a sandbox whose network stack can't traverse the egress proxy), while `curl` can.

The real article body is DITA-generated XHTML that originates from Zoomin (`zoominsoftware.io`)
and is cached/re-served by Salesforce. There are two ways to get it.

## Usage

```bash
python3 scripts/fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_authenticate.htm&type=5"
python3 scripts/fetch_sf_help.py xcloud.remoteaccess_authenticate   # bare topic id
python3 scripts/fetch_sf_help.py <url> --strategy aura|zoomin|auto  # default: auto (aura, then zoomin)
python3 scripts/fetch_sf_help.py <url> --raw                        # raw XHTML instead of extracted text
```

The article content is written to stdout. Progress messages — including which strategy
succeeded — are written to stderr. All network I/O shells out to `curl` so an ambient
`HTTPS_PROXY` + CA bundle are honored automatically.

## Requirements & no-Python environments

The helper needs `python3` and `curl` — nothing else. If the running client has **no Python**
(or no code execution at all), the script can't run, but the skill is still usable: the
Strategy B section below documents the exact HTTP contract (endpoint, headers, `message` /
`aura.context` payloads, and the `release=""` self-discovery step), so an agent can drive it
with the same two `curl` calls plus any JSON tool (`jq`) or its own fetch capability. There is
no non-Python turnkey entrypoint; the Python script is a convenience wrapper around that
documented contract.

If handed a URL for a Salesforce surface it does **not** cover (Trailhead, Trailblazer
Community, `developer.salesforce.com`, or any non-`help.salesforce.com` host), the script exits
`2` with a specific message naming that surface and the real way to fetch it — see below —
rather than a generic "could not determine a topic id".

## Egress preflight

Each strategy first checks that its host is reachable and fails fast with an allowlist hint if
not. A real HTTP status (even 4xx/5xx) counts as reachable; only a proxy/DNS block —
`http_code 000` / a curl CONNECT failure — is treated as unreachable:

- Aura → probes `help.salesforce.com`; on block: _"…is not reachable from this environment. You
  may want to add `*.salesforce.com` to your domain allowlist and retry."_
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

The article body lands in `returnValue.returnValue.record.Content__c` (DITA XHTML). The two
volatile inputs are resolved automatically each run:

1. **`aura.context`** (`fwuid`, `app`, `loaded`) — rotates every Salesforce release. Scraped
   live from the article page (URL-decode + JSON-parse, not brittle regex).
2. **`release`** (e.g. `262.0.0`) — MUST be the current Salesforce release or the call returns
   `SUCCESS` with empty content. Self-discovered: one throwaway call with `release=""` still
   returns `returnValue.latestRNVersion`, which is then reused for the real fetch. Override
   with `HELP_RELEASE=262.0.0` if ever needed.

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
  python3 scripts/fetch_sf_help.py <topicId> --strategy zoomin
```

Without those it cannot retrieve content even when the host is reachable — use Strategy B.

## Other Salesforce doc surfaces (out of scope)

Different sites need different handling — verified separately, not wired into this skill:

- **`developer.salesforce.com/docs/...`** (Atlas): also a SPA, but has its own anonymous JSON
  content API — `GET /docs/get_document/atlas.<lang>.<deliverable>.meta` for the TOC and
  `doc_version`, then `GET /docs/get_document_content/<deliverable>/<topic>.htm/<lang>/<doc_version>`
  returns `{id,title,content}` with the body HTML. Same `*.salesforce.com` allowlist.
- **`trailhead.salesforce.com` modules**: the page HTML exposes only title/description
  (JSON-LD / og tags); the unit body loads via a `/graphql` API (not verified anonymously).
- **`trailhead.salesforce.com/trailblazer-community/feed/...`**: the feed body is not in the
  page HTML, but it _is_ retrievable anonymously via
  `POST https://trailhead.salesforce.com/services/community/graphql` with the `FeedItemDetail`
  operation (`variables.activityId` = the feed id) — no login required; the activity's
  `headline`/`body.segments` carry the text.
- **Server-rendered docs** (e.g. `docs.github.com`) need no skill — plain `curl`/`WebFetch`
  returns the prose directly.
