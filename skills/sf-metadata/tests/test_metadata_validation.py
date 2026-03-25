"""Tests for validate_metadata_operation.py."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import load_script

mod = load_script("skills/sf-metadata/scripts/validate_metadata_operation.py")
MetadataOperationValidator = mod.MetadataOperationValidator

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_good_custom_field_scores_high():
    result = MetadataOperationValidator("CustomField", _fixture("good-customfield.json")).validate()
    assert result["status"] == "pass"
    assert result["overall_score"] >= 96


def test_missing_required_field_is_critical_signal():
    result = MetadataOperationValidator("CustomField", _fixture("bad-customfield-missing-type.json")).validate()
    assert result["status"] != "pass"
    assert any("Missing required field 'type'" in i["message"] for i in result["issues"])


def test_permissionset_modify_all_data_flags_security():
    result = MetadataOperationValidator("PermissionSet", _fixture("bad-permissionset-modifyalldata.json")).validate()
    assert result["overall_score"] <= 110
    assert any("ModifyAllData" in i["message"] for i in result["issues"])


def test_edge_empty_formula_still_returns_required_keys_and_bounds():
    result = MetadataOperationValidator("ValidationRule", _fixture("edge-validationrule-empty-formula.json")).validate()
    assert 0 <= result["overall_score"] <= result["max_score"]
    for key in ("metadata_type", "overall_score", "max_score", "status", "categories", "issues"):
        assert key in result
