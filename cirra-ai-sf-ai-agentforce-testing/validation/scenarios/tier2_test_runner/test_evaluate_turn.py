"""
Tier 2 — evaluate_turn() unit tests.

Tests ALL check types supported by evaluate_turn() / _run_check():
response_not_empty, response_contains, response_contains_any, response_not_contains,
topic_contains, escalation_triggered, guardrail_triggered, action_invoked,
response_acknowledges_change, response_offers_help, no_re_ask_for, context_retained,
resumes_normal, conversation_resolved, response_declines_gracefully, and unknown checks.

Each test builds a TurnResult via sample_turn_result and verifies the expected
pass/fail outcome from evaluate_turn().
"""

import pytest

from multi_turn_test_runner import (
    evaluate_turn,
)


# ─────────────────────────────────────────────────────────────────────────
# response_not_empty
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_response_not_empty_passes(sample_turn_result):
    """Non-empty response with response_not_empty: true should pass."""
    turn = sample_turn_result(agent_text="I can help you with that.")
    result = evaluate_turn(turn, {"response_not_empty": True}, [])
    assert result["passed"] is True
    assert result["pass_count"] == 1
    assert result["fail_count"] == 0


@pytest.mark.tier2
@pytest.mark.offline
def test_response_not_empty_fails(sample_turn_result):
    """Empty response with response_not_empty: true should fail."""
    turn = sample_turn_result(agent_text="")
    result = evaluate_turn(turn, {"response_not_empty": True}, [])
    assert result["passed"] is False
    assert result["fail_count"] == 1


