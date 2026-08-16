#!/usr/bin/env python3
"""
Fetch readable Salesforce documentation content as text — without a browser.

Salesforce docs are JavaScript single-page apps, so curl/WebFetch only get a
"Loading…" shell. This script pulls the real body through Salesforce's own
anonymous content APIs, dispatching by host:

  * help.salesforce.com/s/articleView  -> the Aura endpoint (strategies B/A below)
  * developer.salesforce.com/docs/...   -> the Atlas content API (fetch_developer_docs)

For help.salesforce.com the actual article body is DITA-generated XHTML that
comes from Zoomin (zoominsoftware.io) and is cached/re-served by Salesforce.

Two Help strategies (default `auto` tries B first, then A):

  B. AURA ENDPOINT  (primary; anonymous; only needs help.salesforce.com reachable)
       POST https://help.salesforce.com/s/sfsites/aura   (ApexActionController)
       classname=Help_ArticleDataController  method=getData
     Handles both help article kinds, dispatched by id shape:
       * type=5 Help Docs topics (xcloud.<name>.htm) -> requestedArticleType
         "HelpDocs"; body in record.Content__c; SF `release` self-discovered
         (a call with release="" returns returnValue.latestRNVersion).
       * type=1 Knowledge Articles (numeric id, e.g. 005360285) ->
         requestedArticleType "KBKnowledgeArticle"; body spread across rich-text
         fields (summary/description/steps/task/resolution/...), joined in order.
     The aura.context (fwuid / app / loaded) is scraped live each run. No
     DevTools capture, no hardcoded version.

  A. ZOOMIN DIRECT  (optional; requires *.zoominsoftware.io allowlisted AND creds)
       GET https://zd-ht-prod.zoominsoftware.io/v1/topics/<topicId>/content
     This is the upstream source Salesforce caches (record.URL__c), but the host
     is a credentialed service adaptor: it needs HTTP Basic auth PLUS an unnamed
     required header (server-side H&T creds), so it only runs when ZOOMIN_BASIC /
     ZOOMIN_HEADER are supplied. Not anonymously accessible.

  C. DEVELOPER DOCS  (developer.salesforce.com; anonymous)
       1. MARKDOWN TWIN (fast path): fetch the same path with a '.md' extension;
          many pages (esp. newer '/docs/<cloud>/<product>/guide/<topic>' ones)
          return clean Markdown. Detected via Content-Type: text/markdown — a
          page without a twin still 200s with the HTML shell, so status alone
          won't tell you.
       2. ATLAS JSON API (fallback; atlas.<lang>.<deliverable>.meta URLs):
          GET /docs/get_document/atlas.<lang>.<deliverable>.meta       -> manifest
          GET /docs/get_document_content/<deliverable>/<topic>.htm/<locale>/<doc_version>
     The deliverable/locale/doc_version are read from the manifest, so a
     version-less URL still resolves the current release.

All network calls shell out to `curl` so the session's HTTPS_PROXY + CA bundle
are honored automatically (Node's built-in fetch and headless Chromium do not
traverse this proxy reliably).

Retrieval is fully automatic — the caller only supplies the URL (or a Help topic
id). The host picks the path; for Help, Aura is the anonymous path that works out
of the box and the credentialed Zoomin fallback is used only if ZOOMIN_BASIC is
set in the environment.

Release info (strategy D): the skill also answers Salesforce release questions.

  * A help.salesforce.com URL with a `release=NNN` query param (release-notes
    pages) fetches that release's notes, not silently the current one. The Aura
    API serves roughly the previous, current, and preview releases; older
    releases return NotFound and the error points at the archive index topic
    (release-notes.rn_previous_release_notes.htm).
  * `fetch_sf_help.py release-info` prints the current + preview release
    (name and version, self-discovered from the release-notes landing pages)
    and upcoming release maintenance windows from the anonymous Salesforce
    Trust status API (https://api.status.salesforce.com/v1/docs/).
  * `fetch_sf_help.py release-info <INSTANCE>` (e.g. NA209) prints that
    instance's running release and its upcoming release maintenance windows.
    A https://status.salesforce.com/instances/<KEY> URL routes here too.

Usage:
    python3 fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_authenticate.htm&type=5"
    python3 fetch_sf_help.py xcloud.remoteaccess_authenticate           # bare topic id
    python3 fetch_sf_help.py "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_features_list_views.htm"
    python3 fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow.htm&release=262&type=5"
    python3 fetch_sf_help.py release-info            # current + preview release, upcoming windows
    python3 fetch_sf_help.py release-info AP52       # one instance's release + windows
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse

ZOOMIN_HOST = "https://zd-ht-prod.zoominsoftware.io"
HELP_HOST   = "https://help.salesforce.com"
DEV_HOST    = "https://developer.salesforce.com"
STATUS_HOST = "https://api.status.salesforce.com"
LANG        = "en_US"

# The archive index for release notes older than the served window (previous /
# current / preview). Itself a normal HelpDocs topic this skill can fetch.
RN_ARCHIVE_TOPIC = "release-notes.rn_previous_release_notes.htm"
# The release-notes landing topic; its title carries the seasonal release name
# ("Salesforce Summer '26 Release Notes"), which is how release-info resolves
# a release number to a name without any hardcoded mapping.
RN_LANDING_TOPIC = "release-notes.salesforce_release_notes.htm"

# --- Strategy B action contract (verified from a live request) ----------------
# The Salesforce Help SPA fetches article bodies via this guest-accessible Aura
# Apex action (also visible in the x-sfdc-lds-endpoints request header):
#     aura://ApexActionController/ACTION$execute
#     classname = Help_ArticleDataController   method = getData
#     params.articleParameters = {
#         urlName: "<topicId>.htm", language: "en_US",
#         release: "<262.0.0>",           # MUST be the current SF release, else
#                                         # SUCCESS but empty content
#         requestedArticleType: "HelpDocs", requestedArticleTypeNumber: "5" }
# The `release` is discovered automatically: a call with release="" still returns
# returnValue.latestRNVersion, which we then use for the real fetch. No hardcoding,
# no DevTools capture needed.
HELP_APEX_CLASS  = "Help_ArticleDataController"
HELP_APEX_METHOD = "getData"


def curl(args, timeout=30):
    return subprocess.run(["curl", "-sS", "--max-time", str(timeout), *args],
                          capture_output=True, text=True)


def assert_reachable(host, allowlist):
    """Fail fast (with an allowlist hint) if `host` isn't reachable from here.

    A real HTTP status (even 4xx/5xx) means reachable. Only an egress/proxy
    block — curl CONNECT failure, DNS failure, timeout — yields http_code 000
    (or empty), which is what we treat as 'not reachable'."""
    r = curl(["-o", os.devnull, "-w", "%{http_code}", f"https://{host}/"], timeout=12)
    code = (r.stdout or "").strip()
    if code in ("", "000"):
        raise RuntimeError(
            f"{host} is not reachable from this environment. "
            f"You may want to add {allowlist} to your domain allowlist and retry.")


def unsupported_url_message(arg):
    """If `arg` is a URL for a Salesforce doc surface this skill does NOT handle,
    return a clear, actionable message naming the surface and the real path for
    it; otherwise return None. Keeps failures self-explanatory instead of a
    generic "could not determine a topic id".

    Note: help.salesforce.com articleView pages (type=5 Help Docs topics and
    type=1 numeric Knowledge Articles) and developer.salesforce.com/docs pages
    are all supported, so they return None."""
    if not arg.startswith("http"):
        return None
    parts = urllib.parse.urlparse(arg)
    host, path = parts.netloc.lower(), parts.path
    if host in ("help.salesforce.com", ""):
        return None  # supported: type=5 topics and type=1 Knowledge Articles
    if host == "developer.salesforce.com" and path.startswith("/docs/"):
        return None  # supported: Atlas content API (see fetch_developer_docs)
    if host in ("status.salesforce.com", "api.status.salesforce.com"):
        return None  # supported: Trust status API (see fetch_release_info)
    if host == "trailhead.salesforce.com":
        if "/trailblazer-community/" in path:
            return (
                "Trailblazer Community pages aren't handled by sf-help-fetch. The feed body "
                "IS available anonymously via POST https://trailhead.salesforce.com/services/"
                "community/graphql (operation FeedItemDetail, variables.activityId=<feed id "
                "from the URL>) — drive that directly rather than through this skill."
            )
        return (
            "Trailhead learning content isn't handled by sf-help-fetch. Only the title/"
            "description are anonymously available (JSON-LD / og tags on the page); the unit "
            "body loads via a token/auth-gated /graphql API."
        )
    return (
        f"{host} isn't handled by sf-help-fetch — this skill reads "
        "help.salesforce.com/s/articleView and developer.salesforce.com/docs pages."
    )


def topic_id_from(arg):
    """Accept a full articleView URL or a bare topic id; return e.g. xcloud.remoteaccess_authenticate."""
    if arg.startswith("http"):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(arg).query)
        raw = (q.get("id") or [""])[0]
    else:
        raw = arg
    topic = re.sub(r"\.htm$", "", raw.strip())
    if not topic:
        raise ValueError(
            f"could not determine a topic id from {arg!r} — pass a "
            "help.salesforce.com/s/articleView?id=<topic>.htm URL or a bare topic id")
    return topic


def release_from(arg):
    """Explicit `release` query param from a help.salesforce.com URL, normalized
    to the three-part form the Aura API expects (256 -> 256.0.0), or None when
    absent (a bare topic id, or a URL without the param).

    Release-notes URLs carry the release as e.g. `release=262`; passing it
    through matters because the Aura API otherwise defaults to the current
    release — the caller would silently get the wrong release's notes."""
    if not arg.startswith("http"):
        return None
    q = urllib.parse.parse_qs(urllib.parse.urlparse(arg).query)
    raw = (q.get("release") or [""])[0].strip()
    if not raw:
        return None
    if not re.fullmatch(r"\d+(\.\d+){0,2}", raw):
        raise ValueError(f"unrecognized release {raw!r} in {arg!r} — expected a "
                         "number like 262 or 262.0.0")
    return ".".join((raw.split(".") + ["0", "0"])[:3])


