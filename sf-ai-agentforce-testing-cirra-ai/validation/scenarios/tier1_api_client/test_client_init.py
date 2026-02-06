"""
Tier 1: AgentAPIClient constructor tests.

Tests that __init__ correctly reads env vars, normalizes my_domain,
caps timeout, and accepts explicit overrides.

Points: 5
"""

import pytest
from agent_api_client import AgentAPIClient


@pytest.mark.tier1
@pytest.mark.offline
class TestClientInit:
    """AgentAPIClient.__init__ behaviour."""

    def test_defaults_from_env(self, monkeypatch):
        """Constructor picks up SF_MY_DOMAIN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET
        from env when no explicit args are provided."""
        monkeypatch.setenv("SF_MY_DOMAIN", "env-domain.my.salesforce.com")
        monkeypatch.setenv("SF_CONSUMER_KEY", "env-key-123")
        monkeypatch.setenv("SF_CONSUMER_SECRET", "env-secret-456")

        client = AgentAPIClient()

        assert client.my_domain == "https://env-domain.my.salesforce.com"
        assert client._consumer_key == "env-key-123"
        assert client._consumer_secret == "env-secret-456"

    def test_explicit_args_override_env(self, monkeypatch):
        """Explicit constructor args take precedence over env vars."""
        monkeypatch.setenv("SF_MY_DOMAIN", "env-domain.my.salesforce.com")
        monkeypatch.setenv("SF_CONSUMER_KEY", "env-key")
        monkeypatch.setenv("SF_CONSUMER_SECRET", "env-secret")

        client = AgentAPIClient(
            my_domain="https://explicit.my.salesforce.com",
            consumer_key="explicit-key",
            consumer_secret="explicit-secret",
        )

        assert client.my_domain == "https://explicit.my.salesforce.com"
        assert client._consumer_key == "explicit-key"
        assert client._consumer_secret == "explicit-secret"

    def test_https_prefix_added(self, monkeypatch):
        """my_domain without https:// gets the prefix added."""
        monkeypatch.delenv("SF_MY_DOMAIN", raising=False)
        monkeypatch.delenv("SF_CONSUMER_KEY", raising=False)
        monkeypatch.delenv("SF_CONSUMER_SECRET", raising=False)

        client = AgentAPIClient(my_domain="test.my.salesforce.com")

        assert client.my_domain == "https://test.my.salesforce.com"

    def test_https_prefix_not_doubled(self, monkeypatch):
        """my_domain that already has https:// does not get doubled."""
        monkeypatch.delenv("SF_MY_DOMAIN", raising=False)

        client = AgentAPIClient(my_domain="https://test.my.salesforce.com")

        assert client.my_domain == "https://test.my.salesforce.com"

    def test_timeout_capped_at_120(self, monkeypatch):
        """Timeout values above 120 are capped at 120 (API max)."""
        monkeypatch.delenv("SF_MY_DOMAIN", raising=False)

        client = AgentAPIClient(timeout=300)

        assert client._timeout == 120

    def test_trailing_slash_stripped(self, monkeypatch):
        """Trailing slash on my_domain is removed."""
        monkeypatch.delenv("SF_MY_DOMAIN", raising=False)

        client = AgentAPIClient(my_domain="https://test.my.salesforce.com/")

        assert client.my_domain == "https://test.my.salesforce.com"
