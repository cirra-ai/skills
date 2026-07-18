"""Tests for the sf-help-fetch fetcher.

All network access goes through the module-level ``curl`` helper, so tests
monkeypatch it (or the higher-level ``_getdata`` / ``scrape_aura_context``) and
never touch the network.

Covers:
  - topic_id_from: URL / bare id parsing, .htm stripping, fail-fast on empty
  - html_to_text: tag stripping, entity decoding, script/style removal
  - assert_reachable: reachable vs proxy-blocked (http_code 000)
  - scrape_aura_context: picking the fwuid-bearing context blob
  - _getdata: success parse + clear errors on curl failure / non-JSON / markers
  - fetch_aura: release self-discovery then content fetch
"""

import urllib.parse
from types import SimpleNamespace

import pytest
from conftest import load_script

mod = load_script("skills/sf-help-fetch/scripts/fetch_sf_help.py")


def _proc(stdout="", stderr="", returncode=0):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


class TestTopicIdFrom:
    def test_full_url(self):
        url = (
            "https://help.salesforce.com/s/articleView"
            "?id=xcloud.remoteaccess_authenticate.htm&type=5"
        )
        assert mod.topic_id_from(url) == "xcloud.remoteaccess_authenticate"

    def test_bare_id_with_htm(self):
        assert mod.topic_id_from("xcloud.foo.htm") == "xcloud.foo"

    def test_bare_id(self):
        assert mod.topic_id_from("xcloud.foo") == "xcloud.foo"

    def test_url_without_id_raises(self):
        with pytest.raises(ValueError):
            mod.topic_id_from("https://help.salesforce.com/s/articleView?type=5")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            mod.topic_id_from("")


class TestHtmlToText:
    def test_strips_tags_and_collapses_whitespace(self):
        assert mod.html_to_text("<h1>Hi</h1>  <p>there</p>") == "Hi there"

    def test_decodes_entities(self):
        assert mod.html_to_text("<p>a &amp; b &#39;c&#39; &lt;x&gt;</p>") == "a & b 'c' <x>"

    def test_drops_script_and_style(self):
        markup = "<style>x{}</style><script>bad()</script><p>ok</p>"
        assert mod.html_to_text(markup) == "ok"


class TestAssertReachable:
    def test_reachable(self, monkeypatch):
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout="200"))
        mod.assert_reachable("help.salesforce.com", "*.salesforce.com")  # no raise

    def test_blocked_prompts_allowlist(self, monkeypatch):
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout="000", returncode=56))
        with pytest.raises(RuntimeError, match="allowlist"):
            mod.assert_reachable("help.salesforce.com", "*.salesforce.com")


class TestScrapeAuraContext:
    def test_picks_fwuid_bearing_blob(self, monkeypatch):
        noise = '{"mode":"PROD","parts":"f"}'  # first {"mode"...} but no fwuid
        real = (
            '{"mode":"PROD","fwuid":"FW123","app":"siteforce:communityApp",'
            '"loaded":{"APPLICATION@markup://siteforce:communityApp":"L1"}}'
        )
        page = (
            f'x <script src="/s/sfsites/l/{urllib.parse.quote(noise)}a.js"></script>'
            f'<script src="/s/sfsites/l/{urllib.parse.quote(real)}b.js"></script>'
        )
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout=page))
        ctx = mod.scrape_aura_context("xcloud.foo")
        assert ctx["fwuid"] == "FW123"
        assert ctx["app"] == "siteforce:communityApp"
        assert ctx["loaded"] == {"APPLICATION@markup://siteforce:communityApp": "L1"}

    def test_missing_context_raises(self, monkeypatch):
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout="<html>no context</html>"))
        with pytest.raises(RuntimeError, match="aura.context"):
            mod.scrape_aura_context("xcloud.foo")


class TestGetData:
    def test_success(self, monkeypatch):
        resp = (
            '{"actions":[{"state":"SUCCESS","returnValue":{"returnValue":'
            '{"record":{"Content__c":"<p>hi</p>"}}}}]}'
        )
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout=resp))
        rv = mod._getdata({"fwuid": "x"}, "xcloud.foo.htm", "262.0.0")
        assert rv["record"]["Content__c"] == "<p>hi</p>"

    def test_curl_failure_raises_clear_error(self, monkeypatch):
        monkeypatch.setattr(
            mod, "curl",
            lambda *a, **k: _proc(stderr="curl: (56) CONNECT tunnel failed", returncode=56),
        )
        with pytest.raises(RuntimeError, match="request failed"):
            mod._getdata({}, "x.htm", "1")

    def test_non_json_raises_clear_error(self, monkeypatch):
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout="<html>error</html>"))
        with pytest.raises(RuntimeError, match="not JSON"):
            mod._getdata({}, "x.htm", "1")

    def test_aura_error_marker(self, monkeypatch):
        marker = '/*ERROR*/{"message":"No apex action available"}/*ERROR*/'
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout=marker))
        with pytest.raises(RuntimeError, match="aura error"):
            mod._getdata({}, "x.htm", "1")


class TestFetchAura:
    def test_discovers_release_then_fetches(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(
            mod, "scrape_aura_context", lambda t: {"fwuid": "x", "app": "a", "loaded": {}}
        )
        releases = []

        def fake_getdata(ctx, url_name, release, type_number="5"):
            releases.append(release)
            if release == "":  # release-discovery call
                return {"latestRNVersion": "262.0.0"}
            return {"record": {"Content__c": "<h1>Title</h1><p>Body &amp; more</p>"}}

        monkeypatch.setattr(mod, "_getdata", fake_getdata)
        monkeypatch.delenv("HELP_RELEASE", raising=False)
        out = mod.fetch_aura("xcloud.foo")
        assert out == "Title Body & more"
        assert releases == ["", "262.0.0"]


class TestUnsupportedUrlMessage:
    def test_help_url_is_supported(self):
        url = "https://help.salesforce.com/s/articleView?id=xcloud.foo.htm&type=5"
        assert mod.unsupported_url_message(url) is None

    def test_bare_topic_id_is_supported(self):
        assert mod.unsupported_url_message("xcloud.foo") is None

    def test_trailhead_community_names_graphql(self):
        msg = mod.unsupported_url_message(
            "https://trailhead.salesforce.com/trailblazer-community/feed/0D54S00000A8hLaSAJ"
        )
        assert msg and "community/graphql" in msg and "FeedItemDetail" in msg

    def test_trailhead_module_explains_limits(self):
        msg = mod.unsupported_url_message(
            "https://trailhead.salesforce.com/content/learn/modules/x/y"
        )
        assert msg and "Trailhead" in msg and "graphql" in msg

    def test_developer_docs_names_atlas_api(self):
        msg = mod.unsupported_url_message(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/x.htm"
        )
        assert msg and "get_document_content" in msg

    def test_other_host_generic(self):
        msg = mod.unsupported_url_message("https://example.com/docs/foo")
        assert msg and "only reads" in msg

    def test_type1_knowledge_article_url(self):
        msg = mod.unsupported_url_message(
            "https://help.salesforce.com/s/articleView?id=005360285&type=1"
        )
        assert msg and "Knowledge Article" in msg and "type=1" in msg

    def test_numeric_bare_id_is_knowledge_article(self):
        msg = mod.unsupported_url_message("005360285")
        assert msg and "Knowledge Article" in msg

    def test_help_docs_topic_url_still_supported(self):
        url = "https://help.salesforce.com/s/articleView?id=xcloud.foo.htm&type=5"
        assert mod.unsupported_url_message(url) is None