def html_to_text(markup):
    markup = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", markup, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", markup)
    text = html.unescape(text)  # decode entities (&amp; &#39; …) rather than dropping them
    return re.sub(r"\s+", " ", text).strip()


# --- Strategy A: Zoomin "H&T adaptor" (credentialed) --------------------------
# VERIFIED CONTRACT (from the live openapi.json at ZOOMIN_HOST/openapi.json):
#   GET /v1/topics/{topic_id}/content
#       ?lang=<en>&locale=<en-us>&major=<262>&minor=<0>&patch=<0>   (all required)
# AUTH WALL (verified empirically): this host is NOT an anonymous content API.
#   It requires BOTH:
#     * Authorization: Basic <base64(user:pass)>   (a Bearer token yields
#       401 "Basic prefix is missing from Authorization header")
#     * an additional unnamed request header — without it every content route
#       returns 406 {"error":{"code":406,"message":"required header is missing"}}
#   These are the Salesforce H&T *service* credentials/headers used server-side;
#   they do NOT appear in browser DevTools (the browser only ever calls the
#   Aura endpoint on help.salesforce.com — see Strategy B). So Strategy A only
#   works if you can supply real credentials + the required header out-of-band:
#       ZOOMIN_BASIC="user:pass"  ZOOMIN_HEADER="Name: value"  python3 fetch_sf_help.py ...
# Version (major/minor/patch) is the Salesforce release the doc was published in
# (e.g. 262.0.0); override with ZOOMIN_VERSION="262.0.0".
def fetch_zoomin(topic_id):
    assert_reachable("zd-ht-prod.zoominsoftware.io", "*.zoominsoftware.io")
    ver = os.environ.get("ZOOMIN_VERSION", "262.0.0")
    major, minor, patch = (ver.split(".") + ["0", "0"])[:3]
    lang   = os.environ.get("ZOOMIN_LANG", "en")
    locale = os.environ.get("ZOOMIN_LOCALE", "en-us")
    q = urllib.parse.urlencode({"lang": lang, "locale": locale,
                                "major": major, "minor": minor, "patch": patch})
    url = f"{ZOOMIN_HOST}/v1/topics/{topic_id}/content?{q}"
    args = ["-w", "\n__HTTP__%{http_code}"]
    if os.environ.get("ZOOMIN_BASIC"):
        args += ["-u", os.environ["ZOOMIN_BASIC"]]
    if os.environ.get("ZOOMIN_HEADER"):
        args += ["-H", os.environ["ZOOMIN_HEADER"]]
    r = curl(args + [url])
    body = r.stdout
    marker = body.rfind("\n__HTTP__")
    code = body[marker + len("\n__HTTP__"):].strip() if marker >= 0 else ""
    body = body[:marker] if marker >= 0 else body
    if code == "406":
        raise RuntimeError("zoomin 406: credentialed adaptor — set ZOOMIN_BASIC and ZOOMIN_HEADER "
                           "(Salesforce H&T service creds; not anonymously accessible)")
    if code in ("401", "403"):
        raise RuntimeError(f"zoomin {code}: auth rejected (check ZOOMIN_BASIC)")
    if not code.startswith("2"):
        raise RuntimeError(f"zoomin HTTP {code or '000'} ({r.stderr.strip() or 'unavailable'})")
    stripped = body.lstrip()
    if stripped.startswith("{"):
        try:
            j = json.loads(body)
            body_html = j.get("body") or j.get("html") or j.get("content") or json.dumps(j, indent=2)[:4000]
            return html_to_text(body_html)
        except json.JSONDecodeError:
            pass
    return html_to_text(body)


