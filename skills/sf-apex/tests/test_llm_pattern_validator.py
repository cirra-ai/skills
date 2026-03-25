"""Tests for LLMPatternValidator — LLM-specific Apex anti-pattern detection."""

import os

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-apex/scripts/llm_pattern_validator.py")
LLMPatternValidator = mod.LLMPatternValidator

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _validate_fixture(name: str) -> dict:
    path = os.path.join(FIXTURES_DIR, name)
    return LLMPatternValidator(path).validate()


def _messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("issues", [])]


class TestJavaAndHallucinatedApis:
    def test_java_types_flagged(self):
        r = _validate_fixture("java_hallucinations.cls")
        msgs = _messages(r)
        assert any("does not exist in Apex" in m and "ArrayList" in m for m in msgs)

    def test_hallucinated_methods_flagged(self):
        r = _validate_fixture("java_hallucinations.cls")
        msgs = _messages(r)
        assert any("addMilliseconds" in m for m in msgs)
        assert any("stream()" in m for m in msgs)


class TestMapAccessPatterns:
    def test_unsafe_map_access_flagged(self):
        r = _validate_fixture("unsafe_map_access.cls")
        msgs = _messages(r)
        assert any("Potential NPE" in m for m in msgs)

    def test_safe_map_access_not_flagged(self):
        r = _validate_fixture("safe_map_access.cls")
        msgs = _messages(r)
        assert not any("Potential NPE" in m for m in msgs)


class TestSoqlFieldCoverageHeuristic:
    def test_minimal_query_with_many_field_accesses_warns(self):
        r = _validate_fixture("soql_field_coverage_risk.cls")
        msgs = _messages(r)
        assert any("queries" in m and "fields" in m for m in msgs)
