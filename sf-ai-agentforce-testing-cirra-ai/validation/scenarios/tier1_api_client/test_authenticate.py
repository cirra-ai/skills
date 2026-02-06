"""
Tier 1: AgentAPIClient.authenticate() tests.

Tests the OAuth Client Credentials flow, error handling for missing
credentials, HTTP errors, and malformed responses.

Points: 6
"""

import sys
from pathlib import Path

import pytest
from urllib.error import URLError

# Allow importing helpers from the validation conftest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_api_client import AgentAPIClient, AgentAPIError
from conftest import make_mock_response, make_http_error


@pytest.mark.tier1
@pytest.mark.offline
class TestAuthenticate:
    """AgentAPIClient.authenticate() behaviour."""

    def test_successful_auth(self, mock_urlopen):
        """Successful auth stores the token and returns it."""
        mock_urlopen.return_value = make_mock_response(
            200, {"access_token": "tok123"}
        )

        client = AgentAPIClient(
            my_domain="https://test.my.salesforce.com",
            consumer_key="ck",
            consumer_secret="cs",
        )
        token = client.authenticate()

        assert token == "tok123"
        assert client._access_token == "tok123"

    def test_token_issued_at_set(self, mock_urlopen):
        """After auth, _token_issued_at should be a positive timestamp."""
        mock_urlopen.return_value = make_mock_response(
            200, {"access_token": "tok123"}
        )

        client = AgentAPIClient(
            my_domain="https://test.my.salesforce.com",
            consumer_key="ck",
            consumer_secret="cs",
        )
        client.authenticate()

        assert client._token_issued_at > 0

    def test_missing_my_domain_raises(self):
        """authenticate() raises AgentAPIError when my_domain is empty."""
        client = AgentAPIClient(
            my_domain="",
            consumer_key="ck",
            consumer_secret="cs",
        )

        with pytest.raises(AgentAPIError, match="my_domain is required"):
            client.authenticate()

    def test_missing_consumer_key_raises(self):
        """authenticate() raises AgentAPIError when consumer_key is empty."""
        client = AgentAPIClient(
            my_domain="https://test.my.salesforce.com",
            consumer_key="",
            consumer_secret="cs",
        )

        with pytest.raises(AgentAPIError, match="consumer_key is required"):
            client.authenticate()

    def test_missing_consumer_secret_raises(self):
        """authenticate() raises AgentAPIError when consumer_secret is empty."""
        client = AgentAPIClient(
            my_domain="https://test.my.salesforce.com",
            consumer_key="ck",
            consumer_secret="",
        )

        with pytest.raises(AgentAPIError, match="consumer_secret is required"):
            client.authenticate()

    def test_http_error_during_auth(self, mock_urlopen):
        """HTTPError during auth is wrapped as AgentAPIError with the HTTP status."""
        mock_urlopen.side_effect = make_http_error(
            401, {"error": "invalid_client", "error_description": "Bad credentials"}
        )

        client = AgentAPIClient(
            my_domain="https://test.my.salesforce.com",
            consumer_key="ck",
            consumer_secret="cs",
        )

        with pytest.raises(AgentAPIError) as exc_info:
            client.authenticate()

        assert exc_info.value.status_code == 401

    def test_url_error_during_auth(self, mock_urlopen):
        """URLError during auth is wrapped as AgentAPIError."""
        mock_urlopen.side_effect = URLError("DNS failure")

        client = AgentAPIClient(
            my_domain="https://test.my.salesforce.com",
            consumer_key="ck",
            consumer_secret="cs",
        )

        with pytest.raises(AgentAPIError, match="Connection error during auth"):
            client.authenticate()

    def test_no_access_token_in_response(self, mock_urlopen):
        """Response without access_token raises AgentAPIError."""
        mock_urlopen.return_value = make_mock_response(
            200, {"instance_url": "https://something.salesforce.com"}
        )

        client = AgentAPIClient(
            my_domain="https://test.my.salesforce.com",
            consumer_key="ck",
            consumer_secret="cs",
        )

        with pytest.raises(AgentAPIError, match="No access_token"):
            client.authenticate()