# --- Strategy B: Aura endpoint on help.salesforce.com -------------------------
def scrape_aura_context(topic_id):
    """Fetch the live article page and pull the current aura.context blob.

    The page embeds the context as a URL-encoded JSON object inside a
    `/s/sfsites/l/%7B...%7D...` script src. We locate it, URL-decode, and
    JSON-parse the leading object rather than regex-matching encoded fields
    (the values contain encoded ':' and '/' which defeat naive regexes)."""
    # The aura.context (fwuid/app/loaded) is global to the site, so any article
    # page works; build a faithful URL for the id kind just to be safe.
    if topic_id.isdigit():
        page_url = f"{HELP_HOST}/s/articleView?id={topic_id}&type=1"
    else:
        page_url = f"{HELP_HOST}/s/articleView?id={topic_id}.htm&type=5"
    page = curl(["-L", page_url], timeout=30).stdout
    # The page has several `%7B%22mode%22...%7D` (i.e. {"mode"...}) context blobs;
    # only the app-bootstrap one carries fwuid. Try each until one parses with fwuid.
    obj = None
    for mm in re.finditer(r"%7B%22mode%22", page):
        decoded = urllib.parse.unquote(page[mm.start():mm.start() + 4000])
        try:
            cand, _ = json.JSONDecoder().raw_decode(decoded)
        except json.JSONDecodeError:
            continue
        if "fwuid" in cand and "app" in cand:
            obj = cand
            break
    if obj is None:
        raise RuntimeError("could not locate an aura.context with fwuid (page shape changed?)")
    ctx = {"mode": obj.get("mode", "PROD"), "fwuid": obj["fwuid"], "app": obj["app"],
           "dns": obj.get("dns", "c"), "pathPrefix": obj.get("pathPrefix", ""), "ls": 1}
    if "loaded" in obj:
        ctx["loaded"] = obj["loaded"]
    return ctx


