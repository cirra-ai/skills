#!/usr/bin/env python3
"""
PreToolUse hook adapter for Apex MCP deployment validation.

Fires before metadata_create, metadata_update, or tooling_api_dml calls.
Extracts the Apex code body from the MCP payload and validates it using
the 150-point static analysis pipeline.

Decisions:
  - CRITICAL/HIGH issues (SOQL/DML in loops, injection)  → deny deployment
  - Score < 67% (< 100/150)                              → allow with warning
  - Pass                                                 → allow with score summary
  - Non-Apex type or validator unavailable               → allow silently

To disable validation for a project, create a file named
.no-apex-validation in the project root ($CLAUDE_PROJECT_DIR).
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

THRESHOLD_PCT = 67  # block advisory below this percentage


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


def main() -> int:
    # Opt-out flag file
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir and os.path.exists(os.path.join(project_dir, ".no-apex-validation")):
        print(json.dumps(_allow()))
        return 0

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        print(json.dumps(_allow()))
        return 0

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Strip mcp__<server>__ prefix → base tool name
    base_tool = re.sub(r"^mcp__[^_]+__", "", tool_name)

    validator_input = {"tool": base_tool, "params": tool_input}

    try:
        from mcp_validator import ApexMCPValidator

        result = ApexMCPValidator().validate(validator_input)
    except (ImportError, Exception):
        # Validator unavailable — allow through silently
        print(json.dumps(_allow()))
        return 0

    status = result.get("status", "")

    # Not an Apex type — skip
    if status in ("skipped", "error"):
        print(json.dumps(_allow()))
        return 0

    # Scored result
    score = result.get("score", result.get("overall_score", 0))
    max_score = result.get("max_score", result.get("total_max", 150))
    full_name = result.get("full_name", "class")
    issues = result.get("issues", [])
    critical_issues = result.get("critical_issues", [])
    all_issues = critical_issues + issues
    pct = (score / max_score * 100) if max_score > 0 else 0

    # Critical/High issues → deny
    blocking = [i for i in all_issues if i.get("severity") in ("CRITICAL", "HIGH")]
    if blocking:
        lines = []
        for issue in blocking[:5]:
            loc = f" (line {issue['line']})" if issue.get("line") else ""
            lines.append(f"• {issue['message']}{loc}")
        if len(blocking) > 5:
            lines.append(f"• ...and {len(blocking) - 5} more critical issues")

        reason = (
            f"Apex validation blocked deployment of '{full_name}' "
            f"(score: {score}/{max_score}, {pct:.0f}%).\n\n"
            f"Critical issues must be fixed before deploying:\n"
            + "\n".join(lines)
        )
        print(json.dumps(_deny(reason)))
        return 0

    # Below threshold — allow with advisory warning
    if pct < THRESHOLD_PCT:
        top = all_issues[:4]
        issue_lines = [f"• {i['message']}" for i in top]
        if len(all_issues) > 4:
            issue_lines.append(f"• ...and {len(all_issues) - 4} more issues")
        summary = "\n".join(issue_lines)

        context = (
            f"⚠️ Apex score below threshold for '{full_name}': "
            f"{score}/{max_score} ({pct:.0f}% — threshold is {THRESHOLD_PCT}%). "
            f"Consider fixing before deploying:\n{summary}"
        )
        print(json.dumps(_allow(context)))
        return 0

    # Pass — allow with score summary
    if pct >= 90:
        stars = "⭐⭐⭐⭐⭐"
    elif pct >= 75:
        stars = "⭐⭐⭐⭐"
    else:
        stars = "⭐⭐⭐"

    print(json.dumps(_allow(f"✅ Apex validation passed for '{full_name}': {score}/{max_score} {stars}")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
