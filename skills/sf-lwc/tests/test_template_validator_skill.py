"""Skill-local tests for template anti-pattern validation."""

from __future__ import annotations

from pathlib import Path

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-lwc/scripts/template_validator.py")
LWCTemplateValidator = mod.LWCTemplateValidator

FIXTURES = Path(__file__).parent / "fixtures"


def _validate_fixture(name: str) -> dict:
    return LWCTemplateValidator(str(FIXTURES / name)).validate()


def test_good_fixture_has_no_issues():
    result = _validate_fixture("good_template.html")
    assert result["issue_count"] == 0
    assert result["issues"] == []


def test_bad_fixture_reports_critical_issue():
    result = _validate_fixture("bad_template_inline_ternary.html")
    assert result["issue_count"] > 0
    assert any(i["severity"] == "CRITICAL" for i in result["issues"])
    assert any("Ternary" in i["message"] for i in result["issues"])


def test_edge_empty_fixture_is_handled():
    result = _validate_fixture("edge_empty_template.html")
    assert set(result.keys()) >= {"file", "issues", "issue_count"}
    assert result["issue_count"] == 0


def test_single_line_iteration_without_key_is_flagged_regression():
    result = _validate_fixture("single_line_missing_key.html")
    assert any(i["category"] == "iteration" for i in result["issues"])


def test_single_line_iteration_with_key_is_not_flagged_regression():
    result = _validate_fixture("single_line_with_key.html")
    assert not any(i["category"] == "iteration" for i in result["issues"])


def test_comment_pattern_false_positive_regression():
    result = _validate_fixture("comment_false_positive.html")
    assert result["issue_count"] == 0
