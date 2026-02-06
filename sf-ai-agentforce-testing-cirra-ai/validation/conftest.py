"""
Shared pytest fixtures for sf-ai-agentforce-testing validation.

Provides:
- Mock urllib fixtures (replace network calls)
- Pre-authenticated AgentAPIClient fixtures
- Mock AgentSession and TurnResult factories
- YAML scenario builders
- Custom markers and CLI options for tiered testing

Usage:
    @pytest.mark.tier1
    @pytest.mark.offline
    def test_client_defaults(mock_urlopen):
        # Uses mocked urllib — never hits network
        pass

    @pytest.mark.tier5
    @pytest.mark.live_api
    def test_real_auth(live_client):
        # Uses real Salesforce credentials
        pass
"""

import io
import json
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

# Add skill scripts to path
SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_ROOT / "hooks" / "scripts"
TEMPLATES_DIR = SKILL_ROOT / "templates"
sys.path.insert(0, str(SCRIPTS_DIR))

from agent_api_client import (
    AgentAPIClient,
    AgentSession,
    AgentMessage,
    TurnResult,
    AgentAPIError,
    parse_variables,
    _parse_messages,
)


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "tier1: Tier 1 - API Client Unit Tests (25 pts)")
    config.addinivalue_line("markers", "tier2: Tier 2 - Test Runner Unit Tests (25 pts)")
    config.addinivalue_line("markers", "tier3: Tier 3 - Template Validation (15 pts)")
    config.addinivalue_line("markers", "tier4: Tier 4 - Negative & Error Tests (15 pts)")
    config.addinivalue_line("markers", "tier5: Tier 5 - Live API Tests (20 pts)")
    config.addinivalue_line("markers", "offline: Test uses only local fixtures (no network)")
    config.addinivalue_line("markers", "live_api: Test requires live Salesforce API")
    config.addinivalue_line("markers", "slow: Test is slow-running")


def pytest_collection_modifyitems(config, items):
    """Apply skip logic based on CLI flags."""
    offline = config.getoption("--offline", default=False)
    tier_filter = config.getoption("--tier", default=None)

    for item in items:
        # Skip live_api tests when --offline
        if offline and "live_api" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Skipping live API tests (--offline)"))

        # Skip non-matching tiers when --tier specified
        if tier_filter:
            tier_marker = f"tier{tier_filter.replace('T', '').replace('t', '')}"
            if tier_marker not in item.keywords:
                item.add_marker(pytest.mark.skip(reason=f"Skipping (--tier {tier_filter})"))


def pytest_addoption(parser):
    """Add custom CLI options."""
    parser.addoption("--offline", action="store_true", default=False,
                     help="Run only offline tests (skip T5 live API)")
    parser.addoption("--tier", action="store", default=None,
                     help="Run specific tier only (T1, T2, T3, T4, T5)")
    parser.addoption("--my-domain", action="store", default=None,
                     help="Salesforce My Domain for T5 live tests")
    parser.addoption("--consumer-key", action="store", default=None,
                     help="ECA Consumer Key for T5 live tests")
    parser.addoption("--consumer-secret", action="store", default=None,
                     help="ECA Consumer Secret for T5 live tests")
    parser.addoption("--agent-id", action="store", default=None,
                     help="BotDefinition ID for T5 live tests")


# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def scripts_dir() -> Path:
    """Path to hooks/scripts/ directory."""
    return SCRIPTS_DIR


@pytest.fixture(scope="session")
def templates_dir() -> Path:
    """Path to templates/ directory."""
    return TEMPLATES_DIR


@pytest.fixture(scope="session")
def scenario_registry() -> dict:
    """Load scenario_registry.json configuration."""
    registry_path = Path(__file__).parent / "scenario_registry.json"
    with open(registry_path) as f:
        return json.load(f)


# =============================================================================
# Mock urllib Fixtures
# =============================================================================

def make_mock_response(status: int = 200, body: Any = None, headers: dict = None):
    """
    Create a mock urllib response object.

    Args:
        status: HTTP status code
        body: Response body (will be JSON-encoded if dict/list)
        headers: Optional response headers

    Returns:
        MagicMock mimicking urllib response context manager
    """
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.code = status

    if body is None:
        body = {}
    if isinstance(body, (dict, list)):
        raw_body = json.dumps(body).encode("utf-8")
    elif isinstance(body, str):
        raw_body = body.encode("utf-8")
    else:
        raw_body = body

    mock_resp.read.return_value = raw_body
    mock_resp.headers = headers or {}
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def make_http_error(code: int = 400, body: Any = None, url: str = "https://test"):
    """
    Create a mock urllib HTTPError.

    Args:
        code: HTTP status code
        body: Error response body
        url: Request URL

    Returns:
        HTTPError instance
    """
    if body is None:
        body = {"error": "test_error", "error_description": "Test error"}
    if isinstance(body, (dict, list)):
        raw = json.dumps(body).encode("utf-8")
    elif isinstance(body, str):
        raw = body.encode("utf-8")
    else:
        raw = body

    return HTTPError(
        url=url,
        code=code,
        msg=f"HTTP {code}",
        hdrs={},
        fp=io.BytesIO(raw),
    )


@pytest.fixture
def mock_urlopen():
    """
    Patch urllib.request.urlopen for the agent_api_client module.

    Usage:
        def test_something(mock_urlopen):
            mock_urlopen.return_value = make_mock_response(200, {"access_token": "tok123"})
            client = AgentAPIClient(...)
            client.authenticate()
    """
    with patch("agent_api_client.urllib.request.urlopen") as mock:
        yield mock


# =============================================================================
# Mock Client Fixtures
# =============================================================================

