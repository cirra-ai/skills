"""Tier 5 — Live session lifecycle tests (9 points).

Tests real session create / send / end against the Agentforce Runtime API.
Every test creates its own session and cleans up via try/finally.
"""

import pytest


# ---------------------------------------------------------------------------
# T5-SESS-01: Session create returns an ID (2 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
def test_session_create_returns_id(live_client, live_agent_id):
    """start_session() returns a session with a non-empty session_id."""
    session = live_client.start_session(agent_id=live_agent_id)
    try:
        assert session.session_id, "session_id should be non-empty"
        assert isinstance(session.session_id, str)
        assert len(session.session_id) > 5, f"session_id too short: {session.session_id!r}"
    finally:
        session.end()


# ---------------------------------------------------------------------------
# T5-SESS-02: Sending a message returns a response (3 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
def test_send_returns_response(live_client, live_agent_id):
    """Sending 'Hello' produces a non-empty agent response."""
    session = live_client.start_session(agent_id=live_agent_id)
    try:
        turn = session.send("Hello")
        assert turn.has_response, f"Expected has_response=True, got False. Raw: {turn.raw_response}"
        assert turn.agent_text, "agent_text should be a non-empty string"
    finally:
        session.end()


# ---------------------------------------------------------------------------
# T5-SESS-03: End session completes cleanly (2 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
def test_end_session_clean(live_client, live_agent_id):
    """end() returns without error and marks session as ended."""
    session = live_client.start_session(agent_id=live_agent_id)
    try:
        session.end()
        assert session._ended is True, "session._ended should be True after end()"
    finally:
        # end() is idempotent — safe to call again if already ended
        if not session._ended:
            session.end()


# ---------------------------------------------------------------------------
# T5-SESS-04: Session with variables receives response (2 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
def test_session_with_variables(live_client, live_agent_id):
    """Creating a session with variables still produces a valid response."""
    variables = [
        {
            "name": "$Context.EndUserLanguage",
            "type": "Text",
            "value": "en_US",
        },
    ]
    session = live_client.start_session(
        agent_id=live_agent_id,
        variables=variables,
    )
    try:
        turn = session.send("Hello")
        assert turn.has_response, "Expected a response when session has variables"
        assert turn.agent_text, "agent_text should be non-empty with session variables"
    finally:
        session.end()
