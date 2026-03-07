"""Root-level tests for cirra-ai-sf-metadata validators."""

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-metadata/scripts/validate_metadata_operation.py")
MetadataOperationValidator = mod.MetadataOperationValidator
analyze_formula_safety = mod.analyze_formula_safety


def test_validator_returns_critical_for_empty_payload():
    result = MetadataOperationValidator("CustomField", {}).validate()
    assert result["status"] == "critical"


def test_do_while_layout_regression_is_detected():
    findings = analyze_formula_safety("do { insert rec; } while(x > 0);")
    assert any("do/while" in f for f in findings)
