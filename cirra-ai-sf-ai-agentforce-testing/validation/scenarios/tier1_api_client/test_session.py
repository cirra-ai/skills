"""
Tier 1: AgentSession lifecycle tests.

Tests send sequencing, turn tracking, initial greeting, end/cleanup
behaviour, context manager protocol, and post-end safety.

Points: 7
"""

import pytest
from unittest.mock import patch

from agent_api_client import AgentAPIError


@pytest.mark.tier1
@pytest.mark.offline
class TestSession:
    """AgentSession behaviour."""

    def _mock_api_response(self, text: str = "Agent reply") -> dict:
        """Standard mock response from the messages endpoint."""
        return {
            "messages": [
                {
                    "type": "Inform",
                    "id": "msg-001",
                    "message": text,
                }
            ]
        }

    def test_send_increments_sequence_id(self, mock_client, mock_session):
        """Each send() increments sequence_id: 1, 2, 3."""
        with patch.object(mock_client, "_api_request", return_value=self._mock_api_response()):
            r1 = mock_session.send("First")
            r2 = mock_session.send("Second")
            r3 = mock_session.send("Third")

        assert r1.sequence_id == 1
        assert r2.sequence_id == 2
        assert r3.sequence_id == 3

    def test_send_returns_turn_result(self, mock_client, mock_session):
        """send() returns a TurnResult with the correct user_message."""
        with patch.object(
            mock_client, "_api_request", return_value=self._mock_api_response("Hi there")
        ):
            result = mock_session.send("Hello agent")

        assert result.user_message == "Hello agent"
        assert result.agent_text == "Hi there"

    def test_turn_count(self, mock_client, mock_session):
        """turn_count reflects the number of send() calls."""
        with patch.object(mock_client, "_api_request", return_value=self._mock_api_response()):
            mock_session.send("One")
            mock_session.send("Two")

        assert mock_session.turn_count == 2

    def test_turns_returns_copy(self, mock_client, mock_session):
        """session.turns returns a copy; modifying it does not affect internal state."""
        with patch.object(mock_client, "_api_request", return_value=self._mock_api_response()):
            mock_session.send("Hello")

        turns_copy = mock_session.turns
        turns_copy.clear()

        assert mock_session.turn_count == 1
        assert len(mock_session.turns) == 1

    def test_initial_greeting(self, mock_session):
        """initial_greeting property returns the greeting text from session start."""
        assert mock_session.initial_greeting == "Hello! How can I help you today?"

    def test_end_sends_delete(self, mock_client, mock_session):
        """end() sends a DELETE request with x-session-end-reason header."""
        with patch.object(mock_client, "_api_request", return_value={}) as mock_req:
            mock_session.end()

        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args

        assert args[0] == "DELETE"
        assert "sessions/test-session-id-abc123" in args[1]
        assert kwargs["headers"]["x-session-end-reason"] == "UserRequest"

    def test_end_idempotent(self, mock_client, mock_session):
        """Calling end() a second time returns {} without making another API call."""
        with patch.object(mock_client, "_api_request", return_value={}) as mock_req:
            first = mock_session.end()
            second = mock_session.end()

        assert first == {}
        assert second == {}
        assert mock_req.call_count == 1

    def test_context_manager(self, mock_client, mock_session):
        """Using the session as a context manager calls end() on exit."""
        with patch.object(mock_client, "_api_request", return_value={}) as mock_req:
            with mock_session:
                pass  # just enter and exit

        # end() should have been called once via __exit__
        mock_req.assert_called_once()
        args, _ = mock_req.call_args
        assert args[0] == "DELETE"

    def test_send_after_end_raises(self, mock_client, mock_session):
        """send() after end() raises AgentAPIError(400)."""
        with patch.object(mock_client, "_api_request", return_value={}):
            mock_session.end()

        with pytest.raises(AgentAPIError) as exc_info:
            mock_session.send("Should fail")

        assert exc_info.value.status_code == 400
        assert "Session already ended" in exc_info.value.message
