#!/usr/bin/env python3
"""Validate dist/openai packages against ChatGPT/Codex packaging rules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "dist" / "openai"
CONFIG_PATH = REPO_ROOT / "scripts" / "openai-package-config.yaml"

ALLOWED_FM_KEYS = {"name", "description"}
UNSUPPORTED_FM_KEYS = {"plugin", "argument-hint", "hooks", "metadata"}


def load_budgets() -> dict:
    text = CONFIG_PATH.read_text()
    if yaml is not None:
        return (yaml.safe_load(text) or {}).get("budgets", {})
    budgets = {}
    in_budgets = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip() == "budgets:":
            in_budgets = True
            continue
        if in_budgets:
            if line and not line[0].isspace():
                break
            if ":" in line:
                k, v = line.strip().split(":", 1)
                budgets[k.strip()] = int(v.strip())
    return budgets


def parse_frontmatter(skill_md: Path) -> tuple[set[str], dict]:
    content = skill_md.read_text()
    if not content.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = content.index("\n---\n", 4)
    fm_text = content[4:end]
    keys = {
        line.split(":")[0].strip()
        for line in fm_text.splitlines()
        if line and not line[0].isspace() and ":" in line
    }
    if yaml is not None:
        data = yaml.safe_load(fm_text) or {}
    else:
        data = {}
    return keys, data


def referenced_paths(skill_dir: Path, skill_md: Path) -> list[str]:
    """Collect relative paths referenced from SKILL.md and openai.yaml."""
    refs: list[str] = []
    text = skill_md.read_text()
    # markdown links and bare path mentions to references/ scripts/ assets/
    for match in re.finditer(
        r"(?:references|scripts|assets)/[A-Za-z0-9_./\-]+", text
    ):
        refs.append(match.group(0).rstrip(").,;`\"'"))
    yaml_path = skill_dir / "agents" / "openai.yaml"
    if yaml_path.exists():
        for match in re.finditer(r"\./(assets/[A-Za-z0-9_./\-]+)", yaml_path.read_text()):
            refs.append(match.group(1))
    return sorted(set(refs))


def dir_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def validate(strict_lines: bool = False) -> int:
    """Validate dist/openai.

    SKILL.md line count defaults to warning-only: ChatGPT previously accepted
    several skills over the progressive-disclosure guideline. Size/file-count/
    frontmatter remain hard failures.
    """
    errors: list[str] = []
    warnings: list[str] = []
    budgets = load_budgets()
    max_lines = budgets.get("max_skill_md_lines", 550)
    max_files = budgets.get("max_files_per_skill", 80)
    max_bytes = budgets.get("max_bytes_per_skill", 450000)
    max_plugin = budgets.get("max_plugin_bytes", 6000000)

    if not DIST.is_dir():
        print(f"error: {DIST} does not exist — run scripts/package-openai.sh first", file=sys.stderr)
        return 1

    required = [
        DIST / ".codex-plugin" / "plugin.json",
        DIST / ".mcp.json",
        DIST / "manifest.json",
        DIST / "skills",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(REPO_ROOT)}")

    manifest = {}
    if (DIST / "manifest.json").exists():
        manifest = json.loads((DIST / "manifest.json").read_text())

    plugin_bytes = dir_size(DIST)
    if plugin_bytes > max_plugin:
        errors.append(
            f"plugin size {plugin_bytes} exceeds budget {max_plugin}"
        )

    skills_dir = DIST / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            rel = skill_dir.relative_to(REPO_ROOT)
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                errors.append(f"{rel}: missing SKILL.md")
                continue

            try:
                keys, data = parse_frontmatter(skill_md)
            except Exception as exc:
                errors.append(f"{rel}: invalid frontmatter ({exc})")
                continue

            bad = keys & UNSUPPORTED_FM_KEYS
            if bad:
                errors.append(f"{rel}: unsupported frontmatter keys: {sorted(bad)}")
            unexpected = keys - ALLOWED_FM_KEYS
            if unexpected:
                errors.append(f"{rel}: unexpected frontmatter keys: {sorted(unexpected)}")
            if "name" not in data or "description" not in data:
                # yaml may be missing; still require keys present in raw
                if "name" not in keys or "description" not in keys:
                    errors.append(f"{rel}: frontmatter must include name and description")

            line_count = len(skill_md.read_text().splitlines())
            if line_count > max_lines:
                msg = f"{rel}: SKILL.md has {line_count} lines (budget {max_lines})"
                if strict_lines:
                    errors.append(msg)
                else:
                    warnings.append(msg)

            file_count = sum(1 for p in skill_dir.rglob("*") if p.is_file())
            if file_count > max_files:
                errors.append(
                    f"{rel}: {file_count} files exceeds budget {max_files}"
                )

            size = dir_size(skill_dir)
            if size > max_bytes:
                errors.append(
                    f"{rel}: size {size} bytes exceeds budget {max_bytes}"
                )

            if not (skill_dir / "assets" / "icon.svg").exists():
                errors.append(f"{rel}: missing assets/icon.svg")
            if not (skill_dir / "agents" / "openai.yaml").exists():
                errors.append(f"{rel}: missing agents/openai.yaml")

            for ref in referenced_paths(skill_dir, skill_md):
                # Require packaged references/ targets. Asset templates may be
                # intentionally omitted from the slim distro. scripts/ links
                # sometimes point at repo-root helpers that are not part of the
                # skill package — warn instead of failing.
                if ref.startswith("assets/") and ref != "assets/icon.svg":
                    continue
                candidate = skill_dir / ref
                if candidate.exists():
                    continue
                if ref.startswith("scripts/"):
                    warnings.append(f"{rel}: referenced script not packaged: {ref}")
                    continue
                if ref.startswith("references/"):
                    errors.append(f"{rel}: referenced path missing: {ref}")


            # Forbidden leftovers
            for forbidden in ("README.md", "tests", "fixtures", "icon-large.png", "icon-small.png"):
                if (skill_dir / forbidden).exists():
                    errors.append(f"{rel}: must not include {forbidden}")

            # Manifest entry
            skills_meta = manifest.get("skills") or {}
            if skill_dir.name not in skills_meta:
                errors.append(f"manifest.json missing skill entry: {skill_dir.name}")

    for msg in warnings:
        print(f"warn:  {msg}")
    for msg in errors:
        print(f"error: {msg}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"✓ dist/openai OK ({len(warnings)} warning(s))")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict-lines",
        action="store_true",
        help="Fail when SKILL.md exceeds the line budget (default: warn only)",
    )
    args = parser.parse_args()
    sys.exit(validate(strict_lines=args.strict_lines))


if __name__ == "__main__":
    main()
