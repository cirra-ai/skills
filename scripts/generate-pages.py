#!/usr/bin/env python3
"""
Generates the docs/index.html downloads page.

Reads docs/index.html as a template and replaces placeholder comments with
auto-generated cards derived from plugin.json files and skill READMEs.

Placeholders in docs/index.html:
  <!-- @@PLUGIN_CARDS@@ -->  — replaced with one card per plugin
  <!-- @@SKILL_CARDS@@ -->   — replaced with one card per skill (skill-only zips)

Usage:
  # CI — overwrite docs/index.html with the generated page:
  bash scripts/generate-pages.sh

  # Local preview — open in the default browser (does not touch docs/index.html):
  bash scripts/generate-pages.sh --preview
  python3 scripts/generate-pages.py . --preview

  # stdout (for debugging or custom pipelines):
  python3 scripts/generate-pages.py [repo_root]

  # Generate with download links pointing to a specific release tag (e.g. "preview"):
  python3 scripts/generate-pages.py . --release-tag=next
"""

import json
import sys
import webbrowser
import tempfile
from pathlib import Path

_positional = [a for a in sys.argv[1:] if not a.startswith("--")]
REPO_ROOT = Path(_positional[0]).resolve() if _positional else Path.cwd()
PREVIEW = "--preview" in sys.argv
_release_tag_args = [a[len("--release-tag="):] for a in sys.argv if a.startswith("--release-tag=")]
RELEASE_TAG: str | None = _release_tag_args[0] if _release_tag_args else None
_dl_base_args = [a[len("--dl-base="):] for a in sys.argv if a.startswith("--dl-base=")]

# Base URL for download links.
# --dl-base=<url>  explicit override (e.g. "." to serve zips from the same CF Pages deployment)
# --release-tag=<tag>  point to a specific GitHub release
# (default)  resolve to the most recent published release via /latest/
if _dl_base_args:
    DL_BASE = _dl_base_args[0]
elif RELEASE_TAG:
    DL_BASE = f"https://github.com/cirra-ai/skills/releases/download/{RELEASE_TAG}"
else:
    DL_BASE = "https://github.com/cirra-ai/skills/releases/latest/download"

SUPPRESS_KEYWORDS = {"cirra-ai", "salesforce", "orchestration"}


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def find_plugins() -> list[dict]:
    """Scan repo for plugins via */.claude-plugin/plugin.json."""
    plugins = []
    for plugin_json_path in sorted(REPO_ROOT.glob("*/.claude-plugin/plugin.json")):
        plugin_dir = plugin_json_path.parent.parent
        if " " in plugin_dir.name:
            continue
        try:
            data = json.loads(plugin_json_path.read_text())
        except Exception as e:
            print(f"Warning: could not parse {plugin_json_path}: {e}", file=sys.stderr)
            continue

        keywords = [k for k in data.get("keywords", []) if k not in SUPPRESS_KEYWORDS]
        is_featured = "orchestration" in data.get("keywords", [])

        plugins.append({
            "name": data.get("name", plugin_dir.name),
            "version": data.get("version", ""),
            "description": data.get("description", ""),
            "keywords": keywords,
            "is_featured": is_featured,
            "skills": find_skills(plugin_dir),
        })

    # Featured plugins first, then alphabetical
    plugins.sort(key=lambda p: (0 if p["is_featured"] else 1, p["name"]))
    return plugins


def find_skills(plugin_dir: Path) -> list[dict]:
    """Find all skills inside a plugin directory."""
    skills = []
    for skill_md in sorted(plugin_dir.glob("skills/*/SKILL.md")):
        skill_dir = skill_md.parent
        name = skill_dir.name
        readme = skill_dir / "README.md"
        description = _readme_first_paragraph(readme) if readme.exists() else ""
        # Derive primary keyword from skill name (strip known prefixes)
        main_kw = name.removeprefix("cirra-ai-sf-").removeprefix("cirra-ai-")
        skills.append({
            "name": name,
            "description": description,
            "keywords": [main_kw] if main_kw and main_kw != name else [],
        })
    return skills