def _getdata(ctx, url_name, release, type_number="5", requested_type="HelpDocs"):
    """One Help_ArticleDataController.getData call; returns the inner returnValue.

    `requested_type`/`type_number` select the article kind: HelpDocs/"5" for
    type=5 Help Docs topics, KBKnowledgeArticle/"1" for type=1 Knowledge Articles."""
    action = {
        "id": "1;a", "descriptor": "aura://ApexActionController/ACTION$execute",
        "callingDescriptor": "UNKNOWN",
        "params": {"namespace": "", "classname": HELP_APEX_CLASS, "method": HELP_APEX_METHOD,
                   "params": {"articleParameters": {
                       "urlName": url_name, "language": LANG, "release": release,
                       "requestedArticleType": requested_type,
                       "requestedArticleTypeNumber": type_number}},
                   "cacheable": False, "isContinuation": False}}
    data = urllib.parse.urlencode({"message": json.dumps({"actions": [action]}),
                                   "aura.context": json.dumps(ctx), "aura.token": "null"})
    res = curl(["-X", "POST", f"{HELP_HOST}/s/sfsites/aura?r=1&aura.ApexAction.execute=1",
                "-H", "content-type: application/x-www-form-urlencoded; charset=UTF-8",
                "-H", f"x-sfdc-lds-endpoints: ApexActionController.execute:{HELP_APEX_CLASS}.{HELP_APEX_METHOD}",
                "--data-raw", data], timeout=30)
    out = res.stdout
    if res.returncode != 0 and not out.strip():
        raise RuntimeError("aura request failed: " + (res.stderr.strip() or "curl error"))
    if "/*ERROR*/" in out:
        m = re.search(r"\{.*\}", out, re.S)
        raise RuntimeError("aura error: " + (m.group(0)[:300] if m else out[:300]))
    try:
        payload = json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "aura response was not JSON (proxy or error page?): "
            + (res.stderr.strip() or out[:200] or str(e))) from e
    try:
        act = payload["actions"][0]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("aura response missing actions[]: " + json.dumps(payload)[:200]) from None
    if act.get("state") != "SUCCESS":
        raise RuntimeError("aura non-success: " + json.dumps(act.get("error", act))[:300])
    try:
        return act["returnValue"]["returnValue"]
    except (KeyError, TypeError):
        raise RuntimeError("aura response missing returnValue: " + json.dumps(act)[:200]) from None


# Knowledge-Article rich-text fields, in reading order. Different KB record
# types populate different subsets; join whichever are non-empty.
HELP_KB_FIELDS = ("summary", "description", "prerequisites", "steps", "task",
                  "resolution", "additionalResources")


def _knowledge_text(rec):
    """Assemble a Knowledge Article's readable body from its rich-text fields."""
    parts = []
    if rec.get("title"):
        parts.append(rec["title"])
    for field in HELP_KB_FIELDS:
        val = rec.get(field)
        if val and str(val).strip():
            parts.append(html_to_text(str(val)))
    return "\n\n".join(p for p in parts if p.strip())


def _fetch_helpdocs(ctx, topic_id, release=None):
    url_name = topic_id if topic_id.endswith(".htm") else topic_id + ".htm"
    # Precedence: explicit release from the URL > HELP_RELEASE override >
    # self-discovery. Discovery: a call with release="" still returns
    # returnValue.latestRNVersion (wrong/empty release => empty content).
    explicit = release
    release = release or os.environ.get("HELP_RELEASE") \
        or _getdata(ctx, url_name, "").get("latestRNVersion")
    if not release:
        raise RuntimeError("could not determine current SF release (latestRNVersion missing)")
    rv = _getdata(ctx, url_name, release)
    rec = rv.get("record")
    if not rec or not rec.get("Content__c"):
        if explicit and rv.get("type") == "NotFound":
            current = rv.get("latestRNVersion") or "unknown"
            raise RuntimeError(
                f"no content for {url_name} at release {explicit}: the Help API only "
                f"serves roughly the previous, current, and preview releases (current is "
                f"{current}). Older release notes are linked from the archive index — "
                f"fetch {RN_ARCHIVE_TOPIC} for the list.")
        raise RuntimeError(f"no content for {url_name} at release {release} "
                           f"(check the topic id / language)")
    return html_to_text(rec["Content__c"])


def _fetch_knowledge(ctx, article_id):
    # Knowledge Articles (type=1, numeric id) use requestedArticleType
    # "KBKnowledgeArticle"; release is not used and the body is spread across
    # rich-text fields rather than a single Content__c.
    rec = _getdata(ctx, article_id, "", type_number="1",
                   requested_type="KBKnowledgeArticle").get("record")
    if not rec:
        raise RuntimeError(f"no Knowledge Article found for id {article_id} "
                           f"(check the article id / language)")
    text = _knowledge_text(rec)
    if not text:
        raise RuntimeError(f"Knowledge Article {article_id} has no readable body fields")
    return text


