"""
Tier 4 — Malformed Response Tests (3 points)

Tests that the client handles malformed or unexpected API response bodies
gracefully (missing fields, non-JSON, empty lists, etc.).

Tests:
    1. test_non_json_response_body — _api_request with non-JSON body raises JSONDecodeError
    2. test_missing_session_id_in_response — start_session raises AgentAPIError
    3. test_empty_messages_list — start_session creates session with empty initial_messages
    4. test_missing_message_fields — _parse_messages uses defaults for missing fields
    5. test_empty_response_from_send — send() returns TurnResult with empty agent_messages
"""

import json
import sys
import time
from pathlib import Path

import pytest

# Allow importing helpers from the validation conftest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_api_client import (
    AgentAPIClient,
    AgentAPIError,
    AgentSession,
    AgentMessage,
    TurnResult,
    _parse_messages,
)
from conftest import make_mock_response, make_http_error


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.tier4
@pytest.mark.offline
def test_non_json_response_body(mock_urlopen, mock_client):
    """_api_request raises json.JSONDecodeError when response body is not JSON.

    The code path: resp_body = resp.read().decode("utf-8"), then json.loads(resp_body).
    Non-JSON body causes json.loads to raise JSONDecodeError, which is not caught.
    """
    mock_urlopen.return_value = make_mock_response(
        status=200,
        body="<html>Not JSON</html>",
    )

    with pytest.raises(json.JSONDecodeError):
        mock_client._api_request("GET", "https://api.salesforce.com/einstein/ai-agent/v1/test")


@pytest.mark.tier4
@pytest.mark.offline
def test_missing_session_id_in_response(mock_urlopen, mock_client):
    """start_session raises AgentAPIError when response has no sessionId."""
    # Response has messages but no sessionId key
    mock_urlopen.return_value = make_mock_response(
        status=200,
        body={"messages": []},
    )

    with pytest.raises(AgentAPIError) as exc_info:
        mock_client.start_session(agent_id="0XxRM0000004ABC")

    assert "No sessionId in response" in exc_info.value.message


@pytest.mark.tier4
@pytest.mark.offline
def test_empty_messages_list(mock_urlopen, mock_client):
    """start_session succeeds with empty messages list; session has no initial_messages."""
    mock_urlopen.return_value = make_mock_response(
        status=200,
        body={"sessionId": "sess-abc-123", "messages": []},
    )

    session = mock_client.start_session(agent_id="0XxRM0000004ABC")

    assert session.session_id == "sess-abc-123"
    assert session.initial_messages == []
    assert session.initial_greeting == ""


@pytest.mark.tier4
@pytest.mark.offline
def test_missing_message_fields():
    """_parse_messages uses defaults when message dict is missing most fields.

    A message dict with only {"foo": "bar"} should still produce an AgentMessage
    with type="Unknown", id="", message="", etc.
    """
    raw_messages = [{"foo": "bar"}]
    parsed = _parse_messages(raw_messages)

    assert len(parsed) == 1
    msg = parsed[0]
    assert msg.type == "Unknown"
    assert msg.id == ""
    assert msg.message == ""
    assert msg.feedback_id == ""
    assert msg.plan_id == ""
    assert msg.is_content_safe is True
    assert msg.result == []
    assert msg.cited_references == []


@pytest.mark.tier4
@pytest.mark.offline
def test_empty_response_from_send(mock_urlopen, mock_client):
    """session.send() returns TurnResult with empty agent_messages on empty messages list."""
    # First call: start_session
    start_resp = make_mock_response(
        status=200,
        body={
            "sessionId": "sess-xyz-789",
            "messages": [{"type": "Inform", "id": "g1", "message": "Hi there!"}],
        },
    )
    # Second call: send() — returns empty messages
    send_resp = make_mock_response(
        status=200,
        body={"messages": []},
    )
    mock_urlopen.side_effect = [start_resp, send_resp]

    session = mock_client.start_session(agent_id="0XxRM0000004ABC")
    turn = session.send("Hello")

    assert isinstance(turn, TurnResult)
    assert turn.agent_messages == []
    assert turn.agent_text == ""
    assert turn.has_response is False
