"""Tier 5 — Live multi-turn conversation tests (7 points).

Tests real multi-turn interactions against the Agentforce Runtime API.
These tests are slow (multiple round-trips per test) and marked accordingly.
"""
import pytest


# ---------------------------------------------------------------------------
# T5-MULTI-01: Three-turn conversation (3 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
@pytest.mark.slow
def test_three_turn_conversation(live_client, live_agent_id):
    """Three sequential messages all produce responses with incrementing sequence IDs."""
    messages = [
        "Hello",
        "What can you help me with?",
        "Thank you, goodbye",
    ]
    session = live_client.start_session(agent_id=live_agent_id)
    try:
        turns = []
        for msg in messages:
            turn = session.send(msg)
            turns.append(turn)

        # All three turns should have responses
        for i, turn in enumerate(turns, start=1):
            assert turn.has_response, (
                f"Turn {i} ({messages[i-1]!r}) did not produce a response"
            )
            assert turn.agent_text, (
                f"Turn {i} agent_text is empty"
            )

        # Sequence IDs should be 1, 2, 3
        seq_ids = [t.sequence_id for t in turns]
        assert seq_ids == [1, 2, 3], (
            f"Expected sequence_ids [1, 2, 3], got {seq_ids}"
        )
    finally:
        session.end()


# ---------------------------------------------------------------------------
# T5-MULTI-02: Sequence ID increments correctly (2 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
@pytest.mark.slow
def test_sequence_id_increments(live_client, live_agent_id):
    """After 2 sends, the session's internal _sequence_id equals 2."""
    session = live_client.start_session(agent_id=live_agent_id)
    try:
        session.send("Hello")
        session.send("What can you help me with?")

        assert session._sequence_id == 2, (
            f"Expected _sequence_id == 2 after 2 sends, "
            f"got {session._sequence_id}"
        )
    finally:
        session.end()


# ---------------------------------------------------------------------------
# T5-MULTI-03: Context manager cleanup (2 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
@pytest.mark.slow
def test_context_manager_cleanup(live_client, live_agent_id):
    """Using the context manager auto-ends the session on exit."""
    session_ref = None
    with live_client.session(agent_id=live_agent_id) as session:
        session_ref = session
        turn = session.send("Hello")
        assert turn.has_response, "Expected a response inside context manager"

    # After exiting the context manager, session should be ended
    assert session_ref._ended is True, (
        "session._ended should be True after exiting context manager"
    )
