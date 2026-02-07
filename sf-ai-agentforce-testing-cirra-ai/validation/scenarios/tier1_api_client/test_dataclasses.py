"""
Tier 1: AgentMessage and TurnResult dataclass tests.

Tests __str__ formatting, agent_text aggregation, property flags
(has_response, has_escalation, has_action_result), and to_dict
serialization.

Points: bonus
"""

import pytest
from agent_api_client import AgentMessage


@pytest.mark.tier1
@pytest.mark.offline
class TestDataclasses:
    """AgentMessage and TurnResult dataclass behaviour."""

    def test_agent_message_str(self):
        """Short messages render as '[Type] message'."""
        msg = AgentMessage(type="Inform", id="m1", message="Hello")

        assert str(msg) == "[Inform] Hello"

    def test_agent_message_str_truncated(self):
        """Messages longer than 80 chars are truncated with '...'."""
        long_text = "A" * 100
        msg = AgentMessage(type="Text", id="m2", message=long_text)

        result = str(msg)

        assert result.endswith("...")
        # "[Text] " is 7 chars, then 80 chars of content, then "..."
        assert result == f"[Text] {'A' * 80}..."

    def test_turn_result_agent_text(self, sample_turn_result):
        """agent_text combines Inform and Text messages, skips Escalation."""
        turn = sample_turn_result(
            messages=[
                {"type": "Inform", "message": "Line one"},
                {"type": "Text", "message": "Line two"},
                {"type": "Escalation", "message": "Transferring..."},
            ]
        )

        assert "Line one" in turn.agent_text
        assert "Line two" in turn.agent_text
        assert "Transferring" not in turn.agent_text

    def test_turn_result_has_response(self, sample_turn_result):
        """has_response is True when agent_text has content."""
        turn = sample_turn_result(agent_text="I can help with that.")

        assert turn.has_response is True

    def test_turn_result_has_escalation(self, sample_turn_result):
        """has_escalation is True when an Escalation-type message is present."""
        turn = sample_turn_result(has_escalation=True)

        assert turn.has_escalation is True

    def test_turn_result_has_action_result(self, sample_turn_result):
        """has_action_result is True when a message contains result data."""
        turn = sample_turn_result(has_action_result=True)

        assert turn.has_action_result is True

    def test_turn_result_to_dict(self, sample_turn_result):
        """to_dict() includes all expected keys."""
        turn = sample_turn_result(
            user_message="Test input",
            agent_text="Test output",
            sequence_id=5,
            elapsed_ms=200.123,
        )

        d = turn.to_dict()

        expected_keys = {
            "sequence_id",
            "user_message",
            "agent_text",
            "message_types",
            "has_response",
            "has_escalation",
            "has_action_result",
            "action_results",
            "elapsed_ms",
            "error",
            "raw_messages",
        }
        assert set(d.keys()) == expected_keys
        assert d["sequence_id"] == 5
        assert d["user_message"] == "Test input"
        assert d["elapsed_ms"] == 200.1
        assert d["error"] is None
