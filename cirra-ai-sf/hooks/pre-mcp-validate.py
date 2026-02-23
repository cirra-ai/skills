#!/usr/bin/env python3
"""
Plugin-level PreToolUse hook dispatcher for cirra-ai-sf.

Reads the hook input from stdin, determines the metadata type, and
delegates to the appropriate sub-skill validator script.

Currently registered delegates:
  - cirra-ai-sf-apex: ApexClass, ApexTrigger
"""

import json
import os
import subprocess
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Map metadata types to their validator script (relative to _PLUGIN_ROOT).
# Add new entries here as sub-skills gain their own pre-deploy validators.
_DELEGATES: dict[str, str] = {
    "ApexClass":      "skills/cirra-ai-sf-apex/scripts/pre-mcp-validate.py",
    "ApexTrigger":    "skills/cirra-ai-sf-apex/scripts/pre-mcp-validate.py",
    "Flow":           "skills/cirra-ai-sf-flow/scripts/pre-mcp-validate.py",
    "FlowDefinition": "skills/cirra-ai-sf-flow/scripts/pre-mcp-validate.py",
}


def _allow() -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


def _metadata_type(tool_name: str, tool_input: dict) -> str:
    """Extract the metadata type from hook input fields."""
    parts = tool_name.split("__", 2)
    base_tool = parts[2] if tool_name.startswith("mcp__") and len(parts) > 2 else tool_name

    if base_tool in ("metadata_create", "metadata_update"):
        return tool_input.get("type", "")
    if base_tool == "tooling_api_dml":
        return tool_input.get("sObject", "")
    return ""


def main() -> int:
    try:
        raw = sys.stdin.buffer.read()
        hook_input = json.loads(raw)
    except Exception:
        print(json.dumps(_allow()))
        return 0

    metadata_type = _metadata_type(
        hook_input.get("tool_name", ""),
        hook_input.get("tool_input", {}),
    )

    delegate_script = _DELEGATES.get(metadata_type)
    if not delegate_script:
        print(json.dumps(_allow()))
        return 0

    script_path = os.path.join(_PLUGIN_ROOT, delegate_script)
    result = subprocess.run(
        [sys.executable, script_path],
        input=raw,
        capture_output=True,
    )

    output = result.stdout.strip()
    if output:
        print(output.decode("utf-8", errors="replace"))
    else:
        print(json.dumps(_allow()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
