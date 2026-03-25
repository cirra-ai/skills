"""Smoke tests for the audit report generator.

Runs generate_reports.py against minimal fixture data and verifies
all expected output files are created with the correct structure.
"""

import json
from pathlib import Path

import pytest

from conftest import load_script

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "minimal"


@pytest.fixture
def gen():
    return load_script("skills/sf-audit/scripts/generate_reports.py")


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "output"


# ── Input loading ───────────────────────────────────────────────────────────


def test_load_inputs_reads_all_files(gen):
    data = gen.load_inputs(str(FIXTURES_DIR))
    assert isinstance(data["counts"], dict)
    assert data["counts"]["apex_classes"] == 3
    assert len(data["apex_scores"]) == 3
    assert len(data["trigger_findings"]) == 1
    assert len(data["flow_scores"]) == 2
    assert len(data["process_builders"]) == 1
    assert len(data["lwc_scores"]) == 1
    assert len(data["permission_findings"]) == 3
    assert len(data["metadata_scores"]) == 2
    assert len(data["validation_rules"]) == 2
    assert len(data["workflow_rules"]) == 1


def test_load_inputs_missing_dir_returns_defaults(gen, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    data = gen.load_inputs(str(empty))
    assert data["counts"] == {}
    assert data["apex_scores"] == []


# ── Score computation ───────────────────────────────────────────────────────


def test_compute_summary_overall_score(gen):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    assert 0 <= summary["overall_score"] <= 100
    assert summary["overall_rating"] in [
        "Excellent",
        "Good",
        "Acceptable",
        "Needs Improvement",
        "Critical",
    ]


def test_compute_summary_domain_scores(gen):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    for domain in ["apex", "flows", "lwc", "metadata"]:
        assert domain in summary["domain_scores"]
        assert 0 <= summary["domain_scores"][domain] <= 100


def test_compute_summary_below_threshold(gen):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    # ContactTriggerHandler scores 95/150 = 63% → below 70
    assert summary["below_threshold"]["apex"] >= 1


def test_compute_summary_severity_counts(gen):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    assert summary["severity_counts"]["CRITICAL"] == 1
    assert summary["severity_counts"]["HIGH"] == 1
    assert summary["severity_counts"]["LOW"] == 1


def test_score_rating_boundaries(gen):
    assert gen.score_rating(100)[0] == "Excellent"
    assert gen.score_rating(80)[0] == "Excellent"
    assert gen.score_rating(79)[0] == "Good"
    assert gen.score_rating(70)[0] == "Good"
    assert gen.score_rating(69)[0] == "Acceptable"
    assert gen.score_rating(60)[0] == "Acceptable"
    assert gen.score_rating(59)[0] == "Needs Improvement"
    assert gen.score_rating(40)[0] == "Needs Improvement"
    assert gen.score_rating(39)[0] == "Critical"
    assert gen.score_rating(0)[0] == "Critical"


# ── HTML generation ─────────────────────────────────────────────────────────


def test_generate_html_creates_file(gen, output_dir):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    output_dir.mkdir(parents=True)
    html_path = output_dir / "report.html"
    gen.generate_html(data, summary, "Test Org", "00D001", "CS42", "2026-03-06", html_path)
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert len(content) > 500
    assert "Test Org" in content
    assert "00D001" in content
    assert "CS42" in content
    assert "2026-03-06" in content
    assert "banner" in content
    assert "417AE4" in content.upper() or "417ae4" in content


def test_html_contains_all_sections(gen, output_dir):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    output_dir.mkdir(parents=True)
    html_path = output_dir / "report.html"
    gen.generate_html(data, summary, "Test Org", "", "", "2026-01-01", html_path)
    content = html_path.read_text(encoding="utf-8")
    for section in [
        "Executive Summary",
        "Domain Scores",
        "Apex Classes",
        "Apex Triggers",
        "Flows",
        "Process Builders",
        "Lightning Web Components",
        "Profiles &amp; Permissions",
        "Data Model",
        "Validation Rules",
        "Workflow Rules",
        "Recommendations",
    ]:
        assert section in content, f"Missing section: {section}"


def test_html_escapes_special_chars(gen, output_dir):
    data = gen.load_inputs(str(FIXTURES_DIR))
    # Inject a name with HTML special chars
    data["apex_scores"][0]["name"] = '<script>alert("xss")</script>'
    summary = gen.compute_summary(data)
    output_dir.mkdir(parents=True)
    html_path = output_dir / "report.html"
    gen.generate_html(data, summary, "Test Org", "", "", "2026-01-01", html_path)
    content = html_path.read_text(encoding="utf-8")
    assert "<script>alert" not in content
    assert "&lt;script&gt;" in content


# ── JSON summary ────────────────────────────────────────────────────────────


def test_generate_json_summary(gen, output_dir):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    output_dir.mkdir(parents=True)
    json_path = output_dir / "summary.json"
    gen.generate_json_summary(summary, "2026-03-06", json_path)
    assert json_path.exists()
    result = json.loads(json_path.read_text(encoding="utf-8"))
    for key in [
        "overall_score",
        "overall_rating",
        "domain_scores",
        "counts",
        "below_threshold",
        "severity_counts",
        "generated_date",
    ]:
        assert key in result, f"Missing key in JSON summary: {key}"


def test_generate_json_summary_does_not_mutate_input(gen, output_dir):
    data = gen.load_inputs(str(FIXTURES_DIR))
    summary = gen.compute_summary(data)
    output_dir.mkdir(parents=True)
    json_path = output_dir / "summary.json"
    gen.generate_json_summary(summary, "2026-03-06", json_path)
    assert "generated_date" not in summary


# ── Empty data handling ─────────────────────────────────────────────────────


def test_generates_reports_with_empty_data(gen, output_dir, tmp_path):
    empty_input = tmp_path / "empty_input"
    empty_input.mkdir()
    data = gen.load_inputs(str(empty_input))
    summary = gen.compute_summary(data)
    output_dir.mkdir(parents=True)
    html_path = output_dir / "report.html"
    gen.generate_html(data, summary, "Empty Org", "", "", "2026-01-01", html_path)
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "Empty Org" in content


def test_json_summary_with_empty_data(gen, output_dir, tmp_path):
    empty_input = tmp_path / "empty_input"
    empty_input.mkdir()
    data = gen.load_inputs(str(empty_input))
    summary = gen.compute_summary(data)
    output_dir.mkdir(parents=True)
    json_path = output_dir / "summary.json"
    gen.generate_json_summary(summary, "2026-01-01", json_path)
    result = json.loads(json_path.read_text(encoding="utf-8"))
    assert result["overall_score"] == 0.0
