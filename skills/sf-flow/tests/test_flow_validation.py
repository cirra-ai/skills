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
        """TC-I2: In a RecordAfterSave flow, missing fault paths are CRITICAL
        (save-blocking risk) — not just warnings."""
        r = _validate("missing_fault_paths.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("save-blocking" in m.lower() or "fault" in m.lower() for m in crits)

    def test_missing_faults_error_handling_score_zero(self):
        """TC-I2: Error handling score is 0 when all DML lacks fault paths."""
        r = _validate("missing_fault_paths.flow-meta.xml")
        eh = r["categories"]["error_handling"]
        assert eh["score"] == 0

    def test_action_call_missing_fault_in_scheduled_flow_flagged_high(self):
        """Regression: a non-RecordAfterSave flow with an actionCall missing
        faultConnector is flagged as HIGH (not just a low-severity warning).

        Reproduces the SFDCDEMO-74-class bug: an emailSimple actionCall with no
        faultConnector silently swallowed failures. The save-blocking rule does
        not apply (no originating save in a scheduled flow), so the general
        fault-path rule must catch it.
        """
        r = _validate("scheduled_action_no_fault.flow-meta.xml")
        eh = r["categories"]["error_handling"]
        crits = eh.get("critical_issues", [])
        assert any(
            i.get("severity") == "HIGH" and "actionCalls" in i.get("message", "")
            for i in crits
        ), f"Expected HIGH-severity actionCalls fault issue in error_handling, got: {crits}"

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


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SAVE-BLOCKING DETECTION — RecordAfterSave fault-connector enforcement
# ═══════════════════════════════════════════════════════════════════════════════


class TestSaveBlockingDetection:
    """Acceptance criteria for the save-blocking validator check.

    Implements the principle: an unhandled fault in a RecordAfterSave flow
    propagates back to the originating DML as CANNOT_EXECUTE_FLOW_TRIGGER,
    blocking the user's save. Side-effect flows must opt out by attaching a
    faultConnector to every fallible element.
    """

    def test_after_save_email_no_fault_is_critical(self):
        """High Value Opp V1 regression — emailSimple without faultConnector is HIGH."""
        r = _validate("after_save_email_no_fault.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("save-blocking" in m.lower() for m in crits)
        assert any("send_email_action" in m.lower() for m in crits)

    def test_after_save_email_with_fault_passes(self):
        """High Value Opp V4 — emailSimple with faultConnector raises no save-blocking issue."""
        r = _validate("after_save_email_with_fault.flow-meta.xml")
        crits = _critical_messages(r)
        warns = _warning_messages(r)
        assert not any("save-blocking" in m.lower() for m in crits + warns)

    def test_save_gating_description_skips_check(self):
        """A RecordAfterSave flow whose description declares 'save-gating'
        opts out of the fault-connector requirement."""
        r = _validate("after_save_save_gating.flow-meta.xml")
        crits = _critical_messages(r)
        warns = _warning_messages(r)
        assert not any("save-blocking" in m.lower() for m in crits + warns)

    def test_before_save_flow_skipped(self):
        """RecordBeforeSave flows are save-gating by definition — no save-blocking check."""
        r = _validate("perfect_before_save.flow-meta.xml")
        crits = _critical_messages(r)
        warns = _warning_messages(r)
        assert not any("save-blocking" in m.lower() for m in crits + warns)

    def test_screen_flow_skipped(self):
        """Screen flows have no originating record save to block."""
        r = _validate("screen_flow_simple.flow-meta.xml")
        crits = _critical_messages(r)
        warns = _warning_messages(r)
        assert not any("save-blocking" in m.lower() for m in crits + warns)

    def test_after_save_lookup_no_fault_is_warning(self):
        """recordLookups without faultConnector in after-save flow is MEDIUM (warning)."""
        r = _validate("after_save_lookup_no_fault.flow-meta.xml")
        warns = _warning_messages(r)
        assert any(
            "save-blocking" in m.lower() and "recordlookups" in m.lower() for m in warns
        )

    def test_nested_save_gating_description_does_not_opt_out(self):
        """Regression: only the flow-level <description> can opt a flow out of
        the save-blocking check. A nested <description> on a sub-element
        (e.g., an actionCalls) that contains 'save-gating' must NOT be picked
        up — the recursive-descendant lookup would match an actionCalls
        description before the top-level one in alphabetical metadata order."""
        r = _validate("after_save_nested_description.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("save-blocking" in m.lower() for m in crits)

    def test_save_blocking_has_actionable_fix(self):
        """Each save-blocking issue includes a remediation hint."""
        r = _validate("after_save_email_no_fault.flow-meta.xml")
        save_blocking = [
            i for i in r["critical_issues"] if "save-blocking" in i["message"].lower()
        ]
        assert save_blocking
        for issue in save_blocking:
            assert "fix" in issue and "faultConnector" in issue["fix"]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. RESOURCE vs NODE — node-only properties on resource elements are CRITICAL
# ═══════════════════════════════════════════════════════════════════════════════


class TestResourcePropertyValidation:
    """Resources (formulas, variables, constants, textTemplates, choices,
    dynamicChoiceSets) do NOT accept node-only properties (label, locationX,
    locationY, connector, faultConnector). Putting them there is a deploy-time
    failure — the validator must catch it as CRITICAL.

    This is the generalised form of the recurring "The FlowFormula element
    doesn't accept a label property" agent error.
    """

    # ── FlowFormula ────────────────────────────────────────────────────────────

    def test_formula_with_label_flagged_critical(self):
        """TC-R1: <label> inside <formulas> is CRITICAL."""
        r = _validate("formula_with_label.flow-meta.xml")
        crits = _critical_messages(r)
        assert any(
            "formulas" in m and "label" in m and "Is_Overdue" in m for m in crits
        ), f"Expected formulas/label/Is_Overdue critical, got: {crits}"

    def test_formula_with_label_fix_lists_allowed(self):
        """TC-R1: The fix message tells the agent what FlowFormula actually accepts."""
        r = _validate("formula_with_label.flow-meta.xml")
        fixes = [i.get("fix", "") for i in r["critical_issues"]]
        assert any("expression" in f and "dataType" in f for f in fixes)

    def test_formula_with_location_flagged_critical(self):
        """TC-R2: <locationX>/<locationY> on a <formulas> entry is CRITICAL —
        resources have no canvas presence."""
        r = _validate("formula_with_location.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("formulas" in m and "locationX" in m for m in crits)
        assert any("formulas" in m and "locationY" in m for m in crits)

    # ── FlowVariable ───────────────────────────────────────────────────────────

    def test_variable_with_label_flagged_critical(self):
        """TC-R3: <label> inside <variables> is CRITICAL."""
        r = _validate("variable_with_label.flow-meta.xml")
        crits = _critical_messages(r)
        assert any(
            "variables" in m and "label" in m and "var_Counter" in m for m in crits
        )

    # ── FlowConstant ───────────────────────────────────────────────────────────

    def test_constant_with_label_flagged_critical(self):
        """TC-R4: <label> inside <constants> is CRITICAL."""
        r = _validate("constant_with_label.flow-meta.xml")
        crits = _critical_messages(r)
        assert any(
            "constants" in m and "label" in m and "DISCOUNT_RATE" in m for m in crits
        )

    # ── FlowTextTemplate ───────────────────────────────────────────────────────

    def test_text_template_with_label_flagged_critical(self):
        """TC-R5: <label> inside <textTemplates> is CRITICAL."""
        r = _validate("text_template_with_label.flow-meta.xml")
        crits = _critical_messages(r)
        assert any(
            "textTemplates" in m and "label" in m and "Greeting_Template" in m
            for m in crits
        )

    # ── FlowChoice ─────────────────────────────────────────────────────────────

    def test_choice_with_location_flagged_critical(self):
        """TC-R6: <locationX>/<locationY> on a <choices> entry is CRITICAL."""
        r = _validate("choice_with_location.flow-meta.xml")
        crits = _critical_messages(r)
        assert any("choices" in m and "locationX" in m for m in crits)

    # ── Negative controls (valid resources must NOT trigger the check) ─────────

    def test_perfect_before_save_no_resource_property_errors(self):
        """Reference: a well-formed flow has zero resource-property critical issues."""
        r = _validate("perfect_before_save.flow-meta.xml")
        crits = _critical_messages(r)
        assert not any(
            "resource elements do not accept" in m for m in crits
        ), f"False positive resource-property errors: {crits}"

    def test_complex_multi_object_no_resource_property_errors(self):
        """Reference: complex flow with valid formulas/variables triggers no
        resource-property errors."""
        r = _validate("complex_multi_object.flow-meta.xml")
        crits = _critical_messages(r)
        assert not any("resource elements do not accept" in m for m in crits)

    # ── Score impact ───────────────────────────────────────────────────────────

    def test_resource_property_error_blocks_deploy_threshold(self):
        """TC-R7: A single resource-property error drops logic_structure but the
        flow may still score above threshold — we don't want the check
        accidentally tanking other unrelated good flows. This test pins the
        deduction so future changes are visible."""
        r = _validate("formula_with_label.flow-meta.xml")
        ls = r["categories"]["logic_structure"]
        # 10-point deduction for resource-property class of error
        assert ls["score"] <= ls["max_score"] - 10

    def test_resource_property_error_has_fix_field(self):
        """TC-R8: Every resource-property critical issue carries an actionable fix."""
        r = _validate("formula_with_label.flow-meta.xml")
        offenders = [
            i for i in r["critical_issues"]
            if "resource elements do not accept" in i["message"]
        ]
        assert offenders
        for issue in offenders:
            assert "fix" in issue
            assert "Remove" in issue["fix"]
            assert "only accepts" in issue["fix"]
