"""Smoke tests for the ChatGPT/Codex packaging pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def openai_dist(tmp_path_factory):
    """Build dist/openai once for this module (writes under repo dist/)."""
    # Package script owns dist/openai; run it.
    subprocess.check_call(
        [sys.executable, str(REPO_ROOT / "scripts" / "package_openai.py")],
        cwd=REPO_ROOT,
    )
    dist = REPO_ROOT / "dist" / "openai"
    assert dist.is_dir()
    return dist


def test_openai_dist_has_codex_manifest(openai_dist: Path):
    plugin_json = openai_dist / ".codex-plugin" / "plugin.json"
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "cirra-ai-sf"
    assert data["skills"] == "./skills/"
    assert (openai_dist / ".mcp.json").exists()
    assert (openai_dist / "manifest.json").exists()


def test_openai_skills_have_minimal_frontmatter(openai_dist: Path):
    for skill_md in (openai_dist / "skills").glob("*/SKILL.md"):
        text = skill_md.read_text()
        assert text.startswith("---\n")
        end = text.index("\n---\n", 4)
        fm = text[4:end]
        keys = {
            line.split(":")[0].strip()
            for line in fm.splitlines()
            if line and not line[0].isspace() and ":" in line
        }
        assert keys <= {"name", "description"}, f"{skill_md}: {keys}"
        assert "plugin" not in keys
        assert "metadata" not in keys
        assert "argument-hint" not in keys


def test_openai_skills_ship_svg_icon_and_openai_yaml(openai_dist: Path):
    for skill_dir in (openai_dist / "skills").iterdir():
        if not skill_dir.is_dir():
            continue
        assert (skill_dir / "assets" / "icon.svg").is_file()
        assert (skill_dir / "agents" / "openai.yaml").is_file()
        assert not (skill_dir / "README.md").exists()
        assert not (skill_dir / "tests").exists()
        assert not (skill_dir / "assets" / "icon-large.png").exists()


def test_help_fetch_has_openai_yaml_in_source():
    path = REPO_ROOT / "skills" / "sf-help-fetch" / "agents" / "openai.yaml"
    assert path.is_file()
    text = path.read_text()
    assert "icon.svg" in text
    assert "display_name" in text


def test_validate_openai_dist_passes(openai_dist: Path):
    subprocess.check_call(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_openai_dist.py")],
        cwd=REPO_ROOT,
    )
