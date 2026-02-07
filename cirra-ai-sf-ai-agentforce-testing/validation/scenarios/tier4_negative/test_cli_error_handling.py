"""
Tier 4 — CLI Error Handling Tests (7 points)

Tests for command-line invocation errors, connection failures,
and token expiration behaviour.

Tests:
    1. test_missing_agent_id_exits_2 — Missing --agent-id exits with code 2
    2. test_nonexistent_scenario_file_exits_2 — Non-existent scenario file exits 2
    3. test_url_error_raises_agent_api_error — URLError wrapped as AgentAPIError
    4. test_expired_token_triggers_reauth — Expired token triggers re-authentication
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from urllib.error import URLError

# Allow importing helpers from the validation conftest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_api_client import AgentAPIClient, AgentAPIError
from conftest import make_mock_response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.tier4
@pytest.mark.offline
def test_missing_agent_id_exits_2(scripts_dir):
    """Running multi_turn_test_runner.py without --agent-id exits with code 2."""
    result = subprocess.run(
        [
            sys.executable,
            str(scripts_dir / "multi_turn_test_runner.py"),
            "--scenarios",
            "test.yaml",
        ],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SF_AGENT_ID": "",
            "SF_MY_DOMAIN": "",
            "SF_CONSUMER_KEY": "",
            "SF_CONSUMER_SECRET": "",
        },
    )

    assert result.returncode == 2
    stderr_lower = result.stderr.lower()
    assert "agent-id" in stderr_lower or "agent_id" in stderr_lower


@pytest.mark.tier4
@pytest.mark.offline
def test_nonexistent_scenario_file_exits_2(scripts_dir):
    """Running with a non-existent scenario file exits with code 2."""
    result = subprocess.run(
        [
            sys.executable,
            str(scripts_dir / "multi_turn_test_runner.py"),
            "--agent-id",
            "0XxRM0000004ABC",
            "--scenarios",
            "/nonexistent/path/scenarios.yaml",
        ],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SF_AGENT_ID": "0XxRM0000004ABC",
            "SF_MY_DOMAIN": "https://test.my.salesforce.com",
            "SF_CONSUMER_KEY": "key",
            "SF_CONSUMER_SECRET": "secret",
        },
    )

    assert result.returncode == 2
    stderr_lower = result.stderr.lower()
    assert "not found" in stderr_lower or "no such file" in stderr_lower


@pytest.mark.tier4
@pytest.mark.offline
def test_url_error_raises_agent_api_error(mock_urlopen, mock_client):
    """URLError from urlopen is wrapped as AgentAPIError with 'Connection error'."""
    mock_urlopen.side_effect = URLError("DNS resolution failed")

    with pytest.raises(AgentAPIError) as exc_info:
        mock_client._api_request(
            "GET",
            "https://api.salesforce.com/einstein/ai-agent/v1/test",
        )

    assert exc_info.value.status_code == 0
    assert "Connection error" in exc_info.value.message


@pytest.mark.tier4
@pytest.mark.offline
def test_expired_token_triggers_reauth(mock_urlopen):
    """An expired token triggers re-authentication before the actual API call.

    When _token_issued_at is more than 3300 seconds old, _ensure_authenticated()
    calls authenticate() first, then the actual request proceeds.
    urlopen should be called twice: once for auth, once for the API request.
    """
    client = AgentAPIClient(
        my_domain="https://test.my.salesforce.com",
        consumer_key="key",
        consumer_secret="secret",
    )
    # Pre-set an expired token (issued 4000 seconds ago)
    client._access_token = "expired-token"
    client._token_issued_at = time.time() - 4000

    # First call: authenticate() — returns fresh token
    auth_resp = make_mock_response(
        status=200,
        body={"access_token": "fresh-token-xyz"},
    )
    # Second call: actual _api_request — returns API data
    api_resp = make_mock_response(
        status=200,
        body={"result": "ok"},
    )
    mock_urlopen.side_effect = [auth_resp, api_resp]

    result = client._api_request(
        "GET",
        "https://api.salesforce.com/einstein/ai-agent/v1/test",
    )

    assert result == {"result": "ok"}
    assert mock_urlopen.call_count == 2
    assert client._access_token == "fresh-token-xyz"
