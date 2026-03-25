"""Tests for EnhancedFlowValidator — 110-point scoring across 6 categories.

Covers:
  - Valid flow creation (simple → complex) produces high scores
  - Issue detection (anti-patterns, missing fault paths, hardcoded IDs)
  - Quality score accuracy and category breakdowns

Test fixtures live in ./fixtures/ and range from a minimal before-save flow
to a maximally complex flow stacked with every anti-pattern.
"""

import os

from conftest import load_script

mod = load_script("skills/sf-flow/scripts/validate_flow.py")
EnhancedFlowValidator = mod.EnhancedFlowValidator

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


# ── helpers ──────────────────────────────────────────────────────────────────


def _validate(fixture_name: str) -> dict:
    """Run the validator on a fixture and return the full result dict."""
    path = os.path.join(FIXTURES_DIR, fixture_name)
    return EnhancedFlowValidator(path).validate()


def _score(fixture_name: str) -> int:
    return _validate(fixture_name)["overall_score"]


def _critical_messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("critical_issues", [])]


def _warning_messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("warnings", [])]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. VALID FLOW CREATION — high scores, no critical issues
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidFlowCreation:
    def test_before_save_scores_above_threshold(self):
        """TC-V1: Simple before-save flow scores ≥ 88/110 (80% deploy threshold)."""
        assert _score("perfect_before_save.flow-meta.xml") >= 88

    def test_before_save_no_critical_issues(self):
        """TC-V1: Simple before-save flow has zero critical issues."""
        r = _validate("perfect_before_save.flow-meta.xml")
        assert len(r["critical_issues"]) == 0

    def test_before_save_correct_api_version(self):
        """TC-V1: API version is 65.0."""
        r = _validate("perfect_before_save.flow-meta.xml")
        assert r["api_version"] == "65.0"

    def test_after_save_scores_above_threshold(self):
        """TC-V2: After-save flow with fault handling scores ≥ 88/110."""
        assert _score("perfect_after_save.flow-meta.xml") >= 88

    def test_after_save_no_critical_issues(self):
        """TC-V2: After-save flow has zero critical issues."""
        r = _validate("perfect_after_save.flow-meta.xml")
        assert len(r["critical_issues"]) == 0

    def test_after_save_full_error_handling_score(self):
        """TC-V2: After-save with fault paths gets full error handling score."""
        r = _validate("perfect_after_save.flow-meta.xml")
        eh = r["categories"]["error_handling"]
        assert eh["score"] == eh["max_score"]

    def test_screen_flow_scores_above_threshold(self):
        """TC-V3: Screen flow scores ≥ 88/110."""
        assert _score("screen_flow_simple.flow-meta.xml") >= 88

    def test_screen_flow_no_critical_issues(self):
        """TC-V3: Screen flow has zero critical issues."""
        r = _validate("screen_flow_simple.flow-meta.xml")
        assert len(r["critical_issues"]) == 0

    def test_scheduled_flow_scores_above_threshold(self):
        """TC-V4: Scheduled flow scores ≥ 88/110."""
        assert _score("scheduled_flow.flow-meta.xml") >= 88

    def test_scheduled_flow_no_critical_issues(self):
        """TC-V4: Scheduled flow has zero critical issues."""
        r = _validate("scheduled_flow.flow-meta.xml")
        assert len(r["critical_issues"]) == 0

    def test_complex_flow_scores_above_threshold(self):
        """TC-V5: Complex multi-object flow scores ≥ 88/110."""
        assert _score("complex_multi_object.flow-meta.xml") >= 88

    def test_complex_flow_no_critical_issues(self):
        """TC-V5: Complex flow has zero critical issues."""
        r = _validate("complex_multi_object.flow-meta.xml")
        assert len(r["critical_issues"]) == 0

    def test_complex_flow_full_performance_score(self):
        """TC-V5: Complex flow with DML outside loop gets full perf score."""
        r = _validate("complex_multi_object.flow-meta.xml")
        perf = r["categories"]["performance_bulk"]
        assert perf["score"] == perf["max_score"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ISSUE DETECTION — anti-patterns are flagged correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestIssueDetection:
    def test_dml_in_loop_flagged_critical(self):
        """TC-I1: DML inside loop is flagged as CRITICAL."""
        r = _validate("dml_in_loop.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("DML" in m and "loop" in m.lower() for m in crits)

    def test_dml_in_loop_below_threshold(self):
        """TC-I1: DML-in-loop flow scores below 80% deploy threshold."""
        assert _score("dml_in_loop.flow-meta.xml") < 88

    def test_dml_in_loop_perf_score_penalized(self):
        """TC-I1: Performance category is heavily penalized."""
        r = _validate("dml_in_loop.flow-meta.xml")
        perf = r["categories"]["performance_bulk"]
        assert perf["score"] < perf["max_score"]

    def test_missing_faults_detected(self):
        """TC-I2: Missing fault paths are flagged as warnings."""
        r = _validate("missing_fault_paths.flow-meta.xml")
        warns = _warning_messages(r)
        assert any("fault" in m.lower() for m in warns)

    def test_missing_faults_error_handling_score_zero(self):
        """TC-I2: Error handling score is 0 when all DML lacks fault paths."""
        r = _validate("missing_fault_paths.flow-meta.xml")
        eh = r["categories"]["error_handling"]
        assert eh["score"] == 0

    def test_recursive_after_save_flagged(self):
        """TC-I3: After-save updating same object without entry conditions is CRITICAL."""
        r = _validate("missing_fault_paths.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("infinite loop" in m.lower() or "recursive" in m.lower() for m in crits)

    def test_hardcoded_id_flagged(self):
        """TC-I4: Hardcoded Salesforce ID is flagged as a warning."""
        r = _validate("hardcoded_ids.flow-meta.xml")
        warns = _warning_messages(r)
        assert any("hardcoded" in m.lower() and "id" in m.lower() for m in warns)

    def test_old_api_detected(self):
        """TC-I5: Old API version gets a lower security/governance score."""
        r = _validate("old_api_version.flow-meta.xml")
        sec = r["categories"]["security_governance"]
        assert sec["score"] < sec["max_score"]

    def test_max_anti_patterns_very_low_score(self):
        """TC-I6: Flow with every anti-pattern scores ≤ 50/110."""
        assert _score("max_complexity_anti_patterns.flow-meta.xml") <= 50

    def test_max_anti_patterns_multiple_criticals(self):
        """TC-I6: Flow with stacked anti-patterns has ≥ 2 critical issues."""
        r = _validate("max_complexity_anti_patterns.flow-meta.xml")
        assert len(r["critical_issues"]) >= 2

    def test_max_anti_patterns_dml_in_loop(self):
        """TC-I6: DML-in-loop detected in complex flow."""
        r = _validate("max_complexity_anti_patterns.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("DML" in m for m in crits)

    def test_max_anti_patterns_soql_in_loop(self):
        """TC-I6: SOQL-in-loop detected in complex flow."""
        r = _validate("max_complexity_anti_patterns.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("SOQL" in m for m in crits)

    def test_max_anti_patterns_hardcoded_ids(self):
        """TC-I6: Hardcoded IDs detected in complex flow."""
        r = _validate("max_complexity_anti_patterns.flow-meta.xml")
        warns = _warning_messages(r)
        assert any("hardcoded" in m.lower() for m in warns)

    def test_max_anti_patterns_store_output_auto(self):
        """TC-I6: storeOutputAutomatically detected in complex flow."""
        r = _validate("max_complexity_anti_patterns.flow-meta.xml")
        warns = _warning_messages(r)
        assert any("store all fields" in m.lower() or "storeoutput" in m.lower() for m in warns)

    def test_max_anti_patterns_missing_faults(self):
        """TC-I6: Missing fault paths detected in complex flow."""
        r = _validate("max_complexity_anti_patterns.flow-meta.xml")
        warns = _warning_messages(r)
        assert any("fault" in m.lower() for m in warns)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. QUALITY SCORE ACCURACY — category breakdowns are correct
# ═══════════════════════════════════════════════════════════════════════════════


class TestQualityScores:
    def test_total_max_is_110(self):
        """All fixtures validate against 110-point max."""
        r = _validate("perfect_before_save.flow-meta.xml")
        total_max = sum(c["max_score"] for c in r["categories"].values())
        assert total_max == 110

    def test_six_categories_present(self):
        """Result always contains exactly 6 scoring categories."""
        r = _validate("perfect_before_save.flow-meta.xml")
        expected = {
            "design_naming",
            "logic_structure",
            "architecture_orchestration",
            "performance_bulk",
            "error_handling",
            "security_governance",
        }
        assert set(r["categories"].keys()) == expected

    def test_category_max_scores(self):
        """Category max scores match the documented breakdown."""
        r = _validate("perfect_before_save.flow-meta.xml")
        expected_maxes = {
            "design_naming": 20,
            "logic_structure": 20,
            "architecture_orchestration": 15,
            "performance_bulk": 20,
            "error_handling": 20,
            "security_governance": 15,
        }
        for cat, expected_max in expected_maxes.items():
            assert r["categories"][cat]["max_score"] == expected_max, f"{cat} max_score mismatch"

    def test_no_category_exceeds_max(self):
        """No category score exceeds its maximum."""
        for fixture in os.listdir(FIXTURES_DIR):
            if not fixture.endswith(".xml"):
                continue
            r = _validate(fixture)
            for cat, data in r["categories"].items():
                assert data["score"] <= data["max_score"], (
                    f"{fixture}: {cat} score {data['score']} > max {data['max_score']}"
                )

    def test_no_category_below_zero(self):
        """No category score goes below zero, even with many anti-patterns."""
        r = _validate("max_complexity_anti_patterns.flow-meta.xml")
        for cat, data in r["categories"].items():
            assert data["score"] >= 0, f"{cat} score went negative: {data['score']}"

    def test_overall_score_equals_category_sum(self):
        """Overall score is the sum of all category scores."""
        for fixture in os.listdir(FIXTURES_DIR):
            if not fixture.endswith(".xml"):
                continue
            r = _validate(fixture)
            cat_sum = sum(c["score"] for c in r["categories"].values())
            assert r["overall_score"] == cat_sum, (
                f"{fixture}: overall {r['overall_score']} != sum {cat_sum}"
            )

    def test_rating_string_present(self):
        """Rating string is always populated."""
        r = _validate("perfect_before_save.flow-meta.xml")
        assert r["rating"] and len(r["rating"]) > 0

    def test_perfect_scores_higher_than_flawed(self):
        """Well-built flows always score higher than anti-pattern flows."""
        perfect = _score("perfect_after_save.flow-meta.xml")
        flawed = _score("dml_in_loop.flow-meta.xml")
        assert perfect > flawed

    def test_complex_good_flow_beats_simple_bad_flow(self):
        """Complex but correct flow scores higher than simple but broken flow."""
        good = _score("complex_multi_object.flow-meta.xml")
        bad = _score("max_complexity_anti_patterns.flow-meta.xml")
        assert good > bad

    def test_score_monotonicity_with_issues(self):
        """More anti-patterns → lower score (max anti-patterns is lowest)."""
        scores = {
            name: _score(name)
            for name in os.listdir(FIXTURES_DIR)
            if name.endswith(".xml")
        }
        assert scores["max_complexity_anti_patterns.flow-meta.xml"] == min(scores.values())
