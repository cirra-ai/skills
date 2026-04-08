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


def test_missing_invocation_target_type_is_flagged():
    payload = {
        "apiName": "Get_Order_Status",
        "description": "Retrieves the current status of a customer order",
        "invocationTarget": "Get_Order_Status_Flow",
    }
    result = AgentforceValidator("GenAiFunction", payload).validate()
    assert any("invocationTargetType" in i["message"] for i in result["issues"])


def test_flow_target_without_dot_is_not_penalized():
    payload = {
        "apiName": "Get_Order_Status",
        "description": "Retrieves the current status of a customer order",
        "invocationTarget": "Get_Order_Status_Flow",
        "invocationTargetType": "flow",
        "capabilities": ["AgentForce"],
        "inputs": [{"name": "orderId", "description": "The order ID"}],
        "outputs": [{"name": "status", "description": "Order status"}],
    }
    result = AgentforceValidator("GenAiFunction", payload).validate()
    assert not any("incomplete" in i["message"].lower() for i in result["issues"])


def test_apex_target_without_dot_is_penalized():
    payload = {
        "apiName": "Get_Case_Details",
        "description": "Retrieves case details for a given case ID",
        "invocationTarget": "CaseService",
        "invocationTargetType": "apex",
        "capabilities": ["AgentForce"],
        "inputs": [{"name": "caseId", "description": "The case ID"}],
        "outputs": [{"name": "caseRecord", "description": "Full case record"}],
    }
    result = AgentforceValidator("GenAiFunction", payload).validate()
    assert any("Apex target" in i["message"] for i in result["issues"])
