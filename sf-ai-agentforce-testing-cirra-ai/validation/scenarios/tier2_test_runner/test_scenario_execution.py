"""
Tier 2 — execute_scenario() unit tests.

Tests scenario execution with fully mocked AgentAPIClient, verifying
status, failure counting, error handling, variable merging, and
metadata capture.
"""

import pytest
from unittest.mock import MagicMock, patch

from agent_api_client import AgentAPIClient, AgentAPIError, TurnResult, AgentMessage
from multi_turn_test_runner import execute_scenario


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _make_turn_result(agent_text="I can help you.", has_action=False, has_esc=False):
    """Build a minimal TurnResult for mocking session.send()."""
    msgs = [AgentMessage(type="Inform", id="msg-001", message=agent_text)]
    if has_esc:
        msgs.append(AgentMessage(type="Escalation", id="msg-002", message="Transferring..."))
    if has_action:
        msgs[0].result = [{"field": "value"}]
    return TurnResult(
        sequence_id=1,
        user_message="test",
        agent_messages=msgs,
        raw_response={},
        elapsed_ms=100.0,
    )


def _make_mock_session(turn_results):
    """Create a mock session context manager whose send() yields turn_results in order."""
    mock_session = MagicMock()
    mock_session.send.side_effect = turn_results
    mock_session.__enter__ = lambda s: s
    mock_session.__exit__ = MagicMock(return_value=False)
    return mock_session


# ─────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.tier2
@pytest.mark.offline
def test_passed_scenario(mock_client):
    """All turns pass their checks -> status == 'passed'."""
    scenario = {
        "name": "happy_path",
        "description": "All turns pass",
        "turns": [
            {"user": "Hello", "expect": {"response_not_empty": True}},
            {"user": "Order status", "expect": {"response_contains": "order"}},
        ],
    }
    turn1 = _make_turn_result(agent_text="Hello! How can I help?")
    turn2 = _make_turn_result(agent_text="Your order ships tomorrow.")
    mock_sess = _make_mock_session([turn1, turn2])

    with patch.object(mock_client, "session", return_value=mock_sess):
        result = execute_scenario(mock_client, "agent-id-001", scenario)

    assert result["status"] == "passed"
    assert result["pass_count"] == 2
    assert result["fail_count"] == 0
    assert result["error"] is None


@pytest.mark.tier2
@pytest.mark.offline
def test_failed_scenario(mock_client):
    """A turn that fails a check -> status == 'failed', fail_count > 0."""
    scenario = {
        "name": "failing_path",
        "description": "Second turn fails",
        "turns": [
            {"user": "Hello", "expect": {"response_not_empty": True}},
            {"user": "Order status", "expect": {"response_contains": "tracking"}},
        ],
    }
    turn1 = _make_turn_result(agent_text="Hi there!")
    turn2 = _make_turn_result(agent_text="I don't have that info.")  # no "tracking"
    mock_sess = _make_mock_session([turn1, turn2])

    with patch.object(mock_client, "session", return_value=mock_sess):
        result = execute_scenario(mock_client, "agent-id-001", scenario)

    assert result["status"] == "failed"
    assert result["fail_count"] == 1
    assert result["pass_count"] == 1


@pytest.mark.tier2
@pytest.mark.offline
def test_error_scenario(mock_client):
    """AgentAPIError during session creation -> status == 'error'."""
    scenario = {
        "name": "error_path",
        "description": "API blows up",
        "turns": [
            {"user": "Hello", "expect": {"response_not_empty": True}},
        ],
    }
    mock_sess = MagicMock()
    mock_sess.__enter__ = MagicMock(side_effect=AgentAPIError("Connection refused", 500))
    mock_sess.__exit__ = MagicMock(return_value=False)

    with patch.object(mock_client, "session", return_value=mock_sess):
        result = execute_scenario(mock_client, "agent-id-001", scenario)

    assert result["status"] == "error"
    assert result["error"] is not None
    assert "Connection refused" in result["error"]


@pytest.mark.tier2
@pytest.mark.offline
def test_variable_merge(mock_client):
    """Global variables override scenario variables with the same name."""
    scenario = {
        "name": "var_merge",
        "description": "Test variable merging",
        "session_variables": [
            {"name": "$Context.AccountId", "type": "Text", "value": "scenario-acct"},
            {"name": "$Context.Language", "type": "Text", "value": "en_US"},
        ],
        "turns": [
            {"user": "Hello", "expect": {"response_not_empty": True}},
        ],
    }
    global_variables = [
        {"name": "$Context.AccountId", "type": "Text", "value": "global-acct"},
    ]

    turn1 = _make_turn_result(agent_text="Hello!")
    mock_sess = _make_mock_session([turn1])

    with patch.object(mock_client, "session", return_value=mock_sess) as patched_session:
        result = execute_scenario(
            mock_client, "agent-id-001", scenario,
            global_variables=global_variables,
        )

    # Verify session was called with merged variables
    call_kwargs = patched_session.call_args
    variables_passed = call_kwargs.kwargs.get("variables") or call_kwargs[1].get("variables")

    # Global var should override the scenario var with same name
    acct_vars = [v for v in variables_passed if v["name"] == "$Context.AccountId"]
    assert len(acct_vars) == 1
    assert acct_vars[0]["value"] == "global-acct"

    # Scenario-only var should still be present
    lang_vars = [v for v in variables_passed if v["name"] == "$Context.Language"]
    assert len(lang_vars) == 1
    assert lang_vars[0]["value"] == "en_US"


@pytest.mark.tier2
@pytest.mark.offline
def test_scenario_filter(mock_client):
    """Name and description are captured from the scenario dict."""
    scenario = {
        "name": "my_unique_scenario",
        "description": "Verifying metadata capture",
        "turns": [
            {"user": "Hello", "expect": {"response_not_empty": True}},
        ],
    }
    turn1 = _make_turn_result(agent_text="Hi!")
    mock_sess = _make_mock_session([turn1])

    with patch.object(mock_client, "session", return_value=mock_sess):
        result = execute_scenario(mock_client, "agent-id-001", scenario)

    assert result["name"] == "my_unique_scenario"
    assert result["description"] == "Verifying metadata capture"
    assert result["total_turns"] == 1