def fetch_aura(topic_id, release=None):
    assert_reachable("help.salesforce.com", "*.salesforce.com")
    ctx = scrape_aura_context(topic_id)              # live fwuid/app/loaded (global)
    ctx.update({"dn": [], "globals": {}, "uad": True})
    # A purely numeric id is a type=1 Knowledge Article (no release concept);
    # otherwise a HelpDocs topic, honoring an explicit release from the URL.
    if topic_id.isdigit():
        return _fetch_knowledge(ctx, topic_id)
    return _fetch_helpdocs(ctx, topic_id, release)


# --- developer.salesforce.com "Atlas" docs (anonymous JSON content API) -------
def is_dev_docs_url(arg):
    """True for a developer.salesforce.com/docs Atlas URL (its own content API)."""
    if not arg.startswith("http"):
        return False
    p = urllib.parse.urlparse(arg)
    return p.netloc.lower() == "developer.salesforce.com" and p.path.startswith("/docs/")


def _dev_get_json(url):
    """GET `url` and JSON-parse it, with clear errors for the blank-200 (bad
    topic id / version) and non-JSON (proxy/error page) failure modes."""
    r = curl(["-L", url], timeout=30)
    out = r.stdout
    if r.returncode != 0 and not out.strip():
        raise RuntimeError("request failed: " + (r.stderr.strip() or "curl error"))
    if not out.strip():
        raise RuntimeError(f"empty response from {url} (topic id / version wrong?)")
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError("developer.salesforce.com response was not JSON "
                           "(proxy or error page?): " + (out[:200] or str(e))) from e


def _dev_docs_parts(url):
    """From a developer.salesforce.com/docs URL return (meta, topic):

    meta  = the 'atlas.<lang>.<deliverable>.meta' path segment (the deliverable
            manifest); topic = the '<name>.htm' leaf page, or None for the
            deliverable landing page. A leaf may live in the last path segment
            or in the URL fragment (developer.salesforce.com uses both)."""
    p = urllib.parse.urlparse(url)
    segs = [s for s in p.path.split("/") if s]
    meta = next((s for s in segs if s.startswith("atlas.") and s.endswith(".meta")), None)
    topic = None
    if segs and re.search(r"\.html?$", segs[-1]):
        topic = re.sub(r"\.html?$", "", segs[-1])
    elif p.fragment and re.search(r"\.html?$", p.fragment):
        topic = re.sub(r"\.html?$", "", p.fragment)
    return meta, topic


def _dev_md_twin_url(url):
    """Return the plain-Markdown twin URL for a developer.salesforce.com/docs page,
    or None if one can't be formed.

    Salesforce serves a Markdown twin of many docs pages at the same path with a
    '.md' extension (e.g. .../guide/mcp.html -> .../guide/mcp.md). We can only
    build it from a page URL whose last path segment is the leaf document
    ('<name>.htm'/'.html', or already '.md'); deliverable-landing URLs (no leaf,
    e.g. '.../atlas.en-us.uiapi.meta/uiapi') have no reliable twin, so return
    None and let the caller use the Atlas JSON API instead."""
    p = urllib.parse.urlparse(url)
    segs = p.path.split("/")
    if not segs or not segs[-1]:
        return None
    leaf = segs[-1]
    if leaf.endswith(".md"):
        new_leaf = leaf
    elif re.search(r"\.html?$", leaf):
        new_leaf = re.sub(r"\.html?$", ".md", leaf)
    else:
        return None
    segs[-1] = new_leaf
    return urllib.parse.urlunparse(p._replace(path="/".join(segs), fragment=""))


def _fetch_dev_md_twin(url):
    """Try the Markdown twin of a dev-docs page; return its text, or None.

    Availability is signalled by the response Content-Type (`text/markdown`),
    NOT the HTTP status: a page without a twin still returns 200 with the
    `text/html` SPA shell (the '.md' effectively falls back to '.htm'), so we
    must gate on Content-Type. When present the body is already clean Markdown,
    so it is returned as-is (no HTML-to-text pass)."""
    twin = _dev_md_twin_url(url)
    if not twin:
        return None
    r = curl(["-L", "-w", "\n__CT__%{content_type}", twin], timeout=30)
    out = r.stdout
    marker = out.rfind("\n__CT__")
    ctype = out[marker + len("\n__CT__"):].strip().lower() if marker >= 0 else ""
    body = out[:marker] if marker >= 0 else out
    if "text/markdown" in ctype and body.strip():
        print(f"# markdown twin: {twin}", file=sys.stderr)
        return body.strip()
    return None


