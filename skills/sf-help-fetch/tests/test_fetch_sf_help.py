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
  - release_from: explicit release=NNN parsing/normalizing from Help URLs
  - fetch_aura with an explicit release: skips discovery; archived -> clear error
  - release info: Trust status URL routing, instance lookup, summary assembly
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

    def test_developer_docs_url_is_supported(self):
        # developer.salesforce.com/docs is handled via the Atlas content API.
        msg = mod.unsupported_url_message(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/x.htm"
        )
        assert msg is None

    def test_other_host_generic(self):
        msg = mod.unsupported_url_message("https://example.com/docs/foo")
        assert msg and "isn't handled" in msg

    def test_type1_knowledge_article_url_is_supported(self):
        # type=1 numeric Knowledge Articles are handled (KBKnowledgeArticle path).
        url = "https://help.salesforce.com/s/articleView?id=005360285&type=1"
        assert mod.unsupported_url_message(url) is None

    def test_numeric_bare_id_is_supported(self):
        assert mod.unsupported_url_message("005360285") is None

    def test_help_docs_topic_url_still_supported(self):
        url = "https://help.salesforce.com/s/articleView?id=xcloud.foo.htm&type=5"
        assert mod.unsupported_url_message(url) is None


class TestKnowledgeArticle:
    def test_knowledge_text_joins_rich_fields_in_order(self):
        rec = {
            "title": "T", "summary": "<p>sum &amp; more</p>", "description": "<p>desc</p>",
            "prerequisites": "", "steps": None, "task": "<p>do it</p>",
            "resolution": "<p>fix</p>", "additionalResources": "<p>links</p>",
        }
        assert mod._knowledge_text(rec) == "T\n\nsum & more\n\ndesc\n\ndo it\n\nfix\n\nlinks"

    def test_knowledge_text_skips_empty_fields(self):
        assert mod._knowledge_text({"title": "Only", "description": "  "}) == "Only"

    def test_fetch_aura_routes_numeric_id_to_knowledge(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "scrape_aura_context", lambda t: {"fwuid": "x"})
        seen = {}

        def fake_getdata(ctx, url_name, release, type_number="5", requested_type="HelpDocs"):
            seen.update(url_name=url_name, type_number=type_number, requested_type=requested_type)
            return {"record": {"title": "KB", "description": "<p>body</p>"}}

        monkeypatch.setattr(mod, "_getdata", fake_getdata)
        out = mod.fetch_aura("005360285")
        assert out == "KB\n\nbody"
        assert seen == {"url_name": "005360285", "type_number": "1",
                        "requested_type": "KBKnowledgeArticle"}

    def test_fetch_aura_routes_topic_to_helpdocs(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "scrape_aura_context", lambda t: {"fwuid": "x"})
        types = []

        def fake_getdata(ctx, url_name, release, type_number="5", requested_type="HelpDocs"):
            types.append(requested_type)
            if release == "":
                return {"latestRNVersion": "262.0.0"}
            return {"record": {"Content__c": "<p>hi</p>"}}

        monkeypatch.setattr(mod, "_getdata", fake_getdata)
        monkeypatch.delenv("HELP_RELEASE", raising=False)
        assert mod.fetch_aura("xcloud.foo") == "hi"
        assert types == ["HelpDocs", "HelpDocs"]


class TestReleaseFrom:
    def test_numeric_release_normalized(self):
        url = "https://help.salesforce.com/s/articleView?id=release-notes.rn_x.htm&release=256&type=5"
        assert mod.release_from(url) == "256.0.0"

    def test_full_release_kept(self):
        url = "https://help.salesforce.com/s/articleView?id=x.htm&release=262.1.5&type=5"
        assert mod.release_from(url) == "262.1.5"

    def test_url_without_release_is_none(self):
        assert mod.release_from(
            "https://help.salesforce.com/s/articleView?id=x.htm&type=5") is None

    def test_bare_topic_id_is_none(self):
        assert mod.release_from("xcloud.foo") is None

    def test_garbage_release_raises(self):
        with pytest.raises(ValueError, match="unrecognized release"):
            mod.release_from("https://help.salesforce.com/s/articleView?id=x.htm&release=abc")


