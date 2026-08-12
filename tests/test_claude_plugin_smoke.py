"""Smoke tests for the committed Claude plugin at plugins/cirra-ai-sf."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "plugins" / "cirra-ai-sf"


def test_claude_plugin_manifest_present_and_valid():
    plugin_json = PLUGIN / ".claude-plugin" / "plugin.json"
    assert plugin_json.is_file()
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "cirra-ai-sf"
    assert data.get("version")
    assert data.get("skills") in ("./skills", "./skills/")


def test_claude_plugin_mcp_config():
    mcp_path = PLUGIN / ".mcp.json"
    assert mcp_path.is_file()
    data = json.loads(mcp_path.read_text())
    servers = data["mcpServers"]
    assert "cirra-ai" in servers
    assert servers["cirra-ai"]["url"] == "https://mcp.cirra.ai/mcp"
    # Claude-native .mcp.json must not embed credentials
    blob = mcp_path.read_text().lower()
    for needle in ("authorization", "api_key", "apikey", "bearer ", "password"):
        assert needle not in blob


def test_claude_plugin_hooks_present():
    hooks_json = PLUGIN / "hooks" / "hooks.json"
    assert hooks_json.is_file()
    data = json.loads(hooks_json.read_text())
    assert "hooks" in data
    assert (PLUGIN / "hooks" / "pre-mcp-validate.py").is_file()


def test_claude_plugin_bundles_skills():
    skills_dir = PLUGIN / "skills"
    assert skills_dir.is_dir()
    skill_names = sorted(p.name for p in skills_dir.iterdir() if (p / "SKILL.md").is_file())
    # Core suite — provisioning may or may not be mirrored; require the published set
    required = {
        "sf-apex",
        "sf-audit",
        "sf-data",
        "sf-diagram",
        "sf-flow",
        "sf-help-fetch",
        "sf-kugamon",
        "sf-lwc",
        "sf-metadata",
        "sf-orders",
        "sf-permissions",
        "sf-provisioning",
    }
    missing = required - set(skill_names)
    assert not missing, f"Claude plugin missing skills: {sorted(missing)}"


def test_claude_plugin_paths_stay_inside_root():
    root = PLUGIN.resolve()
    for path in root.rglob("*"):
        if path.is_symlink():
            target = path.resolve(strict=False)
            target.relative_to(root)
        else:
            path.resolve(strict=False).relative_to(root)


def test_marketplace_version_matches_plugin():
    plugin_version = json.loads(
        (PLUGIN / ".claude-plugin" / "plugin.json").read_text()
    )["version"]
    marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert marketplace["metadata"]["version"] == plugin_version
    entry = next(p for p in marketplace["plugins"] if p["name"] == "cirra-ai-sf")
    assert entry["version"] == plugin_version