def _readme_first_paragraph(readme_path: Path) -> str:
    """Return the first paragraph of prose after the # heading."""
    lines = readme_path.read_text().splitlines()
    in_content = False
    para: list[str] = []
    for line in lines:
        if line.startswith("# "):
            in_content = True
            continue
        if not in_content:
            continue
        stripped = line.strip()
        if not stripped:
            if para:
                break
            continue
        if stripped.startswith("#"):
            break
        para.append(stripped)
    return " ".join(para)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _tags_html(keywords: list[str], version: str = "", extra: list[str] | None = None) -> str:
    tags = []
    if version:
        tags.append(f'<span class="tag">v{_esc(version)}</span>')
    for kw in keywords[:5]:
        tags.append(f'<span class="tag">{_esc(kw)}</span>')
    for kw in (extra or []):
        tags.append(f'<span class="tag">{_esc(kw)}</span>')
    return "\n            ".join(tags)


def _plugin_card(plugin: dict) -> str:
    name = _esc(plugin["name"])
    desc = _esc(plugin["description"])
    tags = _tags_html(plugin["keywords"], plugin["version"])
    dl_url = f"{DL_BASE}/{plugin['name']}.zip"
    cls = "card featured" if plugin["is_featured"] else "card"
    return f"""\
      <div class="{cls}">
        <div class="card-body">
          <div class="card-title">{name}</div>
          <div class="card-desc">{desc}</div>
          <div class="card-tags">
            {tags}
          </div>
        </div>
        <a class="btn btn-outline" href="{dl_url}">&#11015; Download</a>
      </div>"""


def _skill_card(skill: dict) -> str:
    name = _esc(skill["name"])
    desc = skill["description"]
    if len(desc) > 200:
        desc = desc[:197].rstrip() + "\u2026"
    desc = _esc(desc)
    tags = _tags_html(skill["keywords"], extra=["skill-only"])
    dl_url = f"{DL_BASE}/{skill['name']}-skill.zip"
    return f"""\
      <div class="card">
        <div class="card-body">
          <div class="card-title">{name}</div>
          <div class="card-desc">{desc}</div>
          <div class="card-tags">
            {tags}
          </div>
        </div>
        <a class="btn btn-outline" href="{dl_url}">&#11015; Download</a>
      </div>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate() -> str:
    template_path = REPO_ROOT / "docs" / "index.template.html"
    template = template_path.read_text()

    plugins = find_plugins()
    if not plugins:
        print("Warning: no plugins found!", file=sys.stderr)
    print(f"Found {len(plugins)} plugin(s): {[p['name'] for p in plugins]}", file=sys.stderr)

    all_skills = [s for p in plugins for s in p["skills"]]
    print(f"Found {len(all_skills)} skill(s): {[s['name'] for s in all_skills]}", file=sys.stderr)

    plugin_cards = "\n\n".join(_plugin_card(p) for p in plugins)
    skill_cards  = "\n\n".join(_skill_card(s) for s in all_skills)

    output = template.replace("      <!-- @@PLUGIN_CARDS@@ -->", plugin_cards)
    output = output.replace("      <!-- @@SKILL_CARDS@@ -->", skill_cards)

    if "<!-- @@PLUGIN_CARDS@@ -->" in output:
        print("Warning: @@PLUGIN_CARDS@@ placeholder not found/replaced!", file=sys.stderr)
    if "<!-- @@SKILL_CARDS@@ -->" in output:
        print("Warning: @@SKILL_CARDS@@ placeholder not found/replaced!", file=sys.stderr)

    return output


if __name__ == "__main__":
    html = generate()

    if PREVIEW:
        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", prefix="cirra-skills-preview-"
        ) as f:
            f.write(html)
            tmp = f.name
        print(f"Preview: file://{tmp}", file=sys.stderr)
        webbrowser.open(f"file://{tmp}")
    else:
        print(html, end="")
