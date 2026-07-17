#!/usr/bin/env python3
"""
Fetch readable Salesforce Help article content as HTML — without a browser.

Salesforce Help (help.salesforce.com/s/articleView?id=<topic>.htm&type=5) is a
client-rendered Aura/LWC SPA. curl/WebFetch only get the "Loading…" shell. The
actual article body is DITA-generated XHTML that comes from Zoomin
(zoominsoftware.io) and is cached/re-served by Salesforce.

Two strategies (default `auto` tries B first, then A):

  B. AURA ENDPOINT  (primary; anonymous; only needs help.salesforce.com reachable)
       POST https://help.salesforce.com/s/sfsites/aura   (ApexActionController)
       classname=Help_ArticleDataController  method=getData
     The article body lands in returnValue.returnValue.record.Content__c.
     Both volatile inputs are resolved automatically each run: the aura.context
     (fwuid / app / loaded) is scraped live from the article page, and the SF
     `release` is self-discovered (a call with release="" returns
     returnValue.latestRNVersion, reused for the real fetch). No DevTools capture.

  A. ZOOMIN DIRECT  (optional; requires *.zoominsoftware.io allowlisted AND creds)
       GET https://zd-ht-prod.zoominsoftware.io/v1/topics/<topicId>/content
     This is the upstream source Salesforce caches (record.URL__c), but the host
     is a credentialed service adaptor: it needs HTTP Basic auth PLUS an unnamed
     required header (server-side H&T creds), so it only runs when ZOOMIN_BASIC /
     ZOOMIN_HEADER are supplied. Not anonymously accessible.

All network calls shell out to `curl` so the session's HTTPS_PROXY + CA bundle
are honored automatically (Node's built-in fetch and headless Chromium do not
traverse this proxy reliably).

Usage:
    python3 fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_authenticate.htm&type=5"
    python3 fetch_sf_help.py xcloud.remoteaccess_authenticate           # bare topic id
    python3 fetch_sf_help.py <url> --strategy zoomin|aura|auto          # default auto
    python3 fetch_sf_help.py <url> --raw                                # print raw HTML, no text extraction
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse

ZOOMIN_HOST = "https://zd-ht-prod.zoominsoftware.io"
HELP_HOST   = "https://help.salesforce.com"
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


def topic_id_from(arg):
    """Accept a full articleView URL or a bare topic id; return e.g. xcloud.remoteaccess_authenticate."""
    if arg.startswith("http"):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(arg).query)
        raw = (q.get("id") or [""])[0]
    else:
        raw = arg
    return re.sub(r"\.htm$", "", raw.strip())


def html_to_text(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"&#?\w+;", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


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
def fetch_zoomin(topic_id, raw=False):
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
            html = j.get("body") or j.get("html") or j.get("content") or json.dumps(j, indent=2)[:4000]
            return html if raw else html_to_text(html)
        except json.JSONDecodeError:
            pass
    return body if raw else html_to_text(body)


# --- Strategy B: Aura endpoint on help.salesforce.com -------------------------
def scrape_aura_context(topic_id):
    """Fetch the live article page and pull the current aura.context blob.

    The page embeds the context as a URL-encoded JSON object inside a
    `/s/sfsites/l/%7B...%7D...` script src. We locate it, URL-decode, and
    JSON-parse the leading object rather than regex-matching encoded fields
    (the values contain encoded ':' and '/' which defeat naive regexes)."""
    page_url = f"{HELP_HOST}/s/articleView?id={topic_id}.htm&type=5"
    html = curl(["-L", page_url], timeout=30).stdout
    # The page has several `%7B%22mode%22...%7D` (i.e. {"mode"...}) context blobs;
    # only the app-bootstrap one carries fwuid. Try each until one parses with fwuid.
    obj = None
    for mm in re.finditer(r"%7B%22mode%22", html):
        decoded = urllib.parse.unquote(html[mm.start():mm.start() + 4000])
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


def _getdata(ctx, url_name, release, type_number="5"):
    """One Help_ArticleDataController.getData call; returns the inner returnValue."""
    action = {
        "id": "1;a", "descriptor": "aura://ApexActionController/ACTION$execute",
        "callingDescriptor": "UNKNOWN",
        "params": {"namespace": "", "classname": HELP_APEX_CLASS, "method": HELP_APEX_METHOD,
                   "params": {"articleParameters": {
                       "urlName": url_name, "language": LANG, "release": release,
                       "requestedArticleType": "HelpDocs",
                       "requestedArticleTypeNumber": type_number}},
                   "cacheable": False, "isContinuation": False}}
    data = urllib.parse.urlencode({"message": json.dumps({"actions": [action]}),
                                   "aura.context": json.dumps(ctx), "aura.token": "null"})
    out = curl(["-X", "POST", f"{HELP_HOST}/s/sfsites/aura?r=1&aura.ApexAction.execute=1",
                "-H", "content-type: application/x-www-form-urlencoded; charset=UTF-8",
                "-H", f"x-sfdc-lds-endpoints: ApexActionController.execute:{HELP_APEX_CLASS}.{HELP_APEX_METHOD}",
                "--data-raw", data], timeout=30).stdout
    if "/*ERROR*/" in out:
        m = re.search(r"\{.*\}", out, re.S)
        raise RuntimeError("aura error: " + (m.group(0)[:300] if m else out[:300]))
    act = json.loads(out)["actions"][0]
    if act.get("state") != "SUCCESS":
        raise RuntimeError("aura non-success: " + json.dumps(act.get("error", act))[:300])
    return act["returnValue"]["returnValue"]


def fetch_aura(topic_id, raw=False):
    assert_reachable("help.salesforce.com", "*.salesforce.com")
    ctx = scrape_aura_context(topic_id)              # live fwuid/app/loaded
    ctx.update({"dn": [], "globals": {}, "uad": True})
    url_name = topic_id if topic_id.endswith(".htm") else topic_id + ".htm"
    # 1) discover the current SF release (wrong/empty release => empty content)
    release = os.environ.get("HELP_RELEASE") \
        or _getdata(ctx, url_name, "").get("latestRNVersion")
    if not release:
        raise RuntimeError("could not determine current SF release (latestRNVersion missing)")
    # 2) real fetch
    rv = _getdata(ctx, url_name, release)
    rec = rv.get("record")
    if not rec or not rec.get("Content__c"):
        raise RuntimeError(f"no content for {url_name} at release {release} "
                           f"(check the topic id / language)")
    html = rec["Content__c"]
    return html if raw else html_to_text(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="articleView URL or bare topic id")
    ap.add_argument("--strategy", choices=["auto", "zoomin", "aura"], default="auto")
    ap.add_argument("--raw", action="store_true", help="print raw HTML instead of extracted text")
    a = ap.parse_args()
    topic = topic_id_from(a.target)
    print(f"# topic: {topic}", file=sys.stderr)

    # Aura works anonymously (public path); Zoomin needs service creds, so it is
    # only useful when ZOOMIN_BASIC/ZOOMIN_HEADER are supplied.
    order = {"auto": ["aura", "zoomin"], "zoomin": ["zoomin"], "aura": ["aura"]}[a.strategy]
    last = None
    for strat in order:
        try:
            fn = fetch_zoomin if strat == "zoomin" else fetch_aura
            print(f"# trying strategy: {strat}", file=sys.stderr)
            print(fn(topic, raw=a.raw))
            print(f"# OK via {strat}", file=sys.stderr)
            return 0
        except Exception as e:
            last = e
            print(f"# {strat} failed: {e}", file=sys.stderr)
    print(f"ERROR: all strategies failed. last: {last}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
