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

  C. DEVELOPER DOCS  (developer.salesforce.com; anonymous JSON content API)
       GET /docs/get_document/atlas.<lang>.<deliverable>.meta       -> manifest
       GET /docs/get_document_content/<deliverable>/<topic>.htm/<locale>/<doc_version>
     The deliverable/locale/doc_version are read from the manifest (step 1), so
     a version-less URL still resolves the current release.

All network calls shell out to `curl` so the session's HTTPS_PROXY + CA bundle
are honored automatically (Node's built-in fetch and headless Chromium do not
traverse this proxy reliably).

Retrieval is fully automatic — the caller only supplies the URL (or a Help topic
id). The host picks the path; for Help, Aura is the anonymous path that works out
of the box and the credentialed Zoomin fallback is used only if ZOOMIN_BASIC is
set in the environment.

Usage:
    python3 fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_authenticate.htm&type=5"
    python3 fetch_sf_help.py xcloud.remoteaccess_authenticate           # bare topic id
    python3 fetch_sf_help.py "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_features_list_views.htm"
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
LANG        = "en_US"

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


def _fetch_helpdocs(ctx, topic_id):
    url_name = topic_id if topic_id.endswith(".htm") else topic_id + ".htm"
    # 1) discover the current SF release (wrong/empty release => empty content)
    release = os.environ.get("HELP_RELEASE") \
        or _getdata(ctx, url_name, "").get("latestRNVersion")
    if not release:
        raise RuntimeError("could not determine current SF release (latestRNVersion missing)")
    # 2) real fetch
    rec = _getdata(ctx, url_name, release).get("record")
    if not rec or not rec.get("Content__c"):
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


def fetch_aura(topic_id):
    assert_reachable("help.salesforce.com", "*.salesforce.com")
    ctx = scrape_aura_context(topic_id)              # live fwuid/app/loaded (global)
    ctx.update({"dn": [], "globals": {}, "uad": True})
    # A purely numeric id is a type=1 Knowledge Article; otherwise a HelpDocs topic.
    if topic_id.isdigit():
        return _fetch_knowledge(ctx, topic_id)
    return _fetch_helpdocs(ctx, topic_id)


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


def fetch_developer_docs(url):
    """Read a developer.salesforce.com Atlas doc via its anonymous content API.

    developer.salesforce.com/docs is also a JS SPA, but exposes an anonymous
    JSON content API:
      1. GET /docs/get_document/<meta>  -> manifest (deliverable, locale,
         version.doc_version, and the landing page's own body)
      2. GET /docs/get_document_content/<deliverable>/<topic>.htm/<locale>/<doc_version>
         -> {id, title, content}  (content = body HTML)
    deliverable/locale/doc_version come from the manifest (authoritative) rather
    than the URL, so a version-less URL still resolves the current release."""
    assert_reachable("developer.salesforce.com", "*.salesforce.com")
    meta, topic = _dev_docs_parts(url)
    if not meta:
        raise RuntimeError(
            "could not find an 'atlas.<lang>.<deliverable>.meta' segment in "
            f"{url!r} — pass a developer.salesforce.com/docs/... URL")
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


def main():
    ap = argparse.ArgumentParser(
        description="Print the readable body of a Salesforce Help article. "
                    "Give it an articleView URL or a bare topic id — nothing else needed.")
    ap.add_argument("target", help="a Salesforce Help / developer-docs URL or a bare Help topic id")
    a = ap.parse_args()

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
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"# topic: {topic}", file=sys.stderr)

    # Retrieval is fully automatic: Aura is the anonymous path that works out of
    # the box; Zoomin is tried only as a fallback when service creds are present.
    strategies = [("aura", fetch_aura)]
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
