#!/usr/bin/env python3
"""
Validation Scoring Runner for sf-ai-agentforce-testing.

Runs pytest per-tier, collects results, and computes a weighted score.

Usage:
    python3 validation/scripts/run_validation.py --offline
    python3 validation/scripts/run_validation.py --tier T1
    python3 validation/scripts/run_validation.py --json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Try Rich for pretty output, fall back to plain text
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


VALIDATION_DIR = Path(__file__).parent.parent
SCENARIO_DIR = VALIDATION_DIR / "scenarios"
REGISTRY_PATH = VALIDATION_DIR / "scenario_registry.json"


def load_registry() -> dict:
    """Load scenario_registry.json."""
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def run_tier(
    tier_id: str,
    tier_config: dict,
    offline: bool = False,
    verbose: bool = False,
    extra_args: list[str] = None,
) -> dict:
    """
    Run pytest for a single tier and collect results.

    Returns dict with passed, failed, skipped, total, errors, score.
    """
    marker = tier_config["marker"]
    tier_path = VALIDATION_DIR / tier_config["path"]

    if not tier_path.exists():
        return {
            "tier": tier_id,
            "name": tier_config["name"],
            "weight": tier_config["weight"],
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "score": 0.0,
            "status": "missing",
        }

    # Skip non-offline tiers when --offline
    if offline and not tier_config.get("offline", True):
        return {
            "tier": tier_id,
            "name": tier_config["name"],
            "weight": tier_config["weight"],
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "score": 0.0,
            "status": "skipped",
        }

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tier_path),
        "-m",
        marker,
        "--tb=short",
        "-q",
        "--no-header",
    ]

    if offline:
        cmd.append("--offline")

    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(VALIDATION_DIR),
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {
            "tier": tier_id,
            "name": tier_config["name"],
            "weight": tier_config["weight"],
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "score": 0.0,
            "status": "timeout",
        }

    if verbose:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

    # Parse pytest output for counts
    passed, failed, skipped, errors = _parse_pytest_output(result.stdout + result.stderr)
    total = passed + failed + errors

    # Calculate score
    weight = tier_config["weight"]
    score = (passed / total * weight) if total > 0 else 0.0

    return {
        "tier": tier_id,
        "name": tier_config["name"],
        "weight": weight,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "total": total,
        "score": round(score, 1),
        "status": "passed"
        if failed == 0 and errors == 0 and total > 0
        else ("failed" if failed > 0 or errors > 0 else "empty"),
    }


def _parse_pytest_output(output: str) -> tuple:
    """Parse pytest summary line for pass/fail/skip/error counts."""
    import re

    passed = failed = skipped = errors = 0

    # Match patterns like "5 passed", "2 failed", "1 skipped", "1 error"
    for line in output.split("\n"):
        line = line.strip()
        # Look for the summary line: "5 passed, 2 failed, 1 skipped in 1.23s"
        # or "5 passed in 1.23s"
        m = re.search(r"(\d+)\s+passed", line)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", line)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+)\s+skipped", line)
        if m:
            skipped = int(m.group(1))
        m = re.search(r"(\d+)\s+error", line)
        if m:
            errors = int(m.group(1))

    return passed, failed, skipped, errors


def render_rich(results: list[dict], total_score: float, thresholds: dict):
    """Render results using Rich tables."""
    console = Console()

    table = Table(title="Validation Results -- sf-ai-agentforce-testing", show_lines=True)
    table.add_column("Tier", style="bold", width=6)
    table.add_column("Name", width=28)
    table.add_column("Status", width=10)
    table.add_column("Tests", justify="right", width=14)
    table.add_column("Weight", justify="right", width=8)
    table.add_column("Score", justify="right", width=8)

    for r in results:
        status_icon = {
            "passed": "[green]PASS[/green]",
            "failed": "[red]FAIL[/red]",
            "skipped": "[yellow]SKIP[/yellow]",
            "missing": "[dim]N/A[/dim]",
            "timeout": "[red]TIME[/red]",
            "empty": "[dim]EMPTY[/dim]",
        }.get(r["status"], "?")

        tests_str = f"{r['passed']}/{r['total']}" if r["total"] > 0 else "--"
        score_str = f"{r['score']:.1f}" if r["total"] > 0 else "--"

        table.add_row(
            r["tier"],
            r["name"],
            status_icon,
            tests_str,
            str(r["weight"]),
            score_str,
        )

    console.print()
    console.print(table)
    console.print()

    # Overall score
    pass_threshold = thresholds.get("pass_threshold", 80)
    warn_threshold = thresholds.get("warn_threshold", 70)

    if total_score >= pass_threshold:
        style = "bold green"
        label = "PASS"
    elif total_score >= warn_threshold:
        style = "bold yellow"
        label = "WARN"
    else:
        style = "bold red"
        label = "FAIL"

    score_text = Text(f"Overall Score: {total_score:.1f} / 100  ({label})", style=style)
    console.print(Panel(score_text, border_style=style))
    console.print()


def render_plain(results: list[dict], total_score: float, thresholds: dict):
    """Render results as plain text (fallback when Rich not available)."""
    print()
    print("=" * 68)
    print("VALIDATION RESULTS -- sf-ai-agentforce-testing")
    print("=" * 68)
    print()
    print(f"{'Tier':<6} {'Name':<28} {'Status':<10} {'Tests':>8} {'Weight':>8} {'Score':>8}")
    print("-" * 68)

    for r in results:
        status = r["status"].upper()[:6]
        tests_str = f"{r['passed']}/{r['total']}" if r["total"] > 0 else "--"
        score_str = f"{r['score']:.1f}" if r["total"] > 0 else "--"
        print(
            f"{r['tier']:<6} {r['name']:<28} {status:<10} {tests_str:>8} {r['weight']:>8} {score_str:>8}"
        )

    print("-" * 68)

    pass_threshold = thresholds.get("pass_threshold", 80)
    warn_threshold = thresholds.get("warn_threshold", 70)

    if total_score >= pass_threshold:
        label = "PASS"
    elif total_score >= warn_threshold:
        label = "WARN"
    else:
        label = "FAIL"

    print(f"\n  Overall Score: {total_score:.1f} / 100  ({label})")
    print()


def main():
    parser = argparse.ArgumentParser(description="Validation scoring runner")
    parser.add_argument("--offline", action="store_true", help="Skip T5 live API tests")
    parser.add_argument("--tier", type=str, default=None, help="Run specific tier (T1, T2, ...)")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    parser.add_argument("--verbose", action="store_true", help="Show pytest output")

    args = parser.parse_args()

    registry = load_registry()
    tiers = registry["tiers"]

    # Filter tiers
    if args.tier:
        tier_key = args.tier.upper()
        if tier_key not in tiers:
            print(f"ERROR: Unknown tier '{args.tier}'. Available: {', '.join(tiers.keys())}")
            sys.exit(1)
        tiers = {tier_key: tiers[tier_key]}

    # Run each tier
    results = []
    for tier_id, tier_config in tiers.items():
        result = run_tier(
            tier_id=tier_id,
            tier_config=tier_config,
            offline=args.offline,
            verbose=args.verbose,
        )
        results.append(result)

    # Calculate total score
    total_score = sum(r["score"] for r in results)

    thresholds = {
        "pass_threshold": registry.get("pass_threshold", 80),
        "warn_threshold": registry.get("warn_threshold", 70),
    }

    # Output
    if args.json:
        output = {
            "total_score": round(total_score, 1),
            "pass_threshold": thresholds["pass_threshold"],
            "warn_threshold": thresholds["warn_threshold"],
            "status": "pass"
            if total_score >= thresholds["pass_threshold"]
            else ("warn" if total_score >= thresholds["warn_threshold"] else "fail"),
            "tiers": results,
        }
        print(json.dumps(output, indent=2))
    elif HAS_RICH:
        render_rich(results, total_score, thresholds)
    else:
        render_plain(results, total_score, thresholds)

    # Exit code
    if total_score >= thresholds["pass_threshold"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
