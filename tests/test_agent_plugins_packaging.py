"""Tests for the Agent Plugins 1.0 portable package (AGENT-3)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "scripts" / "schemas" / "agent-plugins" / "1.0.0"


@pytest.fixture(scope="module")
def agent_plugins_dist():
    subprocess.check_call(
        [sys.executable, str(REPO_ROOT / "scripts" / "package_openai.py")],
        cwd=REPO_ROOT,
    )
    subprocess.check_call(
        ["bash", str(REPO_ROOT / "scripts" / "package-agent-plugins.sh")],
        cwd=REPO_ROOT,
    )
    dist = REPO_ROOT / "dist" / "agent-plugins"
    assert dist.is_dir()
    return dist


def test_agent_plugins_layout(agent_plugins_dist: Path):
    assert (agent_plugins_dist / "plugin.json").is_file()
    assert (agent_plugins_dist / "mcp.json").is_file()
    assert (agent_plugins_dist / "skills").is_dir()
    # Separate-artifact decision: Claude-specific files stay out of this zip
    assert not (agent_plugins_dist / ".claude-plugin").exists()
    assert not (agent_plugins_dist / "hooks").exists()
    assert not (agent_plugins_dist / ".mcp.json").exists()


def test_plugin_json_schema(agent_plugins_dist: Path):
    schema = json.loads((SCHEMA_DIR / "plugin.schema.json").read_text())
    plugin = json.loads((agent_plugins_dist / "plugin.json").read_text())
    jsonschema.validate(instance=plugin, schema=schema)
    assert plugin["$schema"].endswith("/1.0.0/plugin.schema.json")
    assert plugin["name"] == "cirra-ai-sf"
    assert "skills" not in plugin
    assert "mcpServers" not in plugin
    assert plugin["extensions"]["ai.cirra"]["status"] == "beta"
    assert (agent_plugins_dist / "ai.cirra" / "README.md").is_file()


def test_mcp_json_schema_and_cirra_server(agent_plugins_dist: Path):
    schema = json.loads((SCHEMA_DIR / "mcp.schema.json").read_text())
    mcp = json.loads((agent_plugins_dist / "mcp.json").read_text())
    jsonschema.validate(instance=mcp, schema=schema)
    server = mcp["mcpServers"]["cirra-ai"]
    assert server["type"] == "streamable-http"
    assert server["url"] == "https://mcp.cirra.ai/mcp"
    assert "headers" not in server


def test_validate_agent_plugins_script_passes(agent_plugins_dist: Path):
    subprocess.check_call(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_agent_plugins.py"),
            "--dist",
            str(agent_plugins_dist),
        ],
        cwd=REPO_ROOT,
    )


def test_validator_rejects_wrong_transport(tmp_path: Path, agent_plugins_dist: Path):
    # Copy minimal broken package
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "plugin.json").write_text((agent_plugins_dist / "plugin.json").read_text())
    mcp = json.loads((agent_plugins_dist / "mcp.json").read_text())
    mcp["mcpServers"]["cirra-ai"]["type"] = "streamableHttp"
    (broken / "mcp.json").write_text(json.dumps(mcp))
    skills = broken / "skills" / "sf-apex"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\nname: sf-apex\ndescription: x\n---\n\n# x\n")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_agent_plugins.py"),
            "--dist",
            str(broken),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "streamable-http" in result.stdout
