"""Tests for ApexValidator — 150-point scoring and anti-pattern detection."""

import os

from conftest import load_script

mod = load_script("skills/sf-apex/scripts/validate_apex.py")
ApexValidator = mod.ApexValidator

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _validate_fixture(name: str) -> dict:
    path = os.path.join(FIXTURES_DIR, name)
    return ApexValidator(path).validate()


def _critical_messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("issues", []) if i.get("severity") == "CRITICAL"]


def _warning_messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("issues", []) if i.get("severity") == "WARNING"]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. VALID APEX — high scores and no critical findings
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidApex:
    def test_service_scores_above_threshold(self):
        """Valid service fixture should score in the deploy-ready range."""
        r = _validate_fixture("perfect_service.cls")
        assert r["score"] >= 135

    def test_service_has_no_critical_issues(self):
        r = _validate_fixture("perfect_service.cls")
        assert len(_critical_messages(r)) == 0

    def test_score_never_exceeds_max(self):
        r = _validate_fixture("perfect_service.cls")
        assert r["score"] <= r["max_score"] == 150


# ═══════════════════════════════════════════════════════════════════════════════
# 2. BULKIFICATION DETECTION — critical anti-patterns are flagged
# ═══════════════════════════════════════════════════════════════════════════════


class TestBulkificationDetection:
    def test_dml_in_loop_flagged(self):
        r = _validate_fixture("dml_in_loop.cls")
        crits = _critical_messages(r)
        assert any("DML" in m and "loop" in m.lower() for m in crits)

    def test_soql_in_loop_flagged(self):
        r = _validate_fixture("soql_in_loop.cls")
        crits = _critical_messages(r)
        assert any("SOQL" in m and "loop" in m.lower() for m in crits)

    def test_dml_in_loop_penalizes_bulkification_score(self):
        r = _validate_fixture("dml_in_loop.cls")
        assert r["scores"]["bulkification"] < 25

    def test_soql_in_loop_penalizes_total_score(self):
        r = _validate_fixture("soql_in_loop.cls")
        assert r["score"] < 150

    def test_inline_single_line_dml_in_loop_flagged(self):
        r = _validate_fixture("dml_in_loop_inline.cls")
        crits = _critical_messages(r)
        assert any("DML" in m and "loop" in m.lower() for m in crits)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SECURITY CHECKS — sharing declarations handled correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityChecks:
    def test_missing_sharing_warned(self):
        r = _validate_fixture("missing_sharing.cls")
        warns = _warning_messages(r)
        assert any("sharing" in m.lower() for m in warns)

    def test_test_class_without_sharing_not_warned(self, tmp_path):
        code = """@isTest
private class AccountServiceTest {
    @isTest
    static void itWorks() {}
}"""
        path = tmp_path / "tmp_test_class.cls"
        path.write_text(code, encoding="utf-8")
        r = ApexValidator(str(path)).validate()
        warns = _warning_messages(r)
        assert not any("sharing" in m.lower() for m in warns)


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION-AWARE SECURITY_ENFORCED DETECTION (removed in API 67.0 / Summer '26)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityEnforcedVersionAware:
    def _validate_at(self, api_version):
        path = os.path.join(FIXTURES_DIR, "security_enforced_query.cls")
        return ApexValidator(path, api_version=api_version).validate()

    def test_critical_at_api_67(self):
        """At API 67.0+ the clause no longer compiles — must be CRITICAL."""
        r = self._validate_at(67.0)
        crits = _critical_messages(r)
        assert any("SECURITY_ENFORCED" in m for m in crits)

    def test_info_only_below_67(self):
        """At API <= 66.0 the clause still compiles — advisory only, no penalty."""
        r = self._validate_at(66.0)
        assert not any("SECURITY_ENFORCED" in m for m in _critical_messages(r))
        assert not any("SECURITY_ENFORCED" in m for m in _warning_messages(r))
        infos = [i["message"] for i in r["issues"] if i["severity"] == "INFO"]
        assert any("SECURITY_ENFORCED" in m for m in infos)

    def test_warning_when_version_unknown(self):
        """Unknown version — warn, since new deployments default to 67.0."""
        r = self._validate_at(None)
        warns = _warning_messages(r)
        assert any("SECURITY_ENFORCED" in m for m in warns)

    def test_clean_class_unaffected(self):
        """A USER_MODE class raises no SECURITY_ENFORCED finding at any version."""
        path = os.path.join(FIXTURES_DIR, "perfect_service.cls")
        r = ApexValidator(path, api_version=67.0).validate()
        assert not any("SECURITY_ENFORCED" in i["message"] for i in r["issues"])