def fetch_developer_docs(url):
    """Read a developer.salesforce.com/docs page without a browser.

    Two anonymous paths, tried in order:

      1. MARKDOWN TWIN (fast path). Many pages — notably the newer
         '/docs/<cloud>/<product>/guide/<topic>' deliverables — expose a
         plain-Markdown twin at the same path with a '.md' extension. It's a
         single request and returns clean Markdown. Availability is detected via
         the response Content-Type (text/markdown); pages without a twin (e.g.
         the older 'atlas.<lang>.<deliverable>.meta' guides) fall through.
      2. ATLAS JSON CONTENT API (fallback, atlas.*.meta URLs only):
           a. GET /docs/get_document/<meta>  -> manifest (deliverable, locale,
              version.doc_version, and the landing page's own body)
           b. GET /docs/get_document_content/<deliverable>/<topic>.htm/<locale>/<doc_version>
              -> {id, title, content}  (content = body HTML)
         deliverable/locale/doc_version come from the manifest (authoritative)
         rather than the URL, so a version-less URL still resolves the current
         release."""
    assert_reachable("developer.salesforce.com", "*.salesforce.com")
    md = _fetch_dev_md_twin(url)
    if md is not None:
        return md
    meta, topic = _dev_docs_parts(url)
    if not meta:
        raise RuntimeError(
            f"no Markdown twin (.md) is available for {url!r} and it has no "
            "'atlas.<lang>.<deliverable>.meta' segment to use the Atlas JSON API — "
            "pass a developer.salesforce.com/docs/... URL")
    manifest = _dev_get_json(f"{DEV_HOST}/docs/get_document/{meta}")
    if not topic:
        # No leaf page in the URL: the manifest already carries the landing body.
        body = manifest.get("content")
        if not body:
            raise RuntimeError(f"no landing content in the {meta} manifest")
        return html_to_text(body)
    deliverable = manifest.get("deliverable")
    locale = manifest.get("locale")
    doc_version = (manifest.get("version") or {}).get("doc_version")
    if not (deliverable and locale and doc_version):
        raise RuntimeError(f"{meta} manifest missing deliverable/locale/doc_version "
                           "(page shape changed?)")
    doc = _dev_get_json(
        f"{DEV_HOST}/docs/get_document_content/{deliverable}/{topic}.htm/{locale}/{doc_version}")
    body = doc.get("content")
    if not body:
        raise RuntimeError(f"no content for topic {topic!r} in {deliverable} at "
                           f"{doc_version} (check the topic id)")
    return html_to_text(body)


# --- Strategy D: Salesforce release info (Trust status API + release notes) ---
# VERIFIED CONTRACT (probed live; the hosted Swagger UI at
# https://api.status.salesforce.com/v1/docs/ ships the default petstore stub,
# so the routes below were verified empirically):
#   GET /v1/instances/<KEY>/status  -> instance detail incl. releaseVersion
#       ("Summer '26 Patch 13.7"), releaseNumber ("262.13.7"),
#       maintenanceWindow, and embedded Maintenances[] (upcoming events with
#       name/releaseType/plannedStartTime/plannedEndTime). 404
#       {"message":"Instance Not Found"} for a bad key.
#   GET /v1/search/<QUERY>          -> instance lookup (case-insensitive),
#       returns [{key, location, environment, isActive}, ...].
#   GET /v1/maintenances?limit=N    -> upcoming maintenance events across all
#       instances; release events have type "release" and carry instanceKeys.
# All anonymous — no auth, no tokens.
def is_status_url(arg):
    """True for a Salesforce Trust status URL (status.salesforce.com)."""
    if not arg.startswith("http"):
        return False
    return urllib.parse.urlparse(arg).netloc.lower() in (
        "status.salesforce.com", "api.status.salesforce.com")


def status_instance_from(arg):
    """Instance key from a status.salesforce.com URL ('/instances/NA209/...'),
    or None for status pages that aren't about one instance."""
    segs = [s for s in urllib.parse.urlparse(arg).path.split("/") if s]
    for i, s in enumerate(segs):
        if s.lower() == "instances" and i + 1 < len(segs):
            return segs[i + 1]
    return None


def _status_get_json(path):
    """GET a Trust status API route and JSON-parse it; returns (json, http_code)."""
    r = curl(["-L", "-w", "\n__HTTP__%{http_code}", f"{STATUS_HOST}{path}"], timeout=30)
    out = r.stdout
    marker = out.rfind("\n__HTTP__")
    code = out[marker + len("\n__HTTP__"):].strip() if marker >= 0 else ""
    body = out[:marker] if marker >= 0 else out
    if r.returncode != 0 and not body.strip():
        raise RuntimeError("status API request failed: " + (r.stderr.strip() or "curl error"))
    try:
        return json.loads(body), code
    except json.JSONDecodeError as e:
        raise RuntimeError("status API response was not JSON (proxy or error page?): "
                           + (body[:200] or str(e))) from e


def _release_maintenance_lines(maints):
    """Upcoming release-maintenance events as text lines, deduped by name.

    Several events share one name (per instance group / product); collapse them
    to 'name: earliest .. latest planned start'."""
    windows = {}
    for m in maints:
        if m.get("type") != "release" or not m.get("plannedStartTime"):
            continue
        windows.setdefault(m.get("name") or "?", []).append(m["plannedStartTime"])
    lines = []
    for name, starts in sorted(windows.items(), key=lambda kv: min(kv[1])):
        lo, hi = min(starts)[:10], max(starts)[:10]
        when = lo if lo == hi else f"{lo} .. {hi}"
        lines.append(f"- {name}: {when} ({len(starts)} scheduled event"
                     f"{'s' if len(starts) != 1 else ''})")
    return lines


