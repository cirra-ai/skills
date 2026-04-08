"""Tests for validate_agentforce.py."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-agentforce/scripts/validate_agentforce.py")
AgentforceValidator = mod.AgentforceValidator

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_good_genaifunction_scores_high():
    result = AgentforceValidator("GenAiFunction", _fixture("good-genaifunction.json")).validate()
    assert result["status"] == "pass"
    assert result["overall_score"] >= 80


def test_missing_description_is_flagged():
    result = AgentforceValidator("GenAiFunction", _fixture("bad-genaifunction-missing-description.json")).validate()
    assert result["status"] != "pass"
    assert any("description" in i["message"].lower() for i in result["issues"])


def test_good_genaiplugin_scores_high():
    result = AgentforceValidator("GenAiPlugin", _fixture("good-genaiplugin.json")).validate()
    assert result["status"] == "pass"
    assert result["overall_score"] >= 80


def test_edge_minimal_prompttemplate_returns_required_keys_and_bounds():
    result = AgentforceValidator("PromptTemplate", _fixture("edge-prompttemplate-minimal.json")).validate()
    assert 0 <= result["overall_score"] <= result["max_score"]
    for key in ("metadata_type", "overall_score", "max_score", "status", "categories", "issues"):
        assert key in result


def test_unsupported_type_returns_critical():
    result = AgentforceValidator("UnknownType", {"apiName": "Foo"}).validate()
    assert result["status"] == "critical"
    assert any("Unsupported" in i["message"] for i in result["issues"])


def test_empty_payload_returns_critical():
    result = AgentforceValidator("GenAiFunction", {}).validate()
    assert result["status"] == "critical"
