#!/usr/bin/env python3
"""Validate dist/agent-plugins against Agent Plugins Specification 1.0.0.

Checks:
  - plugin.json / mcp.json exist and validate against vendored JSON Schemas
  - skills/ immediate children contain SKILL.md
  - no package paths escape the plugin root (symlinks, .. components)
  - mcp.json uses streamable-http for Cirra AI and embeds no credentials
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIST = REPO_ROOT / "dist" / "agent-plugins"
SCHEMA_DIR = REPO_ROOT / "scripts" / "schemas" / "agent-plugins" / "1.0.0"

PLUGIN_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

SECRET_KEY_RE = re.compile(
    r"(authorization|api[_-]?key|token|secret|password|bearer)", re.I
)


def load_schema(name: str) -> dict:
    path = SCHEMA_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"missing vendored schema: {path}")
    return json.loads(path.read_text())


def validate_json_schema(instance: dict, schema: dict, label: str, errors: list[str]) -> None:
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"{label}: schema validation failed: {exc.message}")


def path_escapes_root(root: Path, candidate: Path) -> bool:
    try:
        resolved = candidate.resolve(strict=False)
        root_resolved = root.resolve(strict=True)
        resolved.relative_to(root_resolved)
        return False
    except Exception:
        return True


def check_containment(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            target = path.resolve(strict=False)
            if path_escapes_root(root, target):
                errors.append(
                    f"symlink escapes plugin root: {path.relative_to(root)} -> {target}"
                )
            continue
        if path_escapes_root(root, path):
            errors.append(f"path escapes plugin root: {path}")


def check_relative_path_field(root: Path, value: str, label: str, errors: list[str]) -> None:
    if not value:
        return
    if value.startswith("./"):
        candidate = (root / value[2:]).resolve(strict=False)
        if path_escapes_root(root, candidate):
            errors.append(f"{label}: path escapes plugin root: {value}")
        return
    if value.startswith("../") or "/../" in value or value == "..":
        errors.append(f"{label}: path uses parent traversal: {value}")


def check_mcp_semantics(root: Path, mcp: dict, errors: list[str]) -> None:
    if mcp.get("$schema") != MCP_SCHEMA_ID:
        errors.append(f"mcp.json $schema must be {MCP_SCHEMA_ID}")
    servers = mcp.get("mcpServers") or {}
    if "cirra-ai" not in servers:
        errors.append("mcp.json missing mcpServers.cirra-ai")
        return
    server = servers["cirra-ai"]
    if server.get("type") != "streamable-http":
        errors.append(
            f"mcpServers.cirra-ai.type must be 'streamable-http', got {server.get('type')!r}"
        )
    if server.get("url") != "https://mcp.cirra.ai/mcp":
        errors.append(
            f"mcpServers.cirra-ai.url must be https://mcp.cirra.ai/mcp, got {server.get('url')!r}"
        )
    headers = server.get("headers") or {}
    for key, value in headers.items():
        if SECRET_KEY_RE.search(str(key)) or SECRET_KEY_RE.search(str(value)):
            errors.append(f"mcp.json must not embed credentials in headers ({key})")
    for name, entry in servers.items():
        for field in ("command", "cwd"):
            if field in entry and isinstance(entry[field], str):
                check_relative_path_field(
                    root, entry[field], f"mcpServers.{name}.{field}", errors
                )


def check_skills(root: Path, errors: list[str]) -> None:
    skills = root / "skills"
    if not skills.is_dir():
        errors.append("missing skills/ directory")
        return
    children = sorted(p for p in skills.iterdir() if not p.name.startswith("."))
    if not children:
        errors.append("skills/ has no skill directories")
    for child in children:
        if not child.is_dir():
            errors.append(f"skills/{child.name}: not a directory")
            continue
        if not (child / "SKILL.md").is_file():
            errors.append(f"skills/{child.name}: missing SKILL.md")


def validate(dist: Path) -> int:
    errors: list[str] = []

    if not dist.is_dir():
        print(
            f"error: {dist} does not exist — run scripts/package-agent-plugins.sh first",
            file=sys.stderr,
        )
        return 1

    plugin_path = dist / "plugin.json"
    mcp_path = dist / "mcp.json"
    if not plugin_path.is_file():
        errors.append("missing plugin.json")
    if not mcp_path.is_file():
        errors.append("missing mcp.json")

    plugin_schema = load_schema("plugin.schema.json")
    mcp_schema = load_schema("mcp.schema.json")

    plugin = None
    mcp = None
    if plugin_path.is_file():
        try:
            plugin = json.loads(plugin_path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"plugin.json: invalid JSON ({exc})")
        else:
            if plugin.get("$schema") != PLUGIN_SCHEMA_ID:
                errors.append(f"plugin.json $schema must be {PLUGIN_SCHEMA_ID}")
            validate_json_schema(plugin, plugin_schema, "plugin.json", errors)
            for forbidden in ("skills", "mcpServers"):
                if forbidden in plugin:
                    errors.append(f"plugin.json must not contain core field {forbidden!r}")

    if mcp_path.is_file():
        try:
            mcp = json.loads(mcp_path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"mcp.json: invalid JSON ({exc})")
        else:
            validate_json_schema(mcp, mcp_schema, "mcp.json", errors)
            check_mcp_semantics(dist, mcp, errors)

    if plugin and mcp:
        if "1.0.0" not in str(plugin.get("$schema", "")) or "1.0.0" not in str(
            mcp.get("$schema", "")
        ):
            errors.append("plugin.json and mcp.json must target Agent Plugins 1.0.0")

    check_skills(dist, errors)
    check_containment(dist, errors)

    for msg in errors:
        print(f"error: {msg}")
    if errors:
        print(f"\n{len(errors)} error(s)")
        return 1
    print("✓ dist/agent-plugins OK (Agent Plugins 1.0.0)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist",
        type=Path,
        default=DEFAULT_DIST,
        help="Path to agent-plugins dist directory",
    )
    args = parser.parse_args()
    sys.exit(validate(args.dist.resolve()))


if __name__ == "__main__":
    main()
