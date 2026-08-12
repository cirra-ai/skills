#!/usr/bin/env python3
"""Build a ChatGPT / Codex plugin tree under dist/openai/ from skills/.

Produces:
  dist/openai/
    .codex-plugin/plugin.json
    .mcp.json
    manifest.json          # skill versions + provenance
    assets/icon.svg
    skills/<name>/
      SKILL.md             # name + description only
      agents/openai.yaml
      assets/icon.svg
      references/ ...
      scripts/ ...
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML may be missing in minimal envs
    yaml = None


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "scripts" / "openai-package-config.yaml"
OUT_DIR = REPO_ROOT / "dist" / "openai"
PLUGIN_NAME = "cirra-ai-sf"
PLUGIN_VERSION_PATH = REPO_ROOT / "plugins" / "cirra-ai-sf" / ".claude-plugin" / "plugin.json"


def load_config() -> dict:
    text = CONFIG_PATH.read_text()
    if yaml is not None:
        return yaml.safe_load(text)
    # Minimal fallback parser for our simple YAML shape
    return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict:
    """Tiny YAML subset parser for this config file (no external deps)."""
    data: dict = {"budgets": {}, "exclude_always": [], "exclude_by_skill": {}}
    section = None
    current_skill = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        s = line.strip()
        if indent == 0 and s.endswith(":") and not s.startswith("-"):
            section = s[:-1]
            current_skill = None
            continue
        if section == "budgets" and ":" in s:
            k, v = s.split(":", 1)
            data["budgets"][k.strip()] = int(v.strip())
            continue
        if section == "exclude_always" and s.startswith("- "):
            data["exclude_always"].append(s[2:].strip().strip("'\""))
            continue
        if section == "exclude_by_skill":
            if indent == 2 and s.endswith(":"):
                current_skill = s[:-1]
                data["exclude_by_skill"][current_skill] = []
                continue
            if current_skill and s.startswith("- "):
                data["exclude_by_skill"][current_skill].append(s[2:].strip().strip("'\""))
    return data


def git_source_commit() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
            ).strip()
        )
    except Exception:
        return "unknown"


def read_frontmatter(skill_md: Path) -> tuple[dict, str]:
    content = skill_md.read_text()
    if not content.startswith("---\n"):
        raise ValueError(f"{skill_md}: missing YAML frontmatter")
    end = content.index("\n---\n", 4)
    fm_text = content[4:end]
    body = content[end + 5 :]
    # Prefer PyYAML for nested metadata; fall back to name/description only.
    if yaml is not None:
        fm = yaml.safe_load(fm_text) or {}
    else:
        fm = _parse_frontmatter_lite(fm_text)
    return fm, body


def _parse_frontmatter_lite(fm_text: str) -> dict:
    fm: dict = {}
    key = None
    buf: list[str] = []
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        if line and not line[0].isspace() and ":" in line:
            if key is not None:
                fm[key] = _coerce_fm_value(buf)
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest in (">", "|", ""):
                buf = []
            else:
                buf = [rest]
                fm[key] = _coerce_fm_value(buf)
                key = None
                buf = []
        else:
            buf.append(line.strip())
    if key is not None:
        fm[key] = _coerce_fm_value(buf)
    return fm


def _coerce_fm_value(buf: list[str]):
    if not buf:
        return ""
    if len(buf) == 1:
        return buf[0]
    return " ".join(buf)


def write_minimal_skill_md(dst: Path, name: str, description: str, body: str) -> None:
    desc = description.strip()
    # Prefer folded block for multi-line descriptions
    if "\n" in desc or len(desc) > 80:
        fm = f"---\nname: {name}\ndescription: >\n"
        # wrap description roughly
        for para in re.split(r"\s*\n\s*", desc):
            fm += f"  {para.strip()}\n"
        fm += "---\n\n"
    else:
        fm = f"---\nname: {name}\ndescription: {desc}\n---\n\n"
    dst.write_text(fm + body.lstrip("\n"))


def should_exclude(rel: Path, patterns: list[str]) -> bool:
    rel_posix = rel.as_posix()
    name = rel.name
    for pat in patterns:
        pat = pat.strip()
        if not pat:
            continue
        if pat.startswith("*"):
            # suffix glob like *.pyc
            if name.endswith(pat[1:]):
                return True
            continue
        if rel_posix == pat or rel_posix.startswith(pat.rstrip("/") + "/"):
            return True
        if name == pat:
            return True
    return False


def copy_skill(skill_dir: Path, dest: Path, excludes: list[str]) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if should_exclude(rel, excludes):
            continue
        # Skip SKILL.md here; rewritten separately
        if rel.as_posix() == "SKILL.md":
            continue
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)

    # Always ship the SVG icon
    icon_src = REPO_ROOT / "shared" / "assets" / "icon.svg"
    assets = dest / "assets"
    assets.mkdir(exist_ok=True)
    shutil.copy2(icon_src, assets / "icon.svg")


def ensure_openai_yaml(skill_dest: Path, skill_name: str, display: str, short: str, prompt: str) -> None:
    agents = skill_dest / "agents"
    agents.mkdir(exist_ok=True)
    yaml_path = agents / "openai.yaml"
    if yaml_path.exists():
        text = yaml_path.read_text()
        text = text.replace("./assets/icon-small.png", "./assets/icon.svg")
        text = text.replace("./assets/icon-large.png", "./assets/icon.svg")
        # Drop icon_large if both point at same svg — keep both keys for compatibility
        yaml_path.write_text(text)
        return
    yaml_path.write_text(
        "interface:\n"
        f'  display_name: "{display}"\n'
        f'  short_description: "{short}"\n'
        '  icon_small: "./assets/icon.svg"\n'
        '  icon_large: "./assets/icon.svg"\n'
        '  brand_color: "#4068EB"\n'
        f'  default_prompt: "{prompt}"\n'
    )


def plugin_version() -> str:
    data = json.loads(PLUGIN_VERSION_PATH.read_text())
    return data.get("version", "0.0.0")


def build() -> dict:
    config = load_config()
    excludes_always = list(config.get("exclude_always", []))
    excludes_by_skill = config.get("exclude_by_skill", {})

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # Plugin root assets / manifests
    (OUT_DIR / "assets").mkdir()
    shutil.copy2(REPO_ROOT / "shared" / "assets" / "icon.svg", OUT_DIR / "assets" / "icon.svg")
    shutil.copy2(REPO_ROOT / "LICENSE", OUT_DIR / "LICENSE")

    version = plugin_version()
    codex_dir = OUT_DIR / ".codex-plugin"
    codex_dir.mkdir()
    plugin_json = {
        "name": PLUGIN_NAME,
        "version": version,
        "description": "Salesforce admin skills for ChatGPT and Codex via the Cirra AI MCP Server.",
        "author": {"name": "Cirra AI", "email": "info@cirra.ai", "url": "https://github.com/cirra-ai"},
        "homepage": "https://skills.cirra.ai/",
        "repository": "https://github.com/cirra-ai/skills",
        "license": "MIT",
        "keywords": ["salesforce", "cirra-ai", "apex", "flow", "mcp"],
        "skills": "./skills/",
        "mcpServers": "./.mcp.json",
        "interface": {
            "displayName": "Cirra AI Salesforce",
            "shortDescription": "Salesforce admin skills powered by Cirra AI",
            "brandColor": "#4068EB",
            "logo": "./assets/icon.svg",
            "composerIcon": "./assets/icon.svg",
            "defaultPrompt": [
                "Use Cirra AI skills to audit my Salesforce org",
                "Create a production-ready Salesforce Flow with sf-flow",
                "Build an Apex class with sf-apex best practices",
            ],
        },
    }
    (codex_dir / "plugin.json").write_text(json.dumps(plugin_json, indent=2) + "\n")

    mcp = {
        "mcpServers": {
            "cirra-ai": {
                "url": "https://mcp.cirra.ai/mcp"
            }
        }
    }
    (OUT_DIR / ".mcp.json").write_text(json.dumps(mcp, indent=2) + "\n")

    skills_out = OUT_DIR / "skills"
    skills_out.mkdir()
    manifest_skills: dict = {}

    for skill_md in sorted((REPO_ROOT / "skills").glob("*/SKILL.md")):
        skill_dir = skill_md.parent
        skill_name = skill_dir.name
        fm, body = read_frontmatter(skill_md)
        name = fm.get("name", skill_name)
        description = fm.get("description", "")
        if isinstance(description, str):
            description = " ".join(description.split())
        meta = fm.get("metadata") or {}
        skill_version = str(meta.get("version", "0.0.0"))

        excludes = excludes_always + list(excludes_by_skill.get(skill_name, []))
        dest = skills_out / skill_name
        copy_skill(skill_dir, dest, excludes)
        write_minimal_skill_md(dest / "SKILL.md", name, description, body)

        # Normalize / create openai.yaml
        short = description[:64].rstrip()
        if len(description) > 64:
            # keep within OpenAI short_description guidance when generating
            short = short[:61].rstrip() + "..."
        ensure_openai_yaml(
            dest,
            skill_name,
            display=f"Cirra AI {skill_name}",
            short=short if 25 <= len(short) <= 64 else f"Cirra AI skill for {skill_name}",
            prompt=f"Use ${skill_name} to complete this Salesforce task.",
        )

        # LICENSE fallback
        if not (dest / "LICENSE").exists():
            shutil.copy2(REPO_ROOT / "LICENSE", dest / "LICENSE")

        manifest_skills[skill_name] = {
            "version": skill_version,
            "path": f"skills/{skill_name}",
        }
        print(f"  packaged {skill_name} v{skill_version}")

    manifest = {
        "formatVersion": 1,
        "sourceCommit": git_source_commit(),
        "plugin": {"name": PLUGIN_NAME, "version": version},
        "skills": manifest_skills,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assemble",
        action="store_true",
        help="Run assemble.sh + sync shared assets before packaging",
    )
    args = parser.parse_args()
    if args.assemble:
        subprocess.check_call([str(REPO_ROOT / "scripts" / "assemble.sh")], cwd=REPO_ROOT)
        # Copy shared icon.svg into skill assets for source consistency
        icon = REPO_ROOT / "shared" / "assets" / "icon.svg"
        for skill_dir in (REPO_ROOT / "skills").iterdir():
            if (skill_dir / "SKILL.md").exists():
                assets = skill_dir / "assets"
                assets.mkdir(exist_ok=True)
                shutil.copy2(icon, assets / "icon.svg")

    print("=== Packaging OpenAI / ChatGPT plugin ===")
    build()
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
