"""
Tier 1: AgentAPIClient._api_request() retry logic tests.

Tests successful requests, retry on 429/500/URLError, re-auth on 401,
no retry on 4xx (except 401/429), max retries exceeded, and empty
response body handling.

Points: 5
"""

import sys
from pathlib import Path

import pytest
from unittest.mock import patch
from urllib.error import URLError

# Allow importing helpers from the validation conftest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_api_client import AgentAPIClient, AgentAPIError
from conftest import make_mock_response, make_http_error


def _make_authed_client(retry_count: int = 1) -> AgentAPIClient:
    """Create a pre-authenticated client with the given retry_count."""
    client = AgentAPIClient(
        my_domain="https://test.my.salesforce.com",
        consumer_key="ck",
        consumer_secret="cs",
        retry_count=retry_count,
    )
    client._access_token = "tok-valid"
    client._token_issued_at = __import__("time").time()
    return client


@pytest.mark.tier1
@pytest.mark.offline
class TestApiRequest:
    """AgentAPIClient._api_request() behaviour."""

    def test_successful_request(self, mock_urlopen):
        """Successful 200 response returns parsed JSON dict."""
        mock_urlopen.return_value = make_mock_response(200, {"sessionId": "sess-001"})
        client = _make_authed_client()

        result = client._api_request("POST", "https://api.salesforce.com/test")

        assert result == {"sessionId": "sess-001"}

    def test_retry_on_429(self, mock_urlopen):
        """429 (rate limit) triggers a retry; second attempt succeeds."""
        mock_urlopen.side_effect = [
            make_http_error(429, {"error": "rate_limit"}),
            make_mock_response(200, {"ok": True}),
        ]
        client = _make_authed_client(retry_count=1)

        with patch("agent_api_client.time.sleep"):
            result = client._api_request("GET", "https://api.salesforce.com/test")

        assert result == {"ok": True}
        assert mock_urlopen.call_count == 2

    def test_retry_on_500(self, mock_urlopen):
        """500 (server error) triggers a retry; second attempt succeeds."""
        mock_urlopen.side_effect = [
            make_http_error(500, {"error": "internal"}),
            make_mock_response(200, {"recovered": True}),
        ]
        client = _make_authed_client(retry_count=1)

        with patch("agent_api_client.time.sleep"):
            result = client._api_request("POST", "https://api.salesforce.com/test")

        assert result == {"recovered": True}
        assert mock_urlopen.call_count == 2

    def test_reauth_on_401(self, mock_urlopen):
        """401 triggers re-authentication then retries the original request."""
        # Sequence: 1) original call -> 401, 2) re-auth call -> token, 3) retry -> success
        mock_urlopen.side_effect = [
            make_http_error(401, {"error": "INVALID_SESSION_ID"}),
            make_mock_response(200, {"access_token": "new-tok"}),  # re-auth
            make_mock_response(200, {"data": "finally"}),  # retry
        ]
        client = _make_authed_client(retry_count=1)

        with patch("agent_api_client.time.sleep"):
            result = client._api_request("GET", "https://api.salesforce.com/test")

        assert result == {"data": "finally"}
        # 1 original + 1 auth + 1 retry = 3 urlopen calls
        assert mock_urlopen.call_count == 3

    def test_no_retry_on_400(self, mock_urlopen):
        """400 (bad request) raises immediately without retry."""
        mock_urlopen.side_effect = make_http_error(400, {"error": "bad_request"})
        client = _make_authed_client(retry_count=1)

        with pytest.raises(AgentAPIError) as exc_info:
            client._api_request("POST", "https://api.salesforce.com/test")

        assert exc_info.value.status_code == 400
        assert mock_urlopen.call_count == 1

    def test_max_retries_exceeded(self, mock_urlopen):
        """When all retry attempts fail, AgentAPIError is raised."""
        mock_urlopen.side_effect = [
            make_http_error(429, {"error": "rate_limit"}),
            make_http_error(429, {"error": "rate_limit"}),
        ]
        client = _make_authed_client(retry_count=1)

        with patch("agent_api_client.time.sleep"):
            with pytest.raises(AgentAPIError) as exc_info:
                client._api_request("GET", "https://api.salesforce.com/test")

        assert exc_info.value.status_code == 429
        assert mock_urlopen.call_count == 2

    def test_url_error_retry(self, mock_urlopen):
        """URLError triggers a retry; second attempt succeeds."""
        mock_urlopen.side_effect = [
            URLError("Connection refused"),
            make_mock_response(200, {"ok": True}),
        ]
        client = _make_authed_client(retry_count=1)

        with patch("agent_api_client.time.sleep"):
            result = client._api_request("GET", "https://api.salesforce.com/test")

        assert result == {"ok": True}
        assert mock_urlopen.call_count == 2

    def test_empty_response_body(self, mock_urlopen):
        """Empty response body returns empty dict."""
        mock_urlopen.return_value = make_mock_response(200, "")
        client = _make_authed_client()

        # Empty string body -> read() returns b"" which is falsy
        # The code does: if resp_body: return json.loads(...) else return {}
        # make_mock_response with body="" encodes to b"" -> read returns b""
        # resp_body = b"".decode("utf-8") = "" which is falsy
        result = client._api_request("DELETE", "https://api.salesforce.com/test")

        assert result == {}
