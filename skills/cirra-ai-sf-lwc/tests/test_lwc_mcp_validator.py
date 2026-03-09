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


def test_tooling_dml_dict_metadata_returns_error():
    """Tooling API Metadata field is often a dict, not a string."""
    result = LWCMCPValidator().validate({
        "tool": "tooling_api_dml",
        "params": {
            "sObject": "LightningComponentBundle",
            "record": {
                "FullName": "c/testCmp",
                "Metadata": {"apiVersion": 62.0},
            },
        },
    })
    assert result["status"] == "error"
    assert "empty" in result["message"].lower() or "missing" in result["message"].lower()


def test_result_includes_required_metadata_keys():
    result = LWCMCPValidator().validate(_valid_payload())
    for key in ("tier", "tool", "metadata_type", "status", "validator"):
        assert key in result


def test_lwc_resources_dict_format_is_scored():
    """lwcResources sent as {"lwcResource": [...]} dict (actual MCP format) must be scored."""
    payload = {
        "tool": "metadata_create",
        "params": {
            "type": "LightningComponentBundle",
            "metadata": [
                {
                    "fullName": "c/myComponent",
                    "lwcResources": {
                        "lwcResource": [
                            {
                                "filePath": "lwc/myComponent/myComponent.html",
                                "source": "<template><p>{greeting}</p></template>",
                            },
                            {
                                "filePath": "lwc/myComponent/myComponent.js",
                                "source": "import { LightningElement, api } from 'lwc';\nexport default class MyComponent extends LightningElement { @api greeting = 'Hello'; }",
                            },
                        ]
                    },
                }
            ],
        },
    }
    result = LWCMCPValidator().validate(payload)
    assert result["status"] == "scored", (
        f"Expected 'scored' but got '{result['status']}': {result.get('message', '')}"
    )
    assert result["score"] > 0


def test_lwc_resources_list_format_is_scored():
    """lwcResources sent as a flat list (legacy format) must also be scored."""
    payload = {
        "tool": "metadata_create",
        "params": {
            "type": "LightningComponentBundle",
            "metadata": [
                {
                    "fullName": "c/myComponent",
                    "lwcResources": [
                        {
                            "filePath": "lwc/myComponent/myComponent.html",
                            "source": "<template><p>{greeting}</p></template>",
                        }
                    ],
                }
            ],
        },
    }
    result = LWCMCPValidator().validate(payload)
    assert result["status"] == "scored", (
        f"Expected 'scored' but got '{result['status']}': {result.get('message', '')}"
    )
    assert result["score"] > 0
