"""
Tier 2 — format_results() unit tests.

Tests the terminal report formatter: header, pass rate calculation,
failed turn details, and fix instruction sections.
"""

import pytest

from multi_turn_test_runner import format_results


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _make_results(
    scenarios,
    total_scenarios=None,
    passed_scenarios=None,
    failed_scenarios=None,
    error_scenarios=0,
    total_turns=None,
    passed_turns=None,
    failed_turns=None,
):
    """Build a results dict matching the structure produced by main()."""
    if total_scenarios is None:
        total_scenarios = len(scenarios)
    if passed_scenarios is None:
        passed_scenarios = sum(1 for s in scenarios if s["status"] == "passed")
    if failed_scenarios is None:
        failed_scenarios = sum(1 for s in scenarios if s["status"] == "failed")
    if total_turns is None:
        total_turns = sum(s["total_turns"] for s in scenarios)
    if passed_turns is None:
        passed_turns = sum(s["pass_count"] for s in scenarios)
    if failed_turns is None:
        failed_turns = sum(s["fail_count"] for s in scenarios)

    return {
        "agent_id": "test-agent-001",
        "scenario_file": "test_scenarios.yaml",
        "timestamp": "2026-01-01T00:00:00",
        "total_elapsed_ms": 1500,
        "summary": {
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": failed_scenarios,
            "error_scenarios": error_scenarios,
            "total_turns": total_turns,
            "passed_turns": passed_turns,
            "failed_turns": failed_turns,
        },
        "scenarios": scenarios,
    }


def _make_passing_scenario(name="happy_path"):
    """Build a passing scenario result."""
    return {
        "name": name,
        "description": "All turns pass",
        "status": "passed",
        "turns": [
            {
                "turn_number": 1,
                "user_message": "Hello",
                "agent_text": "Hi there!",
                "message_types": ["Inform"],
                "elapsed_ms": 120.0,
                "has_response": True,
                "has_escalation": False,
                "has_action_result": False,
                "error": None,
                "evaluation": {
                    "passed": True,
                    "pass_count": 1,
                    "fail_count": 0,
                    "total_checks": 1,
                    "checks": [
                        {
                            "name": "response_not_empty",
                            "expected": True,
                            "passed": True,
                            "actual": True,
                            "detail": "Response has content",
                        }
                    ],
                },
            }
        ],
        "pass_count": 1,
        "fail_count": 0,
        "total_turns": 1,
        "elapsed_ms": 120.0,
        "error": None,
    }


def _make_failing_scenario(name="failing_path", check_name="response_contains"):
    """Build a scenario with one failing turn."""
    return {
        "name": name,
        "description": "A turn fails",
        "status": "failed",
        "turns": [
            {
                "turn_number": 1,
                "user_message": "Hello",
                "agent_text": "Hi there!",
                "message_types": ["Inform"],
                "elapsed_ms": 100.0,
                "has_response": True,
                "has_escalation": False,
                "has_action_result": False,
                "error": None,
                "evaluation": {
                    "passed": True,
                    "pass_count": 1,
                    "fail_count": 0,
                    "total_checks": 1,
                    "checks": [
                        {
                            "name": "response_not_empty",
                            "expected": True,
                            "passed": True,
                            "actual": True,
                            "detail": "Response has content",
                        }
                    ],
                },
            },
            {
                "turn_number": 2,
                "user_message": "What is my order status?",
                "agent_text": "I don't know.",
                "message_types": ["Inform"],
                "elapsed_ms": 200.0,
                "has_response": True,
                "has_escalation": False,
                "has_action_result": False,
                "error": None,
                "evaluation": {
                    "passed": False,
                    "pass_count": 0,
                    "fail_count": 1,
                    "total_checks": 1,
                    "checks": [
                        {
                            "name": check_name,
                            "expected": "order",
                            "passed": False,
                            "actual": False,
                            "detail": "'order' not found in response",
                        }
                    ],
                },
            },
        ],
        "pass_count": 1,
        "fail_count": 1,
        "total_turns": 2,
        "elapsed_ms": 300.0,
        "error": None,
    }


# ─────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.tier2
@pytest.mark.offline
def test_header_present():
    """Output contains the report header."""
    results = _make_results([_make_passing_scenario()])
    output = format_results(results)
    assert "MULTI-TURN TEST RESULTS" in output


@pytest.mark.tier2
@pytest.mark.offline
def test_pass_rate_calculated():
    """3 of 4 turns passed -> '75.0%' displayed."""
    passing = _make_passing_scenario("s1")
    passing["pass_count"] = 3
    passing["total_turns"] = 3

    failing = _make_failing_scenario("s2")
    failing["pass_count"] = 0
    failing["fail_count"] = 1
    failing["total_turns"] = 1

    results = _make_results(
        [passing, failing],
        total_turns=4,
        passed_turns=3,
        failed_turns=1,
    )
    output = format_results(results)
    assert "75.0%" in output


@pytest.mark.tier2
@pytest.mark.offline
def test_failed_detail_shown():
    """Failed turn shows FAILED TURNS section with check name."""
    failing = _make_failing_scenario("bad_scenario", check_name="response_contains")
    results = _make_results([failing])
    output = format_results(results)
    assert "FAILED TURNS" in output
    assert "response_contains" in output


@pytest.mark.tier2
@pytest.mark.offline
def test_fix_instructions_shown():
    """Results with failures include AGENTIC FIX INSTRUCTIONS section."""
    failing = _make_failing_scenario("bad_scenario", check_name="response_contains")
    results = _make_results([failing])
    output = format_results(results)
    assert "AGENTIC FIX INSTRUCTIONS" in output
