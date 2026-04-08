"""Tests for FlexiPage validation in validate_metadata_operation.py."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import load_script

mod = load_script("skills/sf-metadata/scripts/validate_metadata_operation.py")
MetadataOperationValidator = mod.MetadataOperationValidator

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _issues_messages(result: dict) -> list[str]:
    return [i["message"] for i in result["issues"]]


# --- Good FlexiPage payloads ---


class TestValidFlexiPages:
    def test_record_page_scores_high(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("good-flexipage-record.json")).validate()
        assert result["status"] == "pass"
        assert result["overall_score"] >= 96
        assert result["required_keys_present"] is True

    def test_app_page_scores_high(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("good-flexipage-app.json")).validate()
        assert result["status"] == "pass"
        assert result["overall_score"] >= 96

    def test_home_page_scores_high(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("good-flexipage-home.json")).validate()
        assert result["status"] == "pass"
        assert result["overall_score"] >= 96

    def test_result_contains_all_required_keys(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("good-flexipage-record.json")).validate()
        for key in ("metadata_type", "overall_score", "max_score", "status", "categories", "issues"):
            assert key in result
        assert result["metadata_type"] == "FlexiPage"


# --- Bad FlexiPage payloads ---


class TestFlexiPageSchemaErrors:
    def test_wrong_component_name_flagged(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("bad-flexipage-wrong-component.json")).validate()
        msgs = _issues_messages(result)
        assert any("force:recordDetail" in m and "force:detailPanel" in m for m in msgs)

    def test_missing_sobjecttype_flagged(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("bad-flexipage-missing-sobjecttype.json")).validate()
        msgs = _issues_messages(result)
        assert any("sobjectType" in m for m in msgs)

    def test_no_regions_flagged(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("bad-flexipage-no-regions.json")).validate()
        msgs = _issues_messages(result)
        assert any("no regions" in m for m in msgs)

    def test_invalid_visibility_operator_flagged(self):
        result = MetadataOperationValidator(
            "FlexiPage", _fixture("bad-flexipage-invalid-visibility-op.json")
        ).validate()
        msgs = _issues_messages(result)
        assert any("GREATER_THAN" in m for m in msgs)
        assert any("unsupported" in m.lower() for m in msgs)

    def test_empty_master_label_flagged(self):
        payload = _fixture("good-flexipage-record.json")
        payload["masterLabel"] = ""
        result = MetadataOperationValidator("FlexiPage", payload).validate()
        msgs = _issues_messages(result)
        assert any("blank" in m for m in msgs)

    def test_whitespace_only_master_label_flagged(self):
        payload = _fixture("good-flexipage-record.json")
        payload["masterLabel"] = "   "
        result = MetadataOperationValidator("FlexiPage", payload).validate()
        msgs = _issues_messages(result)
        assert any("blank" in m for m in msgs)

    def test_invalid_type_flagged(self):
        payload = _fixture("good-flexipage-record.json")
        payload["type"] = "InvalidPageType"
        result = MetadataOperationValidator("FlexiPage", payload).validate()
        msgs = _issues_messages(result)
        assert any("InvalidPageType" in m for m in msgs)


class TestFlexiPageDeployability:
    def test_app_page_with_sobjecttype_warned(self):
        payload = _fixture("good-flexipage-app.json")
        payload["sobjectType"] = "Account"
        result = MetadataOperationValidator("FlexiPage", payload).validate()
        msgs = _issues_messages(result)
        assert any("should not have 'sobjectType'" in m for m in msgs)

    def test_wrong_template_warned(self):
        payload = _fixture("good-flexipage-record.json")
        payload["template"] = {"name": "home:desktopTemplate"}
        result = MetadataOperationValidator("FlexiPage", payload).validate()
        msgs = _issues_messages(result)
        assert any("template" in m.lower() for m in msgs)

    def test_empty_flexipage_regions_is_critical(self):
        result = MetadataOperationValidator("FlexiPage", _fixture("bad-flexipage-no-regions.json")).validate()
        critical_issues = [i for i in result["issues"] if i["severity"] == "critical"]
        assert any("no regions" in i["message"] for i in critical_issues)


# --- FlexiPage via MCP validator ---


class TestFlexiPageMCPIntegration:
    def setup_method(self):
        mcp_mod = load_script("skills/sf-metadata/scripts/mcp_validator.py")
        self.validator = mcp_mod.MetadataMCPValidator()

    def test_flexipage_create_is_scored(self):
        r = self.validator.validate({
            "tool": "metadata_create",
            "params": {
                "type": "FlexiPage",
                "metadata": [_fixture("good-flexipage-record.json")],
            },
        })
        assert r["status"] == "scored"
        assert r["quality_status"] == "pass"

    def test_flexipage_update_is_scored(self):
        r = self.validator.validate({
            "tool": "metadata_update",
            "params": {
                "type": "FlexiPage",
                "metadata": [_fixture("good-flexipage-record.json")],
            },
        })
        assert r["status"] == "scored"

    def test_flexipage_read_is_lightweight_pass(self):
        r = self.validator.validate({
            "tool": "metadata_read",
            "params": {
                "type": "FlexiPage",
                "fullNames": ["CirraTest_Account_Record_Page"],
            },
        })
        assert r["status"] == "scored"
        assert r["quality_status"] == "pass"
        assert r["metadata_type"] == "FlexiPage"
        assert r["issues"] == []

    def test_flexipage_bad_payload_has_issues(self):
        r = self.validator.validate({
            "tool": "metadata_create",
            "params": {
                "type": "FlexiPage",
                "metadata": [_fixture("bad-flexipage-invalid-visibility-op.json")],
            },
        })
        assert r["status"] == "scored"
        assert r["quality_status"] in ("critical", "fail", "needs_attention")