class TestExplicitRelease:
    def _patch(self, monkeypatch, getdata):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "scrape_aura_context", lambda t: {"fwuid": "x"})
        monkeypatch.setattr(mod, "_getdata", getdata)
        monkeypatch.delenv("HELP_RELEASE", raising=False)

    def test_explicit_release_skips_discovery(self, monkeypatch):
        releases = []

        def fake_getdata(ctx, url_name, release, type_number="5", requested_type="HelpDocs"):
            releases.append(release)
            return {"record": {"Content__c": "<p>notes</p>"}}

        self._patch(monkeypatch, fake_getdata)
        assert mod.fetch_aura("release-notes.rn_x", "260.0.0") == "notes"
        assert releases == ["260.0.0"]  # no release="" discovery call

    def test_archived_release_names_the_archive(self, monkeypatch):
        def fake_getdata(ctx, url_name, release, type_number="5", requested_type="HelpDocs"):
            return {"type": "NotFound", "latestRNVersion": "262.0.0"}

        self._patch(monkeypatch, fake_getdata)
        with pytest.raises(RuntimeError) as e:
            mod.fetch_aura("release-notes.rn_x", "256.0.0")
        msg = str(e.value)
        assert "256.0.0" in msg and "262.0.0" in msg
        assert mod.RN_ARCHIVE_TOPIC in msg

    def test_missing_topic_without_explicit_release_keeps_generic_error(self, monkeypatch):
        def fake_getdata(ctx, url_name, release, type_number="5", requested_type="HelpDocs"):
            if release == "":
                return {"latestRNVersion": "262.0.0"}
            return {"type": "NotFound"}

        self._patch(monkeypatch, fake_getdata)
        with pytest.raises(RuntimeError, match="check the topic id"):
            mod.fetch_aura("xcloud.nope")


class TestStatusUrlRouting:
    def test_is_status_url(self):
        assert mod.is_status_url("https://status.salesforce.com/instances/AP52")
        assert mod.is_status_url("https://api.status.salesforce.com/v1/instances/AP52/status")
        assert not mod.is_status_url("https://help.salesforce.com/s/articleView?id=x.htm")
        assert not mod.is_status_url("release-info")

    def test_instance_from_url(self):
        assert mod.status_instance_from(
            "https://status.salesforce.com/instances/AP52") == "AP52"
        assert mod.status_instance_from(
            "https://status.salesforce.com/instances/NA209/maintenances") == "NA209"

    def test_no_instance_in_url(self):
        assert mod.status_instance_from("https://status.salesforce.com/products/all") is None

    def test_status_url_is_supported(self):
        assert mod.unsupported_url_message("https://status.salesforce.com/instances/AP52") is None

    def test_second_arg_with_status_url_rejected(self, monkeypatch, capsys):
        # A status URL already names its instance — a stray second argument is
        # an error (exit 2), not silently ignored. Rejected before any network I/O.
        import sys as _sys
        monkeypatch.setattr(_sys, "argv", [
            "fetch_sf_help.py", "https://status.salesforce.com/instances/AP52", "NA1"])
        assert mod.main() == 2
        assert "only valid with the 'release-info' target" in capsys.readouterr().err

    def test_second_arg_with_plain_topic_rejected(self, monkeypatch, capsys):
        import sys as _sys
        monkeypatch.setattr(_sys, "argv", ["fetch_sf_help.py", "xcloud.foo", "NA1"])
        assert mod.main() == 2
        assert "only valid with the 'release-info' target" in capsys.readouterr().err


