#!/usr/bin/env python3
"""
MCP Validator CLI — Two-Tier Model
====================================

Command-line entry point for validating Cirra AI MCP tool call parameters.

Routes based on tool type:
  - soql_query / sobject_dml        -> Tier 1 (lightweight pass/fail)
  - metadata_create / metadata_update / tooling_api_dml -> Tier 2 (code deployment scoring)

Usage:
  # JSON from stdin
  echo '{"tool":"soql_query","params":{...}}' | python mcp_validator_cli.py

  # JSON from file
  python mcp_validator_cli.py input.json

  # Human-readable report (default: JSON)
  python mcp_validator_cli.py --format report < input.json
  python mcp_validator_cli.py --format json < input.json
"""

import json
import sys
from pathlib import Path

# Ensure mcp_validator is importable from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from mcp_validator import MCPOperationValidator


def format_tier1_report(result: dict) -> str:
    """Format Tier 1 (data params) result as a human-readable report."""
    lines = []

    tool = result.get("tool", "unknown")
    status = result.get("status", "unknown")
    errors = result.get("errors", [])
    warnings = result.get("warnings", [])

    status_label = "PASS" if status == "pass" else "FAIL"

    lines.append("=" * 60)
    lines.append("  MCP Pre-Flight Check (Tier 1: Data Params)")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Tool:   {tool}")
    lines.append(f"  Status: {status_label}")
    lines.append("")

    if errors:
        lines.append(f"  Errors ({len(errors)}):")
        lines.append("  " + "-" * 56)
        for err in errors:
            lines.append(f"  [ERR] {err['message']}")
        lines.append("")

    if warnings:
        lines.append(f"  Warnings ({len(warnings)}):")
        lines.append("  " + "-" * 56)
        for warn in warnings:
            lines.append(f"  [WRN] {warn['message']}")
        lines.append("")

    if not errors and not warnings:
        lines.append("  No issues found.")
        lines.append("")

    lines.append("=" * 60)

    if status == "fail":
        lines.append("  BLOCKED -- fix errors before executing")
    elif warnings:
        lines.append("  OK -- review warnings above")
    else:
        lines.append("  OK -- safe to proceed")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_tier2_report(result: dict) -> str:
    """Format Tier 2 (code deployment) result as a human-readable report."""
    lines = []

    tool = result.get("tool", "unknown")
    metadata_type = result.get("metadata_type", "unknown")
    full_name = result.get("full_name", "")
    validator = result.get("validator", "none")
    status = result.get("status", "unknown")

    lines.append("=" * 60)
    lines.append("  MCP Code Deployment Validation (Tier 2)")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Tool:          {tool}")
    lines.append(f"  Metadata Type: {metadata_type}")
    if full_name:
        lines.append(f"  Full Name:     {full_name}")
    lines.append(f"  Validator:     {validator}")
    lines.append(f"  Status:        {status}")
    lines.append("")

    if status == "skipped":
        lines.append(f"  {result.get('message', 'Skipped')}")
        lines.append("")
    elif status == "error":
        lines.append(f"  Error: {result.get('message', 'Unknown error')}")
        lines.append("")
    elif status == "scored":
        # Score info
        score = result.get("score", result.get("overall_score", 0))
        max_score = result.get("max_score", result.get("total_max", 0))
        rating = result.get("rating", "")

        lines.append(f"  Score:  {score}/{max_score}")
        lines.append(f"  Rating: {rating}")
        lines.append("")

        # Issues
        issues = result.get("issues", [])
        critical_issues = result.get("critical_issues", [])
        all_issues = critical_issues + issues

        if all_issues:
            lines.append("  Issues:")
            lines.append("  " + "-" * 56)
            for issue in all_issues[:15]:
                severity = issue.get("severity", "INFO")
                message = issue.get("message", "Unknown")
                icon = "ERR" if severity in ("CRITICAL", "error") else "WRN" if severity in ("WARNING", "warning") else "INF"
                line_num = issue.get("line", "")
                loc = f" (line {line_num})" if line_num else ""
                lines.append(f"  [{icon}] {message}{loc}")
            if len(all_issues) > 15:
                lines.append(f"  ... and {len(all_issues) - 15} more")
            lines.append("")

        # Note (fallback indicator)
        note = result.get("note", "")
        if note:
            lines.append(f"  Note: {note}")
            lines.append("")

    lines.append("=" * 60)

    if status == "scored":
        score = result.get("score", result.get("overall_score", 0))
        max_score = result.get("max_score", result.get("total_max", 150))
        critical = result.get("critical_issues", [])
        pct = (score / max_score * 100) if max_score > 0 else 0
        if critical:
            lines.append("  BLOCKED -- fix critical issues before deploying")
        elif pct >= 70:
            lines.append("  PASSED -- safe to deploy")
        else:
            lines.append("  REVIEW -- address issues before deploying")
    elif status == "skipped":
        lines.append("  SKIPPED -- no code validation needed")
    else:
        lines.append(f"  STATUS: {status}")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_report(result: dict) -> str:
    """Route to the appropriate report formatter based on tier."""
    tier = result.get("tier", "")
    if tier == "data_params":
        return format_tier1_report(result)
    elif tier == "code_deployment":
        return format_tier2_report(result)
    else:
        # Unknown tier — just format as JSON
        return json.dumps(result, indent=2)


def main():
    """Main entry point."""
    # Parse arguments
    fmt = "json"
    input_file = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        elif args[i] in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        elif not args[i].startswith("-"):
            input_file = args[i]
            i += 1
        else:
            print(f"Unknown argument: {args[i]}", file=sys.stderr)
            sys.exit(1)

    # Read input
    try:
        if input_file:
            with open(input_file, encoding="utf-8") as f:
                input_data = json.load(f)
        else:
            input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    # Validate
    validator = MCPOperationValidator()
    result = validator.validate(input_data)

    # Output
    if fmt == "report":
        print(format_report(result))
    else:
        print(json.dumps(result, indent=2))

    # Exit code
    tier = result.get("tier", "")
    if tier == "data_params":
        # Tier 1: exit 1 if fail
        sys.exit(1 if result.get("status") == "fail" else 0)
    elif tier == "code_deployment":
        # Tier 2: exit 1 if critical issues or low score
        if result.get("status") == "error":
            sys.exit(1)
        critical = result.get("critical_issues", [])
        if critical:
            sys.exit(1)
        score = result.get("score", result.get("overall_score", 0))
        max_score = result.get("max_score", result.get("total_max", 150))
        pct = (score / max_score * 100) if max_score > 0 else 0
        sys.exit(1 if pct < 50 else 0)
    else:
        # Unknown tool
        sys.exit(1)


if __name__ == "__main__":
    main()
