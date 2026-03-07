"""Tests for ApexMCPValidator — metadata deployment path behavior."""

import os

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-apex/scripts/mcp_validator.py")
ApexMCPValidator = mod.ApexMCPValidator

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _read_fixture(name: str) -> str:
    with open(os.path.join(FIXTURES_DIR, name), encoding="utf-8") as f:
        return f.read()


def _mcp_create(metadata_type: str, full_name: str, body: str) -> dict:
    return ApexMCPValidator().validate(
        {
            "tool": "metadata_create",
            "params": {
                "type": metadata_type,
                "metadata": [{"fullName": full_name, "body": body}],
            },
        }
    )


def _mcp_update(metadata_type: str, full_name: str, body: str) -> dict:
    return ApexMCPValidator().validate(
        {
            "tool": "metadata_update",
            "params": {
                "type": metadata_type,
                "metadata": [{"fullName": full_name, "body": body}],
            },
        }
    )


def _mcp_tooling_dml(sobject: str, full_name: str, body: str) -> dict:
    return ApexMCPValidator().validate(
        {
            "tool": "tooling_api_dml",
            "params": {
                "sObject": sobject,
                "record": {"FullName": full_name, "Body": body},
            },
        }
    )


class TestSingleCallScoring:
    def test_metadata_create_apex_class_scored(self):
        body = _read_fixture("perfect_service.cls")
        r = _mcp_create("ApexClass", "AccountService", body)
        assert r["status"] == "scored"
        assert r["score"] >= 135

    def test_metadata_update_apex_class_scored(self):
        body = _read_fixture("perfect_service.cls")
        r = _mcp_update("ApexClass", "AccountService", body)
        assert r["status"] == "scored"
        assert r["metadata_type"] == "ApexClass"

    def test_tooling_dml_apex_trigger_scored(self):
        body = _read_fixture("good_trigger.trigger")
        r = _mcp_tooling_dml("ApexTrigger", "AccountTrigger", body)
        assert r["status"] == "scored"
        assert r["metadata_type"] == "ApexTrigger"


class TestErrorAndSkipPaths:
    def test_non_apex_metadata_type_skipped(self):
        r = _mcp_create("Flow", "MyFlow", "<Flow/>")
        assert r["status"] == "skipped"

    def test_unsupported_tool_errors(self):
        r = ApexMCPValidator().validate(
            {
                "tool": "soql_query",
                "params": {"sObject": "Account", "fields": ["Id"], "whereClause": "Id != null"},
            }
        )
        assert r["status"] == "error"

    def test_missing_metadata_type_errors(self):
        r = ApexMCPValidator().validate(
            {
                "tool": "metadata_create",
                "params": {"metadata": [{"fullName": "MissingType", "body": "public class X {}"}]},
            }
        )
        assert r["status"] == "error"

    def test_empty_body_errors(self):
        r = _mcp_create("ApexClass", "EmptyClass", "")
        assert r["status"] == "error"


class TestResultStructure:
    def test_result_has_required_keys(self):
        body = _read_fixture("perfect_service.cls")
        r = _mcp_create("ApexClass", "AccountService", body)
        assert "tier" in r
        assert "tool" in r
        assert "metadata_type" in r
        assert "status" in r
        assert "validator" in r
        assert "score" in r
        assert "max_score" in r

    def test_full_name_preserved(self):
        body = _read_fixture("perfect_service.cls")
        r = _mcp_create("ApexClass", "Custom_Name__c", body)
        assert r["full_name"] == "Custom_Name__c"
