#!/usr/bin/env python3
"""
MCP Validator CLI
==================

Command-line entry point for validating Cirra AI MCP tool call parameters
against the 130-point scoring system.

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


def format_report(result: dict) -> str:
    """Format validation result as a human-readable report."""
    lines = []

    score = result.get("score", 0)
    max_score = result.get("max_score", 130)
    rating = result.get("rating", "")
    status = result.get("status", "")
    tool = result.get("tool", "unknown")

    lines.append("=" * 60)
    lines.append("  MCP Pre-Flight Validation Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Tool:   {tool}")
    lines.append(f"  Score:  {score}/{max_score}")
    lines.append(f"  Rating: {rating}")
    lines.append(f"  Status: {status}")
    lines.append("")

    # Category breakdown
    categories = result.get("categories", {})
    if categories:
        lines.append("  Category Breakdown:")
        lines.append("  " + "-" * 56)
        for cat_name, cat_data in categories.items():
            cat_score = cat_data.get("score", 0)
            cat_max = cat_data.get("max", 0)
            pct = (cat_score / cat_max * 100) if cat_max > 0 else 0
            bar_len = int(pct / 5)
            bar = "#" * bar_len + "." * (20 - bar_len)
            marker = "OK" if pct >= 80 else "!!" if pct >= 60 else "XX"
            lines.append(
                f"  [{marker}] {cat_name:<22s} {cat_score:>3d}/{cat_max:<3d} "
                f"[{bar}] {pct:.0f}%"
            )
        lines.append("")

    # Issues
    issues = result.get("issues", [])
    if issues:
        lines.append("  Issues:")
        lines.append("  " + "-" * 56)
        for issue in issues[:15]:
            severity = issue.get("severity", "warning")
            icon = "ERR" if severity == "error" else "WRN"
            category = issue.get("category", "General")
            message = issue.get("message", "Unknown issue")
            points = issue.get("points", 0)
            lines.append(f"  [{icon}] (-{points}) {message}")
        if len(issues) > 15:
            lines.append(f"  ... and {len(issues) - 15} more issues")
        lines.append("")

    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        lines.append("  Recommendations:")
        lines.append("  " + "-" * 56)
        for rec in recommendations[:8]:
            lines.append(f"  -> {rec}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


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
        elif args[i] == "--help" or args[i] == "-h":
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

    # Exit code: 0 if passed, 1 if blocked
    if result.get("score", 0) < 78:
        sys.exit(1)


if __name__ == "__main__":
    main()
