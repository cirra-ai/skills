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
    """Falls back to README.md first paragraph when SKILL.md has no description."""
    repo_root = fake_repo(num_skills=1)

    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = repo_root
        skills = generate_pages.find_skills()
    finally:
        generate_pages.REPO_ROOT = original

    assert skills[0]["description"] == "A test skill."


def test_find_skills_prefers_skill_md_description(tmp_path):
    """The SKILL.md frontmatter description wins over the README paragraph, and a
    trailing folded-scalar ``Usage:`` line is stripped for the card."""
    skill = tmp_path / "skills" / "sf-demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: sf-demo\n"
        "metadata:\n"
        "  version: 2.1.0\n"
        "description: >\n"
        "  Read the real thing across both surfaces.\n"
        "  It works without a browser.\n"
        "  Usage: /sf-demo [url]\n"
        "---\n\n# sf-demo\n"
    )
    (skill / "README.md").write_text("# sf-demo\n\nREADME paragraph (should be ignored).")

    original = generate_pages.REPO_ROOT
    try:
        generate_pages.REPO_ROOT = tmp_path
        skills = generate_pages.find_skills()
    finally:
        generate_pages.REPO_ROOT = original

    assert skills[0]["description"] == (
        "Read the real thing across both surfaces. It works without a browser."
    )
    assert skills[0]["version"] == "2.1.0"


def test_skill_frontmatter_description_inline():
    """An inline (quoted) description value is read as-is."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "SKILL.md"
        p.write_text('---\nname: x\ndescription: "Just one line."\n---\n# x\n')
        assert generate_pages._skill_frontmatter_description(p) == "Just one line."


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


def test_desc_preview_none_when_short():
    """Text at or under the preview limit is not truncated."""
    short = "x" * generate_pages.CARD_DESC_PREVIEW_LIMIT
    assert generate_pages._desc_preview(short) is None
    assert generate_pages._desc_preview("short") is None


def test_desc_preview_breaks_on_word_boundary():
    """Over-limit text is cut at the last space and ends with an ellipsis."""
    text = ("word " * 50).strip()  # 249 chars
    preview = generate_pages._desc_preview(text)
    assert preview is not None
    assert preview.endswith("\u2026")
    stem = preview[:-1]
    assert stem.endswith("word")
    assert text.startswith(stem)
    assert len(stem) <= generate_pages.CARD_DESC_PREVIEW_LIMIT


def test_card_desc_html_short_is_plain_div():
    """Short descriptions stay a simple div with the full text."""
    html = generate_pages._card_desc_html("A test skill.")
    assert html == '<div class="card-desc">A test skill.</div>'
    assert "details" not in html
    assert "Show more" not in html


def test_card_desc_html_long_is_expandable():
    """Long descriptions keep the full text behind a Show more control."""
    full = (
        "Salesforce CMS content expert. Use whenever the user wants to create, "
        "update, clone, publish, unpublish, tag, or search CMS managed content, "
        "manage CMS workspaces (spaces), folders, or channels, or publish to a site."
    )
    html = generate_pages._card_desc_html(full)
    assert '<details class="card-desc card-desc--expandable">' in html
    assert f'<div class="card-desc-full">{full}</div>' in html
    assert html.index("</summary>") < html.index('class="card-desc-full"')
    assert "card-desc-full" not in html[: html.index("</summary>")]
    assert "Show more" in html
    assert "Show less" in html
    preview = generate_pages._desc_preview(full)
    assert preview is not None
    assert f'<span class="card-desc-preview">{preview}</span>' in html


def test_card_desc_html_escapes_markup():
    """Preview and full text both escape HTML special characters."""
    full = "A <script>alert(1)</script> & more " + ("word " * 40)
    html = generate_pages._card_desc_html(full)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp; more" in html


def test_skill_card_includes_full_description():
    """Skill cards no longer drop the tail of a long SKILL.md description."""
    full = ("Describe the skill for agents and humans. " * 8).strip()
    assert len(full) > generate_pages.CARD_DESC_PREVIEW_LIMIT
    html = generate_pages._skill_card({
        "name": "sf-cms",
        "description": full,
        "version": "1.0.1",
        "keywords": ["cms"],
    })
    assert full in html
    assert "Show more" in html
    assert "sf-cms.zip" in html
    assert "sf-cms.skill" in html


def test_download_href_escapes_name():
    """Download href attributes escape special characters in the package name."""
    skill_html = generate_pages._skill_card({
        "name": 'sf-"cms"',
        "description": "Short.",
        "version": "1.0.1",
        "keywords": ["cms"],
    })
    assert 'href="./sf-&quot;cms&quot;.zip"' in skill_html
    assert 'href="./sf-&quot;cms&quot;.skill"' in skill_html
    assert 'href="./sf-"cms".skill"' not in skill_html
    assert 'href="./sf-"cms".zip"' not in skill_html

    plugin_html = generate_pages._plugin_card({
        "name": 'plug<"in"',
        "description": "Short.",
        "version": "1.0.0",
        "keywords": ["test"],
        "is_featured": False,
    })
    assert 'href="./plug&lt;&quot;in&quot;.zip"' in plugin_html


def test_plugin_card_short_description_stays_simple():
    """Plugin cards with short copy stay a non-expandable div."""
    html = generate_pages._plugin_card({
        "name": "cirra-ai-sf",
        "description": "Salesforce admin plugin for use with the Cirra AI MCP Server.",
        "version": "2.5.0",
        "keywords": ["apex"],
        "is_featured": False,
    })
    assert '<div class="card-desc">' in html
    assert "card-desc--expandable" not in html


def test_skill_card_defaults_to_zip_with_skill_alt():
    """Skill cards download .zip by default and offer .skill for Claude."""
    original = generate_pages.DL_BASE
    try:
        generate_pages.DL_BASE = "."
        html = generate_pages._skill_card({
            "name": "sf-demo",
            "description": "A test skill.",
            "keywords": ["demo"],
            "version": "1.0.0",
        })
    finally:
        generate_pages.DL_BASE = original

    assert 'href="./sf-demo.zip"' in html
    assert 'href="./sf-demo.skill"' in html
    btn_start = html.index("btn btn-outline")
    btn = html[btn_start:html.index("</a>", btn_start)]
    assert ".zip" in btn
    assert ".skill" not in btn


def test_plugin_card_still_uses_zip():
    """Plugin cards keep downloading the plugin zip."""
    original = generate_pages.DL_BASE
    try:
        generate_pages.DL_BASE = "."
        html = generate_pages._plugin_card({
            "name": "my-plugin",
            "description": "Test plugin",
            "keywords": ["test"],
            "version": "1.0.0",
            "is_featured": False,
        })
    finally:
        generate_pages.DL_BASE = original

    assert 'href="./my-plugin.zip"' in html


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