def _release_name_of(ctx, release):
    """Seasonal name ("Summer '26") for a release number, read from that
    release's own release-notes landing title; None if not resolvable."""
    try:
        rec = _getdata(ctx, RN_LANDING_TOPIC, release).get("record") or {}
        m = re.search(r"(Spring|Summer|Winter)\s*[’']\s*(\d{2})",
                      rec.get("Content__c") or "")
        return f"{m.group(1)} '{m.group(2)}" if m else None
    except RuntimeError:
        return None


def _current_api_anchor():
    """(api_version, release_major, release_name) for the CURRENT release —
    e.g. (67, 262, "Summer '26") — or None if not resolvable.

    Read live from the Atlas REST-API doc manifest, whose `version` block ties
    all three together in one anonymous call: version_text "Summer '26 (API
    version 67.0)", release_version "67.0", doc_version "262.0". Cross-checked
    against the REST Versions resource (GET /services/data/ on an instance,
    which lists label + version pairs and shows one API version per seasonal
    release while release majors step by 2)."""
    try:
        v = _dev_get_json(f"{DEV_HOST}/docs/get_document/atlas.en-us.api_rest.meta").get("version") or {}
        api = int(float(v["release_version"]))
        rel = int(float(v["doc_version"]))
        m = re.search(r"(Spring|Summer|Winter)\s*[’']\s*(\d{2})", v.get("version_text") or "")
        return api, rel, (f"{m.group(1)} '{m.group(2)}" if m else None)
    except Exception:
        return None


def _api_version_for(release_major, anchor):
    """API version ("v67.0") for a release major (262), derived from the live
    anchor: each seasonal release adds 2 to the release major and 1 to the API
    version (verified against the /services/data version labels)."""
    api, rel, _ = anchor
    return f"v{api + (release_major - rel) // 2}.0"


def _prev_release_name(name):
    """The seasonal release before `name` ("Winter '27" -> "Summer '26").
    Cadence, verified against the /services/data labels: within a release year
    Spring 'YY -> Summer 'YY -> Winter 'YY+1."""
    season, yy = name.rsplit(" '", 1)
    yy = int(yy)
    if season == "Winter":
        return f"Summer '{yy - 1}"
    if season == "Summer":
        return f"Spring '{yy}"
    return f"Winter '{yy}"


def _instance_release_info(instance):
    """Release info for one instance: running release + upcoming release windows."""
    # Instance keys are letters/digits/dashes/underscores (NA209, AP52,
    # RUNTIMEPLANE-EU). Validate before building the request path so bad input
    # (slashes, query chars) gets a clear error instead of a mangled URL.
    if not re.fullmatch(r"[A-Za-z0-9_-]+", instance):
        raise RuntimeError(f"invalid instance {instance!r} — expected an instance key like "
                           "NA209 or AP52 (letters, digits, dashes)")
    d, code = _status_get_json(f"/v1/instances/{instance.upper()}/status")
    if code == "404" or "key" not in d:
        # Not a key — try the case-insensitive search (e.g. 'ap52', partial keys).
        results, _ = _status_get_json(f"/v1/search/{urllib.parse.quote(instance)}")
        keys = [r.get("key") for r in results if isinstance(r, dict) and r.get("key")]
        if len(keys) == 1:
            d, code = _status_get_json(f"/v1/instances/{keys[0]}/status")
        elif keys:
            raise RuntimeError(f"instance {instance!r} is ambiguous on Trust: {', '.join(keys[:10])} "
                               "— pass one exact instance key")
        else:
            raise RuntimeError(
                f"no instance {instance!r} on Trust (https://status.salesforce.com). Pass the "
                "instance key shown on your org's Company Information page (e.g. NA209, AP52).")
    if code == "404" or "key" not in d:
        raise RuntimeError(f"Trust returned no data for instance {instance!r}")
    api_note = ""
    m = re.match(r"(\d+)", d.get("releaseNumber") or "")
    anchor = _current_api_anchor() if m else None
    if anchor and m:
        api_note = f", API {_api_version_for(int(m.group(1)), anchor)}"
    lines = [f"Instance: {d.get('key')} ({d.get('location')}, {d.get('environment')})",
             f"Status: {d.get('status')}" + ("" if d.get("isActive") else " — NOT active (decommissioned or migrated)"),
             f"Running release: {d.get('releaseVersion') or 'unknown'} "
             f"(releaseNumber {d.get('releaseNumber') or '?'}{api_note})",
             f"Maintenance window: {d.get('maintenanceWindow') or 'unknown'}"]
    rel_lines = _release_maintenance_lines(d.get("Maintenances") or [])
    if rel_lines:
        lines += ["", "Upcoming release maintenance windows:"] + rel_lines
    else:
        lines += ["", "No upcoming release maintenance events published for this instance."]
    return "\n".join(lines)