class TestReleaseInfo:
    def test_instance_info_by_exact_key(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)

        def fake_status(path):
            assert path == "/v1/instances/AP52/status"
            return {"key": "AP52", "location": "APAC", "environment": "production",
                    "status": "OK", "isActive": True,
                    "releaseVersion": "Summer '26 Patch 13.7", "releaseNumber": "262.13.7",
                    "maintenanceWindow": "Saturdays 15:00 - 19:00 UTC",
                    "Maintenances": [
                        {"type": "release", "name": "Winter '27 Major Release",
                         "plannedStartTime": "2026-10-10T16:00:00.000Z"},
                        {"type": "scheduledMaintenance", "name": "not a release",
                         "plannedStartTime": "2026-09-01T00:00:00.000Z"},
                    ]}, "200"

        monkeypatch.setattr(mod, "_status_get_json", fake_status)
        out = mod.fetch_release_info("ap52")
        assert "AP52" in out
        assert "Summer '26 Patch 13.7" in out and "262.13.7" in out
        assert "Winter '27 Major Release: 2026-10-10" in out
        assert "not a release" not in out  # non-release maintenance filtered out

    def test_instance_falls_back_to_search(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        calls = []

        def fake_status(path):
            calls.append(path)
            if path == "/v1/instances/GS0/status":
                return {"message": "Instance Not Found"}, "404"
            if path == "/v1/search/gs0":
                return [{"key": "GS0X", "isActive": True}], "200"
            assert path == "/v1/instances/GS0X/status"
            return {"key": "GS0X", "location": "NA", "environment": "production",
                    "status": "OK", "isActive": True, "releaseVersion": "S",
                    "releaseNumber": "1", "maintenanceWindow": "w",
                    "Maintenances": []}, "200"

        monkeypatch.setattr(mod, "_status_get_json", fake_status)
        out = mod.fetch_release_info("gs0")
        assert "GS0X" in out
        assert "No upcoming release maintenance events" in out

    def test_invalid_instance_key_rejected_before_any_request(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)

        def boom(path):
            raise AssertionError("no request should be made for an invalid key")

        monkeypatch.setattr(mod, "_status_get_json", boom)
        with pytest.raises(RuntimeError, match="invalid instance"):
            mod.fetch_release_info("AP52/../secrets")

    def test_unknown_instance_raises_actionable_error(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(
            mod, "_status_get_json",
            lambda path: ({"message": "Instance Not Found"}, "404")
            if "/instances/" in path else ([], "200"))
        with pytest.raises(RuntimeError, match="Company Information"):
            mod.fetch_release_info("NOSUCH")

    def test_ambiguous_instance_lists_candidates(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(
            mod, "_status_get_json",
            lambda path: ({"message": "Instance Not Found"}, "404")
            if "/instances/" in path else ([{"key": "NA1"}, {"key": "NA2"}], "200"))
        with pytest.raises(RuntimeError, match="NA1, NA2"):
            mod.fetch_release_info("na")

    def test_summary_names_current_and_preview(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "scrape_aura_context", lambda t: {"fwuid": "x"})
        monkeypatch.delenv("HELP_RELEASE", raising=False)

        def fake_getdata(ctx, url_name, release, type_number="5", requested_type="HelpDocs"):
            assert url_name == mod.RN_LANDING_TOPIC
            if release == "":
                return {"latestRNVersion": "262.0.0"}
            title = {"262.0.0": "Salesforce Summer ’26 Release Notes",
                     "264.0.0": "Salesforce Winter ’27 Release Notes"}[release]
            return {"record": {"Content__c": f"<h1>{title}</h1>"}}

        monkeypatch.setattr(mod, "_getdata", fake_getdata)
        monkeypatch.setattr(
            mod, "_status_get_json",
            lambda path: ([{"type": "release", "name": "Winter '27 Major Release",
                            "plannedStartTime": "2026-08-13T00:00:00.000Z"},
                           {"type": "release", "name": "Winter '27 Major Release",
                            "plannedStartTime": "2026-10-03T00:00:00.000Z"}], "200"))
        out = mod.fetch_release_info()
        assert "Current release: Summer '26 (262.0.0)" in out
        assert "Preview release: Winter '27 (264.0.0)" in out
        assert "Winter '27 Major Release: 2026-08-13 .. 2026-10-03 (2 scheduled events)" in out
        assert mod.RN_ARCHIVE_TOPIC in out

    def test_summary_survives_help_outage(self, monkeypatch):
        # Trust data still prints when the release-notes side fails.
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)

        def boom(t):
            raise RuntimeError("help.salesforce.com is down")

        monkeypatch.setattr(mod, "scrape_aura_context", boom)
        monkeypatch.setattr(
            mod, "_status_get_json",
            lambda path: ([{"type": "release", "name": "R",
                            "plannedStartTime": "2026-10-10T00:00:00.000Z"}], "200"))
        out = mod.fetch_release_info()
        assert "Current release: unavailable" in out
        assert "R: 2026-10-10" in out


class TestDeveloperDocs:
    def test_is_dev_docs_url(self):
        assert mod.is_dev_docs_url(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/x.htm"
        )
        assert not mod.is_dev_docs_url("https://help.salesforce.com/s/articleView?id=x.htm&type=5")
        assert not mod.is_dev_docs_url("xcloud.foo")
        # host match but not a /docs/ path
        assert not mod.is_dev_docs_url("https://developer.salesforce.com/tools/vscode")

    def test_dev_docs_parts_leaf_in_path(self):
        meta, topic = mod._dev_docs_parts(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_x.htm"
        )
        assert meta == "atlas.en-us.uiapi.meta"
        assert topic == "ui_api_x"

    def test_dev_docs_parts_leaf_in_fragment(self):
        meta, topic = mod._dev_docs_parts(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta#ui_api_x.htm"
        )
        assert meta == "atlas.en-us.uiapi.meta"
        assert topic == "ui_api_x"

    def test_dev_docs_parts_landing_no_topic(self):
        meta, topic = mod._dev_docs_parts(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta"
        )
        assert meta == "atlas.en-us.uiapi.meta"
        assert topic is None

    def test_fetch_developer_docs_leaf(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "_fetch_dev_md_twin", lambda url: None)  # no twin -> JSON API
        calls = []

        def fake_json(url):
            calls.append(url)
            if "get_document/" in url:
                return {"deliverable": "uiapi", "locale": "en-us",
                        "version": {"doc_version": "262.0"}, "content": "<p>landing</p>"}
            return {"id": "t", "title": "T", "content": "<h1>Title</h1><p>Body &amp; more</p>"}

        monkeypatch.setattr(mod, "_dev_get_json", fake_json)
        out = mod.fetch_developer_docs(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_x.htm"
        )
        assert out == "Title Body & more"
        assert calls == [
            f"{mod.DEV_HOST}/docs/get_document/atlas.en-us.uiapi.meta",
            f"{mod.DEV_HOST}/docs/get_document_content/uiapi/ui_api_x.htm/en-us/262.0",
        ]

    def test_fetch_developer_docs_landing_uses_manifest_body(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "_fetch_dev_md_twin", lambda url: None)  # no twin -> JSON API

        def fake_json(url):
            assert "get_document_content" not in url  # landing never hits step 2
            return {"deliverable": "uiapi", "locale": "en-us",
                    "version": {"doc_version": "262.0"}, "content": "<p>landing body</p>"}

        monkeypatch.setattr(mod, "_dev_get_json", fake_json)
        out = mod.fetch_developer_docs(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta"
        )
        assert out == "landing body"

    def test_fetch_developer_docs_blank_content_raises(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "_fetch_dev_md_twin", lambda url: None)  # no twin -> JSON API

        def fake_json(url):
            if "get_document/" in url:
                return {"deliverable": "uiapi", "locale": "en-us",
                        "version": {"doc_version": "262.0"}, "content": "<p>x</p>"}
            return {"id": "t", "title": "T", "content": ""}  # bad topic -> empty body

        monkeypatch.setattr(mod, "_dev_get_json", fake_json)
        with pytest.raises(RuntimeError, match="no content for topic"):
            mod.fetch_developer_docs(
                "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/bad.htm"
            )

    def test_dev_get_json_blank_200_raises(self, monkeypatch):
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout="", returncode=0))
        with pytest.raises(RuntimeError, match="empty response"):
            mod._dev_get_json(f"{mod.DEV_HOST}/docs/get_document_content/x/y.htm/en-us/262.0")

    def test_dev_get_json_non_json_raises(self, monkeypatch):
        monkeypatch.setattr(mod, "curl", lambda *a, **k: _proc(stdout="<html>oops</html>"))
        with pytest.raises(RuntimeError, match="not JSON"):
            mod._dev_get_json(f"{mod.DEV_HOST}/docs/get_document/atlas.en-us.uiapi.meta")


