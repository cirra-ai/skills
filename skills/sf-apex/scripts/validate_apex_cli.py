#!/usr/bin/env python3
"""
Apex Validation script

Standalone on-demand validation of a local Apex file.
Runs the same 150-point + LLM anti-pattern pipeline as the PostToolUse hook
and prints a scored report to stdout.

Usage:
  python3 validate_apex_cli.py path/to/MyClass.cls [api_version]
  python3 validate_apex_cli.py path/to/AccountTrigger.trigger [api_version]

Pass the ApiVersion the code is (or will be) deployed at so version-sensitive
checks apply correctly (e.g. WITH SECURITY_ENFORCED: CRITICAL at 67.0+ where it
no longer compiles, informational at <= 66.0 where it still does).

Severity labels use the shared five-level scale defined in validate_apex.py
(CRITICAL > HIGH > MODERATE > LOW > INFO).

Exit codes:
  0  — validation passed (score >= 70% and no CRITICAL/HIGH findings)
  1  — validation failed (score < 70%, or any CRITICAL/HIGH finding) or file not found
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from validate_apex import (  # noqa: E402
    SEVERITY_ORDER,
    THRESHOLD_PCT,
    normalize_severity,
    severity_icon,
    severity_rank,
)

__all__ = ["SEVERITY_ORDER", "THRESHOLD_PCT", "run_validation", "main"]


def run_validation(file_path: str, api_version: float | None = None) -> dict:
    """Run full validation pipeline on an Apex file.

    Returns a dict with keys: success, output, score, max_score, pct.
    """
    output_parts = []

    try:
        from validate_apex import ApexValidator

        validator = ApexValidator(file_path, api_version=api_version)
        max_scores = dict(validator.max_scores)
        results = validator.validate()

        score = results.get("score", 0)
        max_score = results.get("max_score", 150)
        issues = list(results.get("issues", []))
        scores = results.get("scores", {})

        # LLM anti-pattern check
        try:
            from llm_pattern_validator import LLMPatternValidator

            llm_results = LLMPatternValidator(file_path).validate()
            for issue in llm_results.get("issues", []):
                issues.append(
                    {
                        "severity": normalize_severity(issue.get("severity"), "MODERATE"),
                        "category": issue.get("category", "llm_pattern"),
                        "message": issue.get("message", ""),
                        "line": issue.get("line", 0),
                        "fix": issue.get("fix", ""),
                        "source": "llm-validator",
                    }
                )
        except Exception:
            pass

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
        output_parts.append(f"🔍 Apex Validation: {os.path.basename(file_path)}")
        output_parts.append("═" * 60)
        output_parts.append(f"📊 Score: {score}/{max_score} {stars} {rating}")

        if scores:
            output_parts.append("")
            output_parts.append("📋 Category Breakdown:")
            for cat, cat_score in scores.items():
                max_cat = max_scores.get(cat, 0)
                if max_cat > 0:
                    icon = "✅" if cat_score == max_cat else ("⚠️" if cat_score >= max_cat * 0.7 else "❌")
                    diff = f" (-{max_cat - cat_score})" if cat_score < max_cat else ""
                    display = cat.replace("_", " ").title()
                    output_parts.append(f"   {icon} {display}: {cat_score}/{max_cat}{diff}")

        if issues:
            output_parts.append("")
            output_parts.append(f"⚠️  Issues Found ({len(issues)}):")
            issues.sort(key=lambda x: severity_rank(x.get("severity")))
            for issue in issues[:12]:
                sev = normalize_severity(issue.get("severity"), "INFO")
                icon = severity_icon(sev)
                source = f"[{issue['source']}] " if issue.get("source") else ""
                line_info = f"L{issue['line']}" if issue.get("line") else ""
                msg = issue["message"][:65] + "..." if len(issue["message"]) > 65 else issue["message"]
                output_parts.append(f"   {icon} {sev} {source}{line_info}: {msg}")
                if issue.get("fix"):
                    fix = issue["fix"][:55] + "..." if len(issue["fix"]) > 55 else issue["fix"]
                    output_parts.append(f"      💡 Fix: {fix}")
            if len(issues) > 12:
                output_parts.append(f"   ... and {len(issues) - 12} more issues")
        else:
            output_parts.append("")
            output_parts.append("✅ No issues found!")

        output_parts.append("═" * 60)
        blocking = [
            i for i in issues if normalize_severity(i.get("severity"), "INFO") in ("CRITICAL", "HIGH")
        ]
        if pct < THRESHOLD_PCT:
            output_parts.append(
                f"❌ BELOW THRESHOLD ({pct:.0f}% < {THRESHOLD_PCT}%) — fix issues before deploying"
            )
        elif blocking:
            output_parts.append(
                f"❌ {len(blocking)} CRITICAL/HIGH finding(s) — fix before deploying regardless of score"
            )
        else:
            output_parts.append("✅ PASSED — safe to deploy")

        return {
            "success": True,
            "output": "\n".join(output_parts),
            "score": score,
            "max_score": max_score,
            "pct": pct,
            "blocking_count": len(blocking),
            "passed": pct >= THRESHOLD_PCT and not blocking,
        }

    except ImportError as e:
        return {"success": False, "output": f"⚠️  Validator not available: {e}", "pct": 0}
    except Exception as e:
        return {"success": False, "output": f"⚠️  Validation error: {e}", "pct": 0}


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: validate_apex_cli.py <file.cls|file.trigger> [api_version]", file=sys.stderr)
        return 1

    file_path = args[0]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}", file=sys.stderr)
        return 1

    api_version = None
    if len(args) > 1:
        try:
            api_version = float(args[1])
        except ValueError:
            print(f"api_version must be a number, got: {args[1]}", file=sys.stderr)
            return 1

    result = run_validation(file_path, api_version=api_version)
    print(result["output"])
    return 0 if result.get("success") and result.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
