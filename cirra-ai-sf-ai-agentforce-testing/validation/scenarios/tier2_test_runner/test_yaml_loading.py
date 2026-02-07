"""
Tier 2 — load_scenarios() unit tests.

Tests YAML loading: valid file, missing file, and empty file edge cases.
"""

import pytest

from multi_turn_test_runner import load_scenarios


@pytest.mark.tier2
@pytest.mark.offline
def test_load_valid_yaml(tmp_path):
    """Valid YAML with scenarios key returns the expected structure."""
    yaml_content = """\
scenarios:
  - name: greet_and_ask
    description: Basic greeting flow
    pattern: topic_re_matching
    turns:
      - user: "Hello"
        expect:
          response_not_empty: true
      - user: "What is my order status?"
        expect:
          response_contains: "order"
"""
    yaml_file = tmp_path / "test_scenarios.yaml"
    yaml_file.write_text(yaml_content)

    data = load_scenarios(str(yaml_file))
    assert isinstance(data, dict)
    assert "scenarios" in data
    assert len(data["scenarios"]) == 1
    assert data["scenarios"][0]["name"] == "greet_and_ask"
    assert len(data["scenarios"][0]["turns"]) == 2


@pytest.mark.tier2
@pytest.mark.offline
def test_load_file_not_found():
    """Non-existent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_scenarios("/tmp/this_file_does_not_exist_12345.yaml")


@pytest.mark.tier2
@pytest.mark.offline
def test_load_empty_file(tmp_path):
    """Empty YAML file returns None (yaml.safe_load of empty string)."""
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("")

    result = load_scenarios(str(yaml_file))
    assert result is None
