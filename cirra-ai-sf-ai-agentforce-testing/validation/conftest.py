"""
Shared pytest fixtures for sf-ai-agentforce-testing validation.

Provides:
- Path fixtures for scripts and templates directories
- Custom markers for tiered testing
"""

import json
import pytest
from pathlib import Path

# Skill paths
SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_ROOT / "hooks" / "scripts"
TEMPLATES_DIR = SKILL_ROOT / "templates"


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "tier3: Tier 3 - Template Validation (15 pts)")
    config.addinivalue_line("markers", "offline: Test uses only local fixtures (no network)")


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
