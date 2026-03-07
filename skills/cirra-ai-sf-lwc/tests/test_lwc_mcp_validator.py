"""Tests for LWC MCP validation adapter behavior."""

from __future__ import annotations

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-lwc/scripts/mcp_validator.py")
LWCMCPValidator = mod.LWCMCPValidator


def _valid_payload() -> dict:
    return {
        "tool": "metadata_create",
        "params": {
            "type": "LightningComponentBundle",
            "metadata": [
                {
                    "fullName": "c/myComponent",
                    "content": "<template><p>{greeting}</p></template>",
                }
            ],
        },
    }


def test_supported_tool_with_valid_payload_scores():
    result = LWCMCPValidator().validate(_valid_payload())
    assert result["status"] == "scored"
    assert 0 <= result["score"] <= result["max_score"]


def test_unsupported_tool_returns_error():
    result = LWCMCPValidator().validate({"tool": "soql_query", "params": {}})
    assert result["status"] == "error"
    assert isinstance(result["message"], str)


def test_non_target_metadata_type_is_skipped():
    payload = _valid_payload()
    payload["params"]["type"] = "CustomObject"
    result = LWCMCPValidator().validate(payload)
    assert result["status"] == "skipped"


def test_missing_or_empty_payload_data_returns_error():
    payload = _valid_payload()
    payload["params"]["metadata"][0]["content"] = ""
    result = LWCMCPValidator().validate(payload)
    assert result["status"] == "error"
    assert isinstance(result["message"], str)


def test_result_includes_required_metadata_keys():
    result = LWCMCPValidator().validate(_valid_payload())
    for key in ("tier", "tool", "metadata_type", "status", "validator"):
        assert key in result
