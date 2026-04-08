"""Tests for Layout validation in validate_metadata_operation.py."""

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


# --- Good Layout payloads ---


class TestValidLayouts:
    def test_good_layout_scores_high(self):
        result = MetadataOperationValidator("Layout", _fixture("good-layout.json")).validate()
        assert result["status"] == "pass"
        assert result["overall_score"] >= 96
        assert result["required_keys_present"] is True

    def test_result_contains_all_required_keys(self):
        result = MetadataOperationValidator("Layout", _fixture("good-layout.json")).validate()
        for key in ("metadata_type", "overall_score", "max_score", "status", "categories", "issues"):
            assert key in result
        assert result["metadata_type"] == "Layout"


# --- Bad Layout payloads ---


class TestLayoutSchemaErrors:
    def test_invalid_section_style_flagged(self):
        result = MetadataOperationValidator("Layout", _fixture("bad-layout-invalid-style.json")).validate()
        msgs = _issues_messages(result)
        assert any("ThreeColumns" in m for m in msgs)

    def test_invalid_item_behavior_flagged(self):
        result = MetadataOperationValidator("Layout", _fixture("bad-layout-invalid-behavior.json")).validate()
        msgs = _issues_messages(result)
        assert any("Editable" in m for m in msgs)

    def test_unlabeled_sections_flagged(self):
        payload = {
            "description": "Layout with unlabeled sections",
            "layoutSections": [
                {"style": "OneColumn", "layoutColumns": []},
                {"style": "OneColumn", "layoutColumns": []},
            ],
        }
        result = MetadataOperationValidator("Layout", payload).validate()
        msgs = _issues_messages(result)
        assert any("missing labels" in m for m in msgs)


class TestLayoutDeployability:
    def test_readonly_behavior_accepted(self):
        payload = {
            "description": "Layout with readonly system fields",
            "layoutSections": [
                {
                    "label": "System Info",
                    "style": "TwoColumnsTopToBottom",
                    "layoutColumns": [
                        {"layoutItems": [{"field": "IsClosedOnCreate", "behavior": "Readonly"}]}
                    ],
                }
            ],
        }
        result = MetadataOperationValidator("Layout", payload).validate()
        assert result["status"] == "pass"
        assert not any("behavior" in m for m in _issues_messages(result))

    def test_valid_related_list_config(self):
        payload = {
            "description": "Layout with configured related list",
            "layoutSections": [{"label": "Info", "style": "OneColumn", "layoutColumns": []}],
            "relatedLists": [
                {
                    "relatedList": "RelatedCaseList",
                    "fields": ["CASES.CASE_NUMBER", "CASES.SUBJECT", "CASES.STATUS"],
                    "sortField": "CASES.CREATED_DATE",
                    "sortOrder": "Desc",
                }
            ],
        }
        result = MetadataOperationValidator("Layout", payload).validate()
        assert result["status"] == "pass"


# --- Layout via MCP validator ---


class TestLayoutMCPIntegration:
    def setup_method(self):
        mcp_mod = load_script("skills/sf-metadata/scripts/mcp_validator.py")
        self.validator = mcp_mod.MetadataMCPValidator()

    def test_layout_create_is_scored(self):
        r = self.validator.validate({
            "tool": "metadata_create",
            "params": {
                "type": "Layout",
                "metadata": [_fixture("good-layout.json")],
            },
        })
        assert r["status"] == "scored"
        assert r["quality_status"] == "pass"

    def test_layout_update_is_scored(self):
        r = self.validator.validate({
            "tool": "metadata_update",
            "params": {
                "type": "Layout",
                "metadata": [_fixture("good-layout.json")],
            },
        })
        assert r["status"] == "scored"

    def test_layout_bad_payload_has_issues(self):
        r = self.validator.validate({
            "tool": "metadata_create",
            "params": {
                "type": "Layout",
                "metadata": [_fixture("bad-layout-invalid-style.json")],
            },
        })
        assert r["status"] == "scored"
        assert len(r.get("issues", [])) > 0
