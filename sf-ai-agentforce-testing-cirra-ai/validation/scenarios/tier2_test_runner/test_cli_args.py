"""
Tier 2 — CLI argument parsing tests.

Tests the argparse setup in main() via subprocess invocation of
multi_turn_test_runner.py, verifying exit codes and flag recognition.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Path to the script under test
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "hooks" / "scripts"
RUNNER_SCRIPT = SCRIPTS_DIR / "multi_turn_test_runner.py"


def _run_cli(*args, env_override=None):
    """Run multi_turn_test_runner.py with the given args via subprocess."""
    import os

    env = os.environ.copy()
    # Clear env vars that could supply defaults and mask missing args
    env.pop("SF_AGENT_ID", None)
    env.pop("SF_MY_DOMAIN", None)
    env.pop("SF_CONSUMER_KEY", None)
    env.pop("SF_CONSUMER_SECRET", None)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [sys.executable, str(RUNNER_SCRIPT)] + list(args),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


@pytest.mark.tier2
@pytest.mark.offline
def test_missing_agent_id_exits_2(tmp_path):
    """Running without --agent-id (and no env var) should exit with code 2."""
    # Create a minimal valid scenario file so --scenarios doesn't fail first
    scenario_file = tmp_path / "dummy.yaml"
    scenario_file.write_text(
        "scenarios:\n  - name: test\n    turns:\n      - user: hi\n        expect:\n          response_not_empty: true\n"
    )
    result = _run_cli("--scenarios", str(scenario_file))
    assert result.returncode == 2


@pytest.mark.tier2
@pytest.mark.offline
def test_missing_scenarios_exits_2():
    """Running without --scenarios should exit with code 2 (argparse error)."""
    result = _run_cli("--agent-id", "0XxRM0000004ABC")
    assert result.returncode == 2


@pytest.mark.tier2
@pytest.mark.offline
def test_nonexistent_scenario_file_exits_2():
    """Running with a non-existent scenario file should exit with code 2."""
    result = _run_cli(
        "--agent-id",
        "0XxRM0000004ABC",
        "--scenarios",
        "/tmp/nonexistent_scenario_12345.yaml",
    )
    assert result.returncode == 2


@pytest.mark.tier2
@pytest.mark.offline
def test_help_flag_exits_0():
    """Running with --help should exit with code 0."""
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "Multi-Turn Agent Test Runner" in result.stdout


@pytest.mark.tier2
@pytest.mark.offline
def test_var_flag_format():
    """--var flag should be recognized in the help text."""
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "--var" in result.stdout


@pytest.mark.tier2
@pytest.mark.offline
def test_json_only_flag():
    """--json-only flag should be recognized in the help text."""
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "--json-only" in result.stdout