# ─────────────────────────────────────────────────────────────────────────
# response_contains
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_response_contains_passes(sample_turn_result):
    """Case-insensitive substring match should pass."""
    turn = sample_turn_result(agent_text="I can help with your order")
    result = evaluate_turn(turn, {"response_contains": "order"}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_response_contains_fails(sample_turn_result):
    """Missing substring should fail."""
    turn = sample_turn_result(agent_text="Hello there")
    result = evaluate_turn(turn, {"response_contains": "order"}, [])
    assert result["passed"] is False


# ─────────────────────────────────────────────────────────────────────────
# response_contains_any
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_response_contains_any_passes(sample_turn_result):
    """At least one word from the list is present."""
    turn = sample_turn_result(agent_text="I can cancel your appointment")
    result = evaluate_turn(turn, {"response_contains_any": ["cancel", "delete"]}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_response_contains_any_fails(sample_turn_result):
    """None of the listed words are present."""
    turn = sample_turn_result(agent_text="Hello there, how are you?")
    result = evaluate_turn(turn, {"response_contains_any": ["cancel", "delete"]}, [])
    assert result["passed"] is False


# ─────────────────────────────────────────────────────────────────────────
# response_not_contains
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_response_not_contains_passes(sample_turn_result):
    """Forbidden word absent from response should pass."""
    turn = sample_turn_result(agent_text="Everything looks good.")
    result = evaluate_turn(turn, {"response_not_contains": "error"}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_response_not_contains_fails(sample_turn_result):
    """Forbidden word present in response should fail."""
    turn = sample_turn_result(agent_text="There was an error processing your request.")
    result = evaluate_turn(turn, {"response_not_contains": "error"}, [])
    assert result["passed"] is False


# ─────────────────────────────────────────────────────────────────────────
# topic_contains
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_topic_contains_passes(sample_turn_result):
    """Response mentions the expected topic keyword."""
    turn = sample_turn_result(agent_text="I can help you cancel your subscription.")
    result = evaluate_turn(turn, {"topic_contains": "cancel"}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# escalation_triggered
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_escalation_triggered_by_message_type(sample_turn_result):
    """TurnResult with Escalation message type should detect escalation."""
    turn = sample_turn_result(
        agent_text="Let me connect you to a specialist.",
        has_escalation=True,
    )
    result = evaluate_turn(turn, {"escalation_triggered": True}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_escalation_triggered_by_pattern(sample_turn_result):
    """Response text matching ESCALATION_PATTERNS should detect escalation."""
    turn = sample_turn_result(
        agent_text="I'll connect you to a human agent right away.",
        has_escalation=False,
    )
    result = evaluate_turn(turn, {"escalation_triggered": True}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_escalation_not_triggered(sample_turn_result):
    """Normal response with escalation_triggered: false should pass."""
    turn = sample_turn_result(agent_text="Here is the information you requested.")
    result = evaluate_turn(turn, {"escalation_triggered": False}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# guardrail_triggered
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_guardrail_triggered_passes(sample_turn_result):
    """Response matching guardrail pattern with guardrail_triggered: true should pass."""
    turn = sample_turn_result(agent_text="I can't help with that request.")
    result = evaluate_turn(turn, {"guardrail_triggered": True}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_guardrail_not_triggered(sample_turn_result):
    """Normal response with guardrail_triggered: false should pass."""
    turn = sample_turn_result(agent_text="Sure, let me look that up for you.")
    result = evaluate_turn(turn, {"guardrail_triggered": False}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# action_invoked
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_action_invoked_passes(sample_turn_result):
    """TurnResult with has_action_result=True should pass action_invoked."""
    turn = sample_turn_result(
        agent_text="I found your order details.",
        has_action_result=True,
    )
    result = evaluate_turn(turn, {"action_invoked": "LookupOrder"}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# response_acknowledges_change
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_response_acknowledges_change(sample_turn_result):
    """Response with acknowledgment phrases should pass."""
    turn = sample_turn_result(agent_text="Sure, let me switch to that instead.")
    result = evaluate_turn(turn, {"response_acknowledges_change": True}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# response_offers_help
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_response_offers_help(sample_turn_result):
    """Response offering assistance should pass."""
    turn = sample_turn_result(agent_text="Can I help you with anything else?")
    result = evaluate_turn(turn, {"response_offers_help": True}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# no_re_ask_for
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_no_re_ask_for_passes(sample_turn_result):
    """Response that does NOT re-ask for already-given info should pass."""
    turn = sample_turn_result(agent_text="I've located order #12345. It ships tomorrow.")
    result = evaluate_turn(turn, {"no_re_ask_for": "order number"}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_no_re_ask_for_fails(sample_turn_result):
    """Response that re-asks for info should fail."""
    turn = sample_turn_result(agent_text="Could you please provide the order number?")
    result = evaluate_turn(turn, {"no_re_ask_for": "order number"}, [])
    assert result["passed"] is False


# ─────────────────────────────────────────────────────────────────────────
# context_retained
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_context_retained_passes(sample_turn_result):
    """Non-empty response without confusion patterns should pass."""
    turn = sample_turn_result(agent_text="Your order ships tomorrow as we discussed.")
    result = evaluate_turn(turn, {"context_retained": True}, [])
    assert result["passed"] is True


@pytest.mark.tier2
@pytest.mark.offline
def test_context_retained_fails(sample_turn_result):
    """Response indicating lost context should fail."""
    turn = sample_turn_result(agent_text="I don't have that information.")
    result = evaluate_turn(turn, {"context_retained": True}, [])
    assert result["passed"] is False


# ─────────────────────────────────────────────────────────────────────────
# resumes_normal
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_resumes_normal_passes(sample_turn_result):
    """Non-empty response without guardrail patterns should pass."""
    turn = sample_turn_result(agent_text="Great, let me look up that order for you.")
    result = evaluate_turn(turn, {"resumes_normal": True}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# conversation_resolved
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_conversation_resolved(sample_turn_result):
    """Response with resolution phrases should pass."""
    turn = sample_turn_result(agent_text="Is there anything else I can help with?")
    result = evaluate_turn(turn, {"conversation_resolved": True}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# response_declines_gracefully
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_response_declines_gracefully(sample_turn_result):
    """Response with decline phrases should pass."""
    turn = sample_turn_result(agent_text="I'm not able to assist with that.")
    result = evaluate_turn(turn, {"response_declines_gracefully": True}, [])
    assert result["passed"] is True


# ─────────────────────────────────────────────────────────────────────────
# Unknown / edge-case checks
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.tier2
@pytest.mark.offline
def test_unknown_check_passes(sample_turn_result):
    """Unknown check name should pass (not fail on unknown)."""
    turn = sample_turn_result(agent_text="Hello there")
    result = evaluate_turn(turn, {"foo_bar": True}, [])
    assert result["passed"] is True
    assert result["checks"][0]["passed"] is True
    assert "Unknown" in result["checks"][0]["detail"]


@pytest.mark.tier2
@pytest.mark.offline
def test_multiple_checks_mixed(sample_turn_result):
    """Mix of passing and failing checks, verify counts."""
    turn = sample_turn_result(agent_text="Hello there, I can help")
    # Build expectations with one passing and one failing check.
    expectations = {
        "response_not_empty": True,  # passes (has content)
        "response_contains": "order",  # fails  ("order" not in text)
        "escalation_triggered": False,  # passes (no escalation)
    }
    result = evaluate_turn(turn, expectations, [])
    assert result["total_checks"] == 3
    assert result["pass_count"] == 2
    assert result["fail_count"] == 1
    assert result["passed"] is False
