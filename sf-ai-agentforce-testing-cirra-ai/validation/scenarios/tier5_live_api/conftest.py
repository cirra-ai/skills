"""Tier 5 local fixtures — live API test helpers."""
import pytest
from agent_api_client import AgentAPIClient


@pytest.fixture(scope="session")
def live_agent_id(live_credentials) -> str:
    """Agent ID from live credentials."""
    return live_credentials["agent_id"]


@pytest.fixture(scope="session")
def live_authenticated_client(live_client) -> AgentAPIClient:
    """Alias for the authenticated live client."""
    return live_client
