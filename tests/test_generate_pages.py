"""Tests for scripts/generate-pages.py plugin and skill discovery."""

import json
from pathlib import Path

import pytest

# Import the module under test
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "generate_pages",
    Path(__file__).resolve().parent.parent / "scripts" / "generate-pages.py",
)
generate_pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generate_pages)


@pytest.fixture
def fake_repo(tmp_path):
    """Create a minimal repo structure for testing."""

    def _create(*, num_skills=2, include_plugins_dir=True):
        """Build a fake repo with plugins/ and skills/ directories.

        Args:
            num_skills: how many skill directories to create under skills/
            include_plugins_dir: whether to create the plugins/ directory
        """
        if include_plugins_dir:
            plugin_dir = tmp_path / "plugins" / "my-plugin"
            plugin_meta = plugin_dir / ".claude-plugin"
            plugin_meta.mkdir(parents=True)
            (plugin_meta / "plugin.json").write_text(json.dumps({
                "name": "my-plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "keywords": ["test"],
            }))

        for i in range(num_skills):
            skill = tmp_path / "skills" / f"my-plugin-skill-{i}"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"# Skill {i}")
            (skill / "README.md").write_text(f"# my-plugin-skill-{i}\n\nA test skill.")

        return tmp_path

    return _create


def test_find_plugins_in_plugins_dir(fake_repo):
    """Plugins under plugins/<name>/ are discovered."""
    repo_root = fake_repo()

    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = repo_root
        plugins = generate_pages.find_plugins()
    finally:
        generate_pages.REPO_ROOT = original

    assert len(plugins) == 1
    assert plugins[0]["name"] == "my-plugin"


def test_find_skills_from_top_level(fake_repo):
    """Skills are discovered from the top-level skills/ directory."""
    repo_root = fake_repo(num_skills=3)

    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = repo_root
        skills = generate_pages.find_skills()
    finally:
        generate_pages.REPO_ROOT = original

    assert len(skills) == 3
    assert skills[0]["name"] == "my-plugin-skill-0"


def test_find_skills_reads_description(fake_repo):
    """Skill description is extracted from README.md first paragraph."""
    repo_root = fake_repo(num_skills=1)

    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = repo_root
        skills = generate_pages.find_skills()
    finally:
        generate_pages.REPO_ROOT = original

    assert skills[0]["description"] == "A test skill."


def test_find_plugins_empty_repo(tmp_path):
    """No plugins found when plugins/ directory doesn't exist."""
    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = tmp_path
        plugins = generate_pages.find_plugins()
    finally:
        generate_pages.REPO_ROOT = original

    assert plugins == []


def test_find_skills_empty_repo(tmp_path):
    """No skills found when skills/ directory doesn't exist."""
    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = tmp_path
        skills = generate_pages.find_skills()
    finally:
        generate_pages.REPO_ROOT = original

    assert skills == []


def test_find_plugins_skips_spaces(tmp_path):
    """Directories with spaces in the name are skipped."""
    bad_dir = tmp_path / "plugins" / "bad plugin"
    meta = bad_dir / ".claude-plugin"
    meta.mkdir(parents=True)
    (meta / "plugin.json").write_text(json.dumps({"name": "bad plugin"}))

    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = tmp_path
        plugins = generate_pages.find_plugins()
    finally:
        generate_pages.REPO_ROOT = original

    assert plugins == []


def test_skills_independent_of_plugins(fake_repo):
    """Skills are found even without a plugins/ directory."""
    repo_root = fake_repo(num_skills=2, include_plugins_dir=False)

    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = repo_root
        plugins = generate_pages.find_plugins()
        skills = generate_pages.find_skills()
    finally:
        generate_pages.REPO_ROOT = original

    assert plugins == []
    assert len(skills) == 2