@pytest.fixture
def mock_client():
    """
    AgentAPIClient with pre-set access token (bypasses authenticate()).

    The client has a valid token so _ensure_authenticated() is a no-op.
    """
    client = AgentAPIClient(
        my_domain="https://test.my.salesforce.com",
        consumer_key="test-consumer-key",
        consumer_secret="test-consumer-secret",
    )
    client._access_token = "mock-access-token-12345"
    client._token_issued_at = __import__("time").time()
    return client


@pytest.fixture
def mock_session(mock_client):
    """
    AgentSession with a fake session_id, backed by mock_client.
    """
    return AgentSession(
        client=mock_client,
        session_id="test-session-id-abc123",
        initial_messages=[
            AgentMessage(
                type="Inform",
                id="greeting-001",
                message="Hello! How can I help you today?",
            )
        ],
    )


# =============================================================================
# TurnResult & AgentMessage Factories
# =============================================================================

@pytest.fixture
def sample_agent_messages():
    """Factory for AgentMessage lists."""
    def _factory(
        messages: List[Dict] = None,
        default_type: str = "Inform",
    ) -> List[AgentMessage]:
        if messages is None:
            messages = [{"message": "Hello, how can I help you?"}]
        result = []
        for msg in messages:
            result.append(AgentMessage(
                type=msg.get("type", default_type),
                id=msg.get("id", f"msg-{len(result)+1:03d}"),
                message=msg.get("message", ""),
                feedback_id=msg.get("feedback_id", ""),
                plan_id=msg.get("plan_id", ""),
                is_content_safe=msg.get("is_content_safe", True),
                result=msg.get("result", []),
                cited_references=msg.get("cited_references", []),
                raw=msg.get("raw", {}),
            ))
        return result
    return _factory


@pytest.fixture
def sample_turn_result(sample_agent_messages):
    """Factory for TurnResult with configurable messages."""
    def _factory(
        user_message: str = "Hello",
        agent_text: str = "Hello, how can I help you?",
        message_type: str = "Inform",
        sequence_id: int = 1,
        elapsed_ms: float = 150.0,
        error: str = None,
        messages: List[Dict] = None,
        has_escalation: bool = False,
        has_action_result: bool = False,
    ) -> TurnResult:
        if messages is None:
            msgs = [{"message": agent_text, "type": message_type}]
            if has_escalation:
                msgs.append({"type": "Escalation", "message": "Transferring to agent..."})
            if has_action_result:
                msgs[0]["result"] = [{"field": "value"}]
        else:
            msgs = messages

        return TurnResult(
            sequence_id=sequence_id,
            user_message=user_message,
            agent_messages=sample_agent_messages(msgs),
            raw_response={"messages": msgs},
            elapsed_ms=elapsed_ms,
            error=error,
        )
    return _factory


# =============================================================================
# YAML Scenario Fixtures
# =============================================================================

@pytest.fixture
def mock_yaml_scenario():
    """Factory for YAML scenario dicts matching the template structure."""
    def _factory(
        name: str = "test_scenario",
        description: str = "A test scenario",
        pattern: str = "topic_re_matching",
        turns: List[Dict] = None,
        session_variables: List[Dict] = None,
    ) -> Dict:
        if turns is None:
            turns = [
                {
                    "user": "Hello",
                    "expect": {
                        "response_not_empty": True,
                    },
                },
                {
                    "user": "I need help with my order",
                    "expect": {
                        "response_not_empty": True,
                        "topic_contains": "order",
                    },
                },
            ]
        scenario = {
            "name": name,
            "description": description,
            "pattern": pattern,
            "priority": "high",
            "turns": turns,
        }
        if session_variables:
            scenario["session_variables"] = session_variables
        return scenario
    return _factory


# =============================================================================
# Temp Directory Fixtures
# =============================================================================

@pytest.fixture
def temp_output_dir():
    """Temporary directory with cleanup for test output."""
    temp_dir = tempfile.mkdtemp(prefix="agent_test_validation_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# Live API Fixtures (T5)
# =============================================================================

@pytest.fixture(scope="session")
def live_credentials(request) -> Dict[str, str]:
    """
    Salesforce credentials from CLI options or environment variables.

    Skips test if no credentials available.
    """
    my_domain = (
        request.config.getoption("--my-domain")
        or os.environ.get("SF_MY_DOMAIN", "")
    )
    consumer_key = (
        request.config.getoption("--consumer-key")
        or os.environ.get("SF_CONSUMER_KEY", "")
    )
    consumer_secret = (
        request.config.getoption("--consumer-secret")
        or os.environ.get("SF_CONSUMER_SECRET", "")
    )
    agent_id = (
        request.config.getoption("--agent-id")
        or os.environ.get("SF_AGENT_ID", "")
    )

    if not all([my_domain, consumer_key, consumer_secret, agent_id]):
        pytest.skip(
            "Live credentials not available. Set SF_MY_DOMAIN, SF_CONSUMER_KEY, "
            "SF_CONSUMER_SECRET, SF_AGENT_ID env vars or pass --my-domain, "
            "--consumer-key, --consumer-secret, --agent-id CLI options."
        )

    return {
        "my_domain": my_domain,
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "agent_id": agent_id,
    }


@pytest.fixture(scope="session")
def live_client(live_credentials) -> AgentAPIClient:
    """
    Authenticated AgentAPIClient for T5 live tests.

    Authenticates once per session and reuses the token.
    """
    client = AgentAPIClient(
        my_domain=live_credentials["my_domain"],
        consumer_key=live_credentials["consumer_key"],
        consumer_secret=live_credentials["consumer_secret"],
    )
    client.authenticate()
    return client