class TestDevMarkdownTwin:
    def test_twin_url_swaps_html_leaf(self):
        assert mod._dev_md_twin_url(
            "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.html"
        ) == "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.md"

    def test_twin_url_swaps_htm_leaf(self):
        assert mod._dev_md_twin_url(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_x.htm"
        ) == "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_x.md"

    def test_twin_url_keeps_md_leaf_and_drops_fragment(self):
        assert mod._dev_md_twin_url(
            "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.md#section"
        ) == "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.md"

    def test_twin_url_none_for_landing_without_leaf(self):
        # A deliverable-landing URL (no leaf document) has no reliable twin.
        assert mod._dev_md_twin_url(
            "https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi"
        ) is None

    def test_fetch_twin_returns_markdown_on_markdown_content_type(self, monkeypatch):
        body = "# Title\n\nSome **markdown** body."
        monkeypatch.setattr(
            mod, "curl",
            lambda *a, **k: _proc(stdout=body + "\n__CT__text/markdown; charset=utf-8"),
        )
        out = mod._fetch_dev_md_twin(
            "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.html"
        )
        assert out == body  # returned as-is (no HTML-to-text), trailing marker stripped

    def test_fetch_twin_returns_none_on_html_shell(self, monkeypatch):
        # A page without a twin still 200s but with text/html (the SPA shell).
        monkeypatch.setattr(
            mod, "curl",
            lambda *a, **k: _proc(stdout="<!DOCTYPE html>...\n__CT__text/html; charset=utf-8"),
        )
        out = mod._fetch_dev_md_twin(
            "https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/x.htm"
        )
        assert out is None

    def test_fetch_developer_docs_prefers_twin(self, monkeypatch):
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "_fetch_dev_md_twin", lambda url: "# md body")

        def boom(url):  # JSON API must NOT be hit when a twin exists
            raise AssertionError("Atlas JSON API should not be called when a twin exists")

        monkeypatch.setattr(mod, "_dev_get_json", boom)
        out = mod.fetch_developer_docs(
            "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.html"
        )
        assert out == "# md body"

    def test_fetch_developer_docs_no_twin_no_meta_raises(self, monkeypatch):
        # Newer guide-style URL: no twin available AND no atlas.*.meta segment.
        monkeypatch.setattr(mod, "assert_reachable", lambda *a, **k: None)
        monkeypatch.setattr(mod, "_fetch_dev_md_twin", lambda url: None)
        with pytest.raises(RuntimeError, match="Markdown twin"):
            mod.fetch_developer_docs(
                "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.html"
            )
