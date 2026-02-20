#!/usr/bin/env python3
"""
Unified PostToolUse dispatcher for file validation.

Runs AFTER Write or Edit tool completes and routes validation to
the correct domain validator based on file extension.

Routing:
  .cls / .trigger      -> Apex 150-point validator + LLM pattern checks
  .flow-meta.xml       -> Flow 110-point validator
  (other extensions)   -> silently pass through (future: LWC, Data)

This hook is ADVISORY - it provides feedback but does not block operations.
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
    # Ensure the module's directory is on sys.path so its own imports resolve
    mod_dir = os.path.dirname(module_path)
    original_path = sys.path[:]
    sys.path.insert(0, mod_dir)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = original_path
    return getattr(mod, class_name)


# ── Apex validation ─────────────────────────────────────────────────────


def _validate_apex(file_path: str) -> dict:
    """Run 150-point Apex validation + LLM pattern checks."""
    apex_dir = os.path.join(SCRIPT_DIR, "apex")
    output_parts = []

    try:
        ApexValidator = _load_class(
            os.path.join(apex_dir, "validate_apex.py"), "apex_validate_apex", "ApexValidator"
        )
        validator = ApexValidator(file_path)
        custom_results = validator.validate()

        custom_score = custom_results.get("score", 0)
        custom_max = custom_results.get("max_score", 150)
        custom_issues = custom_results.get("issues", [])
        custom_scores = custom_results.get("scores", {})

        # LLM pattern validation
        try:
            LLMPatternValidator = _load_class(
                os.path.join(apex_dir, "llm_pattern_validator.py"),
                "apex_llm_pattern_validator",
                "LLMPatternValidator",
            )
            llm_results = LLMPatternValidator(file_path).validate()
            for issue in llm_results.get("issues", []):
                custom_issues.append({
                    "severity": issue.get("severity", "WARNING"),
                    "category": issue.get("category", "llm_pattern"),
                    "message": issue.get("message", ""),
                    "line": issue.get("line", 0),
                    "fix": issue.get("fix", ""),
                    "source": "llm-validator",
                })
        except Exception:
            pass

        # Rating
        pct = (custom_score / custom_max * 100) if custom_max > 0 else 0
        rating_stars, rating = _rating(pct)
        stars = "⭐" * rating_stars + "☆" * (5 - rating_stars)

        output_parts.append("")
        output_parts.append(f"🔍 Apex Validation: {os.path.basename(file_path)}")
        output_parts.append("═" * 60)
        output_parts.append(f"📊 Score: {custom_score}/{custom_max} {stars} {rating}")

        # Category breakdown
        if custom_scores:
            output_parts.append("")
            output_parts.append("📋 Category Breakdown:")
            for cat, score in custom_scores.items():
                max_score = validator.scores.get(cat, 0)
                if max_score > 0:
                    icon = "✅" if score == max_score else ("⚠️" if score >= max_score * 0.7 else "❌")
                    diff = f" (-{max_score - score})" if score < max_score else ""
                    display_name = cat.replace("_", " ").title()
                    output_parts.append(f"   {icon} {display_name}: {score}/{max_score}{diff}")

        _format_issues(output_parts, custom_issues, show_source=True)
        output_parts.append("═" * 60)
        return {"continue": True, "output": "\n".join(output_parts)}

    except ImportError as e:
        return {"continue": True, "output": f"⚠️ Apex validator not available: {e}"}
    except Exception as e:
        return {"continue": True, "output": f"⚠️ Apex validation error: {e}"}


# ── Flow validation ─────────────────────────────────────────────────────


def _validate_flow(file_path: str) -> dict:
    """Run 110-point Flow validation."""
    flow_dir = os.path.join(SCRIPT_DIR, "flow")
    output_parts = []

    try:
        EnhancedFlowValidator = _load_class(
            os.path.join(flow_dir, "validate_flow.py"), "flow_validate_flow", "EnhancedFlowValidator"
        )
        validator = EnhancedFlowValidator(file_path)
        custom_results = validator.validate()

        flow_name = custom_results.get("flow_name", "Unknown")
        custom_score = custom_results.get("overall_score", 0)
        custom_max = 110

        # Collect issues from categories
        custom_issues = []
        category_scores = {}
        for cat_name, cat_data in custom_results.get("categories", {}).items():
            score = cat_data.get("score", 0)
            max_score = cat_data.get("max_score", 0)
            category_scores[cat_name] = (score, max_score)
            for issue in cat_data.get("issues", []):
                custom_issues.append({
                    "severity": issue.get("severity", "INFO"),
                    "message": issue.get("message", ""),
                    "category": cat_name,
                    "fix": issue.get("fix", ""),
                })

        # Rating
        pct = (custom_score / custom_max * 100) if custom_max > 0 else 0
        rating_stars, rating = _rating(pct)
        stars = "⭐" * rating_stars + "☆" * (5 - rating_stars)

        output_parts.append("")
        output_parts.append(f"🔄 Flow Validation: {flow_name}")
        output_parts.append("═" * 60)
        output_parts.append(f"📊 Score: {custom_score}/{custom_max} {stars} {rating}")

        # Category breakdown
        if category_scores:
            output_parts.append("")
            output_parts.append("📋 Category Breakdown:")
            for cat, (score, max_score) in category_scores.items():
                if max_score > 0:
                    icon = "✅" if score == max_score else ("⚠️" if score >= max_score * 0.7 else "❌")
                    diff = f" (-{max_score - score})" if score < max_score else ""
                    display_name = cat.replace("_", " ").title()
                    output_parts.append(f"   {icon} {display_name}: {score}/{max_score}{diff}")

        _format_issues(output_parts, custom_issues, show_source=False)
        output_parts.append("═" * 60)
        return {"continue": True, "output": "\n".join(output_parts)}

    except ImportError as e:
        return {"continue": True, "output": f"⚠️ Flow validator not available: {e}"}
    except Exception as e:
        return {"continue": True, "output": f"⚠️ Flow validation error: {e}"}


# ── Shared helpers ───────────────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "WARNING": 3, "LOW": 4, "INFO": 5}
SEVERITY_ICONS = {"CRITICAL": "🔴", "HIGH": "🟠", "MODERATE": "🟡", "WARNING": "🟡", "LOW": "🔵", "INFO": "⚪"}


def _rating(pct: float) -> tuple:
    """Return (star_count, label) for a percentage score."""
    if pct >= 90:
        return 5, "Excellent"
    if pct >= 75:
        return 4, "Very Good"
    if pct >= 60:
        return 3, "Good"
    if pct >= 45:
        return 2, "Needs Work"
    return 1, "Critical Issues"


def _format_issues(output_parts: list, issues: list, *, show_source: bool) -> None:
    """Append formatted issue list to output_parts."""
    if not issues:
        output_parts.append("")
        output_parts.append("✅ No issues found!")
        return

    issues.sort(key=lambda x: SEVERITY_ORDER.get(x.get("severity", "INFO"), 5))
    output_parts.append("")
    output_parts.append(f"⚠️ Issues Found ({len(issues)}):")

    for issue in issues[:12]:
        sev = issue.get("severity", "INFO")
        icon = SEVERITY_ICONS.get(sev, "⚪")
        source = f"[{issue['source']}] " if show_source and issue.get("source") else ""
        line_info = f"L{issue['line']}" if issue.get("line") else ""
        message = issue["message"][:65] + "..." if len(issue["message"]) > 65 else issue["message"]
        output_parts.append(f"   {icon} {sev} {source}{line_info}: {message}")

        if issue.get("fix"):
            fix = issue["fix"][:55] + "..." if len(issue["fix"]) > 55 else issue["fix"]
            output_parts.append(f"      💡 Fix: {fix}")

    if len(issues) > 12:
        output_parts.append(f"   ... and {len(issues) - 12} more issues")


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        print(json.dumps({"continue": True}))
        return 0

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Skip if the tool operation failed
    tool_response = hook_input.get("tool_response", {})
    if not tool_response.get("success", True):
        print(json.dumps({"continue": True}))
        return 0

    # Route by file extension
    result = {"continue": True}

    if file_path.endswith(".cls") or file_path.endswith(".trigger"):
        result = _validate_apex(file_path)
    elif file_path.endswith(".flow-meta.xml"):
        result = _validate_flow(file_path)
    # Future: .html/.js/.css -> LWC, .soql/.csv -> Data

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
