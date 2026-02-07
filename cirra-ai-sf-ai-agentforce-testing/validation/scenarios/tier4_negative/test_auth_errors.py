"""
Tier 4 — Authentication Error Tests (3 points)

Tests that authentication errors (HTTP 401, 403, malformed responses)
are handled correctly by AgentAPIClient.authenticate().

Tests:
    1. test_http_401_error — 401 raises AgentAPIError with status_code=401
    2. test_http_403_error — 403 raises AgentAPIError with "Authentication failed"
    3. test_malformed_token_response — Non-JSON 200 raises JSONDecodeError
    4. test_error_description_surfaced — error_description from body appears in message
"""

import json
import sys
from pathlib import Path

import pytest

# Allow importing helpers from the validation conftest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_api_client import AgentAPIClient, AgentAPIError
from conftest import make_mock_response, make_http_error


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.tier4
@pytest.mark.offline
def test_http_401_error(mock_urlopen):
    """HTTP 401 from token endpoint raises AgentAPIError with status_code=401."""
    error_body = {
        "error": "invalid_client",
        "error_description": "Invalid credentials",
    }
    mock_urlopen.side_effect = make_http_error(
        code=401,
        body=error_body,
        url="https://test.my.salesforce.com/services/oauth2/token",
    )

    client = AgentAPIClient(
        my_domain="https://test.my.salesforce.com",
        consumer_key="bad-key",
        consumer_secret="bad-secret",
    )

    with pytest.raises(AgentAPIError) as exc_info:
        client.authenticate()

    assert exc_info.value.status_code == 401
    assert "Authentication failed" in exc_info.value.message


@pytest.mark.tier4
@pytest.mark.offline
def test_http_403_error(mock_urlopen):
    """HTTP 403 from token endpoint raises AgentAPIError with 'Authentication failed'."""
    error_body = {
        "error": "forbidden",
        "error_description": "Forbidden",
    }
    mock_urlopen.side_effect = make_http_error(
        code=403,
        body=error_body,
        url="https://test.my.salesforce.com/services/oauth2/token",
    )

    client = AgentAPIClient(
        my_domain="https://test.my.salesforce.com",
        consumer_key="key",
        consumer_secret="secret",
    )

    with pytest.raises(AgentAPIError) as exc_info:
        client.authenticate()

    assert exc_info.value.status_code == 403
    assert "Authentication failed" in exc_info.value.message


@pytest.mark.tier4
@pytest.mark.offline
def test_malformed_token_response(mock_urlopen):
    """Non-JSON 200 response from token endpoint raises json.JSONDecodeError.

    The authenticate() method does json.loads(resp.read().decode()) inside the
    try block. A 200 response with HTML body is not caught by the HTTPError
    handler, so json.JSONDecodeError propagates unhandled.
    """
    mock_urlopen.return_value = make_mock_response(
        status=200,
        body="<html>Error</html>",
    )

    client = AgentAPIClient(
        my_domain="https://test.my.salesforce.com",
        consumer_key="key",
        consumer_secret="secret",
    )

    with pytest.raises(json.JSONDecodeError):
        client.authenticate()


@pytest.mark.tier4
@pytest.mark.offline
def test_error_description_surfaced(mock_urlopen):
    """error_description from the OAuth error body is surfaced in AgentAPIError.message."""
    error_body = {
        "error": "invalid_grant",
        "error_description": "Session expired",
    }
    mock_urlopen.side_effect = make_http_error(
        code=400,
        body=error_body,
        url="https://test.my.salesforce.com/services/oauth2/token",
    )

    client = AgentAPIClient(
        my_domain="https://test.my.salesforce.com",
        consumer_key="key",
        consumer_secret="secret",
    )

    with pytest.raises(AgentAPIError) as exc_info:
        client.authenticate()

    assert "Session expired" in exc_info.value.message
