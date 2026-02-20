#!/usr/bin/env python3
"""
Unified PreToolUse dispatcher for MCP deployment validation.

Routes metadata_create, metadata_update, and tooling_api_dml calls
to the correct domain validator (Apex or Flow) based on the metadata
type in the payload.

Decisions:
  - CRITICAL/HIGH issues   -> deny deployment
  - Score below threshold  -> allow with warning
  - Pass                   -> allow with score summary
  - Unrecognised type      -> allow silently
"""

import importlib.util
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_class(module_path: str, module_name: str, class_name: str):
    """Load a class from a specific file path, bypassing module cache."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    # Temporarily add the module's directory so its own imports resolve
    mod_dir = os.path.dirname(module_path)
    original_path = sys.path[:]
    sys.path.insert(0, mod_dir)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = original_path
    return getattr(mod, class_name)

# Domain thresholds
APEX_THRESHOLD_PCT = 67
FLOW_THRESHOLD_PCT = 80
FLOW_MAX_SCORE = 110


# ── Hook response helpers ────────────────────────────────────────────────


def _allow(context: str = "") -> dict:
    out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
    if context:
        out["hookSpecificOutput"]["additionalContext"] = context
    return out


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


# ── Domain routing ───────────────────────────────────────────────────────

APEX_TYPES = {"ApexClass", "ApexTrigger", "ApexComponent", "ApexPage"}
FLOW_TYPES = {"Flow", "FlowDefinition"}


def _detect_metadata_type(tool_input: dict) -> str:
    """Extract the metadata type from the MCP payload."""
    # metadata_create / metadata_update put type at top level
    mt = tool_input.get("type", "")
    if mt:
        return mt
    # tooling_api_dml uses sObject
    return tool_input.get("sObject", "")


def _route_apex(validator_input: dict) -> dict | None:
    """Run Apex MCP validator and return its result, or None on failure."""
    try:
        apex_mod = os.path.join(SCRIPT_DIR, "apex", "mcp_validator.py")
        ApexMCPValidator = _load_class(apex_mod, "apex_mcp_validator", "ApexMCPValidator")
        return ApexMCPValidator().validate(validator_input)
    except Exception:
        return None


def _route_flow(validator_input: dict) -> dict | None:
    """Run Flow MCP validator and return its result, or None on failure."""
    try:
        flow_mod = os.path.join(SCRIPT_DIR, "flow", "mcp_validator.py")
        FlowMCPValidator = _load_class(flow_mod, "flow_mcp_validator", "FlowMCPValidator")
        return FlowMCPValidator().validate(validator_input)
    except Exception:
        return None


# ── Issue collection (Flow-specific) ────────────────────────────────────


def _collect_flow_issues(result: dict) -> list:
    """Normalise issues from EnhancedFlowValidator and basic_flow_check formats."""
    issues = list(result.get("issues", []))
    for item in result.get("critical_issues", []):
        issues.append({
            "severity": item.get("severity", "CRITICAL"),
            "message": item.get("message", ""),
            "line": 0,
        })
    for item in result.get("warnings", []):
        issues.append({
            "severity": item.get("severity", "HIGH"),
            "message": item.get("message", ""),
            "line": 0,
        })
    for item in result.get("advisory_suggestions", []):
        issues.append({
            "severity": "INFO",
            "message": item if isinstance(item, str) else item.get("message", ""),
            "line": 0,
        })
    return issues


# ── Decision logic (shared) ─────────────────────────────────────────────


def _decide(result: dict, domain: str, threshold_pct: int) -> dict:
    """Apply deny / warn / allow logic to a scored validator result."""
    status = result.get("status", "")
    if status in ("skipped", "error"):
        return _allow()

    score = result.get("score", result.get("overall_score", 0))
    max_score = result.get("max_score", result.get("total_max", FLOW_MAX_SCORE if domain == "Flow" else 150))
    full_name = result.get("full_name", result.get("flow_name", domain.lower()))
    pct = (score / max_score * 100) if max_score > 0 else 0

    # Collect issues
    if domain == "Flow":
        all_issues = _collect_flow_issues(result)
    else:
        critical_issues = result.get("critical_issues", [])
        issues = result.get("issues", [])
        all_issues = critical_issues + issues

    # Critical/High -> deny
    blocking = [i for i in all_issues if i.get("severity") in ("CRITICAL", "HIGH")]
    if blocking:
        lines = []
        for issue in blocking[:5]:
            loc = f" (line {issue['line']})" if issue.get("line") else ""
            lines.append(f"• {issue['message']}{loc}")
        if len(blocking) > 5:
            lines.append(f"• ...and {len(blocking) - 5} more critical issues")

        reason = (
            f"{domain} validation blocked deployment of '{full_name}' "
            f"(score: {score}/{max_score}, {pct:.0f}%).\n\n"
            f"Critical issues must be fixed before deploying:\n"
            + "\n".join(lines)
        )
        return _deny(reason)

    # Below threshold -> allow with advisory warning
    if pct < threshold_pct:
        top = all_issues[:4]
        issue_lines = [f"• {i['message']}" for i in top]
        if len(all_issues) > 4:
            issue_lines.append(f"• ...and {len(all_issues) - 4} more issues")
        summary = "\n".join(issue_lines)

        context = (
            f"⚠️ {domain} score below threshold for '{full_name}': "
            f"{score}/{max_score} ({pct:.0f}% — threshold is {threshold_pct}%). "
            f"Consider fixing before deploying:\n{summary}"
        )
        return _allow(context)

    # Pass
    if pct >= 90:
        stars = "⭐⭐⭐⭐⭐"
    elif pct >= 75:
        stars = "⭐⭐⭐⭐"
    else:
        stars = "⭐⭐⭐"

    return _allow(f"✅ {domain} validation passed for '{full_name}': {score}/{max_score} {stars}")


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        print(json.dumps(_allow()))
        return 0

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Strip mcp__<server>__ prefix -> base tool name
    parts = tool_name.split("__", 2)
    base_tool = parts[2] if tool_name.startswith("mcp__") and len(parts) > 2 else tool_name

    validator_input = {"tool": base_tool, "params": tool_input}
    metadata_type = _detect_metadata_type(tool_input)

    # Route to the correct domain validator
    if metadata_type in APEX_TYPES:
        result = _route_apex(validator_input)
        if result is None:
            print(json.dumps(_allow()))
            return 0
        print(json.dumps(_decide(result, "Apex", APEX_THRESHOLD_PCT)))
        return 0

    if metadata_type in FLOW_TYPES:
        result = _route_flow(validator_input)
        if result is None:
            print(json.dumps(_allow()))
            return 0
        print(json.dumps(_decide(result, "Flow", FLOW_THRESHOLD_PCT)))
        return 0

    # Unrecognised type — allow silently (future: Data, LWC, etc.)
    print(json.dumps(_allow()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