def _release_summary():
    """Org-independent release overview: current + preview release (from the
    release-notes landing pages) and upcoming release windows (from Trust)."""
    lines = []
    anchor = _current_api_anchor()  # (api, release_major, name) or None

    def _api(major):
        return f", API {_api_version_for(major, anchor)}" if anchor else ""

    try:
        ctx = scrape_aura_context(RN_LANDING_TOPIC.replace(".htm", ""))
        ctx.update({"dn": [], "globals": {}, "uad": True})
        current = os.environ.get("HELP_RELEASE") \
            or _getdata(ctx, RN_LANDING_TOPIC, "").get("latestRNVersion")
        if not current:
            raise RuntimeError("latestRNVersion missing")
        cur_major = int(current.split(".")[0])
        name = _release_name_of(ctx, current)
        lines.append(f"Current release: {name or 'unknown name'} ({current}{_api(cur_major)})")
        preview = f"{cur_major + 2}.0.0"
        preview_name = _release_name_of(ctx, preview)
        if preview_name:
            lines.append(f"Preview release: {preview_name} ({preview}{_api(cur_major + 2)}) "
                         "— release notes already published")
        if anchor and name:
            # Recent release <-> API version mapping: current + the 3 before it
            # (and the preview ahead), all derived from the live anchor.
            pairs = [f"{name} = {_api_version_for(cur_major, anchor)} (current)"]
            nm, mj = name, cur_major
            for _ in range(3):
                nm, mj = _prev_release_name(nm), mj - 2
                pairs.append(f"{nm} = {_api_version_for(mj, anchor)}")
            if preview_name:
                pairs.insert(0, f"{preview_name} = {_api_version_for(cur_major + 2, anchor)} (preview)")
            lines.append("Release/API versions: " + ", ".join(pairs))
        lines.append(
            "Release notes are served for roughly the previous, current, and preview releases; "
            f"older ones are linked from the archive index topic {RN_ARCHIVE_TOPIC}.")
    except RuntimeError as e:
        lines.append(f"Current release: unavailable ({e})")
    try:
        maints, _ = _status_get_json("/v1/maintenances?limit=500")
        rel_lines = _release_maintenance_lines(maints if isinstance(maints, list) else [])
        if rel_lines:
            lines += ["", "Upcoming release maintenance windows (all instances, from Trust):"] + rel_lines
    except RuntimeError as e:
        lines += ["", f"Upcoming maintenance windows: unavailable ({e})"]
    lines += ["", "For one instance's dates and running release: "
                  "python3 fetch_sf_help.py release-info YOUR_INSTANCE (e.g. NA209)."]
    return "\n".join(lines)


def fetch_release_info(instance=None):
    """Answer 'what release…' questions from the anonymous Trust status API
    (plus the release-notes landing pages for the org-independent summary)."""
    assert_reachable("api.status.salesforce.com", "*.salesforce.com")
    if instance:
        return _instance_release_info(instance)
    return _release_summary()


def main():
    ap = argparse.ArgumentParser(
        description="Print the readable text of a Salesforce documentation page — "
                    "help.salesforce.com Help articles or developer.salesforce.com/docs "
                    "pages — or Salesforce release info. Give it the page URL (or a "
                    "bare Help topic id); the host selects the retrieval path "
                    "automatically. The literal target 'release-info' prints current/"
                    "preview release and upcoming release windows instead.")
    ap.add_argument("target", help="a Salesforce Help / developer-docs / Trust status URL, "
                                   "a bare Help topic id, or the literal 'release-info'")
    ap.add_argument("instance", nargs="?",
                    help="with 'release-info' only: a Salesforce instance key (e.g. NA209)")
    a = ap.parse_args()

    # Release info: the literal 'release-info' target, or a Trust status URL.
    # The optional second argument is only meaningful with the literal target —
    # a status URL already names its instance, so an extra argument there is a
    # mistake to surface, not to silently ignore.
    if a.instance and a.target.lower() != "release-info":
        print("ERROR: a second argument is only valid with the 'release-info' target",
              file=sys.stderr)
        return 2
    if a.target.lower() == "release-info" or is_status_url(a.target):
        instance = a.instance if a.target.lower() == "release-info" \
            else status_instance_from(a.target)
        print(f"# release info{': ' + instance if instance else ''}", file=sys.stderr)
        try:
            print(fetch_release_info(instance))
            return 0
        except Exception as e:
            print(f"ERROR: could not retrieve release info. {e}", file=sys.stderr)
            return 1

    # developer.salesforce.com/docs has its own anonymous Atlas content API —
    # route it there directly rather than through the Help Aura path.
    if is_dev_docs_url(a.target):
        print("# developer.salesforce.com docs", file=sys.stderr)
        try:
            print(fetch_developer_docs(a.target))
            return 0
        except Exception as e:
            print(f"ERROR: could not retrieve the doc. {e}", file=sys.stderr)
            return 1

    try:
        hint = unsupported_url_message(a.target)
        if hint:
            print(f"ERROR: {hint}", file=sys.stderr)
            return 2
        topic = topic_id_from(a.target)
        release = release_from(a.target)  # explicit release=NNN (release-notes URLs)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"# topic: {topic}" + (f" (release {release})" if release else ""), file=sys.stderr)

    # Retrieval is fully automatic: Aura is the anonymous path that works out of
    # the box; Zoomin is tried only as a fallback when service creds are present.
    strategies = [("aura", lambda t: fetch_aura(t, release))]
    if os.environ.get("ZOOMIN_BASIC"):
        strategies.append(("zoomin", fetch_zoomin))
    last = None
    for name, fn in strategies:
        try:
            print(fn(topic))
            return 0
        except Exception as e:
            last = e
            print(f"# {name} failed: {e}", file=sys.stderr)
    print(f"ERROR: could not retrieve the article. {last}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
