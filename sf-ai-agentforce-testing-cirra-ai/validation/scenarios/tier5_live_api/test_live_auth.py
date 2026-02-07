"""Tier 5 — Live OAuth authentication tests (4 points).

Tests real Client Credentials flow against a Salesforce org.
Requires SF_MY_DOMAIN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET, SF_AGENT_ID
environment variables (or equivalent CLI options).
"""

import pytest


# ---------------------------------------------------------------------------
# T5-AUTH-01: Token obtained (2 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
def test_token_obtained(live_client):
    """live_client has a non-empty _access_token after authentication."""
    assert live_client._access_token, (
        f"Expected _access_token to be set after authenticate(), got: {live_client._access_token!r}"
    )
    assert isinstance(live_client._access_token, str)


# ---------------------------------------------------------------------------
# T5-AUTH-02: Token is a real bearer string (2 pts)
# ---------------------------------------------------------------------------
@pytest.mark.tier5
@pytest.mark.live_api
def test_token_is_string(live_client):
    """The access token is a str instance with length > 10."""
    token = live_client._access_token
    assert isinstance(token, str), f"Expected str, got {type(token).__name__}"
    assert len(token) > 10, f"Token suspiciously short ({len(token)} chars): {token!r}"
