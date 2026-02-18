#!/usr/bin/env python3
"""
Flow Validation CLI

Standalone on-demand validation of a local Flow file.
Runs the 110-point EnhancedFlowValidator pipeline and prints a scored
report to stdout.

Usage:
  python3 validate_flow_cli.py path/to/Auto_Lead_Assignment.flow-meta.xml
  python3 validate_flow_cli.py path/to/MyFlow.xml

Exit codes:
  0  — validation passed (score >= 80%)
  1  — validation failed (score < 80%) or file not found
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

THRESHOLD_PCT = 80
MAX_SCORE = 110


def run_validation(file_path: str) -> dict:
    """Run full validation pipeline on a Flow file.

    Returns a dict with keys: success, output, score, max_score, pct.
    """
    output_parts = []

    try:
        from validate_flow import EnhancedFlowValidator

        validator = EnhancedFlowValidator(file_path)
        results = validator.validate()

        flow_name = results.get("flow_name", os.path.basename(file_path))
        score = results.get("overall_score", 0)
        max_score = MAX_SCORE
        categories = results.get("categories", {})

        # Collect all issues
        issues = []
        for cat_name, cat_data in categories.items():
            for issue in cat_data.get("issues", []):
                issues.append({
                    "severity": issue.get("severity", "INFO"),
                    "category": cat_name,
                    "message": issue.get("message", ""),
                    "line": issue.get("line", 0),
                    "fix": issue.get("fix", ""),
                })

        pct = (score / max_score * 100) if max_score > 0 else 0

        if pct >= 90:
            rating_stars, rating = 5, "Excellent"
        elif pct >= 75:
            rating_stars, rating = 4, "Very Good"
        elif pct >= 60:
            rating_stars, rating = 3, "Good"
        elif pct >= 45:
            rating_stars, rating = 2, "Needs Work"
        else:
            rating_stars, rating = 1, "Critical Issues"

        stars = "⭐" * rating_stars + "☆" * (5 - rating_stars)

        output_parts.append("")
        output_parts.append(f"🔄 Flow Validation: {flow_name}")
        output_parts.append("═" * 60)
        output_parts.append(f"📊 Score: {score}/{max_score} {stars} {rating}")

        if categories:
            output_parts.append("")
            output_parts.append("📋 Category Breakdown:")
            for cat_name, cat_data in categories.items():
                cat_score = cat_data.get("score", 0)
                cat_max = cat_data.get("max_score", 0)
                if cat_max > 0:
                    icon = "✅" if cat_score == cat_max else ("⚠️" if cat_score >= cat_max * 0.7 else "❌")
                    diff = f" (-{cat_max - cat_score})" if cat_score < cat_max else ""
                    display = cat_name.replace("_", " ").title()
                    output_parts.append(f"   {icon} {display}: {cat_score}/{cat_max}{diff}")

        if issues:
            output_parts.append("")
            output_parts.append(f"⚠️  Issues Found ({len(issues)}):")
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "WARNING": 3, "LOW": 4, "INFO": 5}
            issues.sort(key=lambda x: severity_order.get(x.get("severity", "INFO"), 5))
            for issue in issues[:12]:
                sev = issue.get("severity", "INFO")
                icon = {
                    "CRITICAL": "🔴", "HIGH": "🟠", "MODERATE": "🟡",
                    "WARNING": "🟡", "LOW": "🔵", "INFO": "⚪",
                }.get(sev, "⚪")
                line_info = f"L{issue['line']}" if issue.get("line") else ""
                msg = issue["message"][:65] + "..." if len(issue["message"]) > 65 else issue["message"]
                output_parts.append(f"   {icon} {sev} {line_info}: {msg}")
                if issue.get("fix"):
                    fix = issue["fix"][:55] + "..." if len(issue["fix"]) > 55 else issue["fix"]
                    output_parts.append(f"      💡 Fix: {fix}")
            if len(issues) > 12:
                output_parts.append(f"   ... and {len(issues) - 12} more issues")
        else:
            output_parts.append("")
            output_parts.append("✅ No issues found!")

        output_parts.append("═" * 60)
        if pct >= THRESHOLD_PCT:
            output_parts.append("✅ PASSED — safe to deploy")
        else:
            output_parts.append("❌ BELOW THRESHOLD — fix issues before deploying")

        return {"success": True, "output": "\n".join(output_parts), "score": score, "max_score": max_score, "pct": pct}

    except ImportError as e:
        return {"success": False, "output": f"⚠️  Validator not available: {e}", "pct": 0}
    except Exception as e:
        return {"success": False, "output": f"⚠️  Validation error: {e}", "pct": 0}


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: validate_flow_cli.py <file.flow-meta.xml|file.xml>", file=sys.stderr)
        return 1

    file_path = args[0]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}", file=sys.stderr)
        return 1

    result = run_validation(file_path)
    print(result["output"])
    return 0 if result.get("pct", 0) >= THRESHOLD_PCT else 1


if __name__ == "__main__":
    sys.exit(main())
