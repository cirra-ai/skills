"""Tests for skills/cirra-ai-sf-metadata/scripts/mcp_validator.py."""

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-metadata/scripts/mcp_validator.py")
MetadataMCPValidator = mod.MetadataMCPValidator


def _valid_create_input():
    return {
        "tool": "metadata_create",
        "params": {
            "type": "CustomField",
            "metadata": [
                {
                    "fullName": "Invoice__c.Amount__c",
                    "label": "Amount",
                    "type": "Currency",
                    "description": "Stores invoice amount",
                }
            ],
        },
    }


def test_supported_tool_with_valid_payload_is_scored():
    r = MetadataMCPValidator().validate(_valid_create_input())
    assert r["status"] == "scored"


def test_unsupported_tool_returns_error():
    r = MetadataMCPValidator().validate({"tool": "soql_query", "params": {}})
    assert r["status"] == "error"


def test_non_target_metadata_type_is_skipped():
    r = MetadataMCPValidator().validate(
        {"tool": "metadata_create", "params": {"type": "Flow", "metadata": [{"fullName": "X"}]}}
    )
    assert r["status"] == "skipped"


def test_missing_empty_payload_returns_error():
    r = MetadataMCPValidator().validate({"tool": "metadata_create", "params": {"type": "CustomField", "metadata": []}})
    assert r["status"] == "error"


def test_response_contains_required_metadata_keys():
    r = MetadataMCPValidator().validate(_valid_create_input())
    for key in ("tier", "tool", "metadata_type", "status", "validator"):
        assert key in r
