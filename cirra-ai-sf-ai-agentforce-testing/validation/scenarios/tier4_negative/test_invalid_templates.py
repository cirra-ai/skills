"""
Tier 4 — Invalid YAML Template Tests (2 points)

Tests that invalid or malformed YAML scenario files are handled correctly
by load_scenarios().

Tests:
    1. test_invalid_yaml_syntax — Broken YAML raises yaml.YAMLError
    2. test_empty_yaml_file — Empty file returns None from yaml.safe_load
    3. test_missing_scenarios_key — Valid YAML without "scenarios" key
"""

import pytest
import yaml

from multi_turn_test_runner import load_scenarios


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.tier4
@pytest.mark.offline
def test_invalid_yaml_syntax(tmp_path):
    """Broken YAML syntax raises yaml.YAMLError during load_scenarios()."""
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("key: [unclosed\nother: {also broken")

    with pytest.raises(yaml.YAMLError):
        load_scenarios(str(bad_file))


@pytest.mark.tier4
@pytest.mark.offline
def test_empty_yaml_file(tmp_path):
    """Empty YAML file causes yaml.safe_load to return None."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("")

    result = load_scenarios(str(empty_file))

    assert result is None


@pytest.mark.tier4
@pytest.mark.offline
def test_missing_scenarios_key(tmp_path):
    """Valid YAML without a 'scenarios' key returns a dict that lacks that key."""
    no_scenarios = tmp_path / "no_scenarios.yaml"
    no_scenarios.write_text("name: test\ndescription: No scenarios here\n")

    result = load_scenarios(str(no_scenarios))

    assert isinstance(result, dict)
    assert result.get("scenarios") is None
    assert result["name"] == "test"
